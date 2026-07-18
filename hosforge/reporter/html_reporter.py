"""
HOS-Forge Security HTML Reporter — 安全报告生成器。

生成固定格式的 HTML 报告，安全风信子风格设计。
支持：
    - 渗透测试报告
    - 安全审计报告
    - 漏洞扫描报告
    - 打印/PDF 导出优化
    - 深色/浅色模式 (打印时自动切换)
"""

from __future__ import annotations

import base64
import uuid
from datetime import datetime
from typing import Any

from hosforge.reporter.models import ReportData, ReportSection, VulnerabilityEntry


class SecurityHtmlReporter:
    """
    安全报告 HTML 生成器。

    使用示例:
        reporter = SecurityHtmlReporter()
        html = reporter.generate(report_data)
        with open("report.html", "w") as f:
            f.write(html)

    特点:
        - 固定格式输出，确保每次生成结构一致
        - 安全风信子视觉风格
        - 打印优化 (自动切换浅色模式)
        - 支持自定义章节
    """

    STYLE_TEMPLATE = '''
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    body {{
        font-family: 'Outfit', -apple-system, 'Segoe UI', sans-serif;
        background: #1E1F1D;
        color: #E8D8F0;
        line-height: 1.7;
        -webkit-font-smoothing: antialiased;
    }}
    .report-container {{ max-width: 1000px; margin: 0 auto; padding: 40px 24px 80px; }}

    /* ── Header ── */
    .report-header {{
        text-align: center; padding: 48px 0 32px;
        border-bottom: 1px solid #3C3E42; margin-bottom: 32px;
        position: relative;
    }}
    .report-header::after {{
        content: ''; position: absolute; bottom: -1px; left: 50%; transform: translateX(-50%);
        width: 200px; height: 2px;
        background: linear-gradient(90deg, transparent, #8C6E9F, #862C3B, #6CCB4C, transparent);
    }}
    .report-header .brand {{ font-size: 14px; color: #6B6F72; margin-bottom: 8px; }}
    .report-header h1 {{
        font-size: 28px; font-weight: 700; letter-spacing: -0.5px;
        background: linear-gradient(135deg, #B49BC4, #8C6E9F, #862C3B);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text;
    }}
    .report-header .meta {{ margin-top: 12px; font-size: 13px; color: #6B6F72; }}
    .report-header .meta span {{ margin: 0 8px; }}

    /* ── 风险评分 ── */
    .risk-section {{
        text-align: center; padding: 32px 24px; margin-bottom: 32px;
        background: linear-gradient(180deg, #272822 0%, #1E1F1D 100%);
        border: 1px solid #3C3E42; border-radius: 16px;
        position: relative; overflow: hidden;
    }}
    .risk-section::before {{
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
        background: linear-gradient(90deg, transparent, #8C6E9F, transparent); opacity: 0.3;
    }}
    .risk-number {{ font-size: 72px; font-weight: 700; line-height: 1; }}
    .risk-label {{ font-size: 14px; color: #6B6F72; margin-top: 8px; }}
    .risk-bar {{ width: 100%; max-width: 400px; height: 6px;
        background: #2C2D2F; border-radius: 3px; margin: 16px auto 0; overflow: hidden; }}
    .risk-fill {{ height: 100%; border-radius: 3px; transition: width 0.8s ease; }}

    /* ── 漏洞统计卡片 ── */
    .stats-grid {{
        display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
        gap: 12px; margin-bottom: 32px;
    }}
    .stat-card {{
        padding: 20px 16px; border-radius: 12px; text-align: center;
        background: #272822; border: 1px solid #3C3E42;
    }}
    .stat-card .count {{ font-size: 32px; font-weight: 700; line-height: 1; }}
    .stat-card .label {{ font-size: 12px; color: #6B6F72; margin-top: 4px; }}

    /* ── 章节 ── */
    .section {{ margin-bottom: 36px; }}
    .section-title {{
        font-size: 20px; font-weight: 600; color: #B49BC4;
        margin-bottom: 16px; padding-bottom: 8px;
        border-bottom: 1px solid #2C2D2F;
        display: flex; align-items: center; gap: 8px;
    }}
    .section-content {{ font-size: 14px; color: #B49BC4; line-height: 1.8; }}

    /* ── 表格 ── */
    .vuln-table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    .vuln-table th {{
        text-align: left; padding: 10px 12px; font-size: 11px; font-weight: 500;
        color: #6B6F72; text-transform: uppercase; letter-spacing: 0.5px;
        border-bottom: 2px solid #3C3E42;
    }}
    .vuln-table td {{ padding: 10px 12px; border-bottom: 1px solid #2C2D2F; }}

    /* ── 严重程度标签 ── */
    .severity-badge {{
        display: inline-block; padding: 2px 10px; border-radius: 10px;
        font-size: 11px; font-weight: 600; text-transform: uppercase;
    }}
    .sev-critical {{ background: #B33F4E22; color: #B33F4E; border: 1px solid #B33F4E; }}
    .sev-high {{ background: #D4A04022; color: #D4A040; border: 1px solid #D4A040; }}
    .sev-medium {{ background: #8C6E9F22; color: #8C6E9F; border: 1px solid #8C6E9F; }}
    .sev-low {{ background: #6CCB4C22; color: #6CCB4C; border: 1px solid #6CCB4C; }}
    .sev-info {{ background: #6B6F7222; color: #6B6F72; border: 1px solid #6B6F72; }}

    /* ── 建议列表 ── */
    .rec-list {{ list-style: none; padding: 0; }}
    .rec-list li {{
        padding: 12px 16px; margin-bottom: 8px;
        background: #272822; border-left: 3px solid #8C6E9F;
        border-radius: 0 8px 8px 0; font-size: 14px; color: #B49BC4;
    }}

    /* ── 执行摘要 ── */
    .summary-box {{
        padding: 20px 24px; border-radius: 12px;
        background: #272822; border: 1px solid #3C3E42;
        font-size: 14px; line-height: 1.8; color: #B49BC4;
        white-space: pre-wrap;
    }}

    /* ── 阶段网格 ── */
    .phase-grid {{
        display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
        gap: 10px;
    }}
    .phase-item {{
        padding: 14px; border-radius: 10px;
        background: #272822; border: 1px solid #3C3E42; text-align: center;
    }}
    .phase-item .icon {{ font-size: 22px; margin-bottom: 6px; }}
    .phase-item .pname {{ font-size: 12px; font-weight: 500; color: #B49BC4; }}
    .phase-item .pstatus {{ font-size: 11px; margin-top: 4px; }}

    /* ── Footer ── */
    .report-footer {{
        text-align: center; padding: 32px; margin-top: 32px;
        border-top: 1px solid #3C3E42; color: #6B6F72; font-size: 12px;
    }}

    /* ── 打印优化 ── */
    @media print {{
        body {{ background: #fff !important; color: #333 !important; }}
        .report-header h1 {{ -webkit-text-fill-color: #2D1A36 !important; color: #2D1A36 !important; }}
        .risk-section {{ border: 1px solid #ddd !important; background: #f8f8f8 !important; }}
        .stat-card, .summary-box, .phase-item, .rec-list li {{ background: #f8f8f8 !important; border-color: #ddd !important; }}
        .section-title {{ color: #5B4A6F !important; }}
        .section-content, .rec-list li, .vuln-table td, .summary-box {{ color: #555 !important; }}
        .vuln-table th {{ color: #888 !important; }}
        .report-header::after {{ background: linear-gradient(90deg, transparent, #8C6E9F, #862C3B, #6CCB4C, transparent) !important; }}
        @page {{ margin: 2cm; }}
        body {{ font-size: 11pt; }}
        .report-container {{ max-width: none; padding: 0; }}
        .no-print {{ display: none !important; }}
    }}
    '''

    def __init__(self):
        self._style = self.STYLE_TEMPLATE

    def generate(self, data: ReportData) -> str:
        """
        生成完整 HTML 报告。

        Args:
            data: 报告数据

        Returns:
            str: 完整 HTML 文档 (固定格式)
        """
        return self._build_html(data)

    def generate_from_attack_report(
        self,
        pentest_report: Any,  # PentestReport
    ) -> str:
        """
        从渗透测试报告生成 HTML。

        Args:
            pentest_report: AttackAgent 的 PentestReport 对象

        Returns:
            str: HTML 报告
        """
        report_data = ReportData(
            metadata=ReportMetadata(
                title=f'Penetration Test Report — {pentest_report.target.host}',
                report_id=pentest_report.report_id,
                target=pentest_report.target.host,
                created_at=pentest_report.started_at[:10] if pentest_report.started_at else '',
                completed_at=pentest_report.completed_at[:10] if pentest_report.completed_at else '',
                authorized=pentest_report.authorized,
                report_type='pentest',
            ),
            executive_summary=pentest_report.executive_summary,
            risk_score=pentest_report.risk_score,
            vulnerabilities=[
                VulnerabilityEntry(
                    id=v.id,
                    name=v.name,
                    description=v.description,
                    severity=v.severity.value,
                    cve_id=v.cve_id,
                    cwe_id=v.cwe_id,
                    remediation=v.remediation,
                )
                for v in pentest_report.vulnerabilities
            ],
            recommendations=pentest_report.recommendations,
            sections=[
                ReportSection(
                    title='执行阶段',
                    order=2,
                    data={'phases': [
                        {'name': p.phase.value.replace('_', ' ').title(),
                         'status': p.status}
                        for p in pentest_report.phases
                    ]},
                ),
            ],
        )
        return self.generate(report_data)

    def _build_html(self, data: ReportData) -> str:
        """构建完整 HTML"""
        risk_color = self._risk_color(data.risk_score)
        severity_colors = {
            'critical': '#B33F4E', 'high': '#D4A040',
            'medium': '#8C6E9F', 'low': '#6CCB4C', 'info': '#6B6F72',
        }

        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{self._escape(data.metadata.title)}</title>
<style>{self._style}</style>
</head>
<body>
<div class="report-container">

  <!-- ── Header ── -->
  <div class="report-header">
    <div class="brand">🔐 HOS-Forge Security Report</div>
    <h1>{self._escape(data.metadata.title)}</h1>
    <div class="meta">
      <span>ID: {data.metadata.report_id or '-'}</span>
      <span>|</span>
      <span>Target: {self._escape(data.metadata.target)}</span>
      <span>|</span>
      <span>{data.metadata.completed_at or data.metadata.created_at}</span>
    </div>
  </div>

  <!-- ── Risk Score ── -->
  <div class="risk-section">
    <div class="risk-number" style="color:{risk_color}">{data.risk_score}</div>
    <div class="risk-label">综合风险评分 / 100</div>
    <div class="risk-bar">
      <div class="risk-fill" style="width:{data.risk_score}%;background:{risk_color};"></div>
    </div>
  </div>

  <!-- ── Stats ── -->
  <div class="stats-grid">
    <div class="stat-card">
      <div class="count" style="color:#B33F4E;">{data.critical_count}</div>
      <div class="label">Critical</div>
    </div>
    <div class="stat-card">
      <div class="count" style="color:#D4A040;">{data.high_count}</div>
      <div class="label">High</div>
    </div>
    <div class="stat-card">
      <div class="count" style="color:#8C6E9F;">{data.medium_count}</div>
      <div class="label">Medium</div>
    </div>
    <div class="stat-card">
      <div class="count" style="color:#6CCB4C;">{data.low_count}</div>
      <div class="label">Low / Info</div>
    </div>
    <div class="stat-card">
      <div class="count" style="color:#B49BC4;">{data.total_count}</div>
      <div class="label">Total</div>
    </div>
  </div>

  <!-- ── Executive Summary ── -->
  <div class="section">
    <div class="section-title">📋 执行摘要</div>
    <div class="summary-box">{self._escape(data.executive_summary) or '无执行摘要'}</div>
  </div>
'''

        # ── Custom Sections ──
        for section in sorted(data.sections, key=lambda s: s.order):
            html += f'''
  <div class="section">
    <div class="section-title">{self._escape(section.title)}</div>
    <div class="section-content">
'''
            if 'phases' in section.data:
                html += '<div class="phase-grid">\n'
                status_colors = {
                    'completed': '#6CCB4C', 'failed': '#B33F4E',
                    'skipped': '#6B6F72', 'running': '#D4A040', 'pending': '#6B6F72',
                }
                for phase in section.data['phases']:
                    sc = status_colors.get(phase.get('status', ''), '#6B6F72')
                    html += f'''
      <div class="phase-item">
        <div class="pname">{self._escape(phase.get('name', ''))}</div>
        <div class="pstatus" style="color:{sc};">{phase.get('status', '').upper()}</div>
      </div>'''
                html += '\n    </div>'

            if section.content:
                html += f'<p>{self._escape(section.content)}</p>'
            html += '\n    </div>\n  </div>\n'

        # ── Vulnerability Table ──
        vuln_rows = ''
        for i, v in enumerate(data.vulnerabilities, 1):
            color = severity_colors.get(v.severity, '#6B6F72')
            vuln_rows += f'''
    <tr>
        <td>{i}</td>
        <td><span class="severity-badge sev-{v.severity}">{v.severity}</span></td>
        <td><strong>{self._escape(v.name)}</strong></td>
        <td style="color:#6B6F72;">{v.cwe_id or '-'}</td>
        <td style="color:#6B6F72;">{v.cve_id or '-'}</td>
        <td style="color:#B49BC4;font-size:12px;">{self._escape(v.description[:100])}{'...' if len(v.description) > 100 else ''}</td>
    </tr>'''

        html += f'''
  <div class="section">
    <div class="section-title">🔎 漏洞详情 ({data.total_count})</div>
    <table class="vuln-table">
      <thead><tr>
        <th style="width:40px;">#</th>
        <th style="width:90px;">Severity</th>
        <th>Name</th>
        <th style="width:80px;">CWE</th>
        <th style="width:80px;">CVE</th>
        <th>Description</th>
      </tr></thead>
      <tbody>
'''

        if not data.vulnerabilities:
            html += '<tr><td colspan="6" style="text-align:center;padding:32px;color:#6B6F72;">未发现安全漏洞</td></tr>'
        else:
            html += vuln_rows

        html += '''
      </tbody>
    </table>
  </div>
'''

        # ── Recommendations ──
        if data.recommendations:
            html += '''
  <div class="section">
    <div class="section-title">💡 修复建议</div>
    <ol class="rec-list">'''
            for rec in data.recommendations:
                html += f'\n      <li>{self._escape(rec)}</li>'
            html += '''
    </ol>
  </div>
'''

        # ── Footer ──
        now = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
        html += f'''
  <div class="report-footer">
    <p>Generated by <strong>HOS-Forge Security Reporter</strong></p>
    <p style="margin-top:4px;">Report: {data.metadata.report_id or '-'} | {now}</p>
    <p style="margin-top:4px;">{data.metadata.tool_version}</p>
  </div>

</div>
</body>
</html>'''

        return html

    @staticmethod
    def _escape(text: str) -> str:
        """HTML 转义"""
        if not text:
            return ''
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))

    @staticmethod
    def _risk_color(score: int) -> str:
        if score >= 70:
            return '#B33F4E'
        if score >= 40:
            return '#D4A040'
        if score >= 20:
            return '#8C6E9F'
        return '#6CCB4C'
