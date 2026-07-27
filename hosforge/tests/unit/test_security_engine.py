"""Unit tests for Security Engine."""

import pytest
from pathlib import Path
import tempfile
import os

from hosforge.security_engine import SecurityEngine, CodeScanner, SecurityReport, Finding
from hosforge.rule_engine.schema import Severity


class TestSecurityEngine:
    """Test cases for SecurityEngine."""
    
    def test_engine_initialization(self):
        """Test that engine initializes correctly."""
        engine = SecurityEngine()
        assert engine.rule_engine is not None
        assert len(engine.rule_engine.rules) > 0
    
    def test_scan_code_sql_injection(self):
        """Test detection of SQL injection vulnerabilities."""
        engine = SecurityEngine()
        
        code = """
import sqlite3

def get_user(user_id):
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    query = "SELECT * FROM users WHERE id = " + user_id
    cursor.execute(query)
    return cursor.fetchone()
"""
        
        report = engine.scan_code(code, "python")
        
        assert report.total_findings > 0
        assert any(f.rule_name == "sql_injection" for f in report.findings)
        assert any(f.severity == Severity.CRITICAL for f in report.findings)
    
    def test_scan_code_command_injection(self):
        """Test detection of command injection vulnerabilities."""
        engine = SecurityEngine()
        
        code = """
import os

def run_command(user_input):
    os.system("echo " + user_input)
"""
        
        report = engine.scan_code(code, "python")
        
        assert report.total_findings > 0
        assert any(f.rule_name == "command_injection" for f in report.findings)
    
    def test_scan_code_hardcoded_secret(self):
        """Test detection of hardcoded secrets."""
        engine = SecurityEngine()
        
        code = """
def connect_to_database():
    password = "my_secret_password_123"
    api_key = "sk_live_abcdef123456"
    return connect(password, api_key)
"""
        
        report = engine.scan_code(code, "python")
        
        assert report.total_findings > 0
        assert any(f.rule_name == "hardcoded_secret" for f in report.findings)
    
    def test_scan_code_weak_crypto(self):
        """Test detection of weak cryptography."""
        engine = SecurityEngine()
        
        code = """
import hashlib

def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()
"""
        
        report = engine.scan_code(code, "python")
        
        assert report.total_findings > 0
        assert any(f.rule_name == "weak_crypto" for f in report.findings)
    
    def test_scan_code_xss(self):
        """Test detection of XSS vulnerabilities."""
        engine = SecurityEngine()
        
        code = """
from flask import render_template_string

def show_user(name):
    template = "<h1>Welcome " + name + "</h1>"
    return render_template_string(template)
"""
        
        report = engine.scan_code(code, "python")
        
        assert report.total_findings > 0
        assert any(f.rule_name == "xss" for f in report.findings)
    
    def test_scan_code_safe_code(self):
        """Test that safe code doesn't trigger false positives."""
        engine = SecurityEngine()
        
        code = """
import sqlite3

def get_user(user_id):
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    return cursor.fetchone()
"""
        
        report = engine.scan_code(code, "python")
        
        # Should not detect SQL injection when using parameterized queries
        sql_injection_findings = [f for f in report.findings if f.rule_name == "sql_injection"]
        assert len(sql_injection_findings) == 0
    
    def test_scan_file(self):
        """Test scanning a single file."""
        engine = SecurityEngine()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
import os
user_input = input()
os.system(user_input)
""")
            f.flush()
            temp_path = f.name
        
        try:
            report = engine.scan_file(temp_path)
            
            assert report.file_path == temp_path
            assert report.language == "python"
            assert report.total_findings > 0
        finally:
            os.unlink(temp_path)
    
    def test_scan_directory(self):
        """Test scanning a directory."""
        engine = SecurityEngine()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            file1 = Path(temp_dir) / "test1.py"
            file1.write_text("""
import os
os.system("ls")
""")
            
            file2 = Path(temp_dir) / "test2.py"
            file2.write_text("""
password = "secret123"
""")
            
            report = engine.scan_directory(temp_dir)
            
            assert report.file_path == temp_dir
            assert report.language == "mixed"
            assert report.total_findings > 0


class TestSecurityReport:
    """Test cases for SecurityReport."""
    
    def test_report_creation(self):
        """Test creating a security report."""
        findings = [
            Finding(
                rule_name="test_rule",
                severity=Severity.HIGH,
                location="line 10",
                description="Test vulnerability",
            )
        ]
        
        report = SecurityReport(
            file_path="test.py",
            language="python",
            findings=findings,
        )
        
        assert report.total_findings == 1
        assert report.high_count == 1
        assert report.critical_count == 0
    
    def test_report_severity_counts(self):
        """Test severity count calculations."""
        findings = [
            Finding(rule_name="r1", severity=Severity.CRITICAL),
            Finding(rule_name="r2", severity=Severity.HIGH),
            Finding(rule_name="r3", severity=Severity.HIGH),
            Finding(rule_name="r4", severity=Severity.MEDIUM),
            Finding(rule_name="r5", severity=Severity.LOW),
        ]
        
        report = SecurityReport(
            file_path="test.py",
            language="python",
            findings=findings,
        )
        
        assert report.critical_count == 1
        assert report.high_count == 2
        assert report.medium_count == 1
        assert report.low_count == 1
        assert report.info_count == 0
    
    def test_report_to_dict(self):
        """Test converting report to dictionary."""
        findings = [
            Finding(
                rule_name="test_rule",
                severity=Severity.HIGH,
                location="line 10",
                description="Test vulnerability",
            )
        ]
        
        report = SecurityReport(
            file_path="test.py",
            language="python",
            findings=findings,
        )
        
        report_dict = report.to_dict()
        
        assert "file_path" in report_dict
        assert "language" in report_dict
        assert "summary" in report_dict
        assert "findings" in report_dict
        assert report_dict["summary"]["total"] == 1
    
    def test_report_format_text(self):
        """Test formatting report as text."""
        findings = [
            Finding(
                rule_name="test_rule",
                severity=Severity.HIGH,
                location="line 10",
                description="Test vulnerability",
            )
        ]
        
        report = SecurityReport(
            file_path="test.py",
            language="python",
            findings=findings,
        )
        
        text = report.format_text()
        
        assert "SECURITY SCAN REPORT" in text
        assert "test.py" in text
        assert "python" in text
        assert "test_rule" in text
    
    def test_report_merge(self):
        """Test merging two reports."""
        report1 = SecurityReport(
            file_path="test1.py",
            language="python",
            findings=[Finding(rule_name="r1", severity=Severity.HIGH)],
        )
        
        report2 = SecurityReport(
            file_path="test2.py",
            language="python",
            findings=[Finding(rule_name="r2", severity=Severity.MEDIUM)],
        )
        
        merged = report1.merge(report2)
        
        assert merged.total_findings == 2
        assert "test1.py" in merged.file_path
        assert "test2.py" in merged.file_path


class TestCodeScanner:
    """Test cases for CodeScanner."""
    
    def test_scanner_initialization(self):
        """Test that scanner initializes correctly."""
        scanner = CodeScanner()
        assert scanner.engine is not None
        assert scanner.max_workers == 4
    
    def test_scanner_with_exclude_patterns(self):
        """Test scanner with exclude patterns."""
        scanner = CodeScanner(exclude_patterns=["*.test.py", "test_*.py"])
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create files
            file1 = Path(temp_dir) / "app.py"
            file1.write_text("password = 'secret'")
            
            file2 = Path(temp_dir) / "test_app.py"
            file2.write_text("password = 'secret'")
            
            report = scanner.scan_project(temp_dir)
            
            # Should only scan app.py, not test_app.py
            assert report.total_findings > 0
    
    def test_scanner_progress_callback(self):
        """Test scanner with progress callback."""
        scanner = CodeScanner()
        
        progress_calls = []
        
        def callback(current, total, file_path):
            progress_calls.append((current, total, file_path))
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            for i in range(3):
                file = Path(temp_dir) / f"file{i}.py"
                file.write_text(f"var{i} = 'value{i}'")
            
            scanner.scan_project(temp_dir, progress_callback=callback)
            
            # Should have called callback for each file
            assert len(progress_calls) > 0


class TestFinding:
    """Test cases for Finding."""
    
    def test_finding_creation(self):
        """Test creating a finding."""
        finding = Finding(
            rule_name="test_rule",
            severity=Severity.HIGH,
            location="line 10",
            description="Test vulnerability",
            remediation="Fix the issue",
        )
        
        assert finding.rule_name == "test_rule"
        assert finding.severity == Severity.HIGH
        assert finding.location == "line 10"
    
    def test_finding_to_dict(self):
        """Test converting finding to dictionary."""
        finding = Finding(
            rule_name="test_rule",
            severity=Severity.HIGH,
            location="line 10",
            description="Test vulnerability",
        )
        
        finding_dict = finding.to_dict()
        
        assert "rule_name" in finding_dict
        assert "severity" in finding_dict
        assert "location" in finding_dict
        assert finding_dict["severity"] == "high"
    
    def test_finding_format_text(self):
        """Test formatting finding as text."""
        finding = Finding(
            rule_name="test_rule",
            severity=Severity.HIGH,
            location="line 10",
            description="Test vulnerability",
            file_path="test.py",
        )
        
        text = finding.format_text()
        
        assert "[HIGH]" in text
        assert "test_rule" in text
        assert "test.py" in text
        assert "line 10" in text
