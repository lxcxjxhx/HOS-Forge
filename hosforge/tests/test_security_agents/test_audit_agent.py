"""Tests for AuditAgent."""
from unittest.mock import AsyncMock, MagicMock

import pytest

from hosforge.security_agents.audit import AuditAgent
from hosforge.security_agents.base import SecurityAgentConfig, Severity


@pytest.fixture
def audit_agent():
    """Create AuditAgent instance."""
    return AuditAgent()


@pytest.fixture
def custom_config():
    """Create custom agent config."""
    return SecurityAgentConfig(
        name="CustomAudit",
        description="Custom audit agent",
        enabled=True,
        max_vulnerabilities=10,
        min_severity=Severity.HIGH,
    )


class TestAuditAgent:
    """Test cases for AuditAgent."""

    def test_init_default(self, audit_agent):
        """Test default initialization."""
        assert audit_agent.name == "AuditAgent"
        assert audit_agent.config.name == "AuditAgent"
        assert audit_agent.config.enabled is True
        assert audit_agent.config.max_vulnerabilities == 50
        assert len(audit_agent._builtin_rules) > 0

    def test_init_custom_config(self, custom_config):
        """Test initialization with custom config."""
        agent = AuditAgent(config=custom_config)
        assert agent.config.name == "CustomAudit"
        assert agent.config.max_vulnerabilities == 10
        assert agent.config.min_severity == Severity.HIGH

    @pytest.mark.asyncio
    async def test_analyze_empty_target(self, audit_agent):
        """Test analyze with empty target."""
        result = await audit_agent.analyze("")
        assert result.target == ""
        assert result.agent_name == "AuditAgent"
        assert result.success is True
        assert len(result.vulnerabilities) == 0

    @pytest.mark.asyncio
    async def test_analyze_with_target(self, audit_agent):
        """Test analyze with valid target."""
        result = await audit_agent.analyze("/path/to/code")
        assert result.target == "/path/to/code"
        assert result.agent_name == "AuditAgent"
        assert result.success is True
        assert "AuditAgent" in result.summary

    @pytest.mark.asyncio
    async def test_analyze_with_mode(self, audit_agent):
        """Test analyze with different modes."""
        result = await audit_agent.analyze("/path", mode="quick")
        assert "quick" in result.summary

        result = await audit_agent.analyze("/path", mode="full")
        assert "full" in result.summary

    @pytest.mark.asyncio
    async def test_analyze_max_vulnerabilities_limit(self, custom_config):
        """Test that max_vulnerabilities limit is respected."""
        agent = AuditAgent(config=custom_config)
        # Mock _apply_rule to return vulnerabilities
        agent._apply_rule = AsyncMock(
            side_effect=lambda rule, target: MagicMock(severity=Severity.HIGH)
        )
        result = await agent.analyze("/path")
        # Should not exceed max_vulnerabilities
        assert len(result.vulnerabilities) <= custom_config.max_vulnerabilities

    def test_load_default_rules(self, audit_agent):
        """Test that default rules are loaded."""
        rules = audit_agent._builtin_rules
        assert len(rules) > 0
        # Check for SQL injection rule
        sql_rule = next((r for r in rules if "SQL" in r.get("name", "")), None)
        assert sql_rule is not None
        assert sql_rule["severity"] == Severity.CRITICAL

    @pytest.mark.asyncio
    async def test_apply_rule_returns_none(self, audit_agent):
        """Test _apply_rule returns None (placeholder implementation)."""
        rule = {"name": "test_rule", "severity": Severity.HIGH}
        result = await audit_agent._apply_rule(rule, "/path")
        assert result is None
