"""Cursor IDE adapter implementation."""

import re
from typing import Any

from hosforge.adapters.base_adapter import AdapterConfig, IDEAdapter


class CursorAdapter(IDEAdapter):
    """Adapter for Cursor IDE integration.

    Handles @mention command parsing and Markdown output formatting
    for Cursor's chat interface.

    Attributes:
        name: Adapter name ("cursor")
        supported_commands: List of supported @hos commands
    """

    def __init__(self, config: AdapterConfig | None = None) -> None:
        """Initialize the Cursor adapter.

        Args:
            config: Optional adapter configuration. If not provided,
                   a default configuration will be created.
        """
        if config is None:
            config = AdapterConfig(adapter_name="cursor", version="1.0.0", config={})
        super().__init__(config)
        self._supported_commands = ["@hos scan", "@hos nuclei", "@hos semgrep", "@hos skill list", "@hos skill info"]

    def format_input(self, command: str, args: dict[str, Any]) -> dict[str, Any]:
        """Format @mention command for internal processing.

        Parses @hos commands and extracts the command name and arguments.

        Args:
            command: The @mention command (e.g., "@hos scan")
            args: Additional arguments

        Returns:
            Dictionary with "command" and "args" keys

        Raises:
            ValueError: If command format is invalid
        """
        # Parse @mention format: @hos <command> [subcommand]
        pattern = r"^@hos\s+(\w+)(?:\s+(\w+))?"
        match = re.match(pattern, command.strip())

        if not match:
            raise ValueError(f"Invalid @mention command format: {command}")

        main_cmd = match.group(1)
        sub_cmd = match.group(2)

        # Build internal command format
        if sub_cmd:
            internal_command = f"{main_cmd} {sub_cmd}"
        else:
            internal_command = main_cmd

        return {"command": internal_command, "args": args}

    def format_output(self, result: dict[str, Any]) -> dict[str, Any]:
        """Format result as Markdown for Cursor display.

        Converts SkillResult to Markdown-formatted output suitable for
        Cursor's chat interface.

        Args:
            result: Result dictionary from command execution

        Returns:
            Dictionary with "content" (Markdown string) and "metadata"
        """
        # Extract result data
        status = result.get("status", "unknown")
        data = result.get("data", {})
        message = result.get("message", "")

        # Build Markdown content
        markdown_parts = []

        # Add status header
        if status == "success":
            markdown_parts.append("✅ **Success**\n")
        elif status == "error":
            markdown_parts.append("❌ **Error**\n")
        else:
            markdown_parts.append(f"**Status**: {status}\n")

        # Add message if present
        if message:
            markdown_parts.append(f"{message}\n")

        # Add data content
        if data:
            if isinstance(data, dict):
                # Format dict as key-value pairs
                markdown_parts.append("\n**Results**:\n")
                for key, value in data.items():
                    markdown_parts.append(f"- **{key}**: {value}\n")
            elif isinstance(data, list):
                # Format list as bullet points
                markdown_parts.append("\n**Results**:\n")
                for item in data:
                    markdown_parts.append(f"- {item}\n")
            else:
                # Format as plain text
                markdown_parts.append(f"\n{data}\n")

        content = "".join(markdown_parts)

        return {"content": content, "metadata": {"format": "markdown", "status": status, "adapter": self.name}}

    def register_commands(self) -> list[dict[str, Any]]:
        """Register Cursor Rules command definitions.

        Returns command definitions in Cursor Rules format with
        trigger patterns, descriptions, and handlers.

        Returns:
            List of command definition dictionaries
        """
        return [
            {"trigger": "@hos scan", "description": "Run security scan on the codebase", "handler": "handle_scan"},
            {"trigger": "@hos nuclei", "description": "Run Nuclei security scanner", "handler": "handle_nuclei"},
            {"trigger": "@hos semgrep", "description": "Run Semgrep static analysis", "handler": "handle_semgrep"},
            {
                "trigger": "@hos skill list",
                "description": "List available security skills",
                "handler": "handle_skill_list",
            },
            {
                "trigger": "@hos skill info",
                "description": "Get information about a specific skill",
                "handler": "handle_skill_info",
            },
        ]
