"""
HOS MCP Server — 安全工具注册层。

将 HOS-Forge 所有能力注册为 MCP 工具端点。
每个 tool 是一个可以被 MCP 客户端调用的函数。

注意: FastMCP 限制:
    - description 参数不能包含 emoji
    - 函数参数不能使用 **kwargs
    - 所有参数必须有类型注解
"""

from __future__ import annotations

import logging
from typing import Any

from fastmcp import FastMCP

logger = logging.getLogger(__name__)


def register_tools(app: FastMCP) -> None:
    """
    注册所有 HOS-Forge MCP 工具到 FastMCP 服务器。

    Args:
        app: FastMCP 应用实例
    """
    _register_scan_tools(app)
    _register_knowledge_tools(app)
    _register_pentest_tools(app)
    _register_report_tools(app)
    _register_bridge_tools(app)
    _register_orchestrator_tools(app)

    logger.info('Registered all HOS-Forge MCP tools')


# ── 扫描类工具 ──────────────────────────────────────────────────

def _register_scan_tools(app: FastMCP) -> None:

    @app.tool(description='Nmap port scan - scan target host for open ports and services')
    async def hos_nmap_scan(
        target: str,
        ports: str = '1-1024',
        scan_type: str = 'tcp_syn',
        service_detection: bool = True,
    ) -> dict[str, Any]:
        """Nmap 端口扫描。target: IP/域名, ports: 端口范围, scan_type: tcp_syn/tcp_connect/udp"""
        from hosforge.security_tools import NmapTool
        tool = NmapTool()
        result = await tool.run(target, ports=ports, scan_type=scan_type, service_detection=service_detection)
        return result.to_dict()

    @app.tool(description='Semgrep SAST code audit - scan source code for security vulnerabilities')
    async def hos_semgrep_scan(
        target: str,
        rules: str = 'p/default',
        languages: str = '',
        severity: str = 'info',
    ) -> dict[str, Any]:
        """Semgrep 代码安全扫描。target: 路径, rules: 规则集, languages: 语言过滤"""
        from hosforge.security_tools import SemgrepTool
        tool = SemgrepTool()
        result = await tool.run(
            target,
            rules=[rules] if rules else ['p/default'],
            languages=[l.strip() for l in languages.split(',') if l.strip()] if languages else [],
            severity=severity,
        )
        return result.to_dict()

    @app.tool(description='Nuclei vulnerability scan - template-based automated vulnerability detection')
    async def hos_nuclei_scan(
        target: str,
        tags: str = 'cve,misconfiguration',
        severity: str = 'low',
    ) -> dict[str, Any]:
        """Nuclei 漏洞扫描。target: URL/IP, tags: 模板标签, severity: 最低严重级别"""
        from hosforge.security_tools import NucleiTool
        tool = NucleiTool()
        result = await tool.run(target, tags=[t.strip() for t in tags.split(',')], severity=severity)
        return result.to_dict()

    @app.tool(description='Burp Suite integration - execute web security scan via Burp API')
    async def hos_burp_scan(
        target: str,
        action: str = 'scan',
        scan_speed: str = 'medium',
    ) -> dict[str, Any]:
        """Burp Suite 扫描。target: URL, action: scan/proxy_history/report"""
        from hosforge.security_tools import BurpTool
        tool = BurpTool()
        result = await tool.run(target, action=action, scan_speed=scan_speed)
        return result.to_dict()


# ── 知识库类工具 ────────────────────────────────────────────────

def _register_knowledge_tools(app: FastMCP) -> None:

    @app.tool(description='CVE query - query vulnerability details, CVSS score, CWE mapping')
    async def hos_cve_query(
        cve_id: str = '',
        keyword: str = '',
        severity: str = '',
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """查询 CVE 漏洞信息。cve_id: 指定编号, keyword: 关键词搜索, severity: 严重级别过滤"""
        from hosforge.knowledge import LocalKnowledgeBase
        kb = LocalKnowledgeBase()
        if cve_id:
            cve = await kb.get_cve(cve_id)
            return [cve.to_dict()] if cve else []
        results = await kb.search_cve(keyword=keyword, severity=severity, limit=limit)
        return [r.to_dict() for r in results]

    @app.tool(description='CWE query - query weakness classification and mitigations')
    async def hos_cwe_query(
        cwe_id: str = '',
        keyword: str = '',
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """查询 CWE 缺陷分类。cwe_id: 指定编号, keyword: 关键词搜索"""
        from hosforge.knowledge import LocalKnowledgeBase
        kb = LocalKnowledgeBase()
        if cwe_id:
            cwe = await kb.get_cwe(cwe_id)
            return [cwe.to_dict()] if cwe else []
        results = await kb.search_cwe(keyword=keyword, limit=limit)
        return [r.to_dict() for r in results]

    @app.tool(description='Vulnerability explanation - explain vulnerability with CVE/CWE and code context')
    async def hos_vuln_explain(
        cwe_id: str = '',
        cve_id: str = '',
        code_context: str = '',
    ) -> str:
        """解释漏洞原理。cwe_id/cve_id: 漏洞编号, code_context: 相关代码"""
        from hosforge.knowledge import LocalKnowledgeBase
        kb = LocalKnowledgeBase()
        return await kb.explain_vulnerability(cwe_id=cwe_id, cve_id=cve_id, code_context=code_context)

    @app.tool(description='RAG knowledge tagging - auto-classify and tag security knowledge content')
    async def hos_rag_tag(
        content: str,
        source: str = 'custom',
    ) -> dict[str, Any]:
        """对安全知识内容进行 RAG 打标分类。content: 知识内容, source: 来源标识"""
        from hosforge.model_optimizer import SecurityRAGTagger
        tagger = SecurityRAGTagger()
        chunk = await tagger.tag_cve_entry(cve_id='manual', description=content)
        return {'tags': chunk.tags, 'confidence': chunk.confidence, 'source': source}


# ── 渗透测试类工具 ──────────────────────────────────────────────

def _register_pentest_tools(app: FastMCP) -> None:

    @app.tool(description='Pentest execution - start full PTES workflow penetration test')
    async def hos_pentest_run(
        target: str,
        authorized: bool = False,
        fast_mode: bool = False,
        skip_exploit: bool = False,
    ) -> dict[str, Any]:
        """执行渗透测试。target: 目标, authorized: 是否授权, fast_mode: 快速模式"""
        from hosforge.security_agents import AttackAgent, PentestTarget
        agent = AttackAgent()
        report = await agent.run_pentest(
            PentestTarget(host=target, scope_authorized=authorized),
            skip_exploit=skip_exploit or not authorized,
        )
        return report.to_dict()

    @app.tool(description='One-click security audit - auto audit target code/project/network')
    async def hos_security_audit(
        target: str,
        audit_type: str = 'code',
        depth: str = 'quick',
    ) -> dict[str, Any]:
        """执行安全审计。target: 审计目标, audit_type: code/network/web, depth: quick/full"""
        from hosforge.security_agents import AuditAgent
        agent = AuditAgent()
        finding = await agent.analyze(target, mode=depth)
        return finding.to_dict()

    @app.tool(description='Security fix suggestion - generate fix code for detected vulnerabilities')
    async def hos_fix_vulnerability(
        vuln_name: str,
        cwe_id: str = '',
        code_snippet: str = '',
    ) -> str:
        """生成漏洞修复代码。vuln_name: 漏洞名称, cwe_id: CWE 编号, code_snippet: 代码上下文"""
        from hosforge.security_agents import DefenseAgent, SecurityVulnerability, Severity
        agent = DefenseAgent()
        vuln = SecurityVulnerability(name=vuln_name, cwe_id=cwe_id, code_snippet=code_snippet, severity=Severity.HIGH)
        return await agent.fix(vuln)


# ── 报告类工具 ──────────────────────────────────────────────────

def _register_report_tools(app: FastMCP) -> None:

    @app.tool(description='Security report generation - generate fixed-format HTML security report')
    async def hos_report_generate(
        title: str = 'HOS-Forge Security Report',
        target: str = '',
        risk_score: int = 0,
        executive_summary: str = '',
    ) -> str:
        """生成 HTML 安全报告。title: 标题, target: 目标, risk_score: 风险评分(0-100)"""
        from hosforge.reporter import SecurityHtmlReporter, ReportData, ReportMetadata
        data = ReportData(
            metadata=ReportMetadata(title=title, target=target, report_type='scan'),
            executive_summary=executive_summary,
            risk_score=risk_score,
        )
        reporter = SecurityHtmlReporter()
        return reporter.generate(data)


# ── 桥接类工具 ──────────────────────────────────────────────────

def _register_bridge_tools(app: FastMCP) -> None:

    @app.tool(description='MCP service discovery - auto-detect external security MCP services on system')
    async def hos_mcp_discover() -> list[dict[str, Any]]:
        """扫描系统，自动发现可用的外部安全 MCP 服务"""
        from hosforge.mcp_server.bridge.discovery import MCPDiscoveryEngine
        engine = MCPDiscoveryEngine()
        services = await engine.discover_all()
        return [s.to_dict() for s in services]

    @app.tool(description='MCP service connect - connect to specified external MCP service')
    async def hos_mcp_connect(
        service_name: str,
    ) -> dict[str, Any]:
        """连接到外部安全 MCP 服务。service_name: burp-mcp / mcp-security-hub"""
        from hosforge.mcp_server.bridge.connectors.burp import BurpConnector
        from hosforge.mcp_server.bridge.connectors.security_hub import SecurityHubConnector
        connectors = {'burp-mcp': BurpConnector, 'mcp-security-hub': SecurityHubConnector}
        connector_cls = connectors.get(service_name)
        if not connector_cls:
            return {'success': False, 'error': f'Unknown service: {service_name}'}
        connector = connector_cls()
        ok = await connector.connect()
        return {'success': ok, 'service': service_name, 'status': 'connected' if ok else 'failed'}

    @app.tool(description='Burp MCP bridge - get proxy history and scan results via Burp Suite MCP')
    async def hos_burp_bridge(
        action: str = 'proxy_history',
        target: str = '',
        limit: int = 20,
    ) -> dict[str, Any]:
        """桥接 Burp Suite MCP。action: proxy_history/start_scan/analyze_request, target: URL"""
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
            return {'success': False, 'error': f'Invalid action: {action}'}
        finally:
            await connector.disconnect()

    @app.tool(description='Security Hub bridge - call security tools via mcp-security-hub')
    async def hos_security_hub_bridge(
        tool: str = 'nmap',
        target: str = '',
    ) -> dict[str, Any]:
        """桥接 mcp-security-hub。tool: nmap/nuclei_scan/sqlmap_scan/cve_search/subfinder, target: 目标"""
        from hosforge.mcp_server.bridge.connectors.security_hub import SecurityHubConnector
        hub = SecurityHubConnector()
        if not await hub.connect():
            return {'success': False, 'error': 'mcp-security-hub not available'}
        try:
            result = await hub._call(tool, {'target': target})
            return {'success': True, 'tool': tool, 'result': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            await hub.disconnect()


# ── 编排类工具 ──────────────────────────────────────────────────

def _register_orchestrator_tools(app: FastMCP) -> None:

    @app.tool(description='Workflow template list - list available pentest workflow templates')
    async def hos_workflow_templates() -> dict[str, Any]:
        """列出所有预定义的工作流模板"""
        from hosforge.mcp_server.orchestrator import MCPOrchestrator
        return MCPOrchestrator.list_templates()

    @app.tool(description='Workflow execution - run multi-step security test by template')
    async def hos_workflow_run(
        template: str = 'quick_recon',
        target: str = '',
        auto_discover: bool = True,
    ) -> dict[str, Any]:
        """执行安全工作流。template: quick_recon/web_audit/full_pentest, target: 目标域名/IP"""
        from hosforge.mcp_server.orchestrator import MCPOrchestrator
        orchestrator = MCPOrchestrator()
        if auto_discover:
            await orchestrator.discover_services()
            await orchestrator.connect_all()
        result = await orchestrator.run_pipeline(template_name=template, target=target)
        return result.to_dict()

    @app.tool(description='Parallel security scan - run multiple independent security tests concurrently')
    async def hos_parallel_scan(
        target: str = '',
        scans: str = 'nmap,nuclei,subfinder',
    ) -> dict[str, Any]:
        """并行执行多个安全扫描。target: 目标, scans: 逗号分隔的扫描类型"""
        from hosforge.mcp_server.orchestrator import MCPOrchestrator
        scan_list = [s.strip() for s in scans.split(',') if s.strip()]
        orchestrator = MCPOrchestrator()
        await orchestrator.discover_services()
        await orchestrator.connect_all()
        tasks = [{'name': s, 'service': 'security-hub', 'tool': s, 'args': {'target': target}} for s in scan_list]
        results = await orchestrator.run_parallel(tasks)
        return results
