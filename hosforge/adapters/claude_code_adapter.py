"""Claude Code adapter for HOS-Forge IDE integration."""

import json
from pathlib import Path
from typing import Any

from hosforge.adapters.base_adapter import AdapterConfig, IDEAdapter

_TEMPLATES_DIR = Path(__file__).parent / "templates"

# /hos-xxx 命令到内部命令名的映射
_COMMAND_MAP: dict[str, str] = {
    "/hos-scan": "scan",
    "/hos-nuclei": "nuclei",
    "/hos-semgrep": "semgrep",
    "/hos-skill-list": "skill_list",
    "/hos-skill-info": "skill_info",
}


class ClaudeCodeAdapter(IDEAdapter):
    """Adapter for Claude Code skill integration.

    Converts ``/hos-xxx`` slash commands into HOS-Forge's internal
    command format and produces Claude Code compatible skill output.
    """

    def __init__(self, config: AdapterConfig | None = None) -> None:
        """Initialize the Claude Code adapter.

        Args:
            config: Optional adapter configuration.  When *None* a default
                configuration is created automatically.
        """
        if config is None:
            config = AdapterConfig(
                adapter_name="claude_code",
                version="1.0.0",
                config={},
            )
        super().__init__(config)
        self._supported_commands = [
            "/hos-scan",
            "/hos-nuclei",
            "/hos-semgrep",
            "/hos-skill-list",
            "/hos-skill-info",
        ]

    # ------------------------------------------------------------------
    # IDEAdapter interface
    # ------------------------------------------------------------------

    def format_input(self, command: str, args: dict[str, Any]) -> dict[str, Any]:
        """Convert a ``/hos-xxx`` slash command into internal format.

        Args:
            command: Slash command string (e.g. ``"/hos-scan"``).
            args: Command arguments.

        Returns:
            Dictionary with ``command`` (internal name) and ``args`` keys.

        Raises:
            ValueError: If *command* is not a recognised slash command.
        """
        if command not in self._supported_commands:
            raise ValueError(
                f"Unsupported command '{command}'. "
                f"Supported: {self._supported_commands}"
            )
        internal_name = _COMMAND_MAP[command]
        return {"command": internal_name, "args": args}

    def format_output(self, result: dict[str, Any]) -> dict[str, Any]:
        """Convert a :class:`SkillResult` dict into Claude Code skill format.

        The returned dictionary contains:
        - ``response``: human-readable summary string
        - ``tool_results``: list of tool-call result entries

        Args:
            result: Result dictionary produced by command execution.

        Returns:
            Formatted output dictionary for Claude Code consumption.
        """
        status: str = result.get("status", "success")
        message: str = result.get("message", "")
        data: Any = result.get("data")
        tool_results: list[dict[str, Any]] | None = result.get("tool_results")

        response_parts: list[str] = []
        if status != "success":
            response_parts.append(f"[{status}]")
        if message:
            response_parts.append(message)
        response = " ".join(response_parts)

        output: dict[str, Any] = {
            "response": response,
            "tool_results": tool_results if tool_results is not None else [],
            "data": data,
        }
        return output

    def register_commands(self) -> list[dict[str, Any]]:
        """Return Claude Code skill definitions.

        Loads skill metadata from the bundled ``claude_skills.json``
        template and returns a list of skill definition dicts, each
        containing ``name``, ``description``, ``parameters``, and
        ``handler`` fields.

        Returns:
            List of Claude Code skill definition dictionaries.
        """
        skills_path = _TEMPLATES_DIR / "claude_skills.json"
        with open(skills_path, encoding="utf-8") as fh:
            skills_data: list[dict[str, Any]] = json.load(fh)
        return skills_data
