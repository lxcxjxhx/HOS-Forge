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
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from hosforge.mcp_server.bridge.discovery import MCPDiscoveryEngine, DiscoveredService
from hosforge.mcp_server.bridge.connectors.burp import BurpConnector
from hosforge.mcp_server.bridge.connectors.security_hub import SecurityHubConnector

logger = logging.getLogger(__name__)


@dataclass
class WorkflowStep:
    """工作流单个步骤"""
    step_id: str = ''
    name: str = ''
    service: str = ''           # 目标 MCP 服务
    tool: str = ''              # 调用的工具名
    args: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)  # 依赖的 step_id
    timeout: int = 120
    status: str = 'pending'     # pending | running | completed | failed | skipped
    result: Any = None
    error: str = ''
    started_at: str = ''
    completed_at: str = ''


@dataclass
class WorkflowResult:
    """工作流执行结果"""
    workflow_id: str = ''
    name: str = ''
    status: str = 'pending'
    steps: list[WorkflowStep] = field(default_factory=list)
    outputs: dict[str, Any] = field(default_factory=dict)
    summary: str = ''
    started_at: str = ''
    completed_at: str = ''

    def to_dict(self) -> dict[str, Any]:
        return {
            'workflow_id': self.workflow_id,
            'name': self.name,
            'status': self.status,
            'steps': [
                {
                    'step_id': s.step_id,
                    'name': s.name,
                    'service': s.service,
                    'tool': s.tool,
                    'status': s.status,
                    'error': s.error,
                }
                for s in self.steps
            ],
            'summary': self.summary,
        }


# ── 预定义工作流模板 ──────────────────────────────────────────
WORKFLOW_TEMPLATES: dict[str, dict[str, Any]] = {
    'web_audit': {
        'name': 'Web 安全审计',
        'description': '从信息收集到漏洞验证的完整 Web 审计流程',
        'steps': [
            {'name': '端口扫描', 'service': 'security-hub', 'tool': 'nmap',
             'timeout': 300, 'args': {'ports': '1-1024'}},
            {'name': '目录枚举', 'service': 'security-hub', 'tool': 'gobuster_dir',
             'depends_on': [0]},
            {'name': '漏洞扫描', 'service': 'security-hub', 'tool': 'nuclei_scan',
             'depends_on': [0]},
            {'name': 'Burp 分析', 'service': 'burp', 'tool': 'proxy_history',
             'depends_on': [0]},
            {'name': 'SQL 注入检测', 'service': 'security-hub', 'tool': 'sqlmap_scan',
             'depends_on': [0]},
        ],
    },
    'quick_recon': {
        'name': '快速侦察',
        'description': '快速信息收集 — 端口 + 子域名 + WHOIS',
        'steps': [
            {'name': '端口扫描', 'service': 'security-hub', 'tool': 'nmap',
             'timeout': 120, 'args': {'ports': '80,443,22,3389,3306,6379'}},
            {'name': '子域名枚举', 'service': 'security-hub', 'tool': 'subfinder'},
            {'name': 'WHOIS 查询', 'service': 'security-hub', 'tool': 'whois_lookup'},
        ],
    },
    'full_pentest': {
        'name': '完整渗透测试',
        'description': '全流程渗透测试 (PTES 标准)',
        'steps': [
            {'name': '信息收集', 'service': 'security-hub', 'tool': 'nmap',
             'timeout': 600, 'args': {'ports': '1-65535'}},
            {'name': '漏洞扫描', 'service': 'security-hub', 'tool': 'nuclei_scan',
             'depends_on': [0]},
            {'name': 'Web 扫描', 'service': 'burp', 'tool': 'start_scan',
             'depends_on': [0]},
            {'name': '代码审计', 'service': 'hos-forge', 'tool': 'semgrep_scan',
             'args': {'rules': ['p/security-audit']}},
            {'name': '报告生成', 'service': 'hos-forge', 'tool': 'report_generate',
             'depends_on': [1, 2, 3]},
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

        # 自动初始化标准连接器
        for svc in services:
            if 'burp' in svc.name.lower() and 'burp' not in self._connectors:
                self._connectors['burp'] = BurpConnector()
            if 'security-hub' in svc.name.lower() and 'security-hub' not in self._connectors:
                self._connectors['security-hub'] = SecurityHubConnector()

        return services

    async def connect_all(self) -> dict[str, bool]:
        """连接到所有已发现的 MCP 服务"""
        results: dict[str, bool] = {}
        for name, connector in self._connectors.items():
            try:
                ok = await connector.connect()
                results[name] = ok
                if ok:
                    logger.info('Connected: %s', name)
                else:
                    logger.warning('Failed to connect: %s', name)
            except Exception as e:
                results[name] = False
                logger.error('Connection error %s: %s', name, e)
        return results

    def register_connector(self, name: str, connector: Any) -> None:
        """手动注册连接器"""
        self._connectors[name] = connector

    # ── 工作流执行 ─────────────────────────────────────────────

    async def run_pipeline(
        self,
        template_name: str = '',
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
                raise ValueError(f'Unknown workflow template: {template_name}')
            steps = template['steps']
            workflow_name = template['name']
        else:
            workflow_name = 'custom'

        steps = steps or []
        workflow_id = f'wf-{uuid.uuid4().hex[:8]}'
        now = datetime.utcnow().isoformat()

        result = WorkflowResult(
            workflow_id=workflow_id,
            name=workflow_name,
            started_at=now,
        )

        # 注入共享参数
        for step in steps:
            if shared_args.get('target'):
                step.setdefault('args', {})['target'] = shared_args['target']

        # 构建步骤
        workflow_steps: list[WorkflowStep] = []
        for i, s in enumerate(steps):
            depends = [steps[d]['name'] for d in s.pop('depends_on', [])]
            workflow_steps.append(WorkflowStep(
                step_id=f'{workflow_id}-s{i}',
                name=s.get('name', f'step-{i}'),
                service=s.get('service', ''),
                tool=s.get('tool', ''),
                args=s.get('args', {}),
                depends_on=depends,
                timeout=s.get('timeout', 120),
            ))
        result.steps = workflow_steps

        # 按依赖关系执行
        completed: dict[str, Any] = {}
        remaining = list(workflow_steps)

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
                logger.error('Workflow deadlock: steps %s waiting on unmet dependencies', blocked)
                for s in remaining:
                    s.status = 'skipped'
                    s.error = f'Deadlock: unmet dependencies: {s.depends_on}'
                break

            # 并行执行本批步骤
            tasks = [self._execute_step(step) for step in batch]
            await asyncio.gather(*tasks)

            for step in batch:
                completed[step.name] = step.result

        # 汇总
        result.status = 'completed' if all(
            s.status == 'completed' for s in workflow_steps
        ) else 'partial'
        result.completed_at = datetime.utcnow().isoformat()
        result.outputs = completed
        result.summary = self._generate_summary(result)

        self._workflows[workflow_id] = result
        logger.info('Workflow %s completed: %s', workflow_id, result.status)
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
            if shared_args.get('target'):
                task.setdefault('args', {})['target'] = shared_args['target']

        async def run_task(task: dict) -> tuple[str, Any]:
            name = task.get('name', 'task')
            try:
                result = await self._execute_tool_call(
                    task.get('service', ''),
                    task.get('tool', ''),
                    task.get('args', {}),
                )
                return name, result
            except Exception as e:
                return name, {'error': str(e)}

        results = await asyncio.gather(*[run_task(t) for t in tasks])
        return dict(results)

    async def _execute_step(self, step: WorkflowStep) -> None:
        """执行单个工作流步骤"""
        step.status = 'running'
        step.started_at = datetime.utcnow().isoformat()
        logger.info('Step: %s (%s/%s)', step.name, step.service, step.tool)

        try:
            result = await asyncio.wait_for(
                self._execute_tool_call(step.service, step.tool, step.args),
                timeout=step.timeout,
            )
            step.result = result
            step.status = 'completed'
        except asyncio.TimeoutError:
            step.status = 'failed'
            step.error = f'Timeout after {step.timeout}s'
        except Exception as e:
            step.status = 'failed'
            step.error = str(e)

        step.completed_at = datetime.utcnow().isoformat()

    async def _execute_tool_call(
        self,
        service: str,
        tool: str,
        args: dict[str, Any],
    ) -> Any:
        """路由到正确的 MCP 服务执行工具调用"""
        service = service.lower()

        # HOS-Forge 原生工具
        if service in ('hos-forge', 'hos', 'native'):
            from hosforge.mcp_server.tools.security_tools import _call_native_tool
            return await _call_native_tool(tool, args)

        # Burp MCP
        if service == 'burp' and 'burp' in self._connectors:
            burp: BurpConnector = self._connectors['burp']
            tool_map = {
                'proxy_history': burp.get_proxy_history,
                'analyze_request': burp.analyze_request,
                'start_scan': burp.start_scan,
                'repeater': burp.send_to_repeater,
            }
            handler = tool_map.get(tool)
            if handler:
                return await handler(**args)
            return await burp._adapter.call_tool(tool, args)

        # mcp-security-hub
        if service == 'security-hub' and 'security-hub' in self._connectors:
            hub: SecurityHubConnector = self._connectors['security-hub']
            tool_map = {
                'nmap': hub.nmap_scan,
                'nuclei_scan': hub.nuclei_scan,
                'sqlmap_scan': hub.sqlmap_scan,
                'cve_search': hub.cve_search,
                'subfinder': hub.subdomain_enum,
                'gobuster_dir': hub.directory_bruteforce,
                'semgrep_scan': hub.semgrep_scan,
                'whois_lookup': lambda **kw: hub._call('whois_lookup', kw),
                'ghidra_analyze': hub.ghidra_analyze,
            }
            handler = tool_map.get(tool)
            if handler:
                return await handler(**args)
            return await hub._call(tool, args)

        raise ValueError(f'Unknown service: {service}')

    # ── 工作流模板管理 ─────────────────────────────────────────

    @staticmethod
    def list_templates() -> dict[str, dict[str, Any]]:
        """列出所有可用的工作流模板"""
        return {
            name: {
                'name': t['name'],
                'description': t['description'],
                'step_count': len(t['steps']),
                'steps': [s['name'] for s in t['steps']],
            }
            for name, t in WORKFLOW_TEMPLATES.items()
        }

    @staticmethod
    def add_template(name: str, template: dict[str, Any]) -> None:
        """添加自定义工作流模板"""
        WORKFLOW_TEMPLATES[name] = template
        logger.info('Added workflow template: %s', name)

    # ── 辅助 ───────────────────────────────────────────────────

    def get_workflow(self, workflow_id: str) -> WorkflowResult | None:
        """获取工作流结果"""
        return self._workflows.get(workflow_id)

    def _generate_summary(self, result: WorkflowResult) -> str:
        """生成工作流摘要"""
        total = len(result.steps)
        completed = sum(1 for s in result.steps if s.status == 'completed')
        failed = sum(1 for s in result.steps if s.status == 'failed')
        skipped = sum(1 for s in result.steps if s.status == 'skipped')

        parts = [
            f'工作流 "{result.name}" 执行完毕:',
            f'  共 {total} 步, {completed} 完成',
        ]
        if failed:
            parts.append(f'  {failed} 步失败')
        if skipped:
            parts.append(f'  {skipped} 步跳过')

        return '\n'.join(parts)
