"""Unit tests for Security Rule DSL engine."""
import os
import tempfile
from pathlib import Path

import pytest

from hosforge.rule_engine import RuleEngine, RuleMatchResult, RuleParser, SecurityRule
from hosforge.rule_engine.parser import RuleValidationError
from hosforge.rule_engine.schema import (
    LogicOperator,
    PatternType,
    RuleCondition,
    RulePattern,
    RuleType,
    Severity,
)


RULES_DIR = Path(__file__).resolve().parents[2] / "hosforge" / "rule_engine" / "rules"


# --- Schema tests ---


class TestSchema:
    def test_rule_pattern_defaults(self):
        p = RulePattern(type=PatternType.REGEX, language="python", pattern=r"\d+")
        assert p.constraints == {}

    def test_security_rule_defaults(self):
        rule = SecurityRule(
            name="test",
            type=RuleType.VULNERABILITY,
            severity=Severity.HIGH,
            patterns=[],
        )
        assert rule.conditions == []
        assert rule.remediation == ""
        assert rule.metadata == {}
        assert rule.logic_operator == LogicOperator.OR

    def test_rule_match_result(self):
        result = RuleMatchResult(rule_name="test", matched=True)
        assert result.location is None
        assert result.severity is None


# --- Parser tests ---


class TestRuleParser:
    def setup_method(self):
        self.parser = RuleParser()

    def test_parse_file_basic(self, tmp_path: Path):
        yaml_content = """
name: test_rule
type: vulnerability
severity: high
patterns:
  - type: regex
    language: python
    pattern: 'eval\\s*\\('
conditions:
  - input_source: user_input
    not_sanitized_by:
      - sanitize
remediation: "Do not use eval"
metadata:
  cwe: "CWE-95"
"""
        rule_file = tmp_path / "test_rule.yaml"
        rule_file.write_text(yaml_content, encoding="utf-8")

        rule = self.parser.parse_file(rule_file)
        assert rule.name == "test_rule"
        assert rule.type == RuleType.VULNERABILITY
        assert rule.severity == Severity.HIGH
        assert len(rule.patterns) == 1
        assert rule.patterns[0].type == PatternType.REGEX
        assert rule.patterns[0].pattern == r"eval\s*\("
        assert len(rule.conditions) == 1
        assert rule.conditions[0].not_sanitized_by == ["sanitize"]
        assert rule.remediation == "Do not use eval"
        assert rule.metadata["cwe"] == "CWE-95"

    def test_parse_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            self.parser.parse_file("/nonexistent/path.yaml")

    def test_parse_dir(self, tmp_path: Path):
        for i in range(3):
            (tmp_path / f"rule_{i}.yaml").write_text(
                f"""
name: rule_{i}
type: vulnerability
severity: medium
patterns:
  - type: regex
    language: python
    pattern: 'test_{i}'
""",
                encoding="utf-8",
            )

        rules = self.parser.parse_dir(tmp_path)
        assert len(rules) == 3
        assert all(isinstance(r, SecurityRule) for r in rules)

    def test_parse_dir_not_a_directory(self, tmp_path: Path):
        with pytest.raises(NotADirectoryError):
            self.parser.parse_dir(tmp_path / "nonexistent")

    def test_validate_rule_missing_name(self):
        rule = SecurityRule(
            name="",
            type=RuleType.VULNERABILITY,
            severity=Severity.HIGH,
            patterns=[RulePattern(type=PatternType.REGEX, language="python", pattern="x")],
        )
        with pytest.raises(RuleValidationError, match="name"):
            self.parser.validate_rule(rule)

    def test_validate_rule_no_patterns(self):
        rule = SecurityRule(
            name="empty",
            type=RuleType.VULNERABILITY,
            severity=Severity.HIGH,
            patterns=[],
        )
        with pytest.raises(RuleValidationError, match="at least one pattern"):
            self.parser.validate_rule(rule)

    def test_validate_rule_invalid_regex(self):
        rule = SecurityRule(
            name="bad_regex",
            type=RuleType.VULNERABILITY,
            severity=Severity.HIGH,
            patterns=[RulePattern(type=PatternType.REGEX, language="python", pattern="[invalid")],
        )
        with pytest.raises(RuleValidationError, match="invalid regex"):
            self.parser.validate_rule(rule)

    def test_parse_file_with_logic_operator(self, tmp_path: Path):
        yaml_content = """
name: and_rule
type: vulnerability
severity: high
logic_operator: AND
patterns:
  - type: regex
    language: python
    pattern: 'eval\\s*\\('
  - type: regex
    language: python
    pattern: 'input\\s*\\('
"""
        rule_file = tmp_path / "and_rule.yaml"
        rule_file.write_text(yaml_content, encoding="utf-8")

        rule = self.parser.parse_file(rule_file)
        assert rule.logic_operator == LogicOperator.AND
        assert len(rule.patterns) == 2


# --- Engine tests ---


class TestRuleEngine:
    def _make_rule(
        self,
        name: str,
        patterns: list[tuple[str, str]],
        logic: LogicOperator = LogicOperator.OR,
    ) -> SecurityRule:
        return SecurityRule(
            name=name,
            type=RuleType.VULNERABILITY,
            severity=Severity.HIGH,
            patterns=[
                RulePattern(type=PatternType.REGEX, language=lang, pattern=pat)
                for lang, pat in patterns
            ],
            logic_operator=logic,
            remediation="fix it",
        )

    def test_evaluate_regex_match(self):
        rule = self._make_rule("eval_detect", [("python", r"eval\s*\(")])
        engine = RuleEngine([rule])

        results = engine.evaluate("x = eval(user_input)", "python")
        assert len(results) == 1
        assert results[0].matched is True
        assert results[0].rule_name == "eval_detect"
        assert results[0].severity == Severity.HIGH
        assert results[0].location is not None
        assert "line 1" in results[0].location

    def test_evaluate_no_match(self):
        rule = self._make_rule("eval_detect", [("python", r"eval\s*\(")])
        engine = RuleEngine([rule])

        results = engine.evaluate("x = safe_function()", "python")
        assert results[0].matched is False
        assert results[0].severity is None
        assert results[0].remediation is None

    def test_evaluate_language_mismatch(self):
        rule = self._make_rule("eval_detect", [("python", r"eval\s*\(")])
        engine = RuleEngine([rule])

        results = engine.evaluate("eval(user_input)", "javascript")
        assert results[0].matched is False

    def test_evaluate_or_logic(self):
        rule = self._make_rule(
            "multi",
            [("python", r"eval\s*\("), ("python", r"exec\s*\(")],
            LogicOperator.OR,
        )
        engine = RuleEngine([rule])

        # Only second pattern matches
        results = engine.evaluate("exec(cmd)", "python")
        assert results[0].matched is True

    def test_evaluate_and_logic(self):
        rule = self._make_rule(
            "multi_and",
            [("python", r"eval\s*\("), ("python", r"input\s*\(")],
            LogicOperator.AND,
        )
        engine = RuleEngine([rule])

        # Only one pattern matches -> AND fails
        results = engine.evaluate("x = eval(input())", "python")
        # Both patterns match in this case
        assert results[0].matched is True

        # Only eval, no input -> AND fails
        results2 = engine.evaluate("x = eval(something)", "python")
        assert results2[0].matched is False

    def test_evaluate_not_logic(self):
        rule = self._make_rule(
            "not_eval",
            [("python", r"eval\s*\(")],
            LogicOperator.NOT,
        )
        engine = RuleEngine([rule])

        # eval present -> NOT inverts to False
        results = engine.evaluate("eval(bad)", "python")
        assert results[0].matched is False

        # no eval -> NOT inverts to True
        results2 = engine.evaluate("safe_code()", "python")
        assert results2[0].matched is True

    def test_evaluate_multiple_rules(self):
        rules = [
            self._make_rule("rule_a", [("python", r"eval\s*\(")]),
            self._make_rule("rule_b", [("python", r"exec\s*\(")]),
        ]
        engine = RuleEngine(rules)

        results = engine.evaluate("eval(x); exec(y)", "python")
        assert len(results) == 2
        assert all(r.matched for r in results)

    def test_evaluate_multiline_location(self):
        rule = self._make_rule("detect", [("python", r"DANGER")])
        engine = RuleEngine([rule])

        code = "line1\nline2\nDANGER here"
        results = engine.evaluate(code, "python")
        assert results[0].matched is True
        assert "line 3" in results[0].location

    def test_evaluate_ast_match(self):
        rule = SecurityRule(
            name="ast_exec",
            type=RuleType.VULNERABILITY,
            severity=Severity.CRITICAL,
            patterns=[
                RulePattern(
                    type=PatternType.AST_MATCH,
                    language="python",
                    pattern="exec(",
                )
            ],
        )
        engine = RuleEngine([rule])

        results = engine.evaluate("exec('print(1)')", "python")
        assert results[0].matched is True


# --- Predefined rules loading tests ---


class TestPredefinedRules:
    def test_load_all_predefined_rules(self):
        parser = RuleParser()
        rules = parser.parse_dir(RULES_DIR)
        assert len(rules) >= 5
        names = {r.name for r in rules}
        expected = {
            "sql_injection",
            "xss",
            "command_injection",
            "path_traversal",
            "hardcoded_secret",
        }
        assert expected.issubset(names)

    def test_sql_injection_rule_detects(self):
        parser = RuleParser()
        rules = parser.parse_dir(RULES_DIR)
        sql_rule = next(r for r in rules if r.name == "sql_injection")
        engine = RuleEngine([sql_rule])

        code = 'cursor.execute("SELECT * FROM users WHERE id = %s" % user_id)'
        results = engine.evaluate(code, "python")
        assert results[0].matched is True

    def test_command_injection_rule_detects(self):
        parser = RuleParser()
        rules = parser.parse_dir(RULES_DIR)
        cmd_rule = next(r for r in rules if r.name == "command_injection")
        engine = RuleEngine([cmd_rule])

        code = 'os.system("ls " + user_input)'
        results = engine.evaluate(code, "python")
        assert results[0].matched is True

    def test_hardcoded_secret_rule_detects(self):
        parser = RuleParser()
        rules = parser.parse_dir(RULES_DIR)
        secret_rule = next(r for r in rules if r.name == "hardcoded_secret")
        engine = RuleEngine([secret_rule])

        code = 'password = "super_secret_123"'
        results = engine.evaluate(code, "python")
        assert results[0].matched is True

    def test_path_traversal_rule_detects(self):
        parser = RuleParser()
        rules = parser.parse_dir(RULES_DIR)
        path_rule = next(r for r in rules if r.name == "path_traversal")
        engine = RuleEngine([path_rule])

        code = 'f = open("/etc/" + user_input)'
        results = engine.evaluate(code, "python")
        assert results[0].matched is True

    def test_xss_rule_detects_javascript(self):
        parser = RuleParser()
        rules = parser.parse_dir(RULES_DIR)
        xss_rule = next(r for r in rules if r.name == "xss")
        engine = RuleEngine([xss_rule])

        code = 'element.innerHTML = userInput'
        results = engine.evaluate(code, "javascript")
        assert results[0].matched is True

    def test_safe_code_no_match(self):
        parser = RuleParser()
        rules = parser.parse_dir(RULES_DIR)
        engine = RuleEngine(rules)

        safe_code = """
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("API_KEY")
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
"""
        results = engine.evaluate(safe_code, "python")
        # hardcoded_secret should NOT match because os.environ.get is used
        secret_results = [r for r in results if r.rule_name == "hardcoded_secret"]
        assert not secret_results[0].matched
