"""Shared test fixtures for HOS-Forge test suite."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from hosforge.security_agents.base import (
    SecurityAgentConfig,
    SecurityFinding,
    SecurityVulnerability,
    Severity,
)
from hosforge.security_tools.base import SecurityToolResult


@pytest.fixture
def sample_vulnerability() -> SecurityVulnerability:
    """Create a sample vulnerability for testing."""
    return SecurityVulnerability(
        id="VULN-001",
        name="SQL Injection",
        description="SQL injection vulnerability in login form",
        severity=Severity.CRITICAL,
        cwe_id="CWE-89",
        cve_id="CVE-2024-1234",
        file_path="/app/login.py",
        line_number=42,
        code_snippet="cursor.execute(f'SELECT * FROM users WHERE id = {user_id}')",
        remediation="Use parameterized queries",
        references=["https://owasp.org/www-community/attacks/SQL_Injection"],
    )


@pytest.fixture
def sample_finding(sample_vulnerability: SecurityVulnerability) -> SecurityFinding:
    """Create a sample security finding for testing."""
    return SecurityFinding(
        target="/app",
        agent_name="AuditAgent",
        vulnerabilities=[sample_vulnerability],
        summary="Found 1 critical vulnerability",
        scan_duration_ms=1500,
        success=True,
    )


@pytest.fixture
def sample_config() -> SecurityAgentConfig:
    """Create a sample agent configuration for testing."""
    return SecurityAgentConfig(
        name="TestAgent",
        description="Test security agent",
        enabled=True,
        max_vulnerabilities=100,
        min_severity=Severity.LOW,
    )


@pytest.fixture
def mock_tool_result() -> SecurityToolResult:
    """Create a mock tool result for testing."""
    return SecurityToolResult(
        tool_name="mock_tool",
        success=True,
        output="Mock output",
        error="",
        raw_data={"key": "value"},
        execution_time_ms=100.0,
    )


@pytest.fixture
def mock_async_tool() -> AsyncMock:
    """Create a mock async security tool."""
    tool = AsyncMock()
    tool.name = "mock_tool"
    tool.run = AsyncMock()
    tool.validate = AsyncMock(return_value=True)
    return tool
