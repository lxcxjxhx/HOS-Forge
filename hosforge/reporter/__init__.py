"""
HOS-Forge Reporter — 安全报告生成器。

固定格式 HTML/Markdown/PDF 报告生成，适用于：
    - 渗透测试报告
    - 安全审计报告
    - 漏洞扫描报告
    - 合规检查报告

所有报告采用"安全风信子"风格，支持打印导出。
"""

from hosforge.reporter.html_reporter import SecurityHtmlReporter, ReportSection, ReportConfig
from hosforge.reporter.models import ReportData, VulnerabilityEntry, ReportMetadata

__all__ = [
    'SecurityHtmlReporter',
    'ReportSection',
    'ReportConfig',
    'ReportData',
    'VulnerabilityEntry',
    'ReportMetadata',
]
