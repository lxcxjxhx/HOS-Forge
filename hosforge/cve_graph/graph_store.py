"""Graph storage implementation using standard library (no NetworkX dependency)."""

import json
from collections import defaultdict
from typing import Dict, List, Optional, Set, Any
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
from hosforge.logging_config import get_logger

logger = get_logger(__name__)


class CVEGraphStore:
    """CVE knowledge graph storage using adjacency list representation."""

    def __init__(self):
        self._nodes: Dict[str, Dict[str, Any]] = {}
        self._edges: List[GraphEdge] = []
        self._adjacency: Dict[str, List[str]] = defaultdict(list)

    def add_cve(self, cve: CVENode) -> None:
        """Add a CVE node to the graph."""
        node_id = f"cve:{cve.cve_id}"
        self._nodes[node_id] = cve.to_dict()
        self._nodes[node_id]["node_type"] = NodeType.CVE.value

    def add_cwe(self, cwe: CWENode) -> None:
        """Add a CWE node to the graph."""
        node_id = f"cwe:{cwe.cwe_id}"
        self._nodes[node_id] = cwe.to_dict()
        self._nodes[node_id]["node_type"] = NodeType.CWE.value

    def add_exploit(self, exploit: ExploitNode) -> None:
        """Add an Exploit node to the graph."""
        node_id = f"exploit:{exploit.exploit_id}"
        self._nodes[node_id] = exploit.to_dict()
        self._nodes[node_id]["node_type"] = NodeType.EXPLOIT.value

    def add_package(self, package: PackageNode) -> None:
        """Add a Package node to the graph."""
        node_id = f"package:{package.name}:{package.version}"
        self._nodes[node_id] = package.to_dict()
        self._nodes[node_id]["node_type"] = NodeType.PACKAGE.value

    def add_edge(self, edge: GraphEdge) -> None:
        """Add an edge to the graph."""
        self._edges.append(edge)
        source_id = f"{edge.source_type.value}:{edge.source_id}"
        target_id = f"{edge.target_type.value}:{edge.target_id}"
        self._adjacency[source_id].append(target_id)

    def get_node(self, node_type: NodeType, node_id: str) -> Optional[Dict[str, Any]]:
        """Get a node by type and ID."""
        full_id = f"{node_type.value}:{node_id}"
        return self._nodes.get(full_id)

    def get_cve(self, cve_id: str) -> Optional[Dict[str, Any]]:
        """Get a CVE node by ID."""
        return self.get_node(NodeType.CVE, cve_id)

    def get_cwe(self, cwe_id: str) -> Optional[Dict[str, Any]]:
        """Get a CWE node by ID."""
        return self.get_node(NodeType.CWE, cwe_id)

    def get_exploit(self, exploit_id: str) -> Optional[Dict[str, Any]]:
        """Get an Exploit node by ID."""
        return self.get_node(NodeType.EXPLOIT, exploit_id)

    def get_package(self, name: str, version: str) -> Optional[Dict[str, Any]]:
        """Get a Package node by name and version."""
        full_id = f"package:{name}:{version}"
        return self._nodes.get(full_id)

    def get_neighbors(self, node_type: NodeType, node_id: str) -> List[Dict[str, Any]]:
        """Get all neighbors of a node."""
        full_id = f"{node_type.value}:{node_id}"
        neighbor_ids = self._adjacency.get(full_id, [])
        return [self._nodes[nid] for nid in neighbor_ids if nid in self._nodes]

    def get_edges_from(self, node_type: NodeType, node_id: str) -> List[GraphEdge]:
        """Get all edges originating from a node."""
        full_id = f"{node_type.value}:{node_id}"
        return [e for e in self._edges if f"{e.source_type.value}:{e.source_id}" == full_id]

    def get_edges_to(self, node_type: NodeType, node_id: str) -> List[GraphEdge]:
        """Get all edges pointing to a node."""
        full_id = f"{node_type.value}:{node_id}"
        return [e for e in self._edges if f"{e.target_type.value}:{e.target_id}" == full_id]

    def remove_node(self, node_type: NodeType, node_id: str) -> bool:
        """Remove a node and all its edges."""
        full_id = f"{node_type.value}:{node_id}"
        if full_id not in self._nodes:
            return False

        del self._nodes[full_id]
        if full_id in self._adjacency:
            del self._adjacency[full_id]

        self._edges = [
            e for e in self._edges
            if f"{e.source_type.value}:{e.source_id}" != full_id
            and f"{e.target_type.value}:{e.target_id}" != full_id
        ]

        for neighbors in self._adjacency.values():
            if full_id in neighbors:
                neighbors.remove(full_id)

        return True

    def remove_edge(self, edge: GraphEdge) -> bool:
        """Remove a specific edge."""
        for i, e in enumerate(self._edges):
            if (e.source_id == edge.source_id and e.source_type == edge.source_type
                and e.target_id == edge.target_id and e.target_type == edge.target_type
                and e.edge_type == edge.edge_type):
                del self._edges[i]
                source_id = f"{edge.source_type.value}:{edge.source_id}"
                target_id = f"{edge.target_type.value}:{edge.target_id}"
                if target_id in self._adjacency[source_id]:
                    self._adjacency[source_id].remove(target_id)
                return True
        return False

    def get_all_nodes(self, node_type: Optional[NodeType] = None) -> List[Dict[str, Any]]:
        """Get all nodes, optionally filtered by type."""
        if node_type is None:
            return list(self._nodes.values())
        return [n for n in self._nodes.values() if n.get("node_type") == node_type.value]

    def get_all_edges(self) -> List[GraphEdge]:
        """Get all edges."""
        return self._edges.copy()

    def save(self, file_path: str) -> None:
        """Save graph to JSON file."""
        data = {
            "nodes": self._nodes,
            "edges": [e.to_dict() for e in self._edges],
            "adjacency": dict(self._adjacency),
        }
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Graph saved to {file_path}")

    def load(self, file_path: str) -> None:
        """Load graph from JSON file."""
        if not Path(file_path).exists():
            logger.warning(f"Graph file not found: {file_path}")
            return

        with open(file_path, "r") as f:
            data = json.load(f)

        self._nodes = data.get("nodes", {})
        self._edges = [GraphEdge.from_dict(e) for e in data.get("edges", [])]
        self._adjacency = defaultdict(list, data.get("adjacency", {}))
        logger.info(f"Graph loaded from {file_path}")

    def clear(self) -> None:
        """Clear all nodes and edges."""
        self._nodes.clear()
        self._edges.clear()
        self._adjacency.clear()

    def stats(self) -> Dict[str, int]:
        """Get graph statistics."""
        node_counts = defaultdict(int)
        for node in self._nodes.values():
            node_type = node.get("node_type", "unknown")
            node_counts[node_type] += 1

        return {
            "total_nodes": len(self._nodes),
            "total_edges": len(self._edges),
            **{f"{k}_nodes": v for k, v in node_counts.items()},
        }
