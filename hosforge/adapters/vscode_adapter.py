"""VSCode adapter for HOS-Forge IDE integration."""

from typing import Any

from hosforge.adapters.base_adapter import AdapterConfig, IDEAdapter


class VSCodeAdapter(IDEAdapter):
    """Adapter for Visual Studio Code IDE integration.

    Converts between HOS-Forge's internal command format and
    VSCode extension command format.
    """

    _COMMAND_TITLES: dict[str, str] = {
        "hos.skill.run": "HOS: Run Skill",
        "hos.skill.list": "HOS: List Skills",
        "hos.skill.info": "HOS: Skill Info",
        "hos.scan.nuclei": "HOS: Run Nuclei Scan",
        "hos.scan.semgrep": "HOS: Run Semgrep Scan",
    }

    def __init__(self, config: AdapterConfig | None = None) -> None:
        """Initialize the VSCode adapter.

        Args:
            config: Optional adapter configuration.  When *None* a default
                configuration is created automatically.
        """
        if config is None:
            config = AdapterConfig(
                adapter_name="vscode",
                version="1.0.0",
                config={},
            )
        super().__init__(config)
        self._supported_commands = [
            "hos.skill.run",
            "hos.skill.list",
            "hos.skill.info",
            "hos.scan.nuclei",
            "hos.scan.semgrep",
        ]

    # ------------------------------------------------------------------
    # IDEAdapter interface
    # ------------------------------------------------------------------

    def format_input(self, command: str, args: dict[str, Any]) -> dict[str, Any]:
        """Convert a generic command into VSCode command format.

        Args:
            command: Command name (e.g. ``"hos.skill.run"``).
            args: Command arguments.

        Returns:
            Dictionary with ``command`` and ``args`` keys suitable for
            VSCode's ``executeCommand`` API.

        Raises:
            ValueError: If *command* is not in :attr:`supported_commands`.
        """
        if command not in self._supported_commands:
            raise ValueError(
                f"Unsupported command '{command}'. "
                f"Supported: {self._supported_commands}"
            )
        return {"command": command, "args": args}

    def format_output(self, result: dict[str, Any]) -> dict[str, Any]:
        """Convert a :class:`SkillResult` dict into a VSCode-friendly format.

        The returned dictionary always contains the keys ``status``,
        ``message``, and ``data``.  An optional ``actions`` list may be
        included when the result provides follow-up operations.

        Args:
            result: Result dictionary produced by command execution.

        Returns:
            Formatted output dictionary for VSCode consumption.
        """
        status: str = result.get("status", "success")
        message: str = result.get("message", "")
        data: Any = result.get("data")
        actions: list[dict[str, Any]] | None = result.get("actions")

        output: dict[str, Any] = {
            "status": status,
            "message": message,
            "data": data,
        }
        if actions is not None:
            output["actions"] = actions
        return output

    def register_commands(self) -> list[dict[str, Any]]:
        """Return VSCode ``package.json`` command definitions.

        Each entry contains ``command``, ``title``, and ``category``
        fields matching the VSCode extension manifest schema.

        Returns:
            List of command definition dictionaries.
        """
        commands: list[dict[str, Any]] = []
        for cmd in self._supported_commands:
            title = self._COMMAND_TITLES.get(cmd, cmd)
            commands.append({
                "command": cmd,
                "title": title,
                "category": "HOS",
            })
        return commands
