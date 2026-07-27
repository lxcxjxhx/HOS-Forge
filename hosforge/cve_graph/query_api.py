"""Query API for CVE knowledge graph."""

from typing import Dict, List, Any, Optional

from hosforge.cve_graph.schema import NodeType, EdgeType
from hosforge.cve_graph.graph_store import CVEGraphStore
from hosforge.logging_config import get_logger

logger = get_logger(__name__)


class CVEQueryAPI:
    """High-level query API for the CVE knowledge graph."""

    def __init__(self, graph_store: CVEGraphStore):
        self.graph_store = graph_store

    def get_cve(self, cve_id: str) -> Optional[Dict[str, Any]]:
        """Get CVE details by ID.

        Args:
            cve_id: CVE identifier (e.g. CVE-2021-44228)

        Returns:
            CVE node data dict, or None if not found
        """
        return self.graph_store.get_cve(cve_id)

    def get_cwe(self, cwe_id: str) -> Optional[Dict[str, Any]]:
        """Get CWE details by ID.

        Args:
            cwe_id: CWE identifier (e.g. CWE-502)

        Returns:
            CWE node data dict, or None if not found
        """
        return self.graph_store.get_cwe(cwe_id)

    def get_related_cves(self, cwe_id: str) -> List[Dict[str, Any]]:
        """Get all CVEs related to a given CWE.

        Args:
            cwe_id: CWE identifier

        Returns:
            List of CVE node data dicts
        """
        edges = self.graph_store.get_edges_to(NodeType.CWE, cwe_id)
        cves = []
        for edge in edges:
            if edge.edge_type == EdgeType.RELATED_TO and edge.source_type == NodeType.CVE:
                cve = self.graph_store.get_cve(edge.source_id)
                if cve:
                    cves.append(cve)
        return cves

    def get_exploits(self, cve_id: str) -> List[Dict[str, Any]]:
        """Get all exploits related to a given CVE.

        Args:
            cve_id: CVE identifier

        Returns:
            List of Exploit node data dicts
        """
        edges = self.graph_store.get_edges_from(NodeType.CVE, cve_id)
        exploits = []
        for edge in edges:
            if edge.edge_type == EdgeType.HAS_EXPLOIT and edge.target_type == NodeType.EXPLOIT:
                exploit = self.graph_store.get_exploit(edge.target_id)
                if exploit:
                    exploits.append(exploit)
        return exploits

    def get_affected_packages(self, cve_id: str) -> List[Dict[str, Any]]:
        """Get all packages affected by a given CVE.

        Args:
            cve_id: CVE identifier

        Returns:
            List of Package node data dicts
        """
        edges = self.graph_store.get_edges_from(NodeType.CVE, cve_id)
        packages = []
        for edge in edges:
            if edge.edge_type == EdgeType.AFFECTS and edge.target_type == NodeType.PACKAGE:
                # target_id is "name:version"
                parts = edge.target_id.rsplit(":", 1)
                if len(parts) == 2:
                    pkg = self.graph_store.get_package(parts[0], parts[1])
                    if pkg:
                        packages.append(pkg)
        return packages

    def get_cves_for_package(
        self, package_name: str, version: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all CVEs that affect a given package.

        Args:
            package_name: Package name
            version: Optional version filter. If None, matches all versions.

        Returns:
            List of CVE node data dicts
        """
        edges = self.graph_store.get_edges_to(NodeType.PACKAGE, f"{package_name}:{version}")
        if version is None:
            # Search across all versions
            all_edges = self.graph_store.get_all_edges()
            edges = [
                e for e in all_edges
                if e.edge_type == EdgeType.AFFECTS
                and e.target_type == NodeType.PACKAGE
                and e.target_id.startswith(f"{package_name}:")
            ]

        cves = []
        seen_cve_ids = set()
        for edge in edges:
            if edge.edge_type == EdgeType.AFFECTS and edge.source_type == NodeType.CVE:
                if edge.source_id not in seen_cve_ids:
                    cve = self.graph_store.get_cve(edge.source_id)
                    if cve:
                        cves.append(cve)
                        seen_cve_ids.add(edge.source_id)
        return cves

    def get_cve_full_details(self, cve_id: str) -> Optional[Dict[str, Any]]:
        """Get full details of a CVE including related CWEs, exploits, and packages.

        Args:
            cve_id: CVE identifier

        Returns:
            Dict with CVE data plus related entities, or None if not found
        """
        cve = self.get_cve(cve_id)
        if not cve:
            return None

        return {
            "cve": cve,
            "cwes": self._get_cwes_for_cve(cve_id),
            "exploits": self.get_exploits(cve_id),
            "affected_packages": self.get_affected_packages(cve_id),
        }

    def _get_cwes_for_cve(self, cve_id: str) -> List[Dict[str, Any]]:
        """Get all CWEs related to a given CVE."""
        edges = self.graph_store.get_edges_from(NodeType.CVE, cve_id)
        cwes = []
        for edge in edges:
            if edge.edge_type == EdgeType.RELATED_TO and edge.target_type == NodeType.CWE:
                cwe = self.graph_store.get_cwe(edge.target_id)
                if cwe:
                    cwes.append(cwe)
        return cwes

    def search_cves(
        self,
        keyword: Optional[str] = None,
        min_cvss: Optional[float] = None,
        max_cvss: Optional[float] = None,
        severity: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search CVEs with filters.

        Args:
            keyword: Search keyword in description
            min_cvss: Minimum CVSS score
            max_cvss: Maximum CVSS score
            severity: Severity level filter

        Returns:
            List of matching CVE node data dicts
        """
        all_cves = self.graph_store.get_all_nodes(NodeType.CVE)
        results = []

        for cve in all_cves:
            if keyword and keyword.lower() not in cve.get("description", "").lower():
                continue
            if min_cvss is not None and cve.get("cvss_score", 0.0) < min_cvss:
                continue
            if max_cvss is not None and cve.get("cvss_score", 0.0) > max_cvss:
                continue
            if severity and cve.get("severity", "").upper() != severity.upper():
                continue
            results.append(cve)

        return sorted(results, key=lambda c: c.get("cvss_score", 0.0), reverse=True)

    def get_graph_stats(self) -> Dict[str, Any]:
        """Get knowledge graph statistics."""
        return self.graph_store.stats()
