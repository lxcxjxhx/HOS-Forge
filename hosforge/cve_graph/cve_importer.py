"""CVE data importer with built-in sample data."""

import json
from typing import Dict, List, Any
from pathlib import Path

from hosforge.cve_graph.schema import (
    CVENode,
    CWENode,
    ExploitNode,
    PackageNode,
    NodeType,
    EdgeType,
    GraphEdge,
)
from hosforge.cve_graph.graph_store import CVEGraphStore
from hosforge.logging_config import get_logger

logger = get_logger(__name__)


class CVEImporter:
    """Importer for CVE data from various sources."""

    def __init__(self, graph_store: CVEGraphStore):
        self.graph_store = graph_store

    def import_from_nvd_json(self, json_path: str) -> int:
        """Import CVE data from NVD JSON format.

        Args:
            json_path: Path to NVD JSON file

        Returns:
            Number of CVEs imported
        """
        if not Path(json_path).exists():
            logger.error(f"NVD JSON file not found: {json_path}")
            return 0

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        count = 0
        vulnerabilities = data.get("vulnerabilities", [])

        for vuln_item in vulnerabilities:
            cve_data = vuln_item.get("cve", {})
            cve_id = cve_data.get("id", "")

            if not cve_id:
                continue

            # Extract description
            descriptions = cve_data.get("descriptions", [])
            description = ""
            for desc in descriptions:
                if desc.get("lang") == "en":
                    description = desc.get("value", "")
                    break

            # Extract CVSS score and severity
            metrics = cve_data.get("metrics", {})
            cvss_score = 0.0
            severity = ""

            for metric_key in ["cvssMetricV31", "cvssMetricV30", "cvssMetricV2"]:
                if metric_key in metrics:
                    metric_list = metrics[metric_key]
                    if metric_list:
                        cvss_data = metric_list[0].get("cvssData", {})
                        cvss_score = cvss_data.get("baseScore", 0.0)
                        severity = cvss_data.get("baseSeverity", "")
                        break

            # Extract published date
            published_date = cve_data.get("published", "")

            # Create CVE node
            cve_node = CVENode(
                cve_id=cve_id,
                description=description,
                severity=severity,
                cvss_score=cvss_score,
                published_date=published_date,
            )
            self.graph_store.add_cve(cve_node)

            # Extract CWE relationships
            weaknesses = cve_data.get("weaknesses", [])
            for weakness in weaknesses:
                weakness_descs = weakness.get("description", [])
                for weak_desc in weakness_descs:
                    cwe_id = weak_desc.get("value", "")
                    if cwe_id and cwe_id != "N/A":
                        # Create CWE node if not exists
                        if not self.graph_store.get_cwe(cwe_id):
                            cwe_node = CWENode(cwe_id=cwe_id)
                            self.graph_store.add_cwe(cwe_node)

                        # Add edge CVE -> CWE
                        edge = GraphEdge(
                            source_id=cve_id,
                            source_type=NodeType.CVE,
                            target_id=cwe_id,
                            target_type=NodeType.CWE,
                            edge_type=EdgeType.RELATED_TO,
                        )
                        self.graph_store.add_edge(edge)

            count += 1

        logger.info(f"Imported {count} CVEs from {json_path}")
        return count

    def import_sample_data(self) -> int:
        """Import built-in sample CVE data.

        Returns:
            Number of CVEs imported
        """
        sample_data = self._get_sample_cves()

        for cve_data in sample_data:
            # Create CVE node
            cve_node = CVENode(
                cve_id=cve_data["cve_id"],
                description=cve_data["description"],
                severity=cve_data["severity"],
                cvss_score=cve_data["cvss_score"],
                published_date=cve_data["published_date"],
            )
            self.graph_store.add_cve(cve_node)

            # Create CWE nodes and edges
            for cwe_id in cve_data.get("cwe_ids", []):
                if not self.graph_store.get_cwe(cwe_id):
                    cwe_node = CWENode(
                        cwe_id=cwe_id,
                        name=cve_data.get("cwe_names", {}).get(cwe_id, ""),
                    )
                    self.graph_store.add_cwe(cwe_node)

                edge = GraphEdge(
                    source_id=cve_data["cve_id"],
                    source_type=NodeType.CVE,
                    target_id=cwe_id,
                    target_type=NodeType.CWE,
                    edge_type=EdgeType.RELATED_TO,
                )
                self.graph_store.add_edge(edge)

            # Create exploit nodes and edges
            for exploit_data in cve_data.get("exploits", []):
                exploit_id = exploit_data["exploit_id"]
                if not self.graph_store.get_exploit(exploit_id):
                    exploit_node = ExploitNode(
                        exploit_id=exploit_id,
                        title=exploit_data["title"],
                        source=exploit_data["source"],
                        url=exploit_data["url"],
                    )
                    self.graph_store.add_exploit(exploit_node)

                edge = GraphEdge(
                    source_id=cve_data["cve_id"],
                    source_type=NodeType.CVE,
                    target_id=exploit_id,
                    target_type=NodeType.EXPLOIT,
                    edge_type=EdgeType.HAS_EXPLOIT,
                )
                self.graph_store.add_edge(edge)

            # Create package nodes and edges
            for pkg_data in cve_data.get("affected_packages", []):
                pkg_name = pkg_data["name"]
                pkg_version = pkg_data["version"]

                if not self.graph_store.get_package(pkg_name, pkg_version):
                    package_node = PackageNode(
                        name=pkg_name,
                        version=pkg_version,
                        ecosystem=pkg_data.get("ecosystem", ""),
                    )
                    self.graph_store.add_package(package_node)

                edge = GraphEdge(
                    source_id=cve_data["cve_id"],
                    source_type=NodeType.CVE,
                    target_id=f"{pkg_name}:{pkg_version}",
                    target_type=NodeType.PACKAGE,
                    edge_type=EdgeType.AFFECTS,
                )
                self.graph_store.add_edge(edge)

        logger.info(f"Imported {len(sample_data)} sample CVEs")
        return len(sample_data)

    def _get_sample_cves(self) -> List[Dict[str, Any]]:
        """Get built-in sample CVE data."""
        return [
            {
                "cve_id": "CVE-2021-44228",
                "description": "Apache Log4j2 JNDI features do not protect against attacker controlled LDAP and other JNDI related endpoints.",
                "severity": "CRITICAL",
                "cvss_score": 10.0,
                "published_date": "2021-12-10",
                "cwe_ids": ["CWE-502", "CWE-400", "CWE-20"],
                "cwe_names": {
                    "CWE-502": "Deserialization of Untrusted Data",
                    "CWE-400": "Uncontrolled Resource Consumption",
                    "CWE-20": "Improper Input Validation",
                },
                "exploits": [
                    {
                        "exploit_id": "EXP-001",
                        "title": "Log4Shell RCE Exploit",
                        "source": "GitHub",
                        "url": "https://github.com/example/log4shell-exploit",
                    }
                ],
                "affected_packages": [
                    {"name": "log4j-core", "version": "2.14.1", "ecosystem": "maven"},
                    {"name": "log4j-core", "version": "2.15.0", "ecosystem": "maven"},
                ],
            },
            {
                "cve_id": "CVE-2021-34527",
                "description": "Windows Print Spooler Remote Code Execution Vulnerability (PrintNightmare).",
                "severity": "CRITICAL",
                "cvss_score": 8.8,
                "published_date": "2021-07-02",
                "cwe_ids": ["CWE-20"],
                "cwe_names": {"CWE-20": "Improper Input Validation"},
                "exploits": [
                    {
                        "exploit_id": "EXP-002",
                        "title": "PrintNightmare PoC",
                        "source": "GitHub",
                        "url": "https://github.com/example/printnightmare-poc",
                    }
                ],
                "affected_packages": [
                    {"name": "windows-print-spooler", "version": "10.0", "ecosystem": "windows"},
                ],
            },
            {
                "cve_id": "CVE-2020-1472",
                "description": "Netlogon Elevation of Privilege Vulnerability (Zerologon).",
                "severity": "CRITICAL",
                "cvss_score": 10.0,
                "published_date": "2020-08-11",
                "cwe_ids": ["CWE-327"],
                "cwe_names": {"CWE-327": "Use of a Broken or Risky Cryptographic Algorithm"},
                "exploits": [
                    {
                        "exploit_id": "EXP-003",
                        "title": "Zerologon Exploit",
                        "source": "GitHub",
                        "url": "https://github.com/example/zerologon-exploit",
                    }
                ],
                "affected_packages": [
                    {"name": "windows-netlogon", "version": "10.0", "ecosystem": "windows"},
                ],
            },
            {
                "cve_id": "CVE-2021-42287",
                "description": "Active Directory Domain Services Elevation of Privilege Vulnerability (SamAccountName).",
                "severity": "HIGH",
                "cvss_score": 8.0,
                "published_date": "2021-12-14",
                "cwe_ids": ["CWE-20"],
                "cwe_names": {"CWE-20": "Improper Input Validation"},
                "exploits": [],
                "affected_packages": [
                    {"name": "active-directory", "version": "2019", "ecosystem": "windows"},
                ],
            },
            {
                "cve_id": "CVE-2021-42278",
                "description": "Active Directory Domain Services Elevation of Privilege Vulnerability.",
                "severity": "HIGH",
                "cvss_score": 8.0,
                "published_date": "2021-12-14",
                "cwe_ids": ["CWE-20"],
                "cwe_names": {"CWE-20": "Improper Input Validation"},
                "exploits": [],
                "affected_packages": [
                    {"name": "active-directory", "version": "2019", "ecosystem": "windows"},
                ],
            },
            {
                "cve_id": "CVE-2022-22965",
                "description": "Spring Framework RCE via Data Binding on JDK 9+ (Spring4Shell).",
                "severity": "CRITICAL",
                "cvss_score": 9.8,
                "published_date": "2022-03-31",
                "cwe_ids": ["CWE-94"],
                "cwe_names": {"CWE-94": "Improper Control of Generation of Code"},
                "exploits": [
                    {
                        "exploit_id": "EXP-004",
                        "title": "Spring4Shell Exploit",
                        "source": "GitHub",
                        "url": "https://github.com/example/spring4shell-exploit",
                    }
                ],
                "affected_packages": [
                    {"name": "spring-beans", "version": "5.3.17", "ecosystem": "maven"},
                ],
            },
            {
                "cve_id": "CVE-2023-44487",
                "description": "HTTP/2 Rapid Reset Attack vulnerability.",
                "severity": "HIGH",
                "cvss_score": 7.5,
                "published_date": "2023-10-10",
                "cwe_ids": ["CWE-400"],
                "cwe_names": {"CWE-400": "Uncontrolled Resource Consumption"},
                "exploits": [],
                "affected_packages": [
                    {"name": "golang.org/x/net", "version": "0.16.0", "ecosystem": "go"},
                    {"name": "nghttp2", "version": "1.57.0", "ecosystem": "c"},
                ],
            },
            {
                "cve_id": "CVE-2023-34362",
                "description": "MOVEit Transfer SQL Injection Vulnerability.",
                "severity": "CRITICAL",
                "cvss_score": 9.8,
                "published_date": "2023-06-02",
                "cwe_ids": ["CWE-89"],
                "cwe_names": {"CWE-89": "Improper Neutralization of Special Elements used in an SQL Command"},
                "exploits": [
                    {
                        "exploit_id": "EXP-005",
                        "title": "MOVEit Transfer Exploit",
                        "source": "GitHub",
                        "url": "https://github.com/example/moveit-exploit",
                    }
                ],
                "affected_packages": [
                    {"name": "moveit-transfer", "version": "2023.0.1", "ecosystem": "proprietary"},
                ],
            },
            {
                "cve_id": "CVE-2024-3094",
                "description": "XZ Utils backdoor - malicious code in xz/liblzma.",
                "severity": "CRITICAL",
                "cvss_score": 10.0,
                "published_date": "2024-03-29",
                "cwe_ids": ["CWE-506"],
                "cwe_names": {"CWE-506": "Embedded Malicious Code"},
                "exploits": [],
                "affected_packages": [
                    {"name": "xz", "version": "5.6.0", "ecosystem": "c"},
                    {"name": "xz", "version": "5.6.1", "ecosystem": "c"},
                ],
            },
            {
                "cve_id": "CVE-2021-21972",
                "description": "VMware vSphere Client Remote Code Execution Vulnerability.",
                "severity": "CRITICAL",
                "cvss_score": 9.8,
                "published_date": "2021-02-23",
                "cwe_ids": ["CWE-22", "CWE-200"],
                "cwe_names": {
                    "CWE-22": "Improper Limitation of a Pathname to a Restricted Directory",
                    "CWE-200": "Exposure of Sensitive Information to an Unauthorized Actor",
                },
                "exploits": [
                    {
                        "exploit_id": "EXP-006",
                        "title": "vSphere Client RCE",
                        "source": "GitHub",
                        "url": "https://github.com/example/vsphere-rce",
                    }
                ],
                "affected_packages": [
                    {"name": "vsphere-client", "version": "7.0", "ecosystem": "vmware"},
                ],
            },
        ]
