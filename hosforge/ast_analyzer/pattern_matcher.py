"""Pattern matching engine for vulnerability detection."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import yaml

from hosforge.ast_analyzer.python_parser import ASTNode, ParseResult


@dataclass
class VulnerabilityPattern:
    """A single vulnerability pattern loaded from YAML."""

    name: str
    severity: str
    pattern_type: str  # "call", "assignment", "import", "regex", "innerHTML"
    description: str = ""
    remediation: str = ""
    targets: List[str] = field(default_factory=list)
    language: str = ""
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Finding:
    """A single vulnerability finding."""

    pattern_name: str
    severity: str
    description: str
    remediation: str
    file: str = ""
    line: int = 0
    col: int = 0
    matched_value: str = ""


class PatternMatcher:
    """Load vulnerability patterns from YAML and match against parsed AST nodes."""

    def __init__(self) -> None:
        self.patterns: List[VulnerabilityPattern] = []

    # ------------------------------------------------------------------
    # Pattern loading
    # ------------------------------------------------------------------

    def load_patterns(self, yaml_path: str) -> None:
        """Load patterns from a YAML file."""
        with open(yaml_path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)

        if not data or "patterns" not in data:
            return

        for entry in data["patterns"]:
            self.patterns.append(VulnerabilityPattern(
                name=entry.get("name", ""),
                severity=entry.get("severity", "info"),
                pattern_type=entry.get("pattern_type", ""),
                description=entry.get("description", ""),
                remediation=entry.get("remediation", ""),
                targets=entry.get("targets", []),
                language=entry.get("language", ""),
                attributes=entry.get("attributes", {}),
            ))

    def load_from_directory(self, directory: str) -> None:
        """Load all YAML pattern files from a directory."""
        if not os.path.isdir(directory):
            return
        for fname in sorted(os.listdir(directory)):
            if fname.endswith((".yaml", ".yml")):
                self.load_patterns(os.path.join(directory, fname))

    # ------------------------------------------------------------------
    # Matching
    # ------------------------------------------------------------------

    def match(self, parse_result: ParseResult, file_path: str = "") -> List[Finding]:
        """Match loaded patterns against a parse result."""
        findings: List[Finding] = []
        lang_patterns = [p for p in self.patterns if not p.language or p.language == parse_result.language]

        for node in parse_result.nodes:
            for pattern in lang_patterns:
                finding = self._check_pattern(pattern, node, file_path)
                if finding is not None:
                    findings.append(finding)
        return findings

    def _check_pattern(
        self, pattern: VulnerabilityPattern, node: ASTNode, file_path: str
    ) -> Optional[Finding]:
        """Check a single pattern against a single node."""
        matched = False

        if pattern.pattern_type == "call":
            matched = node.node_type == "call" and node.name in pattern.targets
        elif pattern.pattern_type == "assignment":
            if node.node_type != "assignment":
                return None
            name_lower = node.name.lower()
            matched = any(t.lower() in name_lower for t in pattern.targets)
        elif pattern.pattern_type == "import":
            matched = node.node_type == "import" and node.name in pattern.targets
        elif pattern.pattern_type == "innerHTML":
            matched = node.node_type == "innerHTML_assignment"
            if matched and pattern.targets:
                matched = any(t in node.name for t in pattern.targets)
        elif pattern.pattern_type == "regex":
            # Regex patterns are checked against the raw source value
            import re
            for target in pattern.targets:
                if re.search(target, node.value or node.name):
                    matched = True
                    break

        if not matched:
            return None

        return Finding(
            pattern_name=pattern.name,
            severity=pattern.severity,
            description=pattern.description,
            remediation=pattern.remediation,
            file=file_path,
            line=node.line,
            col=node.col,
            matched_value=node.name or node.value,
        )
