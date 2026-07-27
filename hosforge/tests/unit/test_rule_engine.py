"""Unit tests for Rule Engine."""
import pytest
from pathlib import Path

from hosforge.rule_engine import RuleEngine, RuleParser
from hosforge.rule_engine.schema import (
    SecurityRule,
    RulePattern,
    PatternType,
    Severity,
    LogicOperator,
    RuleValidationError,
)


class TestRuleEngine:
    """Test Rule Engine core functionality."""

    def test_engine_initialization(self):
        """Test RuleEngine initialization with rules."""
        rules = [
            SecurityRule(
                name="test_rule",
                type="vulnerability",
                severity=Severity.HIGH,
                description="Test rule",
                patterns=[
                    RulePattern(
                        type=PatternType.REGEX,
                        language="python",
                        pattern="eval\\(",
                    )
                ],
                logic_operator=LogicOperator.OR,
            )
        ]
        engine = RuleEngine(rules)
        assert engine.rules == rules
        assert len(engine.rules) == 1

    def test_evaluate_regex_pattern_match(self):
        """Test evaluating regex pattern that matches."""
        rules = [
            SecurityRule(
                name="test_eval",
                type="vulnerability",
                severity=Severity.HIGH,
                description="Detects eval usage",
                patterns=[
                    RulePattern(
                        type=PatternType.REGEX,
                        language="python",
                        pattern="eval\\(",
                    )
                ],
                logic_operator=LogicOperator.OR,
            )
        ]
        engine = RuleEngine(rules)
        code = "result = eval(user_input)"
        results = engine.evaluate(code, "python")
        
        assert len(results) == 1
        assert results[0].rule_name == "test_eval"
        assert results[0].matched is True
        assert results[0].severity == Severity.HIGH
        assert "line" in results[0].location

    def test_evaluate_regex_pattern_no_match(self):
        """Test evaluating regex pattern that doesn't match."""
        rules = [
            SecurityRule(
                name="test_eval",
                type="vulnerability",
                severity=Severity.HIGH,
                description="Detects eval usage",
                patterns=[
                    RulePattern(
                        type=PatternType.REGEX,
                        language="python",
                        pattern="eval\\(",
                    )
                ],
                logic_operator=LogicOperator.OR,
            )
        ]
        engine = RuleEngine(rules)
        code = "result = safe_function(user_input)"
        results = engine.evaluate(code, "python")
        
        assert len(results) == 1
        assert results[0].matched is False
        assert results[0].severity is None

    def test_evaluate_multiple_rules(self):
        """Test evaluating multiple rules."""
        rules = [
            SecurityRule(
                name="rule1",
                type="vulnerability",
                severity=Severity.HIGH,
                description="Rule 1",
                patterns=[
                    RulePattern(
                        type=PatternType.REGEX,
                        language="python",
                        pattern="eval\\(",
                    )
                ],
                logic_operator=LogicOperator.OR,
            ),
            SecurityRule(
                name="rule2",
                type="vulnerability",
                severity=Severity.CRITICAL,
                description="Rule 2",
                patterns=[
                    RulePattern(
                        type=PatternType.REGEX,
                        language="python",
                        pattern="exec\\(",
                    )
                ],
                logic_operator=LogicOperator.OR,
            ),
        ]
        engine = RuleEngine(rules)
        code = "eval(input())\nexec(code)"
        results = engine.evaluate(code, "python")
        
        assert len(results) == 2
        assert all(r.matched for r in results)

    def test_evaluate_language_filter(self):
        """Test that rules only match specified language."""
        rules = [
            SecurityRule(
                name="python_rule",
                type="vulnerability",
                severity=Severity.HIGH,
                description="Python rule",
                patterns=[
                    RulePattern(
                        type=PatternType.REGEX,
                        language="python",
                        pattern="eval\\(",
                    )
                ],
                logic_operator=LogicOperator.OR,
            )
        ]
        engine = RuleEngine(rules)
        
        # Should match Python code
        python_code = "eval(input())"
        results = engine.evaluate(python_code, "python")
        assert results[0].matched is True
        
        # Should not match JavaScript code (different language)
        js_code = "eval(input())"
        results = engine.evaluate(js_code, "javascript")
        assert results[0].matched is False

    def test_evaluate_logic_operator_and(self):
        """Test AND logic operator."""
        rules = [
            SecurityRule(
                name="and_rule",
                type="vulnerability",
                severity=Severity.HIGH,
                description="AND rule",
                patterns=[
                    RulePattern(
                        type=PatternType.REGEX,
                        language="python",
                        pattern="eval\\(",
                    ),
                    RulePattern(
                        type=PatternType.REGEX,
                        language="python",
                        pattern="input\\(",
                    ),
                ],
                logic_operator=LogicOperator.AND,
            )
        ]
        engine = RuleEngine(rules)
        
        # Both patterns present
        code = "eval(input())"
        results = engine.evaluate(code, "python")
        assert results[0].matched is True
        
        # Only one pattern present
        code = "eval(safe_value)"
        results = engine.evaluate(code, "python")
        assert results[0].matched is False

    def test_evaluate_logic_operator_or(self):
        """Test OR logic operator."""
        rules = [
            SecurityRule(
                name="or_rule",
                type="vulnerability",
                severity=Severity.HIGH,
                description="OR rule",
                patterns=[
                    RulePattern(
                        type=PatternType.REGEX,
                        language="python",
                        pattern="eval\\(",
                    ),
                    RulePattern(
                        type=PatternType.REGEX,
                        language="python",
                        pattern="exec\\(",
                    ),
                ],
                logic_operator=LogicOperator.OR,
            )
        ]
        engine = RuleEngine(rules)
        
        # First pattern present
        code = "eval(input())"
        results = engine.evaluate(code, "python")
        assert results[0].matched is True
        
        # Second pattern present
        code = "exec(code)"
        results = engine.evaluate(code, "python")
        assert results[0].matched is True
        
        # Neither pattern present
        code = "safe_function()"
        results = engine.evaluate(code, "python")
        assert results[0].matched is False

    def test_evaluate_logic_operator_not(self):
        """Test NOT logic operator."""
        rules = [
            SecurityRule(
                name="not_rule",
                type="vulnerability",
                severity=Severity.HIGH,
                description="NOT rule",
                patterns=[
                    RulePattern(
                        type=PatternType.REGEX,
                        language="python",
                        pattern="safe_",
                    ),
                ],
                logic_operator=LogicOperator.NOT,
            )
        ]
        engine = RuleEngine(rules)
        
        # Pattern not present - should match
        code = "dangerous_function()"
        results = engine.evaluate(code, "python")
        assert results[0].matched is True
        
        # Pattern present - should not match
        code = "safe_function()"
        results = engine.evaluate(code, "python")
        assert results[0].matched is False

    def test_evaluate_taint_flow_detection(self):
        """Test taint flow pattern detection."""
        rules = [
            SecurityRule(
                name="taint_rule",
                type="vulnerability",
                severity=Severity.CRITICAL,
                description="Taint flow rule",
                patterns=[
                    RulePattern(
                        type=PatternType.TAINT_FLOW,
                        language="python",
                        pattern="execute",
                        constraints={
                            "sources": ["input", "request.args"],
                            "sinks": ["execute", "cursor.execute"],
                            "sanitizers": ["escape"],
                        },
                    )
                ],
                logic_operator=LogicOperator.OR,
            )
        ]
        engine = RuleEngine(rules)
        
        # Tainted flow detected
        code = """
def process(user_input):
    query = "SELECT * FROM users WHERE id = " + user_input
    cursor.execute(query)
"""
        results = engine.evaluate(code, "python")
        assert results[0].matched is True
        
        # Sanitized flow - should not match
        code = """
def process(user_input):
    safe_input = escape(user_input)
    query = "SELECT * FROM users WHERE id = " + safe_input
    cursor.execute(query)
"""
        results = engine.evaluate(code, "python")
        assert results[0].matched is False

    def test_evaluate_with_metadata(self):
        """Test that metadata is preserved in results."""
        rules = [
            SecurityRule(
                name="test_rule",
                type="vulnerability",
                severity=Severity.HIGH,
                description="Test rule",
                patterns=[
                    RulePattern(
                        type=PatternType.REGEX,
                        language="python",
                        pattern="eval\\(",
                    )
                ],
                logic_operator=LogicOperator.OR,
                metadata={"cwe": "CWE-95", "owasp": "A03:2021"},
            )
        ]
        engine = RuleEngine(rules)
        code = "eval(input())"
        results = engine.evaluate(code, "python")
        
        assert results[0].cwe_ids == ["CWE-95"]
        assert results[0].owasp_category == "A03:2021"

    def test_evaluate_invalid_regex(self):
        """Test handling of invalid regex pattern."""
        rules = [
            SecurityRule(
                name="invalid_regex",
                type="vulnerability",
                severity=Severity.HIGH,
                description="Invalid regex",
                patterns=[
                    RulePattern(
                        type=PatternType.REGEX,
                        language="python",
                        pattern="[invalid(",  # Invalid regex
                    )
                ],
                logic_operator=LogicOperator.OR,
            )
        ]
        engine = RuleEngine(rules)
        code = "some code"
        
        # Should not crash, just return no match
        results = engine.evaluate(code, "python")
        assert results[0].matched is False

    def test_evaluate_empty_code(self):
        """Test evaluating empty code."""
        rules = [
            SecurityRule(
                name="test_rule",
                type="vulnerability",
                severity=Severity.HIGH,
                description="Test rule",
                patterns=[
                    RulePattern(
                        type=PatternType.REGEX,
                        language="python",
                        pattern="eval\\(",
                    )
                ],
                logic_operator=LogicOperator.OR,
            )
        ]
        engine = RuleEngine(rules)
        code = ""
        results = engine.evaluate(code, "python")
        
        assert results[0].matched is False

    def test_evaluate_multiline_code(self):
        """Test evaluating multiline code."""
        rules = [
            SecurityRule(
                name="test_rule",
                type="vulnerability",
                severity=Severity.HIGH,
                description="Test rule",
                patterns=[
                    RulePattern(
                        type=PatternType.REGEX,
                        language="python",
                        pattern="eval\\(",
                    )
                ],
                logic_operator=LogicOperator.OR,
            )
        ]
        engine = RuleEngine(rules)
        code = """
def process():
    x = 1
    y = 2
    result = eval(input())
    return result
"""
        results = engine.evaluate(code, "python")
        
        assert results[0].matched is True
        assert "line" in results[0].location


class TestRuleParser:
    """Test Rule Parser functionality."""

    def test_parse_file_valid(self, tmp_path):
        """Test parsing a valid YAML rule file."""
        rule_content = """
name: test_rule
type: vulnerability
severity: high
description: Test rule
logic_operator: OR
patterns:
  - type: regex
    language: python
    pattern: "eval\\\\("
    constraints: {}
metadata:
  cwe: "CWE-95"
"""
        rule_file = tmp_path / "test_rule.yaml"
        rule_file.write_text(rule_content)
        
        parser = RuleParser()
        rule = parser.parse_file(str(rule_file))
        
        assert rule.name == "test_rule"
        assert rule.type == "vulnerability"
        assert rule.severity == Severity.HIGH
        assert len(rule.patterns) == 1
        assert rule.patterns[0].type == PatternType.REGEX
        assert rule.patterns[0].language == "python"

    def test_parse_file_with_taint_flow(self, tmp_path):
        """Test parsing a rule with taint flow pattern."""
        rule_content = """
name: taint_rule
type: vulnerability
severity: critical
description: Taint flow rule
logic_operator: OR
patterns:
  - type: taint_flow
    language: python
    pattern: "execute"
    constraints:
      sources:
        - input
        - request.args
      sinks:
        - execute
      sanitizers:
        - escape
metadata:
  cwe: "CWE-89"
"""
        rule_file = tmp_path / "taint_rule.yaml"
        rule_file.write_text(rule_content)
        
        parser = RuleParser()
        rule = parser.parse_file(str(rule_file))
        
        assert rule.patterns[0].type == PatternType.TAINT_FLOW
        assert "sources" in rule.patterns[0].constraints
        assert "sinks" in rule.patterns[0].constraints
        assert "sanitizers" in rule.patterns[0].constraints

    def test_parse_dir(self, tmp_path):
        """Test parsing a directory of rule files."""
        rule1_content = """
name: rule1
type: vulnerability
severity: high
description: Rule 1
logic_operator: OR
patterns:
  - type: regex
    language: python
    pattern: "eval\\\\("
"""
        rule2_content = """
name: rule2
type: vulnerability
severity: critical
description: Rule 2
logic_operator: OR
patterns:
  - type: regex
    language: python
    pattern: "exec\\\\("
"""
        (tmp_path / "rule1.yaml").write_text(rule1_content)
        (tmp_path / "rule2.yaml").write_text(rule2_content)
        
        parser = RuleParser()
        rules = parser.parse_dir(str(tmp_path))
        
        assert len(rules) == 2
        rule_names = {r.name for r in rules}
        assert "rule1" in rule_names
        assert "rule2" in rule_names

    def test_parse_file_invalid_yaml(self, tmp_path):
        """Test parsing invalid YAML raises error."""
        rule_content = """
name: test_rule
type: vulnerability
severity: high
description: Test rule
  invalid indentation
"""
        rule_file = tmp_path / "invalid.yaml"
        rule_file.write_text(rule_content)
        
        parser = RuleParser()
        with pytest.raises(Exception):  # yaml.YAMLError
            parser.parse_file(str(rule_file))

    def test_parse_file_missing_required_fields(self, tmp_path):
        """Test parsing file with missing required fields."""
        rule_content = """
name: test_rule
# Missing type, severity, patterns
"""
        rule_file = tmp_path / "incomplete.yaml"
        rule_file.write_text(rule_content)
        
        parser = RuleParser()
        with pytest.raises(RuleValidationError):
            parser.parse_file(str(rule_file))


class TestSecurityRule:
    """Test SecurityRule schema."""

    def test_rule_creation(self):
        """Test creating a SecurityRule."""
        rule = SecurityRule(
            name="test_rule",
            type="vulnerability",
            severity=Severity.HIGH,
            description="Test rule",
            patterns=[],
            logic_operator=LogicOperator.OR,
        )
        assert rule.name == "test_rule"
        assert rule.severity == Severity.HIGH

    def test_rule_with_metadata(self):
        """Test creating a rule with metadata."""
        rule = SecurityRule(
            name="test_rule",
            type="vulnerability",
            severity=Severity.HIGH,
            description="Test rule",
            patterns=[],
            logic_operator=LogicOperator.OR,
            metadata={"cwe": "CWE-95", "owasp": "A03:2021"},
        )
        assert rule.metadata["cwe"] == "CWE-95"
        assert rule.metadata["owasp"] == "A03:2021"


class TestRulePattern:
    """Test RulePattern schema."""

    def test_pattern_creation(self):
        """Test creating a RulePattern."""
        pattern = RulePattern(
            type=PatternType.REGEX,
            language="python",
            pattern="eval\\(",
        )
        assert pattern.type == PatternType.REGEX
        assert pattern.language == "python"

    def test_pattern_with_constraints(self):
        """Test creating a pattern with constraints."""
        pattern = RulePattern(
            type=PatternType.TAINT_FLOW,
            language="python",
            pattern="execute",
            constraints={
                "sources": ["input"],
                "sinks": ["execute"],
                "sanitizers": ["escape"],
            },
        )
        assert "sources" in pattern.constraints
        assert "sinks" in pattern.constraints


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
