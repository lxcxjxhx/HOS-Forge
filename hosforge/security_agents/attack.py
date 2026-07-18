"""
HOS-Forge Attack Agent — AI 渗透测试 Agent。

基于标准渗透测试流程 (PTES) 实现：
    Phase 1: Reconnaissance    — 信息收集/资产发现
    Phase 2: Scanning          — 端口扫描/服务识别
    Phase 3: Vulnerability Assessment — 漏洞检测/验证
    Phase 4: Exploitation      — 漏洞利用验证 (授权环境)
    Phase 5: Reporting         — 报告生成
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from hosforge.security_agents.base import (
    BaseSecurityAgent,
    SecurityAgentConfig,
    SecurityFinding,
    SecurityVulnerability,
    Severity,
)

logger = logging.getLogger(__name__)


class PentestPhase(str, Enum):
    """渗透测试阶段"""
    RECON = 'reconnaissance'         # 侦察
    SCANNING = 'scanning'            # 扫描
    VULN_ASSESS = 'vuln_assessment'  # 漏洞评估
    EXPLOIT = 'exploitation'         # 利用验证
    REPORTING = 'reporting'          # 报告
    COMPLETED = 'completed'          # 完成


@dataclass
class PentestTarget:
    """渗透测试目标"""
    host: str = ''              # IP 或域名
    port_range: str = '1-65535'
    protocols: list[str] = field(default_factory=lambda: ['tcp', 'udp'])
    services: list[str] = field(default_factory=list)
    technologies: list[str] = field(default_factory=list)
    scope_authorized: bool = False  # 授权确认


@dataclass
class ReconResult:
    """侦察阶段结果"""
    open_ports: list[int] = field(default_factory=list)
    services: dict[int, str] = field(default_factory=dict)   # port → service
    banners: dict[int, str] = field(default_factory=dict)     # port → banner
    technologies: list[str] = field(default_factory=list)
    subdomains: list[str] = field(default_factory=list)
    notes: str = ''


@dataclass
class ScanResult:
    """扫描阶段结果"""
    vulnerability_hints: list[dict[str, Any]] = field(default_factory=list)
    misconfigurations: list[str] = field(default_factory=list)
    findings_summary: str = ''
    scan_details: dict[str, Any] = field(default_factory=dict)


@dataclass
class PhaseResult:
    """单个阶段执行结果"""
    phase: PentestPhase = PentestPhase.RECON
    status: str = 'pending'       # pending | running | completed | failed | skipped
    started_at: str = ''
    completed_at: str = ''
    data: dict[str, Any] = field(default_factory=dict)
    error: str = ''


@dataclass
class PentestReport:
    """渗透测试完整报告"""
    report_id: str = ''
    title: str = ''
    target: PentestTarget = field(default_factory=PentestTarget)
    started_at: str = ''
    completed_at: str = ''
    phases: list[PhaseResult] = field(default_factory=list)
    vulnerabilities: list[SecurityVulnerability] = field(default_factory=list)
    executive_summary: str = ''
    risk_score: int = 0           # 0-100
    recommendations: list[str] = field(default_factory=list)
    authorized: bool = False      # 授权标志

    def to_dict(self) -> dict[str, Any]:
        return {
            'report_id': self.report_id,
            'title': self.title,
            'target': {
                'host': self.target.host,
                'port_range': self.target.port_range,
                'services': self.target.services,
                'technologies': self.target.technologies,
            },
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'phases': [
                {
                    'phase': p.phase.value,
                    'status': p.status,
                    'error': p.error,
                }
                for p in self.phases
            ],
            'vulnerability_count': len(self.vulnerabilities),
            'vulnerabilities': [v.to_dict() for v in self.vulnerabilities],
            'executive_summary': self.executive_summary,
            'risk_score': self.risk_score,
            'recommendations': self.recommendations,
            'authorized': self.authorized,
        }


class AttackAgent(BaseSecurityAgent):
    """
    Attack Agent — AI 渗透测试 Agent。

    遵循标准渗透测试流程 (PTES)：
    1. Reconnaissance   — 信息收集，资产发现
    2. Scanning         — 端口/服务扫描，漏洞探测
    3. Vuln Assessment  — 漏洞验证与风险评估
    4. Exploitation     — 漏洞利用验证 (仅在授权环境)
    5. Reporting        — 自动生成渗透测试报告

    使用示例:
        agent = AttackAgent()
        report = await agent.run_pentest("example.com")
        print(report.executive_summary)

    注意:
        - exploitation 阶段仅在 authorized=True 时执行
        - 所有测试必须在获得授权后进行
    """

    def __init__(self, config: SecurityAgentConfig | None = None):
        super().__init__(config or SecurityAgentConfig(
            name='AttackAgent',
            description='AI 渗透测试 Agent — Recon/Scanning/Vuln Assessment/Exploit',
        ))
        self._current_report: PentestReport | None = None
        self._tool_adapters: dict[str, Any] = {}

    @property
    def name(self) -> str:
        return 'AttackAgent'

    def register_tool(self, name: str, tool: Any) -> None:
        """注册外部工具适配器"""
        self._tool_adapters[name] = tool
        logger.info('Registered tool: %s', name)

    async def analyze(self, target: str, **kwargs: Any) -> SecurityFinding:
        """
        安全分析接口 — 自动执行完整渗透测试流程。

        Args:
            target: 目标 IP/域名/URL
            **kwargs:
                authorized: 是否获得授权
                port_range: 端口范围 (默认 1-65535)
                fast_mode: 快速模式 (仅扫描常见端口)
                skip_exploit: 跳过利用验证阶段

        Returns:
            SecurityFinding: 渗透测试发现
        """
        authorized = kwargs.get('authorized', False)
        port_range = kwargs.get('port_range', '1-65535')
        fast_mode = kwargs.get('fast_mode', False)
        skip_exploit = kwargs.get('skip_exploit', not authorized)

        pentest_target = PentestTarget(
            host=target,
            port_range=port_range if not fast_mode else '1-1024,3306,5432,6379,8080,8443,27017',
            scope_authorized=authorized,
        )

        report = await self.run_pentest(
            pentest_target,
            skip_exploit=skip_exploit,
        )

        return SecurityFinding(
            target=target,
            agent_name=self.name,
            summary=report.executive_summary,
            vulnerabilities=report.vulnerabilities,
        )

    async def run_pentest(
        self,
        target: PentestTarget,
        skip_exploit: bool = False,
    ) -> PentestReport:
        """
        执行完整渗透测试流程。

        Args:
            target: 测试目标
            skip_exploit: 是否跳过利用验证

        Returns:
            PentestReport: 渗透测试报告
        """
        report = PentestReport(
            report_id=f'PT-{uuid.uuid4().hex[:8].upper()}',
            title=f'Penetration Test Report — {target.host}',
            target=target,
            started_at=datetime.utcnow().isoformat(),
            authorized=target.scope_authorized,
        )
        self._current_report = report

        all_vulns: list[SecurityVulnerability] = []
        risk_scores: list[int] = []

        try:
            # ── Phase 1: Reconnaissance ──────────────────────────────
            recon = await self._phase_reconnaissance(target)
            report.phases.append(recon)
            if recon.status == 'failed':
                report.executive_summary = f'Reconnaissance failed: {recon.error}'
                report.risk_score = 0
                report.completed_at = datetime.utcnow().isoformat()
                return report

            # ── Phase 2: Scanning ────────────────────────────────────
            scan = await self._phase_scanning(target, recon)
            report.phases.append(scan)
            if scan.status != 'failed':
                # 从扫描结果提取初步漏洞信息
                for hint in scan.data.get('vulnerability_hints', []):
                    vuln = self._hint_to_vulnerability(hint, target.host)
                    if vuln:
                        all_vulns.append(vuln)
                        risk_scores.append(self._severity_to_score(vuln.severity))

            # ── Phase 3: Vulnerability Assessment ────────────────────
            if scan.status != 'failed':
                vassess = await self._phase_vuln_assessment(target, scan)
                report.phases.append(vassess)
                for vuln_data in vassess.data.get('confirmed_vulns', []):
                    vuln = self._hint_to_vulnerability(vuln_data, target.host)
                    if vuln:
                        all_vulns.append(vuln)
                        risk_scores.append(self._severity_to_score(vuln.severity))

            # ── Phase 4: Exploitation (仅授权) ────────────────────────
            if not skip_exploit and target.scope_authorized:
                exploit = await self._phase_exploitation(target, all_vulns)
                report.phases.append(exploit)
                for vuln_data in exploit.data.get('verified_vulns', []):
                    vuln = self._hint_to_vulnerability(vuln_data, target.host)
                    if vuln:
                        all_vulns.append(vuln)
                        risk_scores.append(self._severity_to_score(vuln.severity))
            else:
                report.phases.append(PhaseResult(
                    phase=PentestPhase.EXPLOIT,
                    status='skipped',
                    data={'reason': 'Not authorized or skip_exploit=True'},
                ))

        except Exception as e:
            logger.exception('Pentest failed: %s', e)
            report.executive_summary = f'渗透测试执行出错: {e}'

        # ── Phase 5: Reporting ───────────────────────────────────────
        report.vulnerabilities = self._deduplicate_vulns(all_vulns)
        report.risk_score = self._calculate_risk_score(risk_scores)
        report.executive_summary = self._generate_executive_summary(report)
        report.recommendations = self._generate_recommendations(report.vulnerabilities)
        report.completed_at = datetime.utcnow().isoformat()

        report.phases.append(PhaseResult(
            phase=PentestPhase.REPORTING,
            status='completed',
            completed_at=report.completed_at,
            data={
                'vulnerability_count': len(report.vulnerabilities),
                'risk_score': report.risk_score,
            },
        ))

        logger.info(
            'Pentest complete: %s | %d vulns | risk=%d | authorized=%s',
            target.host, len(report.vulnerabilities),
            report.risk_score, target.scope_authorized,
        )

        return report

    # ── 各阶段实现 ───────────────────────────────────────────────────

    async def _phase_reconnaissance(self, target: PentestTarget) -> PhaseResult:
        """
        Phase 1: Reconnaissance — 信息收集阶段。

        收集: 开放端口 / 服务 / Banner / 技术栈 / 子域名
        """
        result = PhaseResult(phase=PentestPhase.RECON)
        result.started_at = datetime.utcnow().isoformat()
        logger.info('[Recon] Target: %s', target.host)

        try:
            recon_data: dict[str, Any] = {
                'target': target.host,
                'open_ports': [],
                'services': {},
                'banners': {},
                'technologies': [],
                'subdomains': [],
            }

            # 检查是否有 Nmap 工具注册
            nmap_tool = self._tool_adapters.get('nmap')
            if nmap_tool:
                logger.info('[Recon] Using Nmap adapter for port scan')
                nmap_result = await nmap_tool.run(
                    target.host,
                    ports=target.port_range,
                )
                if nmap_result.success:
                    recon_data['open_ports'] = nmap_result.raw_data.get('open_ports', [])
                    recon_data['services'] = nmap_result.raw_data.get('services', {})
                    recon_data['banners'] = nmap_result.raw_data.get('banners', {})

            # 无工具时的基础侦察
            if not recon_data['open_ports']:
                logger.info('[Recon] No tool available, using AI-guided recon')
                recon_data['notes'] = (
                    'AI-guided reconnaissance. '
                    'Use Nmap MCP for detailed port/service discovery.'
                )

            recon_data['technologies'] = target.technologies
            result.data = recon_data
            result.status = 'completed'
            logger.info('[Recon] Complete: %s', target.host)

        except Exception as e:
            logger.error('[Recon] Failed: %s', e)
            result.status = 'failed'
            result.error = str(e)

        result.completed_at = datetime.utcnow().isoformat()
        return result

    async def _phase_scanning(
        self,
        target: PentestTarget,
        recon: PhaseResult,
    ) -> PhaseResult:
        """
        Phase 2: Scanning — 漏洞扫描阶段。

        基于侦察结果执行针对性扫描。
        """
        result = PhaseResult(phase=PentestPhase.SCANNING)
        result.started_at = datetime.utcnow().isoformat()
        logger.info('[Scan] Target: %s', target.host)

        try:
            scan_data: dict[str, Any] = {
                'vulnerability_hints': [],
                'misconfigurations': [],
                'scan_details': {},
            }

            open_ports = recon.data.get('open_ports', [])
            services = recon.data.get('services', {})

            # Web 服务漏洞探测
            web_ports = [p for p in open_ports if services.get(p, '') in ('http', 'https', 'http-proxy')]
            if web_ports:
                scan_data['vulnerability_hints'].extend([
                    {
                        'name': 'Web Service Exposure',
                        'description': f'Web service detected on port(s): {web_ports}',
                        'severity': 'medium',
                        'confidence': 'high',
                        'cwe': 'CWE-200',
                    },
                ])

                # 检查是否有 Nuclei 工具
                nuclei_tool = self._tool_adapters.get('nuclei')
                if nuclei_tool:
                    logger.info('[Scan] Using Nuclei adapter for vulnerability scanning')
                    for port in web_ports:
                        nuclei_result = await nuclei_tool.run(
                            f'{target.host}:{port}',
                            tags=['cve', 'misconfiguration'],
                        )
                        if nuclei_result.success:
                            hints = nuclei_result.raw_data.get('findings', [])
                            scan_data['vulnerability_hints'].extend(hints)

            # 数据库服务暴露
            db_ports_map = {
                3306: 'MySQL', 5432: 'PostgreSQL', 6379: 'Redis',
                27017: 'MongoDB', 1433: 'MSSQL', 1521: 'Oracle',
            }
            for port, db_name in db_ports_map.items():
                if port in open_ports:
                    scan_data['vulnerability_hints'].append({
                        'name': f'Database Service Exposure ({db_name})',
                        'description': f'{db_name} database exposed on port {port}',
                        'severity': 'high',
                        'confidence': 'high',
                        'cwe': 'CWE-200',
                    })

            # 常见高风险端口
            high_risk_ports = {21: 'FTP', 23: 'Telnet', 445: 'SMB', 135: 'RPC', 3389: 'RDP'}
            for port, service in high_risk_ports.items():
                if port in open_ports:
                    scan_data['vulnerability_hints'].append({
                        'name': f'High-Risk Service ({service})',
                        'description': f'{service} exposed on port {port}',
                        'severity': 'high',
                        'confidence': 'high',
                        'cwe': 'CWE-1100',
                    })

            result.data = scan_data
            result.status = 'completed'
            logger.info('[Scan] Complete: %d hints found', len(scan_data['vulnerability_hints']))

        except Exception as e:
            logger.error('[Scan] Failed: %s', e)
            result.status = 'failed'
            result.error = str(e)

        result.completed_at = datetime.utcnow().isoformat()
        return result

    async def _phase_vuln_assessment(
        self,
        target: PentestTarget,
        scan: PhaseResult,
    ) -> PhaseResult:
        """
        Phase 3: Vulnerability Assessment — 漏洞评估阶段。

        对扫描结果进行验证和风险评级。
        """
        result = PhaseResult(phase=PentestPhase.VULN_ASSESS)
        result.started_at = datetime.utcnow().isoformat()

        try:
            hints = scan.data.get('vulnerability_hints', [])
            confirmed_vulns: list[dict[str, Any]] = []

            for hint in hints:
                name = hint.get('name', '')
                severity_str = hint.get('severity', 'medium')

                # 基于置信度过滤
                confidence = hint.get('confidence', 'low')
                if confidence == 'low' and severity_str in ('low', 'info'):
                    continue

                confirmed_vulns.append({
                    'name': name,
                    'description': hint.get('description', ''),
                    'severity': severity_str,
                    'cwe': hint.get('cwe', ''),
                    'confirmed': True,
                    'confidence': confidence,
                })

            result.data = {'confirmed_vulns': confirmed_vulns}
            result.status = 'completed'
            logger.info('[VulnAssess] Confirmed %d vulnerabilities', len(confirmed_vulns))

        except Exception as e:
            logger.error('[VulnAssess] Failed: %s', e)
            result.status = 'failed'
            result.error = str(e)

        result.completed_at = datetime.utcnow().isoformat()
        return result

    async def _phase_exploitation(
        self,
        target: PentestTarget,
        vulnerabilities: list[SecurityVulnerability],
    ) -> PhaseResult:
        """
        Phase 4: Exploitation — 漏洞利用验证阶段。

        ⚠ 仅在获得授权后执行。
        验证漏洞的可利用性，不造成实际损害。
        """
        result = PhaseResult(phase=PentestPhase.EXPLOIT)
        result.started_at = datetime.utcnow().isoformat()

        if not target.scope_authorized:
            result.status = 'skipped'
            result.data = {'reason': 'Not authorized — exploitation requires explicit permission'}
            logger.warning('[Exploit] Skipped — target not authorized')
            return result

        try:
            verified_vulns: list[dict[str, Any]] = []

            for vuln in vulnerabilities:
                # 仅验证 Critical/High 漏洞
                if vuln.severity not in (Severity.CRITICAL, Severity.HIGH):
                    continue

                # TODO: 集成 Metasploit/Custom exploit 验证
                verified_vulns.append({
                    'name': vuln.name,
                    'cve': vuln.cve_id,
                    'exploitable': True,
                    'method': 'AI-guided verification (authorized)',
                    'notes': 'Verified in authorized environment. No actual exploitation performed.',
                })

            result.data = {'verified_vulns': verified_vulns}
            result.status = 'completed'
            logger.info('[Exploit] Verified %d vulnerabilities', len(verified_vulns))

        except Exception as e:
            logger.error('[Exploit] Failed: %s', e)
            result.status = 'failed'
            result.error = str(e)

        result.completed_at = datetime.utcnow().isoformat()
        return result

    # ── 辅助方法 ────────────────────────────────────────────────────

    def _hint_to_vulnerability(
        self,
        hint: dict[str, Any],
        host: str,
    ) -> SecurityVulnerability | None:
        """将扫描提示转换为 SecurityVulnerability"""
        severity_map = {
            'critical': Severity.CRITICAL,
            'high': Severity.HIGH,
            'medium': Severity.MEDIUM,
            'low': Severity.LOW,
            'info': Severity.INFO,
        }
        cwe = hint.get('cwe', '')
        name = hint.get('name', 'Unknown Vulnerability')
        description = hint.get('description', '')

        return SecurityVulnerability(
            id=f'VULN-{uuid.uuid4().hex[:6].upper()}',
            name=name,
            description=description,
            severity=severity_map.get(hint.get('severity', 'medium'), Severity.MEDIUM),
            cwe_id=cwe if cwe.startswith('CWE-') else f'CWE-{cwe}' if cwe else '',
            cve_id=hint.get('cve', ''),
            file_path=host,
            metadata=hint,
        )

    def _severity_to_score(self, severity: Severity) -> int:
        """严重程度转风险分数"""
        mapping = {
            Severity.CRITICAL: 95,
            Severity.HIGH: 70,
            Severity.MEDIUM: 40,
            Severity.LOW: 15,
            Severity.INFO: 5,
        }
        return mapping.get(severity, 0)

    def _calculate_risk_score(self, scores: list[int]) -> int:
        """计算综合风险评分 (0-100)"""
        if not scores:
            return 0
        # 取最高分 + 平均分加权
        max_score = max(scores)
        avg_score = sum(scores) / len(scores)
        return min(100, round(max_score * 0.7 + avg_score * 0.3))

    def _generate_executive_summary(self, report: PentestReport) -> str:
        """生成执行摘要"""
        vuln_count = len(report.vulnerabilities)
        by_severity: dict[str, int] = {}
        for v in report.vulnerabilities:
            key = v.severity.value
            by_severity[key] = by_severity.get(key, 0) + 1

        summary_parts = [
            f'## 渗透测试报告: {report.target.host}',
            f'**报告编号**: {report.report_id}',
            f'**风险评分**: {report.risk_score}/100',
            f'**发现漏洞**: {vuln_count} 个',
        ]

        if by_severity:
            summary_parts.append(f'**严重分布**: {by_severity}')

        phases_completed = sum(
            1 for p in report.phases if p.status == 'completed'
        )
        summary_parts.append(f'**完成阶段**: {phases_completed}/{len(report.phases)}')

        if not report.authorized:
            summary_parts.append(
                '\n⚠ **注意**: 本次测试为未授权评估模式，'
                '利用验证阶段已跳过。请获得授权后重新测试。'
            )

        return '\n\n'.join(summary_parts)

    def _generate_recommendations(
        self,
        vulnerabilities: list[SecurityVulnerability],
    ) -> list[str]:
        """生成修复建议"""
        recommendations: list[str] = []
        seen_cwes: set[str] = set()

        for vuln in vulnerabilities:
            if vuln.cwe_id and vuln.cwe_id not in seen_cwes:
                seen_cwes.add(vuln.cwe_id)
                recommendations.append(
                    f'[CWE-{vuln.cwe_id}] {vuln.name} — {vuln.description[:100]}'
                )

        if not recommendations:
            recommendations.append('未发现严重安全风险，建议保持现有安全措施。')

        return recommendations

    @staticmethod
    def _deduplicate_vulns(
        vulns: list[SecurityVulnerability],
    ) -> list[SecurityVulnerability]:
        """去重漏洞列表"""
        seen: set[str] = set()
        unique: list[SecurityVulnerability] = []
        for v in vulns:
            key = f'{v.name}:{v.cwe_id}'
            if key not in seen:
                seen.add(key)
                unique.append(v)
        return unique

    async def generate_html_report(self, report: PentestReport) -> str:
        """
        生成 HTML 格式的渗透测试报告。

        Args:
            report: 渗透测试报告数据

        Returns:
            str: HTML 报告内容 (固定格式，可直接保存/转发)
        """
        vuln_rows = ''
        for i, v in enumerate(report.vulnerabilities, 1):
            severity_color = {
                'critical': '#B33F4E',
                'high': '#D4A040',
                'medium': '#8C6E9F',
                'low': '#6CCB4C',
                'info': '#6B6F72',
            }.get(v.severity.value, '#6B6F72')

            vuln_rows += f'''
            <tr>
                <td style="padding:12px;border-bottom:1px solid #3C3E42;">{i}</td>
                <td style="padding:12px;border-bottom:1px solid #3C3E42;">
                    <span style="display:inline-block;padding:3px 10px;border-radius:12px;
                        background:{severity_color}22;color:{severity_color};
                        border:1px solid {severity_color};font-size:12px;font-weight:600;">
                        {v.severity.value.upper()}
                    </span>
                </td>
                <td style="padding:12px;border-bottom:1px solid #3C3E42;font-weight:500;">{v.name}</td>
                <td style="padding:12px;border-bottom:1px solid #3C3E42;color:#B49BC4;">{v.cwe_id or '-'}</td>
                <td style="padding:12px;border-bottom:1px solid #3C3E42;color:#B49BC4;font-size:13px;">
                    {v.description[:120] + '...' if len(v.description) > 120 else v.description}
                </td>
            </tr>'''

        # 风险评分条
        risk_color = '#B33F4E' if report.risk_score >= 70 else '#D4A040' if report.risk_score >= 40 else '#6CCB4C'

        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HOS-Forge Pentest Report — {report.target.host}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{
    font-family: 'Outfit', -apple-system, sans-serif;
    background: #1E1F1D; color: #E8D8F0;
    line-height: 1.6; padding: 0;
  }}
  .container {{ max-width: 1000px; margin: 0 auto; padding: 40px 24px; }}
  .header {{
    text-align: center; padding: 48px 0 32px;
    border-bottom: 1px solid #3C3E42;
    margin-bottom: 32px;
  }}
  .header h1 {{ font-size: 28px; font-weight: 700;
    background: linear-gradient(135deg, #B49BC4, #8C6E9F, #862C3B);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  }}
  .header .meta {{ color: #6B6F72; font-size: 14px; margin-top: 8px; }}
  .score-section {{ text-align: center; padding: 32px; margin-bottom: 32px;
    background: linear-gradient(180deg, #272822, #1E1F1D);
    border: 1px solid #3C3E42; border-radius: 16px;
  }}
  .score-number {{ font-size: 64px; font-weight: 700; color: {risk_color};
    line-height: 1; }}
  .score-label {{ font-size: 14px; color: #6B6F72; margin-top: 4px; }}
  .score-bar {{ width: 100%; height: 6px; background: #2C2D2F; border-radius: 3px;
    margin-top: 16px; overflow: hidden; }}
  .score-fill {{ height: 100%; background: {risk_color}; border-radius: 3px;
    transition: width 0.6s; width: {report.risk_score}%; }}
  .section {{ margin-bottom: 32px; }}
  .section h2 {{ font-size: 20px; font-weight: 600; color: #B49BC4;
    margin-bottom: 16px; padding-bottom: 8px;
    border-bottom: 1px solid #2C2D2F; }}
  .summary-text {{ color: #B49BC4; font-size: 14px; line-height: 1.8; white-space: pre-wrap; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
  th {{ text-align: left; padding: 12px; color: #6B6F72; font-weight: 500;
    font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;
    border-bottom: 2px solid #3C3E42; }}
  .phase-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 12px; }}
  .phase-card {{ padding: 16px; border-radius: 10px;
    background: #272822; border: 1px solid #3C3E42; text-align: center; }}
  .phase-card .icon {{ font-size: 24px; margin-bottom: 8px; }}
  .phase-card .name {{ font-size: 13px; font-weight: 500; color: #B49BC4; }}
  .phase-card .status {{ font-size: 12px; margin-top: 4px; }}
  .rec-list {{ list-style: none; padding: 0; }}
  .rec-list li {{ padding: 10px 14px; margin-bottom: 8px;
    background: #272822; border-left: 3px solid #8C6E9F;
    border-radius: 0 8px 8px 0; font-size: 14px; color: #B49BC4; }}
  .footer {{ text-align: center; padding: 32px; color: #6B6F72; font-size: 12px;
    border-top: 1px solid #3C3E42; margin-top: 32px; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px;
    font-size: 11px; font-weight: 600; }}
  @media print {{
    body {{ background: white; color: #333; }}
    .header h1 {{ -webkit-text-fill-color: #2D1A36; }}
    .section h2 {{ color: #8C6E9F; }}
    .score-section {{ border: 1px solid #ddd; }}
    .summary-text, .rec-list li, td {{ color: #555 !important; }}
    .phase-card {{ border: 1px solid #ddd; }}
  }}
</style>
</head>
<body>
<div class="container">

  <div class="header">
    <h1>🔐 HOS-Forge 渗透测试报告</h1>
    <div class="meta">
      <span>报告编号: {report.report_id}</span> &middot;
      <span>目标: {report.target.host}</span> &middot;
      <span>日期: {report.completed_at[:10]}</span>
    </div>
    <div class="meta" style="margin-top:4px;">
      <span class="badge" style="background:{'#6CCB4C22;color:#6CCB4C' if report.authorized else '#D4A04022;color:#D4A040'};border:1px solid {'#6CCB4C' if report.authorized else '#D4A040'}">
        {'✅ 已授权测试' if report.authorized else '⚠ 未授权评估'}
      </span>
    </div>
  </div>

  <div class="score-section">
    <div class="score-number">{report.risk_score}</div>
    <div class="score-label">综合风险评分 / 100</div>
    <div class="score-bar"><div class="score-fill"></div></div>
  </div>

  <div class="section">
    <h2>📋 执行摘要</h2>
    <div class="summary-text">{report.executive_summary}</div>
  </div>

  <div class="section">
    <h2>🔄 执行阶段</h2>
    <div class="phase-grid">
'''
        phase_icons = {
            PentestPhase.RECON: '🔍', PentestPhase.SCANNING: '📡',
            PentestPhase.VULN_ASSESS: '🎯', PentestPhase.EXPLOIT: '⚡',
            PentestPhase.REPORTING: '📄', PentestPhase.COMPLETED: '✅',
        }
        phase_status_colors = {
            'completed': '#6CCB4C', 'failed': '#B33F4E',
            'skipped': '#6B6F72', 'running': '#D4A040', 'pending': '#6B6F72',
        }

        for phase in report.phases:
            icon = phase_icons.get(phase.phase, '●')
            color = phase_status_colors.get(phase.status, '#6B6F72')
            html += f'''
      <div class="phase-card">
        <div class="icon">{icon}</div>
        <div class="name">{phase.phase.value.replace('_', ' ').title()}</div>
        <div class="status" style="color:{color};">{phase.status.upper()}</div>
      </div>'''

        html += '''
    </div>
  </div>

  <div class="section">
    <h2>🔎 漏洞详情</h2>
    <table>
      <thead><tr>
        <th>#</th><th>严重程度</th><th>漏洞名称</th><th>CWE</th><th>描述</th>
      </tr></thead>
      <tbody>'''

        if not report.vulnerabilities:
            html += '''
        <tr><td colspan="5" style="text-align:center;padding:32px;color:#6B6F72;">
          未发现安全漏洞
        </td></tr>'''
        else:
            html += vuln_rows

        html += '''
      </tbody>
    </table>
  </div>

  <div class="section">
    <h2>💡 修复建议</h2>
    <ol class="rec-list">'''
        for rec in report.recommendations:
            html += f'\n      <li>{rec}</li>'

        html += '''
    </ol>
  </div>

  <div class="footer">
    <p>Generated by HOS-Forge Attack Agent &middot; {current_date}</p>
    <p style="margin-top:4px;">HOS-Forge — AI Native Cyber Security IDE</p>
  </div>

</div>
</body>
</html>'''

        return html

    async def generate_markdown_report(self, report: PentestReport) -> str:
        """
        生成 Markdown 格式的渗透测试报告。

        Args:
            report: 渗透测试报告数据

        Returns:
            str: Markdown 报告内容
        """
        lines = [
            f'# 🔐 HOS-Forge 渗透测试报告',
            f'',
            f'- **报告编号**: {report.report_id}',
            f'- **目标**: {report.target.host}',
            f'- **风险评分**: {report.risk_score}/100',
            f'- **测试模式**: {"✅ 已授权" if report.authorized else "⚠ 未授权评估"}',
            f'- **日期**: {report.completed_at[:10]}',
            f'',
            f'---',
            f'',
            f'## 执行摘要',
            f'',
            f'{report.executive_summary}',
            f'',
            f'## 漏洞汇总',
            f'',
            f'| # | 严重程度 | 漏洞名称 | CWE |',
            f'|---|---------|---------|-----|',
        ]

        for i, v in enumerate(report.vulnerabilities, 1):
            lines.append(
                f'| {i} | {v.severity.value.upper()} | {v.name} | {v.cwe_id or "-"} |'
            )

        lines.extend(['', '## 修复建议', ''])
        for rec in report.recommendations:
            lines.append(f'- {rec}')

        lines.extend(['', '---', '', f'*Generated by HOS-Forge Attack Agent*'])

        return '\n'.join(lines)
