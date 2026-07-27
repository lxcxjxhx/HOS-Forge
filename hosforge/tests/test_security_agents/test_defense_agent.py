"""Tests for DefenseAgent."""

import pytest

from hosforge.security_agents.base import (
    SecurityAgentConfig,
    SecurityVulnerability,
    Severity,
)
from hosforge.security_agents.defense import DefenseAgent


@pytest.fixture
def defense_agent():
    """Create DefenseAgent instance."""
    return DefenseAgent()


@pytest.fixture
def sample_vulnerability():
    """Create a sample vulnerability for testing."""
    return SecurityVulnerability(
        id="VULN-001",
        name="SQL Injection",
        description="SQL injection in login form",
        severity=Severity.CRITICAL,
        cwe_id="CWE-89",
        file_path="/app/login.py",
        line_number=42,
        code_snippet="cursor.execute(f'SELECT * FROM users WHERE id = {user_id}')",
    )


class TestDefenseAgent:
    """Test cases for DefenseAgent."""

    def test_init_default(self, defense_agent):
        """Test default initialization."""
        assert defense_agent.name == "DefenseAgent"
        assert defense_agent.config.name == "DefenseAgent"
        assert defense_agent.config.enabled is True
        assert len(defense_agent._fix_templates) > 0

    def test_init_custom_config(self):
        """Test initialization with custom config."""
        config = SecurityAgentConfig(
            name="CustomDefense",
            description="Custom defense agent",
            enabled=True,
        )
        agent = DefenseAgent(config=config)
        assert agent.config.name == "CustomDefense"

    @pytest.mark.asyncio
    async def test_analyze(self, defense_agent):
        """Test analyze method."""
        result = await defense_agent.analyze("/path/to/code")
        assert result.target == "/path/to/code"
        assert result.agent_name == "DefenseAgent"
        assert result.success is True
        assert "DefenseAgent" in result.summary

    @pytest.mark.asyncio
    async def test_fix_with_template(self, defense_agent, sample_vulnerability):
        """Test fix method with known CWE template."""
        fix_code = await defense_agent.fix(sample_vulnerability)
        assert fix_code is not None
        assert "SQL Injection" in fix_code or "CWE-89" in fix_code
        assert "parameterized" in fix_code.lower()

    @pytest.mark.asyncio
    async def test_fix_without_template(self, defense_agent):
        """Test fix method with unknown CWE."""
        vuln = SecurityVulnerability(
            id="VULN-999",
            name="Unknown Issue",
            severity=Severity.MEDIUM,
            cwe_id="CWE-9999",  # Unknown CWE
        )
        fix_code = await defense_agent.fix(vuln)
        assert fix_code is not None
        assert "TODO" in fix_code or "Unknown Issue" in fix_code

    @pytest.mark.asyncio
    async def test_validate_fix(self, defense_agent):
        """Test validate_fix method."""
        original = "cursor.execute(f'SELECT * FROM users WHERE id = {user_id}')"
        fixed = "cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))"
        is_valid = await defense_agent.validate_fix(original, fixed)
        assert is_valid is True

    def test_load_fix_templates(self, defense_agent):
        """Test that fix templates are loaded."""
        templates = defense_agent._fix_templates
        assert len(templates) > 0
        assert "CWE-89" in templates  # SQL Injection
        assert "CWE-79" in templates  # XSS
        assert "CWE-78" in templates  # Command Injection

    def test_apply_template(self, defense_agent, sample_vulnerability):
        """Test _apply_template method."""
        template = defense_agent._fix_templates["CWE-89"]
        result = defense_agent._apply_template(template, sample_vulnerability)
        assert result is not None
        assert len(result) > 0
        assert "SQL Injection" in result or "CWE-89" in result

    def test_template_sql_injection(self, defense_agent):
        """Test SQL injection template."""
        template = defense_agent._template_sql_injection()
        assert "parameterized" in template.lower()
        assert "cursor.execute" in template

    def test_template_xss(self, defense_agent):
        """Test XSS template."""
        template = defense_agent._template_xss()
        assert "escape" in template.lower()
        assert "markupsafe" in template.lower()

    def test_template_command_injection(self, defense_agent):
        """Test command injection template."""
        template = defense_agent._template_command_injection()
        assert "subprocess" in template.lower()
        assert "shell=False" in template

    def test_template_path_traversal(self, defense_agent):
        """Test path traversal template."""
        template = defense_agent._template_path_traversal()
        assert "os.path" in template
        assert "normpath" in template

    def test_template_hardcoded_credentials(self, defense_agent):
        """Test hardcoded credentials template."""
        template = defense_agent._template_hardcoded_credentials()
        assert "os.environ" in template
        assert "APP_PASSWORD" in template
