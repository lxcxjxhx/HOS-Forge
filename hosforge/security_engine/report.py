"""Security report models for vulnerability findings."""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

from hosforge.rule_engine.schema import Severity


@dataclass
class Finding:
    """Represents a single security finding/vulnerability."""
    
    rule_name: str
    severity: Severity
    location: Optional[str] = None
    description: Optional[str] = None
    remediation: Optional[str] = None
    cwe_ids: List[str] = field(default_factory=list)
    owasp_category: Optional[str] = None
    code_context: Optional[str] = None
    file_path: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert finding to dictionary representation."""
        return {
            "rule_name": self.rule_name,
            "severity": self.severity.value if self.severity else None,
            "location": self.location,
            "description": self.description,
            "remediation": self.remediation,
            "cwe_ids": self.cwe_ids,
            "owasp_category": self.owasp_category,
            "code_context": self.code_context,
            "file_path": self.file_path,
        }
    
    def format_text(self) -> str:
        """Format finding as human-readable text."""
        lines = []
        lines.append(f"[{self.severity.value.upper()}] {self.rule_name}")
        
        if self.file_path:
            lines.append(f"  File: {self.file_path}")
        
        if self.location:
            lines.append(f"  Location: {self.location}")
        
        if self.description:
            lines.append(f"  Description: {self.description}")
        
        if self.cwe_ids:
            lines.append(f"  CWE: {', '.join(self.cwe_ids)}")
        
        if self.owasp_category:
            lines.append(f"  OWASP: {self.owasp_category}")
        
        if self.code_context:
            lines.append("  Code:")
            for line in self.code_context.split("\n"):
                lines.append(f"    {line}")
        
        if self.remediation:
            lines.append("  Remediation:")
            for line in self.remediation.split("\n"):
                lines.append(f"    {line}")
        
        return "\n".join(lines)


@dataclass
class SecurityReport:
    """Security scan report containing all findings."""
    
    file_path: str
    language: str
    findings: List[Finding] = field(default_factory=list)
    scan_time: datetime = field(default_factory=datetime.now)
    
    @property
    def total_findings(self) -> int:
        """Total number of findings."""
        return len(self.findings)
    
    @property
    def critical_count(self) -> int:
        """Number of critical severity findings."""
        return sum(1 for f in self.findings if f.severity == Severity.CRITICAL)
    
    @property
    def high_count(self) -> int:
        """Number of high severity findings."""
        return sum(1 for f in self.findings if f.severity == Severity.HIGH)
    
    @property
    def medium_count(self) -> int:
        """Number of medium severity findings."""
        return sum(1 for f in self.findings if f.severity == Severity.MEDIUM)
    
    @property
    def low_count(self) -> int:
        """Number of low severity findings."""
        return sum(1 for f in self.findings if f.severity == Severity.LOW)
    
    @property
    def info_count(self) -> int:
        """Number of info severity findings."""
        return sum(1 for f in self.findings if f.severity == Severity.INFO)
    
    def to_dict(self) -> dict:
        """Convert report to dictionary representation."""
        return {
            "file_path": self.file_path,
            "language": self.language,
            "scan_time": self.scan_time.isoformat(),
            "summary": {
                "total": self.total_findings,
                "critical": self.critical_count,
                "high": self.high_count,
                "medium": self.medium_count,
                "low": self.low_count,
                "info": self.info_count,
            },
            "findings": [f.to_dict() for f in self.findings],
        }
    
    def format_text(self) -> str:
        """Format report as human-readable text."""
        lines = []
        lines.append("=" * 80)
        lines.append("SECURITY SCAN REPORT")
        lines.append("=" * 80)
        lines.append(f"File: {self.file_path}")
        lines.append(f"Language: {self.language}")
        lines.append(f"Scan Time: {self.scan_time.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append("SUMMARY")
        lines.append("-" * 80)
        lines.append(f"Total Findings: {self.total_findings}")
        lines.append(f"  Critical: {self.critical_count}")
        lines.append(f"  High:     {self.high_count}")
        lines.append(f"  Medium:   {self.medium_count}")
        lines.append(f"  Low:      {self.low_count}")
        lines.append(f"  Info:     {self.info_count}")
        lines.append("")
        
        if self.findings:
            lines.append("FINDINGS")
            lines.append("-" * 80)
            for i, finding in enumerate(self.findings, 1):
                lines.append(f"\n[{i}] {finding.format_text()}")
        else:
            lines.append("No security issues found.")
        
        lines.append("\n" + "=" * 80)
        return "\n".join(lines)
    
    def merge(self, other: "SecurityReport") -> "SecurityReport":
        """Merge another report into this one."""
        merged_findings = self.findings + other.findings
        return SecurityReport(
            file_path=f"{self.file_path}, {other.file_path}",
            language=self.language if self.language == other.language else "mixed",
            findings=merged_findings,
        )
