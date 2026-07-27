"""Vulnerability report generation in JSON and text formats."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import List

from hosforge.ast_analyzer.pattern_matcher import Finding
from hosforge.ast_analyzer.taint_analyzer import TaintFinding


@dataclass
class ReportEntry:
    """Normalized entry in the final report."""

    vulnerability_type: str
    severity: str
    file: str
    line: int
    description: str
    remediation: str = ""
    matched_value: str = ""


@dataclass
class Report:
    """Complete vulnerability scan report."""

    timestamp: str = ""
    total_findings: int = 0
    findings: List[ReportEntry] = field(default_factory=list)
    summary: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert report to a dictionary."""
        return {
            "timestamp": self.timestamp,
            "total_findings": self.total_findings,
            "summary": self.summary,
            "findings": [asdict(f) for f in self.findings],
        }


class ReportGenerator:
    """Generate structured vulnerability reports."""

    def generate(
        self,
        findings: List[Finding],
        taint_findings: List[TaintFinding] | None = None,
    ) -> Report:
        """Build a report from pattern findings and optional taint findings."""
        entries: List[ReportEntry] = []

        for f in findings:
            entries.append(ReportEntry(
                vulnerability_type=f.pattern_name,
                severity=f.severity,
                file=f.file,
                line=f.line,
                description=f.description,
                remediation=f.remediation,
                matched_value=f.matched_value,
            ))

        if taint_findings:
            for tf in taint_findings:
                entries.append(ReportEntry(
                    vulnerability_type="taint_flow",
                    severity=tf.severity,
                    file=tf.file,
                    line=tf.line,
                    description=tf.description,
                    remediation="Sanitize user input before passing to dangerous functions.",
                    matched_value=tf.variable,
                ))

        summary = self._build_summary(entries)
        return Report(
            timestamp=datetime.now(timezone.utc).isoformat(),
            total_findings=len(entries),
            findings=entries,
            summary=summary,
        )

    def to_json(self, report: Report, indent: int = 2) -> str:
        """Serialize a report to JSON."""
        return json.dumps(report.to_dict(), indent=indent, ensure_ascii=False)

    def to_text(self, report: Report) -> str:
        """Render a human-readable text report."""
        lines: List[str] = []
        lines.append("=" * 60)
        lines.append("  Security Scan Report")
        lines.append(f"  Generated: {report.timestamp}")
        lines.append("=" * 60)
        lines.append("")

        # Summary
        lines.append(f"Total findings: {report.total_findings}")
        for sev, count in sorted(report.summary.items()):
            lines.append(f"  {sev}: {count}")
        lines.append("")
        lines.append("-" * 60)

        # Individual findings
        for i, entry in enumerate(report.findings, start=1):
            lines.append(f"[{i}] {entry.vulnerability_type}")
            lines.append(f"    Severity:    {entry.severity}")
            lines.append(f"    File:        {entry.file}")
            lines.append(f"    Line:        {entry.line}")
            lines.append(f"    Description: {entry.description}")
            if entry.matched_value:
                lines.append(f"    Matched:     {entry.matched_value}")
            if entry.remediation:
                lines.append(f"    Remediation: {entry.remediation}")
            lines.append("")

        lines.append("=" * 60)
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_summary(entries: List[ReportEntry]) -> dict:
        summary: dict = {}
        for entry in entries:
            sev = entry.severity
            summary[sev] = summary.get(sev, 0) + 1
        return summary
