"""Schema definitions for CVE knowledge graph nodes and edges."""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional, List, Dict, Any


class NodeType(str, Enum):
    """Node types in the CVE knowledge graph."""
    CVE = "cve"
    CWE = "cwe"
    EXPLOIT = "exploit"
    PACKAGE = "package"


class EdgeType(str, Enum):
    """Edge types in the CVE knowledge graph."""
    RELATED_TO = "related_to"      # CVE -> CWE
    HAS_EXPLOIT = "has_exploit"    # CVE -> Exploit
    AFFECTS = "affects"            # CVE -> Package
    VULNERABLE_TO = "vulnerable_to"  # Package -> CWE


@dataclass
class CVENode:
    """CVE node in the knowledge graph."""
    cve_id: str
    description: str = ""
    severity: str = ""
    cvss_score: float = 0.0
    published_date: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CVENode':
        return cls(**data)


@dataclass
class CWENode:
    """CWE node in the knowledge graph."""
    cwe_id: str
    name: str = ""
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CWENode':
        return cls(**data)


@dataclass
class ExploitNode:
    """Exploit node in the knowledge graph."""
    exploit_id: str
    title: str = ""
    source: str = ""
    url: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExploitNode':
        return cls(**data)


@dataclass
class PackageNode:
    """Package node in the knowledge graph."""
    name: str
    version: str = ""
    ecosystem: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PackageNode':
        return cls(**data)


@dataclass
class GraphEdge:
    """Edge in the CVE knowledge graph."""
    source_id: str
    source_type: NodeType
    target_id: str
    target_type: NodeType
    edge_type: EdgeType
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_type": self.source_type.value,
            "target_id": self.target_id,
            "target_type": self.target_type.value,
            "edge_type": self.edge_type.value,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GraphEdge':
        return cls(
            source_id=data["source_id"],
            source_type=NodeType(data["source_type"]),
            target_id=data["target_id"],
            target_type=NodeType(data["target_type"]),
            edge_type=EdgeType(data["edge_type"]),
            metadata=data.get("metadata", {}),
        )
