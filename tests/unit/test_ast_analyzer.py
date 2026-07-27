"""Unit tests for AST analyzer module."""
import json
import os
import tempfile
from pathlib import Path

import pytest

from hosforge.ast_analyzer import (
    JavaScriptParser,
    PatternMatcher,
    PythonASTParser,
    ReportGenerator,
    TaintAnalyzer,
)


# ============================================================================
# Python AST Parser Tests
# ============================================================================


class TestPythonASTParser:
    """Test Python AST parser."""

    def test_parse_simple_code(self):
        """Test parsing simple Python code."""
        parser = PythonASTParser()
        code = """
x = 10
y = 20
"""
        result = parser.parse(code)
        assert result.language == "python"
        assert len(result.errors) == 0
        assert len(result.nodes) > 0

    def test_find_dangerous_calls(self):
        """Test detection of dangerous function calls."""
        parser = PythonASTParser()
        code = """
import os
os.system("ls -la")
eval("1 + 1")
exec("print('hello')")
"""
        findings = parser.find_dangerous_calls(code)
        assert len(findings) >= 2  # os.system, eval, exec
        names = [f.name for f in findings]
        assert "os.system" in names or "eval" in names or "exec" in names

    def test_find_hardcoded_strings(self):
        """Test detection of hardcoded secrets."""
        parser = PythonASTParser()
        code = """
password = "secret123"
api_key = "abc123"
normal_var = "hello"
"""
        findings = parser.find_hardcoded_strings(code)
        assert len(findings) >= 2
        names = [f.name for f in findings]
        assert "password" in names
        assert "api_key" in names

    def test_find_imports(self):
        """Test import detection."""
        parser = PythonASTParser()
        code = """
import os
import sys
from subprocess import call
"""
        imports = parser.find_imports(code)
        assert len(imports) >= 3

    def test_find_dangerous_imports(self):
        """Test detection of dangerous imports."""
        parser = PythonASTParser()
        code = """
import os
import subprocess
import json
"""
        findings = parser.find_dangerous_imports(code)
        assert len(findings) >= 2
        names = [f.name for f in findings]
        assert "os" in names
        assert "subprocess" in names

    def test_parse_syntax_error(self):
        """Test handling of syntax errors."""
        parser = PythonASTParser()
        code = "def foo("
        result = parser.parse(code)
        assert len(result.errors) > 0
        assert "SyntaxError" in result.errors[0]


# ============================================================================
# JavaScript Parser Tests
# ============================================================================


class TestJavaScriptParser:
    """Test JavaScript parser."""

    def test_parse_simple_code(self):
        """Test parsing simple JavaScript code."""
        parser = JavaScriptParser()
        code = """
const x = 10;
let y = 20;
"""
        result = parser.parse(code)
        assert result.language == "javascript"
        assert len(result.errors) == 0
        assert len(result.nodes) > 0

    def test_find_dangerous_calls(self):
        """Test detection of dangerous JavaScript functions."""
        parser = JavaScriptParser()
        code = """
eval("alert('xss')");
document.write("<script>alert('xss')</script>");
setTimeout("doSomething()", 1000);
"""
        findings = parser.find_dangerous_calls(code)
        assert len(findings) >= 2
        names = [f.name for f in findings]
        assert "eval" in names or "document.write" in names

    def test_find_xss_patterns(self):
        """Test XSS pattern detection."""
        parser = JavaScriptParser()
        code = """
element.innerHTML = userInput;
document.write("<p>" + data + "</p>");
"""
        findings = parser.find_xss_patterns(code)
        assert len(findings) >= 1

    def test_find_hardcoded_strings(self):
        """Test detection of hardcoded secrets in JavaScript."""
        parser = JavaScriptParser()
        code = """
const password = "secret123";
let api_key = "abc123";
var normal = "hello";
"""
        findings = parser.find_hardcoded_strings(code)
        assert len(findings) >= 2
        names = [f.name for f in findings]
        assert "password" in names
        assert "api_key" in names

    def test_find_imports(self):
        """Test import detection in JavaScript."""
        parser = JavaScriptParser()
        code = """
import React from 'react';
const fs = require('fs');
"""
        result = parser.parse(code)
        imports = [n for n in result.nodes if n.node_type == "import"]
        assert len(imports) >= 1


# ============================================================================
# Pattern Matcher Tests
# ============================================================================


class TestPatternMatcher:
    """Test pattern matching engine."""

    def test_load_patterns_from_yaml(self):
        """Test loading patterns from YAML file."""
        matcher = PatternMatcher()
        yaml_content = """
patterns:
  - name: test_pattern
    severity: high
    pattern_type: call
    language: python
    description: "Test pattern"
    remediation: "Fix it"
    targets:
      - dangerous_func
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            matcher.load_patterns(yaml_path)
            assert len(matcher.patterns) == 1
            assert matcher.patterns[0].name == "test_pattern"
        finally:
            os.unlink(yaml_path)

    def test_match_dangerous_call(self):
        """Test matching dangerous function calls."""
        parser = PythonASTParser()
        matcher = PatternMatcher()

        # Create a pattern
        yaml_content = """
patterns:
  - name: dangerous_eval
    severity: critical
    pattern_type: call
    language: python
    description: "Dangerous eval"
    remediation: "Don't use eval"
    targets:
      - eval
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            matcher.load_patterns(yaml_path)
            code = 'eval("1 + 1")'
            parse_result = parser.parse(code)
            findings = matcher.match(parse_result, "test.py")
            assert len(findings) > 0
            assert findings[0].pattern_name == "dangerous_eval"
        finally:
            os.unlink(yaml_path)

    def test_match_hardcoded_secret(self):
        """Test matching hardcoded secrets."""
        parser = PythonASTParser()
        matcher = PatternMatcher()

        yaml_content = """
patterns:
  - name: hardcoded_password
    severity: high
    pattern_type: assignment
    language: python
    description: "Hardcoded password"
    remediation: "Use env vars"
    targets:
      - password
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            matcher.load_patterns(yaml_path)
            code = 'password = "secret123"'
            parse_result = parser.parse(code)
            findings = matcher.match(parse_result, "test.py")
            assert len(findings) > 0
            assert findings[0].pattern_name == "hardcoded_password"
        finally:
            os.unlink(yaml_path)

    def test_load_from_directory(self):
        """Test loading patterns from a directory."""
        matcher = PatternMatcher()
        patterns_dir = Path(__file__).parent.parent.parent / "hosforge" / "ast_analyzer" / "patterns"
        if patterns_dir.exists():
            matcher.load_from_directory(str(patterns_dir))
            assert len(matcher.patterns) > 0


# ============================================================================
# Taint Analyzer Tests
# ============================================================================


class TestTaintAnalyzer:
    """Test taint analysis."""

    def test_detect_taint_source(self):
        """Test detection of taint sources."""
        parser = PythonASTParser()
        analyzer = TaintAnalyzer()

        code = """
user_input = input()
"""
        parse_result = parser.parse(code)
        findings = analyzer.analyze(parse_result, "test.py")
        # input() is a source, but no sink yet
        assert isinstance(findings, list)

    def test_taint_propagation(self):
        """Test taint propagation through assignments."""
        parser = PythonASTParser()
        analyzer = TaintAnalyzer()

        code = """
user_input = input()
data = user_input
eval(data)
"""
        parse_result = parser.parse(code)
        findings = analyzer.analyze(parse_result, "test.py")
        # Should detect taint flow to eval
        assert len(findings) > 0

    def test_sanitizer_detection(self):
        """Test that sanitizers block taint propagation."""
        parser = PythonASTParser()
        analyzer = TaintAnalyzer()

        code = """
user_input = input()
safe_data = escape(user_input)
eval(safe_data)
"""
        parse_result = parser.parse(code)
        findings = analyzer.analyze(parse_result, "test.py")
        # escape() should sanitize, so no findings
        assert len(findings) == 0

    def test_custom_sources_and_sinks(self):
        """Test custom sources and sinks configuration."""
        analyzer = TaintAnalyzer(
            sources={"custom_source"},
            sinks={"custom_sink"},
        )
        assert "custom_source" in analyzer.sources
        assert "custom_sink" in analyzer.sinks


# ============================================================================
# Report Generator Tests
# ============================================================================


class TestReportGenerator:
    """Test report generation."""

    def test_generate_empty_report(self):
        """Test generating an empty report."""
        generator = ReportGenerator()
        report = generator.generate([], [])
        assert report.total_findings == 0
        assert len(report.findings) == 0

    def test_generate_report_with_findings(self):
        """Test generating a report with findings."""
        from hosforge.ast_analyzer.pattern_matcher import Finding

        generator = ReportGenerator()
        findings = [
            Finding(
                pattern_name="test_vuln",
                severity="high",
                description="Test vulnerability",
                remediation="Fix it",
                file="test.py",
                line=10,
                matched_value="test",
            )
        ]
        report = generator.generate(findings, [])
        assert report.total_findings == 1
        assert report.findings[0].vulnerability_type == "test_vuln"
        assert report.findings[0].severity == "high"

    def test_to_json(self):
        """Test JSON serialization."""
        from hosforge.ast_analyzer.pattern_matcher import Finding

        generator = ReportGenerator()
        findings = [
            Finding(
                pattern_name="test_vuln",
                severity="high",
                description="Test",
                remediation="Fix",
                file="test.py",
                line=10,
            )
        ]
        report = generator.generate(findings, [])
        json_str = generator.to_json(report)
        data = json.loads(json_str)
        assert "findings" in data
        assert data["total_findings"] == 1

    def test_to_text(self):
        """Test text report generation."""
        from hosforge.ast_analyzer.pattern_matcher import Finding

        generator = ReportGenerator()
        findings = [
            Finding(
                pattern_name="test_vuln",
                severity="high",
                description="Test vulnerability",
                remediation="Fix it",
                file="test.py",
                line=10,
            )
        ]
        report = generator.generate(findings, [])
        text = generator.to_text(report)
        assert "Security Scan Report" in text
        assert "test_vuln" in text
        assert "high" in text

    def test_report_summary(self):
        """Test report summary generation."""
        from hosforge.ast_analyzer.pattern_matcher import Finding

        generator = ReportGenerator()
        findings = [
            Finding("vuln1", "high", "desc", "fix", "file.py", 1),
            Finding("vuln2", "high", "desc", "fix", "file.py", 2),
            Finding("vuln3", "medium", "desc", "fix", "file.py", 3),
        ]
        report = generator.generate(findings, [])
        assert report.summary["high"] == 2
        assert report.summary["medium"] == 1


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Integration tests for the full pipeline."""

    def test_full_python_scan(self):
        """Test full scan pipeline for Python code."""
        code = """
import os
password = "secret123"
os.system("ls")
eval(user_input)
"""
        parser = PythonASTParser()
        matcher = PatternMatcher()
        analyzer = TaintAnalyzer()
        generator = ReportGenerator()

        # Load patterns
        patterns_dir = Path(__file__).parent.parent.parent / "hosforge" / "ast_analyzer" / "patterns"
        if patterns_dir.exists():
            matcher.load_from_directory(str(patterns_dir))

        # Parse
        parse_result = parser.parse(code)

        # Match patterns
        findings = matcher.match(parse_result, "test.py")

        # Taint analysis
        taint_findings = analyzer.analyze(parse_result, "test.py")

        # Generate report
        report = generator.generate(findings, taint_findings)

        assert report.total_findings > 0
        assert len(report.findings) > 0

    def test_full_javascript_scan(self):
        """Test full scan pipeline for JavaScript code."""
        code = """
const password = "secret123";
element.innerHTML = userInput;
eval("alert('xss')");
"""
        parser = JavaScriptParser()
        matcher = PatternMatcher()
        generator = ReportGenerator()

        # Load patterns
        patterns_dir = Path(__file__).parent.parent.parent / "hosforge" / "ast_analyzer" / "patterns"
        if patterns_dir.exists():
            matcher.load_from_directory(str(patterns_dir))

        # Parse
        parse_result = parser.parse(code)

        # Match patterns
        findings = matcher.match(parse_result, "test.js")

        # Generate report
        report = generator.generate(findings, [])

        assert report.total_findings > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
