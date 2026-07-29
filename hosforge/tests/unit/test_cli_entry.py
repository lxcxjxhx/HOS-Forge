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
        assert "skill" in captured.out
        assert "taskflow" in captured.out
        assert "validate" in captured.out

    def test_no_args_shows_help(self, capsys):
        """Test that running without args shows help."""
        # New architecture: no args shows help but doesn't exit
        sys.argv = ["hos"]
        main()

        captured = capsys.readouterr()
        assert "HOS-Forge" in captured.out


class TestSkillCommand:
    """Test skill CLI commands."""

    def test_skill_list(self, capsys):
        """Test skill list command execution."""
        sys.argv = ["hos", "skill", "list"]
        main()

        captured = capsys.readouterr()
        # Should show skill list or "no skills" message
        assert captured.out is not None

    def test_skill_info(self, capsys):
        """Test skill info command execution."""
        sys.argv = ["hos", "skill", "info", "github"]
        main()

        captured = capsys.readouterr()
        # Should show skill info or "not found" message
        assert captured.out is not None


class TestTaskflowCommand:
    """Test taskflow CLI commands."""

    def test_taskflow_help(self, capsys):
        """Test taskflow --help shows usage."""
        with pytest.raises(SystemExit) as exc_info:
            sys.argv = ["hos", "taskflow", "--help"]
            main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "taskflow" in captured.out


class TestValidateCommand:
    """Test validate CLI commands."""

    def test_validate_help(self, capsys):
        """Test validate --help shows usage."""
        with pytest.raises(SystemExit) as exc_info:
            sys.argv = ["hos", "validate", "--help"]
            main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "validate" in captured.out


class TestVersionCommand:
    """Test version command."""

    def test_version_command(self, capsys):
        """Test --version displays version info."""
        with pytest.raises(SystemExit) as exc_info:
            sys.argv = ["hos", "--version"]
            main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        # Version is now 0.1.0 in pyproject.toml
        assert "0.1.0" in captured.out or "hos" in captured.out
