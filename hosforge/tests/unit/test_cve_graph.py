"""Unit tests for CVE knowledge graph module."""

import pytest
import tempfile
import json
from pathlib import Path

from hosforge.cve_graph import (
    CVENode,
    CWENode,
    ExploitNode,
    PackageNode,
    EdgeType,
    GraphEdge,
    CVEGraphStore,
    CVEImporter,
    CVEQueryAPI,
    ImpactAnalyzer,
)
from hosforge.cve_graph.schema import NodeType


class TestSchema:
    """Test schema data structures."""

    def test_cve_node_creation(self):
        """Test CVE node creation and serialization."""
        cve = CVENode(
            cve_id="CVE-2021-44228",
            description="Log4Shell vulnerability",
            severity="CRITICAL",
            cvss_score=10.0,
            published_date="2021-12-10",
        )
        assert cve.cve_id == "CVE-2021-44228"
        assert cve.cvss_score == 10.0
        
        data = cve.to_dict()
        assert data["cve_id"] == "CVE-2021-44228"
        
        cve2 = CVENode.from_dict(data)
        assert cve2.cve_id == cve.cve_id

    def test_cwe_node_creation(self):
        """Test CWE node creation."""
        cwe = CWENode(cwe_id="CWE-502", name="Deserialization of Untrusted Data")
        assert cwe.cwe_id == "CWE-502"
        assert cwe.name == "Deserialization of Untrusted Data"

    def test_exploit_node_creation(self):
        """Test Exploit node creation."""
        exploit = ExploitNode(
            exploit_id="EXP-001",
            title="Log4Shell RCE",
            source="GitHub",
            url="https://github.com/example/exploit",
        )
        assert exploit.exploit_id == "EXP-001"

    def test_package_node_creation(self):
        """Test Package node creation."""
        pkg = PackageNode(name="log4j-core", version="2.14.1", ecosystem="maven")
        assert pkg.name == "log4j-core"
        assert pkg.version == "2.14.1"

    def test_graph_edge_creation(self):
        """Test GraphEdge creation and serialization."""
        edge = GraphEdge(
            source_id="CVE-2021-44228",
            source_type=NodeType.CVE,
            target_id="CWE-502",
            target_type=NodeType.CWE,
            edge_type=EdgeType.RELATED_TO,
        )
        assert edge.source_id == "CVE-2021-44228"
        assert edge.edge_type == EdgeType.RELATED_TO
        
        data = edge.to_dict()
        assert data["edge_type"] == "related_to"
        
        edge2 = GraphEdge.from_dict(data)
        assert edge2.source_id == edge.source_id


class TestGraphStore:
    """Test graph storage operations."""

    def test_add_and_get_cve(self):
        """Test adding and retrieving CVE nodes."""
        store = CVEGraphStore()
        cve = CVENode(cve_id="CVE-2021-44228", description="Log4Shell", cvss_score=10.0)
        store.add_cve(cve)
        
        retrieved = store.get_cve("CVE-2021-44228")
        assert retrieved is not None
        assert retrieved["cve_id"] == "CVE-2021-44228"

    def test_add_and_get_cwe(self):
        """Test adding and retrieving CWE nodes."""
        store = CVEGraphStore()
        cwe = CWENode(cwe_id="CWE-502", name="Deserialization")
        store.add_cwe(cwe)
        
        retrieved = store.get_cwe("CWE-502")
        assert retrieved is not None
        assert retrieved["cwe_id"] == "CWE-502"

    def test_add_edge(self):
        """Test adding edges between nodes."""
        store = CVEGraphStore()
        cve = CVENode(cve_id="CVE-2021-44228")
        cwe = CWENode(cwe_id="CWE-502")
        store.add_cve(cve)
        store.add_cwe(cwe)
        
        edge = GraphEdge(
            source_id="CVE-2021-44228",
            source_type=NodeType.CVE,
            target_id="CWE-502",
            target_type=NodeType.CWE,
            edge_type=EdgeType.RELATED_TO,
        )
        store.add_edge(edge)
        
        edges = store.get_edges_from(NodeType.CVE, "CVE-2021-44228")
        assert len(edges) == 1
        assert edges[0].target_id == "CWE-502"

    def test_get_neighbors(self):
        """Test getting neighbor nodes."""
        store = CVEGraphStore()
        cve = CVENode(cve_id="CVE-2021-44228")
        cwe1 = CWENode(cwe_id="CWE-502")
        cwe2 = CWENode(cwe_id="CWE-20")
        store.add_cve(cve)
        store.add_cwe(cwe1)
        store.add_cwe(cwe2)
        
        edge1 = GraphEdge("CVE-2021-44228", NodeType.CVE, "CWE-502", NodeType.CWE, EdgeType.RELATED_TO)
        edge2 = GraphEdge("CVE-2021-44228", NodeType.CVE, "CWE-20", NodeType.CWE, EdgeType.RELATED_TO)
        store.add_edge(edge1)
        store.add_edge(edge2)
        
        neighbors = store.get_neighbors(NodeType.CVE, "CVE-2021-44228")
        assert len(neighbors) == 2

    def test_remove_node(self):
        """Test removing nodes and associated edges."""
        store = CVEGraphStore()
        cve = CVENode(cve_id="CVE-2021-44228")
        cwe = CWENode(cwe_id="CWE-502")
        store.add_cve(cve)
        store.add_cwe(cwe)
        
        edge = GraphEdge("CVE-2021-44228", NodeType.CVE, "CWE-502", NodeType.CWE, EdgeType.RELATED_TO)
        store.add_edge(edge)
        
        result = store.remove_node(NodeType.CVE, "CVE-2021-44228")
        assert result is True
        assert store.get_cve("CVE-2021-44228") is None
        
        edges = store.get_all_edges()
        assert len(edges) == 0

    def test_save_and_load(self):
        """Test graph serialization and deserialization."""
        store = CVEGraphStore()
        cve = CVENode(cve_id="CVE-2021-44228", description="Log4Shell")
        cwe = CWENode(cwe_id="CWE-502", name="Deserialization")
        store.add_cve(cve)
        store.add_cwe(cwe)
        
        edge = GraphEdge("CVE-2021-44228", NodeType.CVE, "CWE-502", NodeType.CWE, EdgeType.RELATED_TO)
        store.add_edge(edge)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "graph.json"
            store.save(str(file_path))
            
            store2 = CVEGraphStore()
            store2.load(str(file_path))
            
            assert store2.get_cve("CVE-2021-44228") is not None
            assert store2.get_cwe("CWE-502") is not None
            assert len(store2.get_all_edges()) == 1

    def test_stats(self):
        """Test graph statistics."""
        store = CVEGraphStore()
        store.add_cve(CVENode(cve_id="CVE-2021-44228"))
        store.add_cve(CVENode(cve_id="CVE-2021-34527"))
        store.add_cwe(CWENode(cwe_id="CWE-502"))
        
        stats = store.stats()
        assert stats["total_nodes"] == 3
        assert stats["cve_nodes"] == 2
        assert stats["cwe_nodes"] == 1


class TestCVEImporter:
    """Test CVE data import functionality."""

    def test_import_sample_data(self):
        """Test importing built-in sample CVE data."""
        store = CVEGraphStore()
        importer = CVEImporter(store)
        
        count = importer.import_sample_data()
        assert count > 0
        
        # Verify some known CVEs were imported
        assert store.get_cve("CVE-2021-44228") is not None
        assert store.get_cve("CVE-2021-34527") is not None
        assert store.get_cve("CVE-2020-1472") is not None

    def test_import_from_nvd_json(self):
        """Test importing from NVD JSON format."""
        nvd_data = {
            "vulnerabilities": [
                {
                    "cve": {
                        "id": "CVE-2024-12345",
                        "descriptions": [
                            {"lang": "en", "value": "Test vulnerability"}
                        ],
                        "metrics": {
                            "cvssMetricV31": [
                                {
                                    "cvssData": {
                                        "baseScore": 8.5,
                                        "baseSeverity": "HIGH",
                                        "vectorString": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
                                    }
                                }
                            ]
                        },
                        "weaknesses": [
                            {
                                "description": [
                                    {"lang": "en", "value": "CWE-79"}
                                ]
                            }
                        ],
                        "published": "2024-01-15"
                    }
                }
            ]
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "nvd.json"
            with open(json_path, "w") as f:
                json.dump(nvd_data, f)
            
            store = CVEGraphStore()
            importer = CVEImporter(store)
            count = importer.import_from_nvd_json(str(json_path))
            
            assert count == 1
            cve = store.get_cve("CVE-2024-12345")
            assert cve is not None
            assert cve["cvss_score"] == 8.5
            assert cve["severity"] == "HIGH"
            
            # Verify CWE was created
            assert store.get_cwe("CWE-79") is not None


class TestQueryAPI:
    """Test query API functionality."""

    def test_get_cve(self):
        """Test retrieving CVE details."""
        store = CVEGraphStore()
        importer = CVEImporter(store)
        importer.import_sample_data()
        
        api = CVEQueryAPI(store)
        cve = api.get_cve("CVE-2021-44228")
        
        assert cve is not None
        assert cve["cve_id"] == "CVE-2021-44228"
        assert cve["cvss_score"] == 10.0

    def test_get_related_cves(self):
        """Test getting CVEs related to a CWE."""
        store = CVEGraphStore()
        importer = CVEImporter(store)
        importer.import_sample_data()
        
        api = CVEQueryAPI(store)
        cves = api.get_related_cves("CWE-20")
        
        assert len(cves) > 0
        cve_ids = [c["cve_id"] for c in cves]
        assert "CVE-2021-44228" in cve_ids

    def test_get_exploits(self):
        """Test getting exploits for a CVE."""
        store = CVEGraphStore()
        importer = CVEImporter(store)
        importer.import_sample_data()
        
        api = CVEQueryAPI(store)
        exploits = api.get_exploits("CVE-2021-44228")
        
        assert len(exploits) > 0
        assert exploits[0]["exploit_id"] == "EXP-001"

    def test_get_affected_packages(self):
        """Test getting packages affected by a CVE."""
        store = CVEGraphStore()
        importer = CVEImporter(store)
        importer.import_sample_data()
        
        api = CVEQueryAPI(store)
        packages = api.get_affected_packages("CVE-2021-44228")
        
        assert len(packages) > 0
        pkg_names = [p["name"] for p in packages]
        assert "log4j-core" in pkg_names

    def test_get_cves_for_package(self):
        """Test getting CVEs affecting a package."""
        store = CVEGraphStore()
        importer = CVEImporter(store)
        importer.import_sample_data()
        
        api = CVEQueryAPI(store)
        cves = api.get_cves_for_package("log4j-core")
        
        assert len(cves) > 0
        cve_ids = [c["cve_id"] for c in cves]
        assert "CVE-2021-44228" in cve_ids

    def test_search_cves(self):
        """Test searching CVEs with filters."""
        store = CVEGraphStore()
        importer = CVEImporter(store)
        importer.import_sample_data()
        
        api = CVEQueryAPI(store)
        
        # Search by keyword
        results = api.search_cves(keyword="Log4j")
        assert len(results) > 0
        
        # Search by CVSS range
        results = api.search_cves(min_cvss=9.0)
        assert all(c["cvss_score"] >= 9.0 for c in results)
        
        # Search by severity
        results = api.search_cves(severity="CRITICAL")
        assert all(c["severity"] == "CRITICAL" for c in results)

    def test_get_cve_full_details(self):
        """Test getting full CVE details with related entities."""
        store = CVEGraphStore()
        importer = CVEImporter(store)
        importer.import_sample_data()
        
        api = CVEQueryAPI(store)
        details = api.get_cve_full_details("CVE-2021-44228")
        
        assert details is not None
        assert "cve" in details
        assert "cwes" in details
        assert "exploits" in details
        assert "affected_packages" in details
        
        assert len(details["cwes"]) > 0
        assert len(details["exploits"]) > 0
        assert len(details["affected_packages"]) > 0


class TestImpactAnalyzer:
    """Test impact analysis functionality."""

    def test_analyze_packages(self):
        """Test analyzing a list of packages."""
        store = CVEGraphStore()
        importer = CVEImporter(store)
        importer.import_sample_data()
        
        analyzer = ImpactAnalyzer(store)
        packages = [
            {"name": "log4j-core", "version": "2.14.1"},
            {"name": "spring-beans", "version": "5.3.17"},
            {"name": "requests", "version": "2.28.0"},
        ]
        
        report = analyzer.analyze_packages(packages, project_name="test-project")
        
        assert report.project_name == "test-project"
        assert report.total_packages == 3
        assert report.total_findings > 0
        assert report.vulnerable_packages > 0

    def test_analyze_requirements_txt(self):
        """Test analyzing requirements.txt file."""
        store = CVEGraphStore()
        importer = CVEImporter(store)
        importer.import_sample_data()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            req_file = Path(tmpdir) / "requirements.txt"
            with open(req_file, "w") as f:
                f.write("log4j-core==2.14.1\n")
                f.write("spring-beans==5.3.17\n")
                f.write("requests==2.28.0\n")
            
            analyzer = ImpactAnalyzer(store)
            report = analyzer.analyze_requirements_txt(str(req_file), project_name="python-project")
            
            assert report.total_packages == 3
            assert report.total_findings > 0

    def test_analyze_package_json(self):
        """Test analyzing package.json file."""
        store = CVEGraphStore()
        importer = CVEImporter(store)
        importer.import_sample_data()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            pkg_file = Path(tmpdir) / "package.json"
            pkg_data = {
                "dependencies": {
                    "log4j-core": "2.14.1",
                    "express": "4.18.2"
                }
            }
            with open(pkg_file, "w") as f:
                json.dump(pkg_data, f)
            
            analyzer = ImpactAnalyzer(store)
            report = analyzer.analyze_package_json(str(pkg_file), project_name="node-project")
            
            assert report.total_packages == 2
            assert report.total_findings > 0

    def test_risk_score_calculation(self):
        """Test risk score calculation."""
        store = CVEGraphStore()
        analyzer = ImpactAnalyzer(store)
        
        # CVSS 10.0 with exploit
        score = analyzer._calculate_risk_score(10.0, has_exploit=True)
        assert score == 100.0  # 10.0 * 10 * 1.5 = 150, capped at 100
        
        # CVSS 10.0 without exploit
        score = analyzer._calculate_risk_score(10.0, has_exploit=False)
        assert score == 100.0  # 10.0 * 10 = 100
        
        # CVSS 5.0 with exploit
        score = analyzer._calculate_risk_score(5.0, has_exploit=True)
        assert score == 75.0  # 5.0 * 10 * 1.5 = 75
        
        # CVSS 5.0 without exploit
        score = analyzer._calculate_risk_score(5.0, has_exploit=False)
        assert score == 50.0  # 5.0 * 10 = 50

    def test_priority_actions(self):
        """Test priority action generation."""
        store = CVEGraphStore()
        importer = CVEImporter(store)
        importer.import_sample_data()
        
        analyzer = ImpactAnalyzer(store)
        packages = [
            {"name": "log4j-core", "version": "2.14.1"},
        ]
        
        report = analyzer.analyze_packages(packages)
        
        assert len(report.priority_actions) > 0
        action = report.priority_actions[0]
        assert "priority" in action
        assert "package" in action
        assert "risk_score" in action
        assert "cve_ids" in action

    def test_report_serialization(self):
        """Test impact report serialization."""
        store = CVEGraphStore()
        importer = CVEImporter(store)
        importer.import_sample_data()
        
        analyzer = ImpactAnalyzer(store)
        packages = [{"name": "log4j-core", "version": "2.14.1"}]
        report = analyzer.analyze_packages(packages)
        
        data = report.to_dict()
        assert "project_name" in data
        assert "total_findings" in data
        assert "findings" in data
        assert "priority_actions" in data


def test_integration_full_workflow():
    """Integration test: full workflow from import to analysis."""
    # Create graph store
    store = CVEGraphStore()
    
    # Import sample data
    importer = CVEImporter(store)
    count = importer.import_sample_data()
    assert count > 0
    
    # Query the graph
    api = CVEQueryAPI(store)
    
    # Get a specific CVE
    cve = api.get_cve("CVE-2021-44228")
    assert cve is not None
    assert cve["cvss_score"] == 10.0
    
    # Get related entities
    details = api.get_cve_full_details("CVE-2021-44228")
    assert details is not None
    assert len(details["cwes"]) > 0
    assert len(details["exploits"]) > 0
    assert len(details["affected_packages"]) > 0
    
    # Analyze impact
    analyzer = ImpactAnalyzer(store)
    packages = [
        {"name": "log4j-core", "version": "2.14.1"},
        {"name": "spring-beans", "version": "5.3.17"},
    ]
    report = analyzer.analyze_packages(packages, project_name="integration-test")
    
    assert report.total_findings > 0
    assert report.vulnerable_packages > 0
    assert len(report.priority_actions) > 0
    
    # Verify graph stats
    stats = api.get_graph_stats()
    assert stats["total_nodes"] > 0
    assert stats["total_edges"] > 0
