"""VSCode adapter unit tests."""

import pytest

from hosforge.adapters.base_adapter import AdapterConfig
from hosforge.adapters.vscode_adapter import VSCodeAdapter


class TestVSCodeAdapter:
    """Test VSCodeAdapter implementation."""

    def test_adapter_initialization_default(self):
        """Test adapter initialization with default config."""
        adapter = VSCodeAdapter()

        assert adapter.name == "vscode"
        assert adapter._config.version == "1.0.0"
        assert len(adapter.supported_commands) == 5

    def test_adapter_initialization_custom_config(self):
        """Test adapter initialization with custom config."""
        config = AdapterConfig(
            adapter_name="vscode",
            version="2.0.0",
            config={"key": "value"},
        )
        adapter = VSCodeAdapter(config)

        assert adapter.name == "vscode"
        assert adapter._config.version == "2.0.0"
        assert adapter._config.config == {"key": "value"}

    def test_supported_commands(self):
        """Test supported commands list."""
        adapter = VSCodeAdapter()

        expected_commands = [
            "hos.skill.run",
            "hos.skill.list",
            "hos.skill.info",
            "hos.scan.nuclei",
            "hos.scan.semgrep",
        ]

        for cmd in expected_commands:
            assert cmd in adapter.supported_commands

        assert len(adapter.supported_commands) == len(expected_commands)

    def test_format_input_valid_command(self):
        """Test format_input with valid command."""
        adapter = VSCodeAdapter()

        result = adapter.format_input(
            "hos.skill.run",
            {"skill_name": "test_skill", "args": {"param1": "value1"}},
        )

        assert result["command"] == "hos.skill.run"
        assert result["args"]["skill_name"] == "test_skill"
        assert result["args"]["args"]["param1"] == "value1"

    def test_format_input_invalid_command(self):
        """Test format_input with unsupported command raises ValueError."""
        adapter = VSCodeAdapter()

        with pytest.raises(ValueError, match="Unsupported command"):
            adapter.format_input("invalid.command", {})

    def test_format_output_with_all_fields(self):
        """Test format_output with all result fields."""
        adapter = VSCodeAdapter()

        result = {
            "status": "success",
            "message": "Skill executed successfully",
            "data": {"output": "test output"},
            "actions": [
                {"command": "hos.skill.info", "label": "View Details"},
            ],
        }

        formatted = adapter.format_output(result)

        assert formatted["status"] == "success"
        assert formatted["message"] == "Skill executed successfully"
        assert formatted["data"] == {"output": "test output"}
        assert formatted["actions"] == [
            {"command": "hos.skill.info", "label": "View Details"},
        ]

    def test_format_output_without_actions(self):
        """Test format_output without actions field."""
        adapter = VSCodeAdapter()

        result = {
            "status": "error",
            "message": "Skill not found",
            "data": None,
        }

        formatted = adapter.format_output(result)

        assert formatted["status"] == "error"
        assert formatted["message"] == "Skill not found"
        assert formatted["data"] is None
        assert "actions" not in formatted

    def test_format_output_with_defaults(self):
        """Test format_output with missing fields uses defaults."""
        adapter = VSCodeAdapter()

        result = {}

        formatted = adapter.format_output(result)

        assert formatted["status"] == "success"
        assert formatted["message"] == ""
        assert formatted["data"] is None

    def test_register_commands_structure(self):
        """Test register_commands returns correct structure."""
        adapter = VSCodeAdapter()

        commands = adapter.register_commands()

        assert len(commands) == 5

        # Check first command structure
        cmd = commands[0]
        assert "command" in cmd
        assert "title" in cmd
        assert "category" in cmd
        assert cmd["category"] == "HOS"

    def test_register_commands_content(self):
        """Test register_commands returns expected command definitions."""
        adapter = VSCodeAdapter()

        commands = adapter.register_commands()

        # Verify all expected commands are present
        command_names = [cmd["command"] for cmd in commands]
        assert "hos.skill.run" in command_names
        assert "hos.skill.list" in command_names
        assert "hos.skill.info" in command_names
        assert "hos.scan.nuclei" in command_names
        assert "hos.scan.semgrep" in command_names

        # Verify titles
        for cmd in commands:
            if cmd["command"] == "hos.skill.run":
                assert cmd["title"] == "HOS: Run Skill"
            elif cmd["command"] == "hos.skill.list":
                assert cmd["title"] == "HOS: List Skills"

    def test_format_input_empty_args(self):
        """Test format_input with empty args dictionary."""
        adapter = VSCodeAdapter()

        result = adapter.format_input("hos.skill.list", {})

        assert result["command"] == "hos.skill.list"
        assert result["args"] == {}

    def test_format_input_complex_args(self):
        """Test format_input with complex nested arguments."""
        adapter = VSCodeAdapter()

        complex_args = {
            "skill_name": "nuclei_scan",
            "parameters": {
                "target": "example.com",
                "templates": ["cves", "exposures"],
                "options": {"severity": ["high", "critical"]},
            },
        }

        result = adapter.format_input("hos.skill.run", complex_args)

        assert result["command"] == "hos.skill.run"
        assert result["args"] == complex_args
        assert result["args"]["parameters"]["target"] == "example.com"
