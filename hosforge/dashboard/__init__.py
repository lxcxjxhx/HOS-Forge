"""
HOS-Forge Security Dashboard — 信息安全态势仪表盘。

提供:
    - 漏洞统计可视化 (Python 生成 HTML 片段)
    - 风险评分 UI 组件
    - 渗透测试结果展示
    - 安全态势感知看板

可直接嵌入到 OpenHands 前端或独立部署。
"""

from hosforge.dashboard.dashboard import (
    SecurityDashboard,
    DashboardWidget,
    VulnStatWidget,
    RiskScoreWidget,
    PentestResultWidget,
    MCPTopologyWidget,
    RecentFindingsWidget,
)

__all__ = [
    'SecurityDashboard',
    'DashboardWidget',
    'VulnStatWidget',
    'RiskScoreWidget',
    'PentestResultWidget',
    'MCPTopologyWidget',
    'RecentFindingsWidget',
]
