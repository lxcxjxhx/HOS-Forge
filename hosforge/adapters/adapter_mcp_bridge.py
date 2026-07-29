"""Bridge between IDE adapters and MCP Server.

Connects IDE adapters with MCP Server to enable tool execution
through adapter-specific formatting.
"""

import subprocess
import sys
from typing import Any, Dict

from hosforge.adapters.base_adapter import IDEAdapter
from hosforge.adapters.mcp_client import MCPClient


class AdapterMCPBridge:
    """Bridge connecting IDE adapters to MCP Server.

    Facilitates communication between IDE-specific command formats
    and MCP Server tool execution.

    Attributes:
        mcp_client: MCP client instance for server communication
    """

    def __init__(self, mcp_client: MCPClient | None = None) -> None:
        """Initialize the bridge.

        Args:
            mcp_client: Optional MCP client instance. If not provided,
                       a new client will be created.
        """
        self._mcp_client = mcp_client or MCPClient()

    @property
    def mcp_client(self) -> MCPClient:
        """Get the MCP client instance."""
        return self._mcp_client

    def execute_via_mcp(self, adapter: IDEAdapter, command: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute command through MCP Server using adapter formatting.

        Flow:
        1. Use adapter to format input command
        2. Call corresponding MCP tool via client
        3. Use adapter to format output result

        Args:
            adapter: IDE adapter for input/output formatting
            command: Command name to execute
            args: Command arguments

        Returns:
            Formatted result dictionary from adapter

        Raises:
            RuntimeError: If MCP client is not connected
            ValueError: If adapter formatting fails
            httpx.HTTPStatusError: If MCP tool execution fails
        """
        # Step 1: Format input using adapter
        formatted_input = adapter.format_input(command, args)

        # Extract tool name and arguments from formatted input
        # Adapter should return {"command": tool_name, "args": {...}}
        tool_name = formatted_input.get("command", command)
        tool_args = formatted_input.get("args", args)

        # Step 2: Execute tool via MCP client
        mcp_result = self._mcp_client.call_tool(tool_name, tool_args)

        # Step 3: Format output using adapter
        # Convert MCP result to adapter-expected format
        adapter_result = self._mcp_result_to_adapter_format(mcp_result)
        formatted_output = adapter.format_output(adapter_result)

        return formatted_output

    def _mcp_result_to_adapter_format(self, mcp_result: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MCP tool result to adapter-expected format.

        Args:
            mcp_result: MCP tool execution result with content and isError fields

        Returns:
            Dictionary with status, message, and data fields for adapter
        """
        is_error = mcp_result.get("isError", False)
        content_list = mcp_result.get("content", [])

        # Extract text from content
        text = ""
        if content_list and len(content_list) > 0:
            text = content_list[0].get("text", "")

        # Build adapter format
        if is_error:
            return {
                "status": "error",
                "message": "Tool execution failed",
                "data": {"error": text},
            }
        else:
            # Try to parse JSON if possible
            import json

            try:
                data = json.loads(text) if text else {}
            except (json.JSONDecodeError, ValueError):
                data = {"result": text}

            return {
                "status": "success",
                "message": "Tool executed successfully",
                "data": data,
            }

    def start_mcp_server_for_adapter(self, adapter: IDEAdapter, port: int = 8000) -> subprocess.Popen:
        """Start MCP Server instance for the specified adapter.

        Launches a subprocess running the MCP Server on the given port.
        The adapter can then connect to this server instance.

        Args:
            adapter: IDE adapter that will use this server
            port: Port number for the MCP Server (default: 8000)

        Returns:
            subprocess.Popen object for the server process

        Note:
            The caller is responsible for managing the server process lifecycle
            (e.g., calling process.terminate() when done).
        """
        # Start MCP Server as subprocess
        cmd = [
            sys.executable,
            "-m",
            "hosforge.mcp_server.server",
        ]

        # Set environment variable for port if needed
        env = {"MCP_PORT": str(port)}

        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        return process
