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

    Args:
        app: FastMCP 应用实例
    """
    _register_scan_tools(app)
    _register_knowledge_tools(app)
    _register_pentest_tools(app)
    _register_report_tools(app)

    logger.info('Registered all HOS-Forge MCP tools')


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

    @app.tool(description='🔍 Reality Score 检测 — 检查代码中的 Mock 数据/Regex 滥用/沉默失败')
    async def hos_reality_check(
        code: str,
        filename: str = 'anonymous',
    ) -> dict[str, Any]:
        """
        对代码执行 HOS-Silly-Mock 现实检测。

        检查:
            - MOCK 数据泄漏
            - Regex 用于结构化解析
            - 变量缺少 source→sink 链路
            - 沉默失败 (空 catch / 无错误处理)
        """
        from hosforge.reality_enforcement import enforce_text

        lines = code.split('\n')
        result = enforce_text(lines, filename=filename)
        return result.to_dict()


# 辅助导入 (避免循环)
from hosforge.security_agents import PentestTarget  # noqa: E402
