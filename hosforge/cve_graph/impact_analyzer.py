"""Impact analyzer for CVE knowledge graph."""

import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass, field, asdict

from hosforge.cve_graph.schema import NodeType, EdgeType
from hosforge.cve_graph.graph_store import CVEGraphStore
from hosforge.cve_graph.query_api import CVEQueryAPI
from hosforge.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ImpactFinding:
    """A single impact finding for a package."""
    cve_id: str
    package_name: str
    package_version: str
    cvss_score: float
    severity: str
    has_exploit: bool
    risk_score: float
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ImpactReport:
    """Impact analysis report for a project."""
    project_name: str = ""
    total_packages: int = 0
    vulnerable_packages: int = 0
    total_findings: int = 0
    critical_findings: int = 0
    high_findings: int = 0
    medium_findings: int = 0
    low_findings: int = 0
    overall_risk_score: float = 0.0
    findings: List[ImpactFinding] = field(default_factory=list)
    priority_actions: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "total_packages": self.total_packages,
            "vulnerable_packages": self.vulnerable_packages,
            "total_findings": self.total_findings,
            "critical_findings": self.critical_findings,
            "high_findings": self.high_findings,
            "medium_findings": self.medium_findings,
            "low_findings": self.low_findings,
            "overall_risk_score": self.overall_risk_score,
            "findings": [f.to_dict() for f in self.findings],
            "priority_actions": self.priority_actions,
        }


class ImpactAnalyzer:
    """Analyzes project dependencies against the CVE knowledge graph."""

    def __init__(self, graph_store: CVEGraphStore):
        self.graph_store = graph_store
        self.query_api = CVEQueryAPI(graph_store)

    def analyze_requirements_txt(self, file_path: str, project_name: str = "") -> ImpactReport:
        """Analyze a Python requirements.txt file.

        Args:
            file_path: Path to requirements.txt
            project_name: Optional project name for the report

        Returns:
            ImpactReport with findings
        """
        packages = self._parse_requirements_txt(file_path)
        return self.analyze_packages(packages, ecosystem="pypi", project_name=project_name)

    def analyze_package_json(self, file_path: str, project_name: str = "") -> ImpactReport:
        """Analyze a Node.js package.json file.

        Args:
            file_path: Path to package.json
            project_name: Optional project name for the report

        Returns:
            ImpactReport with findings
        """
        packages = self._parse_package_json(file_path)
        return self.analyze_packages(packages, ecosystem="npm", project_name=project_name)

    def analyze_packages(
        self,
        packages: List[Dict[str, str]],
        ecosystem: str = "",
        project_name: str = "",
    ) -> ImpactReport:
        """Analyze a list of packages against the CVE knowledge graph.

        Args:
            packages: List of dicts with 'name' and 'version' keys
            ecosystem: Package ecosystem (pypi, npm, maven, etc.)
            project_name: Optional project name for the report

        Returns:
            ImpactReport with findings
        """
        report = ImpactReport(project_name=project_name, total_packages=len(packages))
        vulnerable_pkg_names = set()

        for pkg in packages:
            pkg_name = pkg["name"]
            pkg_version = pkg.get("version", "")

            cves = self.query_api.get_cves_for_package(pkg_name)

            for cve_data in cves:
                cve_id = cve_data.get("cve_id", "")
                cvss_score = cve_data.get("cvss_score", 0.0)
                severity = cve_data.get("severity", "")
                description = cve_data.get("description", "")

                exploits = self.query_api.get_exploits(cve_id)
                has_exploit = len(exploits) > 0

                risk_score = self._calculate_risk_score(cvss_score, has_exploit)

                finding = ImpactFinding(
                    cve_id=cve_id,
                    package_name=pkg_name,
                    package_version=pkg_version,
                    cvss_score=cvss_score,
                    severity=severity,
                    has_exploit=has_exploit,
                    risk_score=risk_score,
                    description=description,
                )
                report.findings.append(finding)
                vulnerable_pkg_names.add(pkg_name)

        report.vulnerable_packages = len(vulnerable_pkg_names)
        report.total_findings = len(report.findings)

        for f in report.findings:
            sev = f.severity.upper()
            if sev == "CRITICAL":
                report.critical_findings += 1
            elif sev == "HIGH":
                report.high_findings += 1
            elif sev == "MEDIUM":
                report.medium_findings += 1
            elif sev == "LOW":
                report.low_findings += 1

        if report.findings:
            report.overall_risk_score = (
                sum(f.risk_score for f in report.findings) / len(report.findings)
            )

        report.findings.sort(key=lambda f: f.risk_score, reverse=True)
        report.priority_actions = self._generate_priority_actions(report)

        logger.info(
            f"Impact analysis for '{project_name}': "
            f"{report.total_findings} findings across "
            f"{report.vulnerable_packages} packages"
        )
        return report

    def _calculate_risk_score(self, cvss_score: float, has_exploit: bool) -> float:
        """Calculate a risk score based on CVSS and exploit availability.

        Risk score formula:
            base = cvss_score * 10  (0-100)
            exploit_multiplier = 1.5 if exploit available, else 1.0
            risk = min(base * exploit_multiplier, 100.0)
        """
        base = cvss_score * 10.0
        if has_exploit:
            base *= 1.5
        return min(base, 100.0)

    def _generate_priority_actions(self, report: ImpactReport) -> List[Dict[str, Any]]:
        """Generate prioritized remediation actions."""
        actions: List[Dict[str, Any]] = []

        # Group findings by package
        pkg_findings: Dict[str, List[ImpactFinding]] = {}
        for f in report.findings:
            key = f"{f.package_name}@{f.package_version}"
            pkg_findings.setdefault(key, []).append(f)

        for pkg_key, findings in pkg_findings.items():
            max_risk = max(f.risk_score for f in findings)
            cve_ids = [f.cve_id for f in findings]
            has_exploit = any(f.has_exploit for f in findings)

            priority = "P0" if max_risk >= 90 else "P1" if max_risk >= 70 else "P2" if max_risk >= 40 else "P3"

            actions.append({
                "priority": priority,
                "package": pkg_key,
                "risk_score": max_risk,
                "cve_count": len(findings),
                "cve_ids": cve_ids,
                "has_exploit": has_exploit,
                "action": f"Update or patch {pkg_key} to address {len(cve_ids)} CVE(s)",
            })

        actions.sort(key=lambda a: a["risk_score"], reverse=True)
        return actions

    def _parse_requirements_txt(self, file_path: str) -> List[Dict[str, str]]:
        """Parse a requirements.txt file into package list."""
        packages: List[Dict[str, str]] = []
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"requirements.txt not found: {file_path}")
            return packages

        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("-"):
                    continue

                # Handle ==, >=, <=, ~=, !=
                for sep in ["==", ">=", "<=", "~=", "!="]:
                    if sep in line:
                        parts = line.split(sep, 1)
                        name = parts[0].strip().lower()
                        version = parts[1].strip().split(",")[0].strip()
                        packages.append({"name": name, "version": version})
                        break
                else:
                    # No version specifier
                    name = line.split("[")[0].strip().lower()
                    if name:
                        packages.append({"name": name, "version": ""})

        return packages

    def _parse_package_json(self, file_path: str) -> List[Dict[str, str]]:
        """Parse a package.json file into package list."""
        packages: List[Dict[str, str]] = []
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"package.json not found: {file_path}")
            return packages

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for dep_section in ["dependencies", "devDependencies"]:
            deps = data.get(dep_section, {})
            for name, version_spec in deps.items():
                # Strip semver range chars
                version = version_spec.lstrip("^~>=<").strip()
                packages.append({"name": name, "version": version})

        return packages
