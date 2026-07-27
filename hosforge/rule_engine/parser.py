"""YAML rule parser for Security Rule DSL."""
import os
from pathlib import Path
from typing import Any

import yaml

from hosforge.rule_engine.schema import (
    DataFlowPattern,
    LogicOperator,
    PatternType,
    RuleCondition,
    RulePattern,
    RuleType,
    RuleValidationError,
    Sanitizer,
    SecurityRule,
    Severity,
    TaintSink,
    TaintSource,
)


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

        # Build taint analysis components
        taint_sources = [self._build_taint_source(s) for s in data.get("taint_sources", [])]
        taint_sinks = [self._build_taint_sink(s) for s in data.get("taint_sinks", [])]
        sanitizers = [self._build_sanitizer(s) for s in data.get("sanitizers", [])]
        data_flow = self._build_data_flow(data.get("data_flow")) if data.get("data_flow") else None

        return SecurityRule(
            name=data.get("name", ""),
            type=RuleType(data.get("type", "vulnerability")),
            severity=Severity(data.get("severity", "medium")),
            patterns=patterns,
            conditions=conditions,
            remediation=data.get("remediation", ""),
            metadata=data.get("metadata", {}),
            logic_operator=logic_op,
            taint_sources=taint_sources,
            taint_sinks=taint_sinks,
            sanitizers=sanitizers,
            data_flow=data_flow,
        )

    def _build_pattern(self, data: dict[str, Any]) -> RulePattern:
        """Build a RulePattern from parsed YAML data."""
        return RulePattern(
            type=PatternType(data.get("type", "regex")),
            language=data.get("language", "python"),
            pattern=data.get("pattern", ""),
            constraints=data.get("constraints", {}),
            is_source=data.get("is_source", False),
            is_sink=data.get("is_sink", False),
            is_sanitizer=data.get("is_sanitizer", False),
        )

    def _build_condition(self, data: dict[str, Any]) -> RuleCondition:
        """Build a RuleCondition from parsed YAML data."""
        return RuleCondition(
            input_source=data.get("input_source", ""),
            not_sanitized_by=data.get("not_sanitized_by", []),
        )

    def _build_taint_source(self, data: dict[str, Any]) -> TaintSource:
        """Build a TaintSource from parsed YAML data."""
        return TaintSource(
            name=data.get("name", ""),
            pattern=data.get("pattern", ""),
            language=data.get("language", "python"),
            description=data.get("description", ""),
        )

    def _build_taint_sink(self, data: dict[str, Any]) -> TaintSink:
        """Build a TaintSink from parsed YAML data."""
        severity_str = data.get("severity", "high")
        try:
            severity = Severity(severity_str)
        except ValueError:
            severity = Severity.HIGH
        return TaintSink(
            name=data.get("name", ""),
            pattern=data.get("pattern", ""),
            language=data.get("language", "python"),
            description=data.get("description", ""),
            severity=severity,
        )

    def _build_sanitizer(self, data: dict[str, Any]) -> Sanitizer:
        """Build a Sanitizer from parsed YAML data."""
        return Sanitizer(
            name=data.get("name", ""),
            pattern=data.get("pattern", ""),
            language=data.get("language", "python"),
            description=data.get("description", ""),
        )

    def _build_data_flow(self, data: dict[str, Any] | None) -> DataFlowPattern | None:
        """Build a DataFlowPattern from parsed YAML data."""
        if not data:
            return None
        return DataFlowPattern(
            source_pattern=data.get("source_pattern", ""),
            sink_pattern=data.get("sink_pattern", ""),
            sanitizers=data.get("sanitizers", []),
            language=data.get("language", "python"),
            description=data.get("description", ""),
        )
