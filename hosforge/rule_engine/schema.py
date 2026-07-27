"""Security Rule DSL schema definitions."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class RuleValidationError(Exception):
    """Exception raised when rule validation fails."""
    pass


class PatternType(str, Enum):
    """Pattern matching type."""
    AST_MATCH = "ast_match"
    REGEX = "regex"
    SEMANTIC = "semantic"  # Semantic pattern matching
    TAINT_FLOW = "taint_flow"  # Taint analysis pattern


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
    INJECTION = "injection"
    AUTH = "authentication"
    CRYPTO = "cryptography"


class LogicOperator(str, Enum):
    """Logic operators for rule combination."""
    AND = "AND"
    OR = "OR"
    NOT = "NOT"


class Language(str, Enum):
    """Supported programming languages."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    GO = "go"
    RUST = "rust"
    PHP = "php"
    RUBY = "ruby"
    CSHARP = "csharp"
    CPP = "cpp"


@dataclass
class RulePattern:
    """Pattern definition for security rule matching."""
    type: PatternType
    language: str
    pattern: str
    constraints: dict[str, Any] = field(default_factory=dict)
    # For taint analysis
    is_source: bool = False  # Marks this pattern as a taint source
    is_sink: bool = False  # Marks this pattern as a taint sink
    is_sanitizer: bool = False  # Marks this pattern as a sanitizer


@dataclass
class TaintSource:
    """Definition of a taint source (user input entry point)."""
    name: str
    pattern: str
    language: str
    description: str = ""


@dataclass
class TaintSink:
    """Definition of a taint sink (dangerous operation)."""
    name: str
    pattern: str
    language: str
    description: str = ""
    severity: Severity = Severity.HIGH


@dataclass
class Sanitizer:
    """Definition of a sanitizer (cleanses tainted data)."""
    name: str
    pattern: str
    language: str
    description: str = ""


@dataclass
class DataFlowPattern:
    """Pattern for data flow analysis."""
    source_pattern: str
    sink_pattern: str
    sanitizers: list[str] = field(default_factory=list)
    language: str = "python"
    description: str = ""


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
    # Enhanced fields for taint analysis
    taint_sources: list[TaintSource] = field(default_factory=list)
    taint_sinks: list[TaintSink] = field(default_factory=list)
    sanitizers: list[Sanitizer] = field(default_factory=list)
    data_flow: Optional[DataFlowPattern] = None


@dataclass
class MatchLocation:
    """Detailed location information for a match."""
    line: int
    column: int = 0
    end_line: Optional[int] = None
    end_column: Optional[int] = None
    file_path: Optional[str] = None
    code_snippet: Optional[str] = None


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
    # Enhanced fields
    match_location: Optional[MatchLocation] = None
    confidence: float = 1.0  # 0.0 to 1.0
    cwe_ids: list[str] = field(default_factory=list)
    owasp_category: Optional[str] = None
    code_context: Optional[str] = None  # Surrounding code for context
    suggestions: list[str] = field(default_factory=list)
