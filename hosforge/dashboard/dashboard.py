"""
HOS-Forge Security Dashboard — 信息安全态势仪表盘。

提供可嵌入的 HTML/React 组件，用于展示安全态势。
所有组件遵循安全风信子设计系统，支持浅色/深色模式。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class DashboardWidget:
    """仪表盘组件基类"""
    title: str = ''
    width: str = 'full'        # full | half | third
    height: str = 'auto'
    data: dict[str, Any] = field(default_factory=dict)

    def render_html(self) -> str:
        """渲染为 HTML"""
        return f'<div class="hos-widget">{self.title}</div>'


@dataclass
class VulnStatWidget(DashboardWidget):
    """漏洞统计组件"""
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0

    @property
    def total(self) -> int:
        return self.critical + self.high + self.medium + self.low + self.info

    def render_html(self) -> str:
        sev_colors = {
            'critical': '#B33F4E', 'high': '#D4A040',
            'medium': '#8C6E9F', 'low': '#6CCB4C', 'info': '#6B6F72',
        }
        items = [
            ('Critical', self.critical, 'critical'),
            ('High', self.high, 'high'),
            ('Medium', self.medium, 'medium'),
            ('Low', self.low, 'low'),
            ('Info', self.info, 'info'),
        ]

        cards = ''
        for label, count, key in items:
            color = sev_colors[key]
            cards += f'''
            <div style="flex:1;padding:16px;border-radius:10px;
                background:#272822;border:1px solid #3C3E42;text-align:center;
                min-width:80px;">
                <div style="font-size:28px;font-weight:700;color:{color};">{count}</div>
                <div style="font-size:11px;color:#6B6F72;margin-top:4px;">{label}</div>
            </div>'''

        return f'''
        <div class="hos-widget" style="margin-bottom:16px;">
            <div style="display:flex;align-items:center;justify-content:space-between;
                margin-bottom:12px;">
                <h3 style="font-size:16px;font-weight:600;color:#B49BC4;margin:0;">
                    {self.title or '漏洞统计'}</h3>
                <span style="font-size:12px;color:#6B6F72;">总计: {self.total}</span>
            </div>
            <div style="display:flex;gap:8px;flex-wrap:wrap;">{cards}</div>
        </div>'''


@dataclass
class RiskScoreWidget(DashboardWidget):
    """风险评分组件"""
    score: int = 0
    max_score: int = 100

    def render_html(self) -> str:
        pct = min(100, max(0, self.score))
        if pct >= 70:
            color = '#B33F4E'; label = '高风险'
        elif pct >= 40:
            color = '#D4A040'; label = '中风险'
        elif pct >= 20:
            color = '#8C6E9F'; label = '低风险'
        else:
            color = '#6CCB4C'; label = '安全'

        return f'''
        <div class="hos-widget" style="padding:24px;border-radius:12px;
            background:linear-gradient(180deg,#272822,#1E1F1D);
            border:1px solid #3C3E42;text-align:center;margin-bottom:16px;">
            <div style="font-size:48px;font-weight:700;color:{color};line-height:1;">
                {pct}</div>
            <div style="font-size:13px;color:#6B6F72;margin-top:4px;">
                {label} · 综合风险评分</div>
            <div style="width:100%;max-width:300px;height:6px;background:#2C2D2F;
                border-radius:3px;margin:12px auto 0;overflow:hidden;">
                <div style="width:{pct}%;height:100%;background:{color};
                    border-radius:3px;transition:width 0.6s ease;"></div>
            </div>
        </div>'''


@dataclass
class PentestResultWidget(DashboardWidget):
    """渗透测试结果组件"""
    target: str = ''
    phases: list[dict[str, str]] = field(default_factory=list)
    findings_count: int = 0

    def render_html(self) -> str:
        phase_icons = {
            'reconnaissance': '🔍', 'scanning': '📡',
            'vuln_assessment': '🎯', 'exploitation': '⚡',
            'reporting': '📄', 'completed': '✅',
        }
        status_colors = {
            'completed': '#6CCB4C', 'failed': '#B33F4E',
            'skipped': '#6B6F72', 'running': '#D4A040',
        }

        phases_html = ''
        for p in self.phases:
            icon = phase_icons.get(p.get('phase', ''), '●')
            sc = status_colors.get(p.get('status', ''), '#6B6F72')
            name = p.get('phase', '').replace('_', ' ').title()
            phases_html += f'''
            <div style="padding:10px 14px;border-radius:8px;
                background:#272822;border:1px solid #3C3E42;
                display:flex;align-items:center;gap:8px;font-size:13px;">
                <span>{icon}</span>
                <span style="flex:1;color:#B49BC4;font-weight:500;">{name}</span>
                <span style="color:{sc};font-size:11px;font-weight:600;">
                    {p.get('status', '').upper()}</span>
            </div>'''

        return f'''
        <div class="hos-widget" style="margin-bottom:16px;">
            <h3 style="font-size:16px;font-weight:600;color:#B49BC4;margin:0 0 12px 0;">
                🎯 渗透测试: {self.target}</h3>
            <div style="display:flex;flex-direction:column;gap:6px;">{phases_html}</div>
            <div style="margin-top:12px;font-size:12px;color:#6B6F72;">
                发现 {self.findings_count} 个安全发现</div>
        </div>'''


@dataclass
class MCPTopologyWidget(DashboardWidget):
    """MCP 服务拓扑组件 — 可视化展示所有已连接的 MCP 安全服务"""
    services: list[dict[str, Any]] = field(default_factory=list)

    def render_html(self) -> str:
        if not self.services:
            return '''
            <div class="hos-widget" style="margin-bottom:16px;">
                <h3 style="font-size:16px;font-weight:600;color:#B49BC4;margin:0 0 12px 0;">
                    🔌 MCP 服务拓扑</h3>
                <div style="text-align:center;padding:24px;color:#6B6F72;font-size:13px;">
                    未发现 MCP 安全服务
                </div>
            </div>'''

        cards = ''
        for svc in self.services:
            name = svc.get('name', 'unknown')
            desc = svc.get('description', '')[:60]
            status = svc.get('status', 'discovered')
            tools = svc.get('tools_count', 0)
            source = svc.get('source', '')

            status_color = {'connected': '#6CCB4C', 'discovered': '#8C6E9F',
                           'failed': '#B33F4E'}.get(status, '#6B6F72')
            source_icon = {'process': '⚙️', 'docker': '🐳', 'config': '📋',
                          'env': '🌐', 'port': '🔌'}.get(source, '🔗')

            cards += f'''
            <div style="padding:14px;border-radius:10px;background:#272822;
                border:1px solid #3C3E42;display:flex;align-items:center;gap:12px;">
                <span style="font-size:20px;">{source_icon}</span>
                <div style="flex:1;min-width:0;">
                    <div style="font-size:14px;font-weight:500;color:#B49BC4;">{name}</div>
                    <div style="font-size:11px;color:#6B6F72;margin-top:2px;">{desc}</div>
                </div>
                <div style="text-align:right;">
                    <div style="display:flex;align-items:center;gap:6px;justify-content:flex-end;">
                        <span style="display:inline-block;width:8px;height:8px;border-radius:50%;
                            background:{status_color};box-shadow:0 0 6px {status_color};"></span>
                        <span style="font-size:11px;color:{status_color};font-weight:500;">
                            {status.upper()}</span>
                    </div>
                    <div style="font-size:10px;color:#6B6F72;margin-top:2px;">
                        {tools} tools · {source}</div>
                </div>
            </div>'''

        return f'''
        <div class="hos-widget" style="margin-bottom:16px;">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
                <h3 style="font-size:16px;font-weight:600;color:#B49BC4;margin:0;">
                    🔌 MCP 服务拓扑</h3>
                <span style="font-size:12px;color:#6B6F72;">{len(self.services)} 个服务</span>
            </div>
            <div style="display:flex;flex-direction:column;gap:8px;">{cards}</div>
        </div>'''


@dataclass
class RecentFindingsWidget(DashboardWidget):
    """最近发现组件"""
    items: list[dict[str, Any]] = field(default_factory=list)

    def render_html(self) -> str:
        if not self.items:
            return '<div style="color:#6B6F72;font-size:13px;padding:16px;">暂无安全发现</div>'

        rows = ''
        for item in self.items[:10]:
            sev = item.get('severity', 'info')
            color = {'critical': '#B33F4E', 'high': '#D4A040',
                     'medium': '#8C6E9F', 'low': '#6CCB4C',
                     'info': '#6B6F72'}.get(sev, '#6B6F72')
            rows += f'''
            <div style="display:flex;align-items:center;gap:10px;padding:8px 0;
                border-bottom:1px solid #2C2D2F;font-size:13px;">
                <span style="display:inline-block;width:8px;height:8px;
                    border-radius:50%;background:{color};flex-shrink:0;
                    box-shadow:0 0 6px {color};"></span>
                <span style="flex:1;color:#B49BC4;">{item.get('name', '')}</span>
                <span style="color:{color};font-size:11px;font-weight:600;">
                    {sev.upper()}</span>
                <span style="color:#6B6F72;font-size:11px;">
                    {item.get('time', '')}</span>
            </div>'''

        return f'''
        <div class="hos-widget" style="margin-bottom:16px;">
            <h3 style="font-size:16px;font-weight:600;color:#B49BC4;margin:0 0 8px 0;">
                {self.title or '最近发现'}</h3>
            {rows}
        </div>'''


class SecurityDashboard:
    """
    安全仪表盘 — 聚合所有组件为完整的态势看板。

    使用示例:
        dashboard = SecurityDashboard(title='安全态势感知')
        dashboard.add_widget(RiskScoreWidget(score=72, title='综合风险'))
        dashboard.add_widget(VulnStatWidget(critical=2, high=5, medium=8, low=12))
        html = dashboard.render_html()
    """

    def __init__(self, title: str = 'HOS-Forge Security Dashboard'):
        self.title = title
        self.widgets: list[DashboardWidget] = []

    def add_widget(self, widget: DashboardWidget) -> None:
        """添加仪表盘组件"""
        self.widgets.append(widget)

    def render_html(self) -> str:
        """
        渲染完整仪表盘 HTML。

        Returns:
            str: 完整 HTML 文档，可直接在 iframe/webview 中显示
        """
        widgets_html = '\n'.join(w.render_html() for w in self.widgets)
        now = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')

        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{self.title}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{
      font-family: 'Outfit', -apple-system, sans-serif;
      background: #1E1F1D; color: #E8D8F0;
      padding: 24px; min-height: 100vh;
  }}
  .dashboard-header {{
      display:flex;align-items:center;justify-content:space-between;
      margin-bottom:24px;padding-bottom:16px;
      border-bottom:1px solid #3C3E42;
  }}
  .dashboard-header h1 {{
      font-size:22px;font-weight:700;
      background:linear-gradient(135deg,#B49BC4,#8C6E9F,#862C3B);
      -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  }}
  .dashboard-header .time {{ font-size:12px;color:#6B6F72; }}
  .hos-widget {{
      background: #1E1F1D; padding:0; margin:0;
  }}
  .dashboard-grid {{
      display:grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap:16px;
  }}
  .dashboard-grid .full {{ grid-column: 1 / -1; }}
  @media (max-width: 640px) {{
      body {{ padding: 12px; }}
      .dashboard-grid {{ grid-template-columns: 1fr; }}
  }}
  @media print {{
      body {{ background:#fff;color:#333; }}
      .dashboard-header h1 {{ -webkit-text-fill-color:#2D1A36; }}
  }}
</style>
</head>
<body>
<div class="dashboard-header">
  <h1>🔐 {self.title}</h1>
  <div class="time">{now}</div>
</div>
<div class="dashboard-grid">
{self._wrap_widgets(widgets_html)}
</div>
</body>
</html>'''

    def render_widget_script(self) -> str:
        """
        生成 React 可嵌入的 widget 脚本。

        返回一个 JS 代码片段,包含组件数据和渲染函数。
        """
        widget_data = []
        for w in self.widgets:
            if isinstance(w, VulnStatWidget):
                widget_data.append({
                    'type': 'vuln-stats',
                    'data': {
                        'critical': w.critical, 'high': w.high,
                        'medium': w.medium, 'low': w.low, 'info': w.info,
                        'total': w.total,
                    },
                })
            elif isinstance(w, RiskScoreWidget):
                widget_data.append({
                    'type': 'risk-score',
                    'data': {'score': w.score, 'max': w.max_score},
                })
            elif isinstance(w, PentestResultWidget):
                widget_data.append({
                    'type': 'pentest-result',
                    'data': {
                        'target': w.target,
                        'phases': w.phases,
                        'findings_count': w.findings_count,
                    },
                })

        import json
        return f'''
// HOS-Forge Dashboard Widget Data
window.__HOS_DASHBOARD_DATA__ = {json.dumps(widget_data, ensure_ascii=False)};
'''

    @staticmethod
    def _wrap_widgets(html: str) -> str:
        """将组件放入网格"""
        return html.replace(
            '<div class="hos-widget"',
            '<div class="hos-widget"',
        )

    @classmethod
    def from_pentest_report(cls, report: Any) -> SecurityDashboard:
        """
        从渗透测试报告构建仪表盘。

        Args:
            report: PentestReport 对象

        Returns:
            SecurityDashboard: 安全仪表盘
        """
        from hosforge.security_agents import PentestReport

        dashboard = cls(title=f'渗透测试报告 — {report.target.host}')

        dashboard.add_widget(RiskScoreWidget(
            title='综合风险评分',
            score=report.risk_score,
        ))

        by_severity = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0}
        for v in report.vulnerabilities:
            key = v.severity.value
            if key in by_severity:
                by_severity[key] += 1

        dashboard.add_widget(VulnStatWidget(
            title='漏洞统计',
            **by_severity,
        ))

        phases = [
            {'phase': p.phase.value, 'status': p.status}
            for p in report.phases
        ]
        dashboard.add_widget(PentestResultWidget(
            title='执行阶段',
            target=report.target.host,
            phases=phases,
            findings_count=len(report.vulnerabilities),
        ))

        findings = [
            {
                'name': v.name,
                'severity': v.severity.value,
                'time': report.completed_at[:10] if report.completed_at else '',
            }
            for v in report.vulnerabilities[:20]
        ]
        dashboard.add_widget(RecentFindingsWidget(
            title='漏洞列表',
            items=findings,
        ))

        return dashboard
