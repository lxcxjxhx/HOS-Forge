"""Integration test configuration and shared fixtures.

This module provides pytest fixtures for end-to-end integration testing,
including skill instances, registry setup, and test environment configuration.
"""

from typing import Any, Dict
from unittest.mock import MagicMock

import pytest

from hosforge.adapters.adapter_mcp_bridge import AdapterMCPBridge
from hosforge.adapters.adapter_registry import AdapterRegistry
from hosforge.adapters.claude_code_adapter import ClaudeCodeAdapter
from hosforge.adapters.cursor_adapter import CursorAdapter
from hosforge.adapters.mcp_client import MCPClient
from hosforge.adapters.vscode_adapter import VSCodeAdapter
from hosforge.mcp_server.server import create_app
from hosforge.mcp_server.skill_bridge import MCPToolExecutor, SkillToMCPTool
from hosforge.skills.base_skill import Skill, SkillResult
from hosforge.skills.loader import SkillLoader
from hosforge.skills.registry import SkillRegistry
from hosforge.skills.security import (
    GitHubIntegrationSkill,
    NucleiScanSkill,
    SemgrepScanSkill,
)


class MockSkill(Skill):
    """Mock skill for testing purposes."""

    def __init__(
        self,
        name: str = "mock_skill",
        description: str = "A mock skill for testing",
        parameters: Dict[str, Any] = None,
    ) -> None:
        super().__init__(
            name=name,
            description=description,
            parameters=parameters
            or {
                "type": "object",
                "properties": {"input": {"type": "string", "description": "Test input"}},
                "required": ["input"],
            },
        )

    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute mock skill logic."""
        input_val = kwargs.get("input", "default")
        return {"result": f"Processed: {input_val}", "status": "success"}


class ErrorSkill(Skill):
    """Skill that raises errors for testing error handling."""

    def __init__(self) -> None:
        super().__init__(
            name="error_skill",
            description="A skill that raises errors",
            parameters={
                "type": "object",
                "properties": {
                    "error_type": {
                        "type": "string",
                        "enum": ["value_error", "runtime_error", "timeout"],
                    }
                },
                "required": ["error_type"],
            },
        )

    def execute(self, **kwargs) -> Dict[str, Any]:
        """Raise specified error type."""
        error_type = kwargs.get("error_type", "value_error")
        if error_type == "value_error":
            raise ValueError("Test value error")
        elif error_type == "runtime_error":
            raise RuntimeError("Test runtime error")
        elif error_type == "timeout":
            import time

            time.sleep(10)  # Will timeout
        return {"result": "should not reach here"}


@pytest.fixture
def mock_skill():
    """Provide a mock skill instance."""
    return MockSkill()


@pytest.fixture
def error_skill():
    """Provide an error skill instance."""
    return ErrorSkill()


@pytest.fixture
def github_skill():
    """Provide a GitHub integration skill instance."""
    return GitHubIntegrationSkill()


@pytest.fixture
def nuclei_skill():
    """Provide a Nuclei scan skill instance."""
    return NucleiScanSkill()


@pytest.fixture
def semgrep_skill():
    """Provide a Semgrep scan skill instance."""
    return SemgrepScanSkill()


@pytest.fixture
def skill_registry(mock_skill, error_skill):
    """Provide a skill registry with test skills."""
    registry = SkillRegistry()
    registry.register(mock_skill)
    registry.register(error_skill)
    return registry


@pytest.fixture
def full_skill_registry(github_skill, nuclei_skill, semgrep_skill):
    """Provide a registry with all built-in skills."""
    registry = SkillRegistry()
    registry.register(github_skill)
    registry.register(nuclei_skill)
    registry.register(semgrep_skill)
    return registry


@pytest.fixture
def skill_loader():
    """Provide a skill loader instance."""
    return SkillLoader()


@pytest.fixture
def vscode_adapter():
    """Provide a VSCode adapter instance."""
    return VSCodeAdapter()


@pytest.fixture
def cursor_adapter():
    """Provide a Cursor adapter instance."""
    return CursorAdapter()


@pytest.fixture
def claude_adapter():
    """Provide a Claude Code adapter instance."""
    return ClaudeCodeAdapter()


@pytest.fixture
def adapter_registry(vscode_adapter, cursor_adapter, claude_adapter):
    """Provide an adapter registry with all adapters."""
    registry = AdapterRegistry()
    registry.register(vscode_adapter)
    registry.register(cursor_adapter)
    registry.register(claude_adapter)
    return registry


@pytest.fixture
def mcp_tool_executor(skill_registry):
    """Provide an MCP tool executor."""
    return MCPToolExecutor(skill_registry)


@pytest.fixture
def mcp_app(full_skill_registry):
    """Provide a FastAPI test app."""
    return create_app(full_skill_registry)


@pytest.fixture
def mock_mcp_client():
    """Provide a mock MCP client."""
    client = MagicMock(spec=MCPClient)
    client.is_connected = True
    client.server_url = "http://localhost:8000"
    return client


@pytest.fixture
def adapter_mcp_bridge(mock_mcp_client):
    """Provide an adapter MCP bridge with mock client."""
    return AdapterMCPBridge(mock_mcp_client)


@pytest.fixture
def test_data_dir():
    """Provide path to test data directory."""
    from pathlib import Path

    return Path(__file__).parent / "test_data"


@pytest.fixture
def sample_skills_dir(test_data_dir):
    """Provide path to sample skills directory."""
    return test_data_dir / "sample_skills"
