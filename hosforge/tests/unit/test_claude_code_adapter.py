"""Claude Code adapter unit tests."""

import pytest
from typing import Any

from hosforge.adapters import AdapterConfig
from hosforge.adapters.claude_code_adapter import ClaudeCodeAdapter


class TestClaudeCodeAdapter:
    """Test ClaudeCodeAdapter implementation."""

    def test_adapter_initialization(self):
        """Test adapter instantiation with default config."""
        adapter = ClaudeCodeAdapter()

        assert adapter.name == "claude_code"
        assert adapter._config.version == "1.0.0"
        assert adapter._config.config == {}

    def test_adapter_initialization_with_custom_config(self):
        """Test adapter instantiation with custom config."""
        config = AdapterConfig(
            adapter_name="claude_code",
            version="2.0.0",
            config={"key": "value"}
        )
        adapter = ClaudeCodeAdapter(config)

        assert adapter.name == "claude_code"
        assert adapter._config.version == "2.0.0"
        assert adapter._config.config == {"key": "value"}

    def test_supported_commands(self):
        """Test supported commands property."""
        adapter = ClaudeCodeAdapter()

        expected_commands = [
            "/hos-scan",
            "/hos-nuclei",
            "/hos-semgrep",
            "/hos-skill-list",
            "/hos-skill-info",
        ]

        assert adapter.supported_commands == expected_commands
        assert len(adapter.supported_commands) == 5

    def test_format_input_scan_command(self):
        """Test input formatting for /hos-scan command."""
        adapter = ClaudeCodeAdapter()

        result = adapter.format_input("/hos-scan", {"target": "example.com"})

        assert result["command"] == "scan"
        assert result["args"] == {"target": "example.com"}

    def test_format_input_nuclei_command(self):
        """Test input formatting for /hos-nuclei command."""
        adapter = ClaudeCodeAdapter()

        result = adapter.format_input(
            "/hos-nuclei",
            {"target": "example.com", "severity": "high"}
        )

        assert result["command"] == "nuclei"
        assert result["args"] == {"target": "example.com", "severity": "high"}

    def test_format_input_semgrep_command(self):
        """Test input formatting for /hos-semgrep command."""
        adapter = ClaudeCodeAdapter()

        result = adapter.format_input(
            "/hos-semgrep",
            {"path": "/src", "language": "python"}
        )

        assert result["command"] == "semgrep"
        assert result["args"] == {"path": "/src", "language": "python"}

    def test_format_input_skill_list_command(self):
        """Test input formatting for /hos-skill-list command."""
        adapter = ClaudeCodeAdapter()

        result = adapter.format_input("/hos-skill-list", {"category": "security"})

        assert result["command"] == "skill_list"
        assert result["args"] == {"category": "security"}

    def test_format_input_skill_info_command(self):
        """Test input formatting for /hos-skill-info command."""
        adapter = ClaudeCodeAdapter()

        result = adapter.format_input("/hos-skill-info", {"skill_name": "nuclei"})

        assert result["command"] == "skill_info"
        assert result["args"] == {"skill_name": "nuclei"}

    def test_format_input_unsupported_command(self):
        """Test input formatting raises error for unsupported command."""
        adapter = ClaudeCodeAdapter()

        with pytest.raises(ValueError, match="Unsupported command"):
            adapter.format_input("/unsupported", {"arg": "value"})

    def test_format_output_success(self):
        """Test output formatting for successful result."""
        adapter = ClaudeCodeAdapter()

        result = adapter.format_output({
            "status": "success",
            "message": "Scan completed",
            "data": {"findings": 5},
            "tool_results": [{"tool": "nuclei", "result": "ok"}]
        })

        assert result["response"] == "Scan completed"
        assert result["data"] == {"findings": 5}
        assert result["tool_results"] == [{"tool": "nuclei", "result": "ok"}]

    def test_format_output_error(self):
        """Test output formatting for error result."""
        adapter = ClaudeCodeAdapter()

        result = adapter.format_output({
            "status": "error",
            "message": "Scan failed",
            "data": None,
            "tool_results": []
        })

        assert result["response"] == "[error] Scan failed"
        assert result["data"] is None
        assert result["tool_results"] == []

    def test_format_output_missing_fields(self):
        """Test output formatting with missing optional fields."""
        adapter = ClaudeCodeAdapter()

        result = adapter.format_output({"status": "success"})

        assert result["response"] == ""
        assert result["tool_results"] == []
        assert result["data"] is None

    def test_register_commands(self):
        """Test command registration returns skill definitions."""
        adapter = ClaudeCodeAdapter()

        commands = adapter.register_commands()

        assert isinstance(commands, list)
        assert len(commands) == 5

        # Verify structure of first command
        first_cmd = commands[0]
        assert "name" in first_cmd
        assert "description" in first_cmd
        assert "parameters" in first_cmd
        assert "handler" in first_cmd

        # Verify command names
        command_names = [cmd["name"] for cmd in commands]
        assert "hos-scan" in command_names
        assert "hos-nuclei" in command_names
        assert "hos-semgrep" in command_names
        assert "hos-skill-list" in command_names
        assert "hos-skill-info" in command_names
