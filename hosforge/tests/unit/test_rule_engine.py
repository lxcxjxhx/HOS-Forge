"""Unit tests for Rule Engine."""
import pytest
from pathlib import Path

from hosforge.rule_engine import (
    RuleEngine,
    RuleParser,
    SecurityRule,
    RuleMatchResult,
    Severity,
    PatternType,
    RuleType,
)


class TestRuleEngine:
    """Test Rule Engine functionality."""

    def test_regex_pattern_matching(self):
        """Test regex pattern matching."""
        from hosforge.rule_engine.schema import RulePattern, LogicOperator
        
        rule = SecurityRule(
            name="test_rule",
            type=RuleType.VULNERABILITY,
            severity=Severity.HIGH,
            patterns=[
                RulePattern(
                    type=PatternType.REGEX,
                    language="python",
                    pattern=r"exec\s*\(",
                )
            ],
            logic_operator=LogicOperator.OR,
        )
        
        engine = RuleEngine([rule])
        
        # Should match
        code_with_exec = "user_input = input()\nexec(user_input)"
        results = engine.evaluate(code_with_exec, "python")
        assert len(results) == 1
        assert results[0].matched is True
        assert results[0].rule_name == "test_rule"
        
        # Should not match
        code_without_exec = "user_input = input()\nprint(user_input)"
        results = engine.evaluate(code_without_exec, "python")
        assert results[0].matched is False

    def test_taint_flow_detection(self):
        """Test taint flow pattern detection."""
        from hosforge.rule_engine.schema import RulePattern, LogicOperator
        
        rule = SecurityRule(
            name="taint_test",
            type=RuleType.VULNERABILITY,
            severity=Severity.CRITICAL,
            patterns=[
                RulePattern(
                    type=PatternType.TAINT_FLOW,
                    language="python",
                    pattern="taint_flow",
                )
            ],
            logic_operator=LogicOperator.OR,
        )
        
        engine = RuleEngine([rule])
        
        # Should detect taint flow: input() -> exec()
        tainted_code = """
user_input = input()
exec(user_input)
"""
        results = engine.evaluate(tainted_code, "python")
        assert results[0].matched is True
        
        # Should not detect: no source
        clean_code = """
data = "static"
exec(data)
"""
        results = engine.evaluate(clean_code, "python")
        assert results[0].matched is False

    def test_semantic_pattern_dangerous_function(self):
        """Test semantic pattern for dangerous functions."""
        from hosforge.rule_engine.schema import RulePattern, LogicOperator
        
        rule = SecurityRule(
            name="dangerous_func",
            type=RuleType.VULNERABILITY,
            severity=Severity.HIGH,
            patterns=[
                RulePattern(
                    type=PatternType.SEMANTIC,
                    language="python",
                    pattern="dangerous_function",
                )
            ],
            logic_operator=LogicOperator.OR,
        )
        
        engine = RuleEngine([rule])
        
        # Should detect exec()
        code = "exec('print(1)')"
        results = engine.evaluate(code, "python")
        assert results[0].matched is True
        
        # Should detect eval()
        code = "eval('1+1')"
        results = engine.evaluate(code, "python")
        assert results[0].matched is True

    def test_semantic_pattern_hardcoded_credential(self):
        """Test semantic pattern for hardcoded credentials."""
        from hosforge.rule_engine.schema import RulePattern, LogicOperator
        
        rule = SecurityRule(
            name="hardcoded_cred",
            type=RuleType.VULNERABILITY,
            severity=Severity.HIGH,
            patterns=[
                RulePattern(
                    type=PatternType.SEMANTIC,
                    language="python",
                    pattern="hardcoded_credential",
                )
            ],
            logic_operator=LogicOperator.OR,
        )
        
        engine = RuleEngine([rule])
        
        # Should detect hardcoded password
        code = 'password = "secret123"'
        results = engine.evaluate(code, "python")
        assert results[0].matched is True
        
        # Should detect hardcoded api_key
        code = 'api_key = "abc123"'
        results = engine.evaluate(code, "python")
        assert results[0].matched is True

    def test_logic_operator_and(self):
        """Test AND logic operator."""
        from hosforge.rule_engine.schema import RulePattern, LogicOperator
        
        rule = SecurityRule(
            name="and_test",
            type=RuleType.VULNERABILITY,
            severity=Severity.MEDIUM,
            patterns=[
                RulePattern(
                    type=PatternType.REGEX,
                    language="python",
                    pattern=r"exec\s*\(",
                ),
                RulePattern(
                    type=PatternType.REGEX,
                    language="python",
                    pattern=r"input\s*\(",
                ),
            ],
            logic_operator=LogicOperator.AND,
        )
        
        engine = RuleEngine([rule])
        
        # Should match: both patterns present
        code = "user = input()\nexec(user)"
        results = engine.evaluate(code, "python")
        assert results[0].matched is True
        
        # Should not match: only one pattern present
        code = "exec('static')"
        results = engine.evaluate(code, "python")
        assert results[0].matched is False

    def test_logic_operator_not(self):
        """Test NOT logic operator."""
        from hosforge.rule_engine.schema import RulePattern, LogicOperator
        
        rule = SecurityRule(
            name="not_test",
            type=RuleType.BEST_PRACTICE,
            severity=Severity.LOW,
            patterns=[
                RulePattern(
                    type=PatternType.REGEX,
                    language="python",
                    pattern=r"# TODO",
                ),
            ],
            logic_operator=LogicOperator.NOT,
        )
        
        engine = RuleEngine([rule])
        
        # Should match: no TODO found (NOT condition satisfied)
        code = "# This is a comment"
        results = engine.evaluate(code, "python")
        assert results[0].matched is True
        
        # Should not match: TODO found
        code = "# TODO: fix this"
        results = engine.evaluate(code, "python")
        assert results[0].matched is False

    def test_cwe_and_owasp_extraction(self):
        """Test CWE and OWASP category extraction from metadata."""
        from hosforge.rule_engine.schema import RulePattern, LogicOperator
        
        rule = SecurityRule(
            name="metadata_test",
            type=RuleType.VULNERABILITY,
            severity=Severity.HIGH,
            patterns=[
                RulePattern(
                    type=PatternType.REGEX,
                    language="python",
                    pattern=r"exec\s*\(",
                )
            ],
            logic_operator=LogicOperator.OR,
            metadata={
                "cwe": "CWE-95",
                "owasp": "A03:2021",
                "description": "Test vulnerability",
            },
        )
        
        engine = RuleEngine([rule])
        code = "exec('test')"
        results = engine.evaluate(code, "python")
        
        assert results[0].matched is True
        assert "CWE-95" in results[0].cwe_ids
        assert results[0].owasp_category == "A03:2021"


class TestRuleParser:
    """Test Rule Parser functionality."""

    def test_parse_simple_rule(self, tmp_path):
        """Test parsing a simple YAML rule."""
        rule_content = """
name: test_rule
type: vulnerability
severity: high
logic_operator: OR

patterns:
  - type: regex
    language: python
    pattern: 'exec\\s*\\('

remediation: "Avoid using exec()"

metadata:
  cwe: "CWE-95"
  description: "Test rule"
"""
        rule_file = tmp_path / "test_rule.yaml"
        rule_file.write_text(rule_content)
        
        parser = RuleParser()
        rule = parser.parse_file(rule_file)
        
        assert rule.name == "test_rule"
        assert rule.type == RuleType.VULNERABILITY
        assert rule.severity == Severity.HIGH
        assert len(rule.patterns) == 1
        assert rule.patterns[0].type == PatternType.REGEX
        assert rule.patterns[0].language == "python"
        assert rule.remediation == "Avoid using exec()"
        assert rule.metadata["cwe"] == "CWE-95"

    def test_parse_rule_with_taint_components(self, tmp_path):
        """Test parsing rule with taint analysis components."""
        rule_content = """
name: taint_rule
type: vulnerability
severity: critical
logic_operator: OR

patterns:
  - type: taint_flow
    language: python
    pattern: "taint_flow"

taint_sources:
  - name: user_input
    pattern: "input\\(\\)"
    language: python
    description: "User input from stdin"

taint_sinks:
  - name: exec_sink
    pattern: "exec\\("
    language: python
    severity: critical

sanitizers:
  - name: escape_input
    pattern: "escape\\("
    language: python
"""
        rule_file = tmp_path / "taint_rule.yaml"
        rule_file.write_text(rule_content)
        
        parser = RuleParser()
        rule = parser.parse_file(rule_file)
        
        assert len(rule.taint_sources) == 1
        assert rule.taint_sources[0].name == "user_input"
        
        assert len(rule.taint_sinks) == 1
        assert rule.taint_sinks[0].name == "exec_sink"
        
        assert len(rule.sanitizers) == 1
        assert rule.sanitizers[0].name == "escape_input"

    def test_parse_directory(self, tmp_path):
        """Test parsing all rules from a directory."""
        rule1 = """
name: rule1
type: vulnerability
severity: high
patterns:
  - type: regex
    language: python
    pattern: 'test1'
"""
        rule2 = """
name: rule2
type: misconfiguration
severity: medium
patterns:
  - type: regex
    language: python
    pattern: 'test2'
"""
        (tmp_path / "rule1.yaml").write_text(rule1)
        (tmp_path / "rule2.yaml").write_text(rule2)
        
        parser = RuleParser()
        rules = parser.parse_dir(tmp_path)
        
        assert len(rules) == 2
        assert rules[0].name == "rule1"
        assert rules[1].name == "rule2"

    def test_validate_invalid_regex(self, tmp_path):
        """Test validation of invalid regex pattern."""
        rule_content = """
name: invalid_regex
type: vulnerability
severity: high
patterns:
  - type: regex
    language: python
    pattern: '[invalid'
"""
        rule_file = tmp_path / "invalid.yaml"
        rule_file.write_text(rule_content)
        
        parser = RuleParser()
        with pytest.raises(Exception):  # RuleValidationError
            parser.parse_file(rule_file)


class TestBuiltinRules:
    """Test built-in security rules."""

    def test_load_builtin_rules(self):
        """Test loading built-in rules from rules directory."""
        rules_dir = Path(__file__).parent.parent.parent / "rule_engine" / "rules"
        
        if rules_dir.exists():
            parser = RuleParser()
            rules = parser.parse_dir(rules_dir)
            
            # Should have at least some rules
            assert len(rules) > 0
            
            # All rules should be valid
            for rule in rules:
                assert rule.name != ""
                assert len(rule.patterns) > 0

    def test_sql_injection_rule(self):
        """Test SQL injection rule."""
        rules_dir = Path(__file__).parent.parent.parent / "rule_engine" / "rules"
        sql_rule_file = rules_dir / "sql_injection.yaml"
        
        if sql_rule_file.exists():
            parser = RuleParser()
            rule = parser.parse_file(sql_rule_file)
            
            engine = RuleEngine([rule])
            
            # Should detect SQL injection
            vulnerable_code = """
query = "SELECT * FROM users WHERE id = " + user_id
cursor.execute(query)
"""
            results = engine.evaluate(vulnerable_code, "python")
            assert any(r.matched for r in results)

    def test_xss_rule(self):
        """Test XSS rule."""
        rules_dir = Path(__file__).parent.parent.parent / "rule_engine" / "rules"
        xss_rule_file = rules_dir / "xss.yaml"
        
        if xss_rule_file.exists():
            parser = RuleParser()
            rule = parser.parse_file(xss_rule_file)
            
            engine = RuleEngine([rule])
            
            # Should detect XSS in Python
            vulnerable_code = 'render_template_string("<h1>" + user_input + "</h1>")'
            results = engine.evaluate(vulnerable_code, "python")
            assert any(r.matched for r in results)
