"""Cursor adapter unit tests."""

import pytest

from hosforge.adapters.base_adapter import AdapterConfig
from hosforge.adapters.cursor_adapter import CursorAdapter


class TestCursorAdapter:
    """Test CursorAdapter implementation."""

    def test_adapter_initialization_default(self):
        """Test adapter initialization with default config."""
        adapter = CursorAdapter()

        assert adapter.name == "cursor"
        assert adapter._config.version == "1.0.0"
        assert len(adapter.supported_commands) == 5

    def test_adapter_initialization_custom_config(self):
        """Test adapter initialization with custom config."""
        config = AdapterConfig(adapter_name="cursor", version="2.0.0", config={"custom": "value"})
        adapter = CursorAdapter(config)

        assert adapter.name == "cursor"
        assert adapter._config.version == "2.0.0"
        assert adapter._config.config == {"custom": "value"}

    def test_supported_commands(self):
        """Test supported commands list."""
        adapter = CursorAdapter()

        expected_commands = ["@hos scan", "@hos nuclei", "@hos semgrep", "@hos skill list", "@hos skill info"]

        for cmd in expected_commands:
            assert cmd in adapter.supported_commands
        assert len(adapter.supported_commands) == 5

    def test_format_input_simple_command(self):
        """Test parsing simple @mention command."""
        adapter = CursorAdapter()

        result = adapter.format_input("@hos scan", {"target": "src/"})

        assert result["command"] == "scan"
        assert result["args"] == {"target": "src/"}

    def test_format_input_command_with_subcommand(self):
        """Test parsing @mention command with subcommand."""
        adapter = CursorAdapter()

        result = adapter.format_input("@hos skill list", {"category": "web"})

        assert result["command"] == "skill list"
        assert result["args"] == {"category": "web"}

    def test_format_input_invalid_command(self):
        """Test parsing invalid command raises ValueError."""
        adapter = CursorAdapter()

        with pytest.raises(ValueError, match="Invalid @mention command format"):
            adapter.format_input("invalid command", {})

    def test_format_output_success_with_dict(self):
        """Test formatting successful result with dict data."""
        adapter = CursorAdapter()

        result = {
            "status": "success",
            "message": "Scan completed",
            "data": {"vulnerabilities": 5, "files_scanned": 100},
        }

        output = adapter.format_output(result)

        assert "✅ **Success**" in output["content"]
        assert "Scan completed" in output["content"]
        assert "**vulnerabilities**: 5" in output["content"]
        assert "**files_scanned**: 100" in output["content"]
        assert output["metadata"]["format"] == "markdown"
        assert output["metadata"]["status"] == "success"
        assert output["metadata"]["adapter"] == "cursor"

    def test_format_output_error(self):
        """Test formatting error result."""
        adapter = CursorAdapter()

        result = {"status": "error", "message": "Scan failed"}

        output = adapter.format_output(result)

        assert "❌ **Error**" in output["content"]
        assert "Scan failed" in output["content"]
        assert output["metadata"]["status"] == "error"

    def test_format_output_with_list_data(self):
        """Test formatting result with list data."""
        adapter = CursorAdapter()

        result = {"status": "success", "data": ["item1", "item2", "item3"]}

        output = adapter.format_output(result)

        assert "- item1" in output["content"]
        assert "- item2" in output["content"]
        assert "- item3" in output["content"]

    def test_format_output_with_plain_data(self):
        """Test formatting result with plain text data."""
        adapter = CursorAdapter()

        result = {"status": "success", "data": "Plain text result"}

        output = adapter.format_output(result)

        assert "Plain text result" in output["content"]

    def test_format_output_unknown_status(self):
        """Test formatting result with unknown status."""
        adapter = CursorAdapter()

        result = {"status": "pending", "message": "Processing"}

        output = adapter.format_output(result)

        assert "**Status**: pending" in output["content"]
        assert "Processing" in output["content"]

    def test_register_commands(self):
        """Test command registration returns correct format."""
        adapter = CursorAdapter()

        commands = adapter.register_commands()

        assert len(commands) == 5

        # Check first command structure
        scan_cmd = commands[0]
        assert scan_cmd["trigger"] == "@hos scan"
        assert "description" in scan_cmd
        assert "handler" in scan_cmd
        assert scan_cmd["handler"] == "handle_scan"

        # Check all commands have required fields
        for cmd in commands:
            assert "trigger" in cmd
            assert "description" in cmd
            assert "handler" in cmd
            assert cmd["trigger"].startswith("@hos")

    def test_register_commands_contains_all_supported(self):
        """Test registered commands match supported commands."""
        adapter = CursorAdapter()

        commands = adapter.register_commands()
        triggers = [cmd["trigger"] for cmd in commands]

        for supported_cmd in adapter.supported_commands:
            assert supported_cmd in triggers

    def test_format_input_with_whitespace(self):
        """Test parsing command with extra whitespace."""
        adapter = CursorAdapter()

        result = adapter.format_input("  @hos scan  ", {"arg": "value"})

        assert result["command"] == "scan"
        assert result["args"] == {"arg": "value"}

    def test_format_output_empty_data(self):
        """Test formatting result with empty data."""
        adapter = CursorAdapter()

        result = {"status": "success", "data": {}}

        output = adapter.format_output(result)

        assert "✅ **Success**" in output["content"]
        assert "**Results**" not in output["content"]
