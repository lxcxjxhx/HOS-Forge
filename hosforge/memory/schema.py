"""Security Memory Schema - Data models for security knowledge base."""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class Severity(Enum):
    """漏洞严重级别"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FindingStatus(Enum):
    """漏洞发现状态"""
    OPEN = "open"
    CONFIRMED = "confirmed"
    FALSE_POSITIVE = "false_positive"
    FIXED = "fixed"
    MITIGATED = "mitigated"
    IGNORED = "ignored"


@dataclass
class VulnerabilityFinding:
    """安全漏洞发现记录"""
    id: str
    title: str
    severity: str
    cwe_id: Optional[str]
    file_path: str
    line_number: int
    description: str
    status: str = "open"
    confidence: float = 1.0
    false_positive_rate: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VulnerabilityFinding':
        """从字典创建实例"""
        return cls(**data)


@dataclass
class CVEKnowledge:
    """CVE 知识库条目"""
    cve_id: str
    description: str
    cvss_score: float
    affected_versions: List[str] = field(default_factory=list)
    patch_url: Optional[str] = None
    references: List[str] = field(default_factory=list)
    published_date: Optional[str] = None
    last_modified: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CVEKnowledge':
        """从字典创建实例"""
        return cls(**data)


@dataclass
class VulnerabilityPattern:
    """漏洞模式识别"""
    pattern_id: str
    name: str
    description: str
    code_pattern: str
    severity: str
    false_positive_rate: float = 0.0
    detection_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VulnerabilityPattern':
        """从字典创建实例"""
        return cls(**data)


@dataclass
class PatchHistory:
    """补丁历史记录"""
    patch_id: str
    finding_id: str
    original_code: str
    patched_code: str
    patch_description: str
    applied_at: str = field(default_factory=lambda: datetime.now().isoformat())
    success_rate: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PatchHistory':
        """从字典创建实例"""
        return cls(**data)
