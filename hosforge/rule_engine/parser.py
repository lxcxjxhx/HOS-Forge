"""YAML rule parser for Security Rule DSL."""
import os
from pathlib import Path
from typing import Any

import yaml

from hosforge.rule_engine.schema import (
    LogicOperator,
    PatternType,
    RuleCondition,
    RulePattern,
    RuleType,
    SecurityRule,
    Severity,
)


class RuleValidationError(Exception):
    """Raised when a rule fails validation."""


class RuleParser:
    """Parser for YAML security rules."""

    def parse_file(self, path: str | Path) -> SecurityRule:
        """Load a single rule from a YAML file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Rule file not found: {path}")

        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        rule = self._build_rule(data)
        self.validate_rule(rule)
        return rule

    def parse_dir(self, dir_path: str | Path) -> list[SecurityRule]:
        """Load all YAML rules from a directory."""
        dir_path = Path(dir_path)
        if not dir_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {dir_path}")

        rules: list[SecurityRule] = []
        for yaml_file in sorted(dir_path.glob("*.yaml")):
            rules.append(self.parse_file(yaml_file))
        for yaml_file in sorted(dir_path.glob("*.yml")):
            rules.append(self.parse_file(yaml_file))
        return rules

    def validate_rule(self, rule: SecurityRule) -> None:
        """Validate a rule's structure and values."""
        if not rule.name:
            raise RuleValidationError("Rule name is required")
        if not rule.patterns:
            raise RuleValidationError(f"Rule '{rule.name}' must have at least one pattern")
        for i, pattern in enumerate(rule.patterns):
            if not pattern.pattern:
                raise RuleValidationError(
                    f"Rule '{rule.name}' pattern[{i}] has empty pattern"
                )
            if pattern.type == PatternType.REGEX:
                import re
                try:
                    re.compile(pattern.pattern)
                except re.error as e:
                    raise RuleValidationError(
                        f"Rule '{rule.name}' pattern[{i}] has invalid regex: {e}"
                    ) from e

    def _build_rule(self, data: dict[str, Any]) -> SecurityRule:
        """Build a SecurityRule from parsed YAML data."""
        patterns = [self._build_pattern(p) for p in data.get("patterns", [])]
        conditions = [self._build_condition(c) for c in data.get("conditions", [])]

        logic_op_str = data.get("logic_operator", "OR")
        try:
            logic_op = LogicOperator(logic_op_str)
        except ValueError:
            logic_op = LogicOperator.OR

        return SecurityRule(
            name=data.get("name", ""),
            type=RuleType(data.get("type", "vulnerability")),
            severity=Severity(data.get("severity", "medium")),
            patterns=patterns,
            conditions=conditions,
            remediation=data.get("remediation", ""),
            metadata=data.get("metadata", {}),
            logic_operator=logic_op,
        )

    def _build_pattern(self, data: dict[str, Any]) -> RulePattern:
        """Build a RulePattern from parsed YAML data."""
        return RulePattern(
            type=PatternType(data.get("type", "regex")),
            language=data.get("language", "python"),
            pattern=data.get("pattern", ""),
            constraints=data.get("constraints", {}),
        )

    def _build_condition(self, data: dict[str, Any]) -> RuleCondition:
        """Build a RuleCondition from parsed YAML data."""
        return RuleCondition(
            input_source=data.get("input_source", ""),
            not_sanitized_by=data.get("not_sanitized_by", []),
        )
