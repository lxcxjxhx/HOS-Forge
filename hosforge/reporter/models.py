"""
HOS-Forge Reporter — 数据模型。

定义报告生成所需的数据结构。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ReportMetadata:
    """报告元数据"""
    title: str = 'HOS-Forge Security Report'
    report_id: str = ''
    version: str = '0.1.0'
    author: str = 'HOS-Forge Attack Agent'
    target: str = ''
    created_at: str = ''
    completed_at: str = ''
    scan_duration: str = ''
    tool_version: str = 'HOS-Forge v0.1.0'
    authorized: bool = False
    report_type: str = 'pentest'  # pentest | audit | scan | compliance


@dataclass
class VulnerabilityEntry:
    """报告中的漏洞条目"""
    id: str = ''
    name: str = ''
    description: str = ''
    severity: str = 'medium'       # critical | high | medium | low | info
    cvss_score: float = 0.0
    cve_id: str = ''
    cwe_id: str = ''
    affected_component: str = ''
    evidence: str = ''             # 证据/截图
    remediation: str = ''          # 修复建议
    references: list[str] = field(default_factory=list)
    status: str = 'open'           # open | fixed | mitigated | accepted
    discovered_at: str = ''

    def severity_level(self) -> int:
        mapping = {'critical': 5, 'high': 4, 'medium': 3, 'low': 2, 'info': 1}
        return mapping.get(self.severity, 0)


@dataclass
class ReportSection:
    """报告章节"""
    title: str = ''
    content: str = ''
    order: int = 0
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReportData:
    """完整报告数据"""
    metadata: ReportMetadata = field(default_factory=ReportMetadata)
    executive_summary: str = ''
    risk_score: int = 0
    vulnerabilities: list[VulnerabilityEntry] = field(default_factory=list)
    sections: list[ReportSection] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    raw_data: dict[str, Any] = field(default_factory=dict)

    def severity_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for v in self.vulnerabilities:
            counts[v.severity] = counts.get(v.severity, 0) + 1
        return counts

    def severity_count(self, level: str) -> int:
        return sum(1 for v in self.vulnerabilities if v.severity == level)

    @property
    def critical_count(self) -> int:
        return self.severity_count('critical')

    @property
    def high_count(self) -> int:
        return self.severity_count('high')

    @property
    def medium_count(self) -> int:
        return self.severity_count('medium')

    @property
    def low_count(self) -> int:
        return self.severity_count('low')

    @property
    def total_count(self) -> int:
        return len(self.vulnerabilities)
