"""
HOS MCP Orchestrator — 跨 MCP 工作流编排与智能路由引擎。

支持：
    1. 编排链 (Pipeline) — 顺序执行多步安全测试
    2. 并行扫描 (Parallel) — 同时调用多个 MCP 工具
    3. 智能路由 — 根据需求自动选择最优 MCP 服务
    4. 结果聚合 — 多源结果合并去重

工作流示例:
    orchestrator = MCPOrchestrator()
    await orchestrator.discover_services()
    result = await orchestrator.run_pipeline("web_audit", target="example.com")
    # 自动: Nmap扫描 → Nuclei检测 → Burp分析 → 报告生成
"""

from __future__ import annotations

import asyncio
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from hosforge.mcp_server.bridge.connectors.burp import BurpConnector
from hosforge.mcp_server.bridge.connectors.security_hub import SecurityHubConnector
from hosforge.mcp_server.bridge.discovery import DiscoveredService, MCPDiscoveryEngine

logger = logging.getLogger(__name__)


def load_mcp_config() -> dict[str, Any]:
    """
    加载 MCP Server 配置。

    优先级：
    1. 环境变量 HOSFORGE_MCP_CONFIG 指定的配置文件路径
    2. 默认配置文件 hosforge/mcp_server/config.yaml
    3. 内置默认配置（向后兼容）

    Returns:
        dict[str, Any]: 配置字典
    """
    # 内置默认配置
    default_config = {
        "services": {
            "security_hub": {
                "name": "security-hub",
                "env_var": "HOSFORGE_SERVICE_SECURITY_HUB",
                "description": "安全中心服务 - 集成 nmap, nuclei, sqlmap 等工具",
            },
            "burp": {
                "name": "burp",
                "env_var": "HOSFORGE_SERVICE_BURP",
                "description": "Burp Suite 服务 - Web 应用安全测试",
            },
            "hos_forge": {
                "name": "hos-forge",
                "env_var": "HOSFORGE_SERVICE_HOS_FORGE",
                "description": "HOS-Forge 原生服务 - 代码审计和报告生成",
                "aliases": ["hos", "native"],
            },
        },
        "workflows": {
            "default_timeout": 120,
            "max_retries": 3,
        },
        "connectors": {
            "auto_discover": True,
            "connection_timeout": 30,
        },
    }

    # 尝试加载配置文件
    config_path = os.getenv("HOSFORGE_MCP_CONFIG")
    if not config_path:
        # 使用默认路径
        config_path = Path(__file__).parent / "config.yaml"
    else:
        config_path = Path(config_path)

    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                loaded_config = yaml.safe_load(f)
                if loaded_config:
                    # 合并配置（loaded_config 覆盖 default_config）
                    _merge_config(default_config, loaded_config)
                    logger.info("Loaded MCP config from: %s", config_path)
        except Exception as e:
            logger.warning("Failed to load MCP config from %s: %s", config_path, e)

    # 应用环境变量覆盖
    _apply_env_overrides(default_config)

    return default_config


def _merge_config(base: dict[str, Any], override: dict[str, Any]) -> None:
    """递归合并配置字典（override 覆盖 base）"""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _merge_config(base[key], value)
        else:
            base[key] = value


def _apply_env_overrides(config: dict[str, Any]) -> None:
    """应用环境变量覆盖服务名称"""
    services = config.get("services", {})
    for service_key, service_config in services.items():
        env_var = service_config.get("env_var")
        if env_var:
            env_value = os.getenv(env_var)
            if env_value:
                service_config["name"] = env_value
                logger.debug("Service %s overridden by env var %s=%s", service_key, env_var, env_value)


# 全局配置实例
_MCP_CONFIG: dict[str, Any] | None = None


def get_mcp_config() -> dict[str, Any]:
    """获取 MCP 配置（懒加载）"""
    global _MCP_CONFIG
    if _MCP_CONFIG is None:
        _MCP_CONFIG = load_mcp_config()
    return _MCP_CONFIG


def get_service_name(service_key: str) -> str:
    """
    获取服务名称（支持配置和环境变量覆盖）。

    Args:
        service_key: 服务键名（如 'security_hub', 'burp', 'hos_forge'）

    Returns:
        str: 实际服务名称
    """
    config = get_mcp_config()
    services = config.get("services", {})
    service_config = services.get(service_key, {})
    return service_config.get("name", service_key.replace("_", "-"))


@dataclass
class WorkflowStep:
    """工作流单个步骤"""

    step_id: str = ""
    name: str = ""
    service: str = ""  # 目标 MCP 服务
    tool: str = ""  # 调用的工具名
    args: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)  # 依赖的 step_id
    timeout: int = 120
    status: str = "pending"  # pending | running | completed | failed | skipped
    result: Any = None
    error: str = ""
    started_at: str = ""
    completed_at: str = ""


@dataclass
class WorkflowResult:
    """工作流执行结果"""

    workflow_id: str = ""
    name: str = ""
    status: str = "pending"
    steps: list[WorkflowStep] = field(default_factory=list)
    outputs: dict[str, Any] = field(default_factory=dict)
    summary: str = ""
    started_at: str = ""
    completed_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "status": self.status,
            "steps": [
                {
                    "step_id": s.step_id,
                    "name": s.name,
                    "service": s.service,
                    "tool": s.tool,
                    "status": s.status,
                    "error": s.error,
                }
                for s in self.steps
            ],
            "summary": self.summary,
        }


# ── 预定义工作流模板 ──────────────────────────────────────────
# 服务名称使用配置键 (security_hub / burp / hos_forge)，运行时通过 get_service_name() 解析
WORKFLOW_TEMPLATES: dict[str, dict[str, Any]] = {
    "web_audit": {
        "name": "Web 安全审计",
        "description": "从信息收集到漏洞验证的完整 Web 审计流程",
        "steps": [
            {
                "name": "端口扫描",
                "service": "security_hub",
                "tool": "nmap",
                "timeout": 300,
                "args": {"ports": "1-1024"},
            },
            {
                "name": "目录枚举",
                "service": "security_hub",
                "tool": "gobuster_dir",
                "depends_on": [0],
            },
            {
                "name": "漏洞扫描",
                "service": "security_hub",
                "tool": "nuclei_scan",
                "depends_on": [0],
            },
            {"name": "Burp 分析", "service": "burp", "tool": "proxy_history", "depends_on": [0]},
            {
                "name": "SQL 注入检测",
                "service": "security_hub",
                "tool": "sqlmap_scan",
                "depends_on": [0],
            },
        ],
    },
    "quick_recon": {
        "name": "快速侦察",
        "description": "快速信息收集 — 端口 + 子域名 + WHOIS",
        "steps": [
            {
                "name": "端口扫描",
                "service": "security_hub",
                "tool": "nmap",
                "timeout": 120,
                "args": {"ports": "80,443,22,3389,3306,6379"},
            },
            {"name": "子域名枚举", "service": "security_hub", "tool": "subfinder"},
            {"name": "WHOIS 查询", "service": "security_hub", "tool": "whois_lookup"},
        ],
    },
    "full_pentest": {
        "name": "完整渗透测试",
        "description": "全流程渗透测试 (PTES 标准)",
        "steps": [
            {
                "name": "信息收集",
                "service": "security_hub",
                "tool": "nmap",
                "timeout": 600,
                "args": {"ports": "1-65535"},
            },
            {
                "name": "漏洞扫描",
                "service": "security_hub",
                "tool": "nuclei_scan",
                "depends_on": [0],
            },
            {"name": "Web 扫描", "service": "burp", "tool": "start_scan", "depends_on": [0]},
            {
                "name": "代码审计",
                "service": "hos_forge",
                "tool": "semgrep_scan",
                "args": {"rules": ["p/security-audit"]},
            },
            {
                "name": "报告生成",
                "service": "hos_forge",
                "tool": "report_generate",
                "depends_on": [1, 2, 3],
            },
        ],
    },
}


class MCPOrchestrator:
    """
    MCP 工作流编排引擎。

    自动发现外部 MCP 服务，跨服务编排安全测试流程。
    """

    def __init__(self):
        self._discovery = MCPDiscoveryEngine()
        self._connectors: dict[str, Any] = {}
        self._workflows: dict[str, WorkflowResult] = {}

    # ── 服务管理 ───────────────────────────────────────────────

    async def discover_services(self) -> list[DiscoveredService]:
        """发现所有可用的 MCP 服务"""
        services = await self._discovery.discover_all()

        config = get_mcp_config()
        svc_configs = config.get("services", {})

        # 自动初始化标准连接器（基于配置的服务名称和别名）
        connector_classes: dict[str, Any] = {
            "burp": BurpConnector,
            "security_hub": SecurityHubConnector,
        }
        for svc_key, cls in connector_classes.items():
            svc_cfg = svc_configs.get(svc_key, {})
            configured_name = svc_cfg.get("name", svc_key.replace("_", "-"))
            aliases = svc_cfg.get("aliases", [])
            match_names = [configured_name.lower()] + [a.lower() for a in aliases]

            for svc in services:
                svc_lower = svc.name.lower()
                if any(m in svc_lower for m in match_names):
                    if svc_key not in self._connectors:
                        self._connectors[svc_key] = cls()
                    break

        return services

    async def connect_all(self) -> dict[str, bool]:
        """连接到所有已发现的 MCP 服务"""
        results: dict[str, bool] = {}
        for name, connector in self._connectors.items():
            try:
                ok = await connector.connect()
                results[name] = ok
                if ok:
                    logger.info("Connected: %s", name)
                else:
                    logger.warning("Failed to connect: %s", name)
            except Exception as e:
                results[name] = False
                logger.error("Connection error %s: %s", name, e)
        return results

    def register_connector(self, name: str, connector: Any) -> None:
        """手动注册连接器"""
        self._connectors[name] = connector

    # ── 工作流执行 ─────────────────────────────────────────────

    async def run_pipeline(
        self,
        template_name: str = "",
        steps: list[dict[str, Any]] | None = None,
        **shared_args,
    ) -> WorkflowResult:
        """
        运行工作流流水线。

        Args:
            template_name: 模板名称 (web_audit/quick_recon/full_pentest)
            steps: 自定义步骤列表 (覆盖模板)
            **shared_args: 共享参数 (注入到所有步骤)

        Returns:
            WorkflowResult: 工作流执行结果
        """
        # 加载模板
        if not steps and template_name:
            template = WORKFLOW_TEMPLATES.get(template_name)
            if not template:
                raise ValueError(f"Unknown workflow template: {template_name}")
            steps = template["steps"]
            workflow_name = template["name"]
        else:
            workflow_name = "custom"

        steps = steps or []
        workflow_id = f"wf-{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow().isoformat()

        result = WorkflowResult(
            workflow_id=workflow_id,
            name=workflow_name,
            started_at=now,
        )

        # 注入共享参数
        for step in steps:
            if shared_args.get("target"):
                step.setdefault("args", {})["target"] = shared_args["target"]

        # 构建步骤
        workflow_steps: list[WorkflowStep] = []
        for i, s in enumerate(steps):
            depends = [steps[d]["name"] for d in s.pop("depends_on", [])]
            workflow_steps.append(
                WorkflowStep(
                    step_id=f"{workflow_id}-s{i}",
                    name=s.get("name", f"step-{i}"),
                    service=s.get("service", ""),
                    tool=s.get("tool", ""),
                    args=s.get("args", {}),
                    depends_on=depends,
                    timeout=s.get("timeout", 120),
                )
            )
        result.steps = workflow_steps

        # 按依赖关系执行
        completed: dict[str, Any] = {}
        remaining: list[WorkflowStep] = list(workflow_steps)

        while remaining:
            batch: list[WorkflowStep] = []
            for step in list(remaining):
                deps_met = all(d in completed for d in step.depends_on)
                if deps_met:
                    batch.append(step)
                    remaining.remove(step)

            if not batch:
                # 死锁检测
                blocked = [s.name for s in remaining]
                logger.error("Workflow deadlock: steps %s waiting on unmet dependencies", blocked)
                for s in remaining:
                    s.status = "skipped"
                    s.error = f"Deadlock: unmet dependencies: {s.depends_on}"
                break

            # 并行执行本批步骤
            tasks = [self._execute_step(step) for step in batch]
            await asyncio.gather(*tasks)

            for step in batch:
                completed[step.name] = step.result

        # 汇总
        result.status = (
            "completed" if all(s.status == "completed" for s in workflow_steps) else "partial"
        )
        result.completed_at = datetime.utcnow().isoformat()
        result.outputs = completed
        result.summary = self._generate_summary(result)

        self._workflows[workflow_id] = result
        logger.info("Workflow %s completed: %s", workflow_id, result.status)
        return result

    async def run_parallel(
        self,
        tasks: list[dict[str, Any]],
        **shared_args,
    ) -> dict[str, Any]:
        """
        并行执行多个独立安全测试任务。

        Args:
            tasks: 任务列表 [{name, service, tool, args}]
            **shared_args: 共享参数

        Returns:
            dict[str, Any]: 各任务结果
        """
        for task in tasks:
            if shared_args.get("target"):
                task.setdefault("args", {})["target"] = shared_args["target"]

        async def run_task(task: dict) -> tuple[str, Any]:
            name = task.get("name", "task")
            try:
                result = await self._execute_tool_call(
                    task.get("service", ""),
                    task.get("tool", ""),
                    task.get("args", {}),
                )
                return name, result
            except Exception as e:
                return name, {"error": str(e)}

        results = await asyncio.gather(*[run_task(t) for t in tasks])
        return dict(results)

    async def _execute_step(self, step: WorkflowStep) -> None:
        """执行单个工作流步骤"""
        step.status = "running"
        step.started_at = datetime.utcnow().isoformat()
        logger.info("Step: %s (%s/%s)", step.name, step.service, step.tool)

        try:
            result = await asyncio.wait_for(
                self._execute_tool_call(step.service, step.tool, step.args),
                timeout=step.timeout,
            )
            step.result = result
            step.status = "completed"
        except asyncio.TimeoutError:
            step.status = "failed"
            step.error = f"Timeout after {step.timeout}s"
        except Exception as e:
            step.status = "failed"
            step.error = str(e)

        step.completed_at = datetime.utcnow().isoformat()

    def _resolve_service_key(self, service: str) -> str:
        """
        将服务名称（可能是配置键、配置名称或别名）规范化为配置键。

        解析顺序：
        1. 直接匹配配置键（如 'security_hub'）
        2. 匹配配置中的 name 字段（如 'security-hub' -> 'security_hub'）
        3. 匹配配置中的 aliases（如 'hos', 'native' -> 'hos_forge'）
        4. 原样返回（兼容未配置的自定义服务）
        """
        service_lower = service.lower()
        config = get_mcp_config()
        services_cfg = config.get("services", {})

        # 1. 直接匹配配置键
        if service_lower in services_cfg:
            return service_lower

        # 2. 匹配配置中的 name 字段
        for key, svc_cfg in services_cfg.items():
            if svc_cfg.get("name", "").lower() == service_lower:
                return key

        # 3. 匹配别名
        for key, svc_cfg in services_cfg.items():
            aliases = [a.lower() for a in svc_cfg.get("aliases", [])]
            if service_lower in aliases:
                return key

        # 4. 未匹配，原样返回
        return service_lower

    async def _execute_tool_call(
        self,
        service: str,
        tool: str,
        args: dict[str, Any],
    ) -> Any:
        """路由到正确的 MCP 服务执行工具调用（基于配置驱动的服务名称）"""
        service_key = self._resolve_service_key(service)

        # HOS-Forge 原生工具
        if service_key == "hos_forge":
            from hosforge.mcp_server.tools.security_tools import _call_native_tool

            return await _call_native_tool(tool, args)

        # Burp MCP
        if service_key == "burp" and "burp" in self._connectors:
            burp: BurpConnector = self._connectors["burp"]
            tool_map = {
                "proxy_history": burp.get_proxy_history,
                "analyze_request": burp.analyze_request,
                "start_scan": burp.start_scan,
                "repeater": burp.send_to_repeater,
            }
            handler = tool_map.get(tool)
            if handler:
                return await handler(**args)
            return await burp._adapter.call_tool(tool, args)

        # mcp-security-hub
        if service_key == "security_hub" and "security_hub" in self._connectors:
            hub: SecurityHubConnector = self._connectors["security_hub"]
            tool_map = {
                "nmap": hub.nmap_scan,
                "nuclei_scan": hub.nuclei_scan,
                "sqlmap_scan": hub.sqlmap_scan,
                "cve_search": hub.cve_search,
                "subfinder": hub.subdomain_enum,
                "gobuster_dir": hub.directory_bruteforce,
                "semgrep_scan": hub.semgrep_scan,
                "whois_lookup": lambda **kw: hub._call("whois_lookup", kw),
                "ghidra_analyze": hub.ghidra_analyze,
            }
            handler = tool_map.get(tool)
            if handler:
                return await handler(**args)
            return await hub._call(tool, args)

        raise ValueError(f"Unknown service: {service} (resolved key: {service_key})")

    # ── 工作流模板管理 ─────────────────────────────────────────

    @staticmethod
    def list_templates() -> dict[str, dict[str, Any]]:
        """列出所有可用的工作流模板"""
        return {
            name: {
                "name": t["name"],
                "description": t["description"],
                "step_count": len(t["steps"]),
                "steps": [s["name"] for s in t["steps"]],
            }
            for name, t in WORKFLOW_TEMPLATES.items()
        }

    @staticmethod
    def add_template(name: str, template: dict[str, Any]) -> None:
        """添加自定义工作流模板"""
        WORKFLOW_TEMPLATES[name] = template
        logger.info("Added workflow template: %s", name)

    # ── 辅助 ───────────────────────────────────────────────────

    def get_workflow(self, workflow_id: str) -> WorkflowResult | None:
        """获取工作流结果"""
        return self._workflows.get(workflow_id)

    def _generate_summary(self, result: WorkflowResult) -> str:
        """生成工作流摘要"""
        total = len(result.steps)
        completed = sum(1 for s in result.steps if s.status == "completed")
        failed = sum(1 for s in result.steps if s.status == "failed")
        skipped = sum(1 for s in result.steps if s.status == "skipped")

        parts = [
            f'工作流 "{result.name}" 执行完毕:',
            f"  共 {total} 步, {completed} 完成",
        ]
        if failed:
            parts.append(f"  {failed} 步失败")
        if skipped:
            parts.append(f"  {skipped} 步跳过")

        return "\n".join(parts)
