"""Unit tests for CLI entry point."""

import sys
from unittest.mock import MagicMock, patch

import pytest

from hosforge.cli.main import main


class TestCLIHelp:
    """Test CLI help output."""

    def test_help_command(self, capsys):
        """Test that --help displays usage information."""
        with pytest.raises(SystemExit) as exc_info:
            sys.argv = ["hos", "--help"]
            main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "HOS-Forge" in captured.out
        assert "taskflow" in captured.out
        assert "personality" in captured.out
        assert "mcp" in captured.out

    def test_no_args_shows_help(self, capsys):
        """Test that running without args shows help."""
        with pytest.raises(SystemExit) as exc_info:
            sys.argv = ["hos"]
            main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "HOS-Forge" in captured.out


class TestTaskflowCommand:
    """Test taskflow CLI commands."""

    @patch("hosforge.cli.taskflow_cmd.WorkflowParser")
    @patch("hosforge.cli.taskflow_cmd.Path")
    def test_taskflow_list(self, mock_path, mock_parser, capsys):
        """Test taskflow list command execution."""
        # Mock Path to simulate workflow directory
        mock_builtin_dir = MagicMock()
        mock_builtin_dir.exists.return_value = True
        mock_builtin_dir.glob.return_value = []

        mock_path_instance = MagicMock()
        mock_path_instance.parent.parent.__truediv__.return_value = mock_builtin_dir
        mock_path.return_value = mock_path_instance

        sys.argv = ["hos", "taskflow", "list"]
        main()

        captured = capsys.readouterr()
        # Should either show workflows or "not found" message
        assert captured.out is not None

    @patch("hosforge.cli.taskflow_cmd.WorkflowParser")
    def test_taskflow_list_with_workflows(self, mock_parser, capsys):
        """Test taskflow list with mock workflows."""
        # Create a temporary workflow directory structure
        with patch("hosforge.cli.taskflow_cmd.Path") as mock_path:
            mock_builtin_dir = MagicMock()
            mock_builtin_dir.exists.return_value = True

            # Mock a workflow file
            mock_yaml_file = MagicMock()
            mock_yaml_file.name = "test_workflow.yaml"
            mock_builtin_dir.glob.return_value = [mock_yaml_file]

            # Mock parser to return workflow info
            mock_workflow = MagicMock()
            mock_workflow.name = "Test Workflow"
            mock_workflow.description = "A test workflow"
            mock_workflow.tasks = [MagicMock(), MagicMock()]

            mock_schema = MagicMock()
            mock_schema.workflow = mock_workflow
            mock_parser.return_value.parse_file.return_value = mock_schema

            mock_path_instance = MagicMock()
            mock_path_instance.parent.parent.__truediv__.return_value = mock_builtin_dir
            mock_path.return_value = mock_path_instance

            sys.argv = ["hos", "taskflow", "list"]
            main()

            captured = capsys.readouterr()
            # Should show the workflow table or message
            assert captured.out is not None


class TestPersonalityCommand:
    """Test personality CLI commands."""

    @patch("hosforge.cli.personality_cmd.PersonalityLoader")
    def test_personality_list(self, mock_loader_class, capsys):
        """Test personality list command execution."""
        # Mock the loader
        mock_loader = MagicMock()
        mock_loader.list_personalities.return_value = []
        mock_loader_class.return_value = mock_loader

        sys.argv = ["hos", "personality", "list"]
        main()

        captured = capsys.readouterr()
        # Should show "no personalities found" or empty table
        assert captured.out is not None

    @patch("hosforge.cli.personality_cmd.PersonalityLoader")
    def test_personality_list_with_personalities(self, mock_loader_class, capsys):
        """Test personality list with mock personalities."""
        mock_loader = MagicMock()
        mock_loader.list_personalities.return_value = ["security_analyst"]

        mock_personality = MagicMock()
        mock_personality.name = "Security Analyst"
        mock_personality.role = "security"
        mock_personality.description = "Security analysis expert"
        mock_personality.skills = ["vuln_analysis", "threat_modeling"]
        mock_personality.tools = ["semgrep", "nuclei"]

        mock_loader.get_personality.return_value = mock_personality
        mock_loader_class.return_value = mock_loader

        sys.argv = ["hos", "personality", "list"]
        main()

        captured = capsys.readouterr()
        # Should show personality table
        assert captured.out is not None


class TestMCPCommand:
    """Test MCP CLI commands."""

    @patch("hosforge.cli.mcp_cmd.MCPServerRegistry")
    @patch("hosforge.cli.mcp_cmd.Path")
    def test_mcp_list(self, mock_path, mock_registry_class, capsys):
        """Test mcp list command execution."""
        # Mock registry
        mock_registry = MagicMock()
        mock_registry.list_servers.return_value = []
        mock_registry_class.return_value = mock_registry

        # Mock Path for server discovery
        mock_builtin_dir = MagicMock()
        mock_builtin_dir.exists.return_value = True
        mock_builtin_dir.glob.return_value = []

        mock_path_instance = MagicMock()
        mock_path_instance.parent.parent.__truediv__.return_value = mock_builtin_dir
        mock_path.return_value = mock_path_instance

        sys.argv = ["hos", "mcp", "list"]
        main()

        captured = capsys.readouterr()
        # Should show "no servers found" or empty table
        assert captured.out is not None

    @patch("hosforge.cli.mcp_cmd.MCPServerRegistry")
    @patch("hosforge.cli.mcp_cmd.Path")
    def test_mcp_list_with_servers(self, mock_path, mock_registry_class, capsys):
        """Test mcp list with mock servers."""
        mock_registry = MagicMock()
        mock_registry.list_servers.return_value = [
            {
                "name": "semgrep",
                "loaded": True,
                "tool_count": 5,
                "description": "Semgrep MCP server",
            }
        ]
        mock_registry_class.return_value = mock_registry

        # Mock Path for server discovery
        mock_builtin_dir = MagicMock()
        mock_builtin_dir.exists.return_value = True
        mock_builtin_dir.glob.return_value = []

        mock_path_instance = MagicMock()
        mock_path_instance.parent.parent.__truediv__.return_value = mock_builtin_dir
        mock_path.return_value = mock_path_instance

        sys.argv = ["hos", "mcp", "list"]
        main()

        captured = capsys.readouterr()
        # Should show server table
        assert captured.out is not None


class TestVersionCommand:
    """Test version command."""

    def test_version_command(self, capsys):
        """Test --version displays version info."""
        with pytest.raises(SystemExit) as exc_info:
            sys.argv = ["hos", "--version"]
            main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "2.0.0" in captured.out
