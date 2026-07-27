"""Security Rule DSL schema definitions."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class PatternType(str, Enum):
    """Pattern matching type."""
    AST_MATCH = "ast_match"
    REGEX = "regex"
    SEMANTIC = "semantic"
    TAINT_FLOW = "taint_flow"


class Severity(str, Enum):
    """Security issue severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class RuleType(str, Enum):
    """Security rule types."""
    VULNERABILITY = "vulnerability"
    MISCONFIGURATION = "misconfiguration"
    BEST_PRACTICE = "best_practice"


class LogicOperator(str, Enum):
    """Logic operators for rule combination."""
    AND = "AND"
    OR = "OR"
    NOT = "NOT"


@dataclass
class RulePattern:
    """Pattern definition for security rule matching."""
    type: PatternType
    language: str
    pattern: str
    constraints: dict[str, Any] = field(default_factory=dict)


@dataclass
class RuleCondition:
    """Condition for rule evaluation."""
    input_source: str
    not_sanitized_by: list[str] = field(default_factory=list)


@dataclass
class SecurityRule:
    """Security rule definition."""
    name: str
    type: RuleType
    severity: Severity
    patterns: list[RulePattern]
    conditions: list[RuleCondition] = field(default_factory=list)
    remediation: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    logic_operator: LogicOperator = LogicOperator.OR


@dataclass
class RuleMatchResult:
    """Result of rule matching."""
    rule_name: str
    matched: bool
    location: Optional[str] = None
    severity: Optional[Severity] = None
    description: Optional[str] = None
    remediation: Optional[str] = None
    matched_pattern: Optional[str] = None
    cwe_ids: list[str] = field(default_factory=list)
    owasp_category: Optional[str] = None
