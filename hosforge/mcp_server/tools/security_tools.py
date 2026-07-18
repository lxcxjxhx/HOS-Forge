"""
HOS MCP Server — 安全工具注册层。

将 HOS-Forge 所有能力注册为 MCP 工具端点。
每个 tool 是一个可以被 MCP 客户端调用的函数。
"""

from __future__ import annotations

import logging
from typing import Any

from fastmcp import FastMCP

logger = logging.getLogger(__name__)


def register_tools(app: FastMCP) -> None:
    """
    注册所有 HOS-Forge MCP 工具到 FastMCP 服务器。

    包括:
        - 扫描类工具 (Nmap/Nuclei/Semgrep/Burp)
        - 知识库工具 (CVE/CWE/vuln_explain/RAG)
        - 渗透测试工具 (pentest/audit/fix)
        - 报告工具 (HTML/reality check)
        - 桥接工具 (外部MCP发现/连接/路由)
        - 编排工具 (工作流执行)

    Args:
        app: FastMCP 应用实例
    """
    _register_scan_tools(app)
    _register_knowledge_tools(app)
    _register_pentest_tools(app)
    _register_report_tools(app)
    _register_bridge_tools(app)
    _register_orchestrator_tools(app)

    logger.info('Registered all HOS-Forge MCP tools (native=%d, bridge=%d)',
                12, 7)


def _register_scan_tools(app: FastMCP) -> None:
    """注册扫描类工具"""

    @app.tool(description='🔍 Nmap 端口扫描 — 扫描目标主机的开放端口和服务')
    async def hos_nmap_scan(
        target: str,
        ports: str = '1-1024',
        scan_type: str = 'tcp_syn',
        service_detection: bool = True,
    ) -> dict[str, Any]:
        """
        Nmap 端口扫描。

        Args:
            target: 目标 IP/域名 (如 "example.com")
            ports: 端口范围 (如 "22,80,443" 或 "1-65535")
            scan_type: 扫描类型 (tcp_syn/tcp_connect/udp/comprehensive)
            service_detection: 是否检测服务版本

        Returns:
            dict: 扫描结果 (开放端口/服务/版本)
        """
        from hosforge.security_tools import NmapTool

        tool = NmapTool()
        result = await tool.run(
            target,
            ports=ports,
            scan_type=scan_type,
            service_detection=service_detection,
        )
        return result.to_dict()

    @app.tool(description='🔬 Semgrep SAST 代码审计 — 对源代码进行安全扫描')
    async def hos_semgrep_scan(
        target: str,
        rules: list[str] | None = None,
        languages: list[str] | None = None,
        severity: str = 'info',
    ) -> dict[str, Any]:
        """Semgrep 代码安全扫描"""
        from hosforge.security_tools import SemgrepTool

        tool = SemgrepTool()
        result = await tool.run(
            target,
            rules=rules or ['p/default'],
            languages=languages or [],
            severity=severity,
        )
        return result.to_dict()

    @app.tool(description='📡 Nuclei 漏洞扫描 — 基于模板的自动化漏洞检测')
    async def hos_nuclei_scan(
        target: str,
        tags: list[str] | None = None,
        severity: str = 'low',
    ) -> dict[str, Any]:
        """Nuclei 漏洞扫描"""
        from hosforge.security_tools import NucleiTool

        tool = NucleiTool()
        result = await tool.run(
            target,
            tags=tags or ['cve', 'misconfiguration'],
            severity=severity,
        )
        return result.to_dict()

    @app.tool(description='🛡️ Burp Suite 集成 — 通过 Burp API 执行 Web 安全扫描')
    async def hos_burp_scan(
        target: str,
        action: str = 'scan',
        scan_speed: str = 'medium',
    ) -> dict[str, Any]:
        """Burp Suite 扫描"""
        from hosforge.security_tools import BurpTool

        tool = BurpTool()
        result = await tool.run(target, action=action, scan_speed=scan_speed)
        return result.to_dict()


def _register_knowledge_tools(app: FastMCP) -> None:
    """注册知识库类工具"""

    @app.tool(description='📖 CVE 查询 — 查询漏洞详情、CVSS 评分、CWE 关联')
    async def hos_cve_query(
        cve_id: str = '',
        keyword: str = '',
        severity: str = '',
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        查询 CVE 漏洞信息。
        """
        from hosforge.knowledge import LocalKnowledgeBase

        kb = LocalKnowledgeBase()
        if cve_id:
            cve = await kb.get_cve(cve_id)
            return [cve.to_dict()] if cve else []

        results = await kb.search_cve(keyword=keyword, severity=severity, limit=limit)
        return [r.to_dict() for r in results]

    @app.tool(description='📚 CWE 查询 — 查询缺陷分类、缓解措施')
    async def hos_cwe_query(
        cwe_id: str = '',
        keyword: str = '',
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """查询 CWE 缺陷分类"""
        from hosforge.knowledge import LocalKnowledgeBase

        kb = LocalKnowledgeBase()
        if cwe_id:
            cwe = await kb.get_cwe(cwe_id)
            return [cwe.to_dict()] if cwe else []

        results = await kb.search_cwe(keyword=keyword, limit=limit)
        return [r.to_dict() for r in results]

    @app.tool(description='💡 漏洞解释 — 结合 CVE/CWE/代码上下文解释漏洞原理')
    async def hos_vuln_explain(
        cwe_id: str = '',
        cve_id: str = '',
        code_context: str = '',
    ) -> str:
        """解释漏洞原理"""
        from hosforge.knowledge import LocalKnowledgeBase

        kb = LocalKnowledgeBase()
        return await kb.explain_vulnerability(
            cwe_id=cwe_id,
            cve_id=cve_id,
            code_context=code_context,
        )

    @app.tool(description='🏷️ RAG 知识打标 — 对安全知识条目进行自动分类和标签提取')
    async def hos_rag_tag(
        content: str,
        source: str = 'custom',
    ) -> dict[str, Any]:
        """
        对安全知识内容进行 RAG 打标。
        """
        from hosforge.model_optimizer import SecurityRAGTagger

        tagger = SecurityRAGTagger()
        chunk = await tagger.tag_cve_entry(
            cve_id='manual',
            description=content,
        )
        return {
            'tags': chunk.tags,
            'confidence': chunk.confidence,
            'source': source,
        }


def _register_pentest_tools(app: FastMCP) -> None:
    """注册渗透测试类工具"""

    @app.tool(description='🎯 渗透测试执行 — 启动完整 PTES 流程渗透测试')
    async def hos_pentest_run(
        target: str,
        authorized: bool = False,
        fast_mode: bool = False,
        skip_exploit: bool = False,
    ) -> dict[str, Any]:
        """
        执行渗透测试。

        Args:
            target: 目标 IP/域名
            authorized: 是否已获得授权
            fast_mode: 快速模式 (仅扫常见端口)
            skip_exploit: 跳过利用验证
        """
        from hosforge.security_agents import AttackAgent

        agent = AttackAgent()
        report = await agent.run_pentest(
            PentestTarget(host=target, scope_authorized=authorized),
            skip_exploit=skip_exploit or not authorized,
        )
        return report.to_dict()

    @app.tool(description='⚡ 一键安全审计 — 自动审计目标代码/项目/网络')
    async def hos_security_audit(
        target: str,
        audit_type: str = 'code',
        depth: str = 'quick',
    ) -> dict[str, Any]:
        """
        执行安全审计。

        Args:
            target: 审计目标 (代码路径/项目目录/URL)
            audit_type: 审计类型 (code/network/web)
            depth: 深度 (quick/full)
        """
        from hosforge.security_agents import AuditAgent

        agent = AuditAgent()
        finding = await agent.analyze(target, mode=depth)
        return finding.to_dict()

    @app.tool(description='🔧 安全修复建议 — 对发现的漏洞生成修复代码')
    async def hos_fix_vulnerability(
        vuln_name: str,
        cwe_id: str = '',
        code_snippet: str = '',
    ) -> str:
        """生成漏洞修复代码"""
        from hosforge.security_agents import DefenseAgent, SecurityVulnerability, Severity

        agent = DefenseAgent()
        vuln = SecurityVulnerability(
            name=vuln_name,
            cwe_id=cwe_id,
            code_snippet=code_snippet,
            severity=Severity.HIGH,
        )
        return await agent.fix(vuln)


def _register_report_tools(app: FastMCP) -> None:
    """注册报告类工具"""

    @app.tool(description='📄 安全报告生成 — 生成固定格式 HTML 安全报告')
    async def hos_report_generate(
        title: str = 'HOS-Forge Security Report',
        target: str = '',
        risk_score: int = 0,
        vulnerabilities: list[dict[str, Any]] | None = None,
        recommendations: list[str] | None = None,
        executive_summary: str = '',
    ) -> str:
        """
        生成 HTML 安全报告。

        Args:
            title: 报告标题
            target: 报告目标
            risk_score: 风险评分 (0-100)
            vulnerabilities: 漏洞列表 [{
                "name": str, "severity": str,
                "description": str, "cwe_id": str, "cve_id": str
            }]
            recommendations: 修复建议列表
            executive_summary: 执行摘要

        Returns:
            str: 完整 HTML 报告 (固定格式,可直接保存/转发)
        """
        from hosforge.reporter import SecurityHtmlReporter, ReportData, ReportMetadata, VulnerabilityEntry

        vulns = []
        for v in (vulnerabilities or []):
            vulns.append(VulnerabilityEntry(
                name=v.get('name', 'Unknown'),
                severity=v.get('severity', 'medium'),
                description=v.get('description', ''),
                cwe_id=v.get('cwe_id', ''),
                cve_id=v.get('cve_id', ''),
                remediation=v.get('remediation', ''),
                affected_component=v.get('affected_component', target),
            ))

        data = ReportData(
            metadata=ReportMetadata(
                title=title,
                target=target,
                report_type='scan',
            ),
            executive_summary=executive_summary,
            risk_score=risk_score,
            vulnerabilities=vulns,
            recommendations=recommendations or [],
        )

        reporter = SecurityHtmlReporter()
        return reporter.generate(data)




def _register_bridge_tools(app: FastMCP) -> None:
    """注册桥接类工具 — 外部 MCP 服务发现与调用"""

    @app.tool(description='🔌 MCP 服务发现 — 自动检测系统中已安装的外部安全 MCP 服务')
    async def hos_mcp_discover() -> list[dict[str, Any]]:
        """
        扫描系统，自动发现可用的外部安全 MCP 服务。

        检测来源:
            - PATH 中的 MCP 可执行文件
            - Docker 容器中的 MCP 服务
            - 环境变量配置的 MCP 端点
            - 常用 MCP 端口
            - Claude Desktop 配置

        Returns:
            list[dict]: 发现的 MCP 服务列表
        """
        from hosforge.mcp_server.bridge.discovery import MCPDiscoveryEngine

        engine = MCPDiscoveryEngine()
        services = await engine.discover_all()
        return [s.to_dict() for s in services]

    @app.tool(description='🔗 MCP 服务连接 — 连接到指定的外部 MCP 服务')
    async def hos_mcp_connect(
        service_name: str,
    ) -> dict[str, Any]:
        """
        连接到外部安全 MCP 服务。

        Args:
            service_name: 服务名称 (burp-mcp / mcp-security-hub / pentest-mcp)

        Returns:
            dict: 连接结果
        """
        from hosforge.mcp_server.bridge.connectors.burp import BurpConnector
        from hosforge.mcp_server.bridge.connectors.security_hub import SecurityHubConnector

        connectors = {
            'burp-mcp': BurpConnector,
            'mcp-security-hub': SecurityHubConnector,
        }

        connector_cls = connectors.get(service_name)
        if not connector_cls:
            return {'success': False, 'error': f'Unknown service: {service_name}'}

        connector = connector_cls()
        ok = await connector.connect()
        return {
            'success': ok,
            'service': service_name,
            'status': 'connected' if ok else 'failed',
        }

    @app.tool(description='🌉 Burp MCP 桥接 — 通过 Burp Suite MCP 获取代理历史和扫描结果')
    async def hos_burp_bridge(
        action: str = 'proxy_history',
        target: str = '',
        limit: int = 20,
    ) -> dict[str, Any]:
        """
        桥接 Burp Suite MCP 服务。

        Args:
            action: proxy_history | start_scan | analyze_request
            target: 目标 URL (扫描/分析时使用)
            limit: 历史记录条数

        Returns:
            dict: Burp 操作结果
        """
        from hosforge.mcp_server.bridge.connectors.burp import BurpConnector

        connector = BurpConnector()
        if not await connector.connect():
            return {'success': False, 'error': 'Burp MCP not available'}

        try:
            if action == 'proxy_history':
                history = await connector.get_proxy_history(limit=limit)
                return {'success': True, 'action': 'proxy_history', 'messages': history}
            elif action == 'start_scan' and target:
                scan = await connector.start_scan(target)
                return {'success': True, 'action': 'start_scan', 'scan': scan}
            elif action == 'analyze_request' and target:
                result = await connector.analyze_request(target)
                return {'success': True, 'action': 'analyze_request', 'result': result}
            else:
                return {'success': False, 'error': f'Invalid action: {action}'}
        finally:
            await connector.disconnect()

    @app.tool(description='🧩 Security Hub 桥接 — 通过 mcp-security-hub 调用安全工具集合')
    async def hos_security_hub_bridge(
        tool: str = 'nmap',
        target: str = '',
        **kwargs,
    ) -> dict[str, Any]:
        """
        桥接 FuzzingLabs mcp-security-hub 服务。

        Args:
            tool: 工具名 (nmap/nuclei_scan/sqlmap_scan/cve_search/subfinder/ghidra_analyze)
            target: 目标
            **kwargs: 工具特定参数

        Returns:
            dict: 工具执行结果
        """
        from hosforge.mcp_server.bridge.connectors.security_hub import SecurityHubConnector

        hub = SecurityHubConnector()
        if not await hub.connect():
            return {'success': False, 'error': 'mcp-security-hub not available'}

        try:
            result = await hub._call(tool, {'target': target, **kwargs})
            return {'success': True, 'tool': tool, 'result': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            await hub.disconnect()


def _register_orchestrator_tools(app: FastMCP) -> None:
    """注册编排类工具 — 跨 MCP 工作流"""

    @app.tool(description='📋 工作流模板列表 — 列出所有可用的渗透测试工作流模板')
    async def hos_workflow_templates() -> dict[str, Any]:
        """列出所有预定义的工作流模板"""
        from hosforge.mcp_server.orchestrator import MCPOrchestrator

        return MCPOrchestrator.list_templates()

    @app.tool(description='⚡ 执行安全工作流 — 按模板自动编排多步骤安全测试')
    async def hos_workflow_run(
        template: str = 'quick_recon',
        target: str = '',
        auto_discover: bool = True,
    ) -> dict[str, Any]:
        """
        执行预定义的安全工作流。

        Args:
            template: 工作流模板 (quick_recon/web_audit/full_pentest)
            target: 目标域名/IP
            auto_discover: 是否自动发现可用 MCP 服务

        Returns:
            dict: 工作流执行结果
        """
        from hosforge.mcp_server.orchestrator import MCPOrchestrator

        orchestrator = MCPOrchestrator()

        if auto_discover:
            await orchestrator.discover_services()
            await orchestrator.connect_all()

        result = await orchestrator.run_pipeline(
            template_name=template,
            target=target,
        )
        return result.to_dict()

    @app.tool(description='🧪 并行安全测试 — 同时执行多个独立安全测试任务')
    async def hos_parallel_scan(
        target: str = '',
        scans: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        并行执行多个安全扫描。

        Args:
            target: 目标 IP/域名
            scans: 扫描类型列表 (默认: ["nmap", "nuclei", "subfinder"])

        Returns:
            dict: 各扫描结果
        """
        from hosforge.mcp_server.orchestrator import MCPOrchestrator

        scans = scans or ['nmap', 'nuclei', 'subfinder']
        orchestrator = MCPOrchestrator()
        await orchestrator.discover_services()
        await orchestrator.connect_all()

        tasks = [
            {'name': s, 'service': 'security-hub', 'tool': s, 'args': {'target': target}}
            for s in scans
        ]
        results = await orchestrator.run_parallel(tasks)
        return results


async def _call_native_tool(tool: str, args: dict[str, Any]) -> Any:
    """
    供 Orchestrator 调用的原生工具路由。
    将工具名映射到对应的实现函数。
    """
    _tool_map = {
        'nmap_scan': _run_nmap,
        'semgrep_scan': _run_semgrep,
        'nuclei_scan': _run_nuclei,
        'report_generate': _run_report,
        'cve_query': _run_cve_query,
    }

    handler = _tool_map.get(tool)
    if not handler:
        raise ValueError(f'Unknown native tool: {tool}')
    return await handler(**args)


async def _run_nmap(target: str = '', ports: str = '1-1024', **kw) -> dict[str, Any]:
    from hosforge.security_tools import NmapTool
    tool = NmapTool()
    result = await tool.run(target, ports=ports, **kw)
    return result.to_dict()


async def _run_semgrep(target: str = '', rules: list[str] | None = None, **kw) -> dict[str, Any]:
    from hosforge.security_tools import SemgrepTool
    tool = SemgrepTool()
    result = await tool.run(target, rules=rules or ['p/default'], **kw)
    return result.to_dict()


async def _run_nuclei(target: str = '', tags: list[str] | None = None, **kw) -> dict[str, Any]:
    from hosforge.security_tools import NucleiTool
    tool = NucleiTool()
    result = await tool.run(target, tags=tags or ['cve'], **kw)
    return result.to_dict()


async def _run_report(
    title: str = 'Security Report',
    target: str = '',
    risk_score: int = 0,
    vulnerabilities: list | None = None,
    **kw,
) -> str:
    from hosforge.reporter import SecurityHtmlReporter, ReportData, ReportMetadata, VulnerabilityEntry
    vulns = [
        VulnerabilityEntry(
            name=v.get('name', ''),
            severity=v.get('severity', 'medium'),
            description=v.get('description', ''),
        )
        for v in (vulnerabilities or [])
    ]
    data = ReportData(
        metadata=ReportMetadata(title=title, target=target),
        risk_score=risk_score,
        vulnerabilities=vulns,
    )
    reporter = SecurityHtmlReporter()
    return reporter.generate(data)


async def _run_cve_query(cve_id: str = '', keyword: str = '', **kw) -> list[dict[str, Any]]:
    from hosforge.knowledge import LocalKnowledgeBase
    kb = LocalKnowledgeBase()
    if cve_id:
        cve = await kb.get_cve(cve_id)
        return [cve.to_dict()] if cve else []
    results = await kb.search_cve(keyword=keyword, **kw)
    return [r.to_dict() for r in results]


# 辅助导入 (避免循环)
from hosforge.security_agents import PentestTarget  # noqa: E402
