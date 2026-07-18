"""
HOS-Silly-Mock: 类型定义 — 所有检测结果、配置和评分系统的类型。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RiskLevel(str, Enum):
    """风险等级"""
    CRITICAL = 'critical'
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'
    INFO = 'info'


class LayerId(str, Enum):
    """检测层级"""
    MOCK = 'L1-MOCK'
    REGEX = 'L2-REGEX'
    BINDING = 'L3-BINDING'
    SILENT = 'L4-SILENT'


class FindingType(str, Enum):
    """检测结果类型"""
    MOCK_LEAKAGE = 'mock-leakage'
    REGEX_ABUSE = 'regex-abuse'
    UNBOUND_VARIABLE = 'unbound-variable'
    SILENT_FAILURE = 'silent-failure'
    MISSING_ERROR_HANDLING = 'missing-error-handling'


@dataclass
class Finding:
    """单个检测发现"""
    layer: LayerId
    type: FindingType
    severity: RiskLevel
    file: str
    line: int
    column: int | None = None
    message: str = ''
    snippet: str | None = None
    suggestion: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            'layer': self.layer.value,
            'type': self.type.value,
            'severity': self.severity.value,
            'file': self.file,
            'line': self.line,
            'column': self.column,
            'message': self.message,
            'snippet': self.snippet,
            'suggestion': self.suggestion,
        }


@dataclass
class SourceTransformSink:
    """Reality Binding 三元组"""
    name: str
    source: str | None = None
    transforms: list[str] = field(default_factory=list)
    sink: str | None = None
    complete: bool = False


@dataclass
class Dimensions:
    """各维度评分"""
    data_authenticity: int = 100
    mock_leakage_risk: RiskLevel = RiskLevel.INFO
    regex_abuse_risk: RiskLevel = RiskLevel.INFO
    silent_failure_risk: str = 'NO'
    reality_binding: str = 'PASS'


@dataclass
class Summary:
    """统计摘要"""
    total_findings: int = 0
    errors: int = 0
    warnings: int = 0
    info: int = 0


@dataclass
class EnforcementResult:
    """引擎执行结果"""
    passed: bool = True
    reality_score: int = 100
    dimensions: Dimensions = field(default_factory=Dimensions)
    findings: list[Finding] = field(default_factory=list)
    summary: Summary = field(default_factory=Summary)

    def to_dict(self) -> dict[str, Any]:
        return {
            'passed': self.passed,
            'reality_score': self.reality_score,
            'dimensions': {
                'data_authenticity': self.dimensions.data_authenticity,
                'mock_leakage_risk': self.dimensions.mock_leakage_risk.value,
                'regex_abuse_risk': self.dimensions.regex_abuse_risk.value,
                'silent_failure_risk': self.dimensions.silent_failure_risk,
                'reality_binding': self.dimensions.reality_binding,
            },
            'findings': [f.to_dict() for f in self.findings],
            'summary': {
                'total_findings': self.summary.total_findings,
                'errors': self.summary.errors,
                'warnings': self.summary.warnings,
                'info': self.summary.info,
            },
        }
