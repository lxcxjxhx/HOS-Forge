"""Base MCP server implementation."""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class BaseMCPServer:
    """Base class for MCP servers."""

    def __init__(self, name: str, allowed_base_path: Optional[str] = None):
        """Initialize base MCP server.

        Args:
            name: Server name
            allowed_base_path: Optional base path to restrict file access
        """
        self.name = name
        self.tools: Dict[str, Callable] = {}
        self.allowed_base_path = Path(allowed_base_path).resolve() if allowed_base_path else None

    def register_tool(self, name: str, handler: Callable, description: str = "") -> None:
        """Register a tool handler.

        Args:
            name: Tool name
            handler: Tool handler function
            description: Tool description
        """
        self.tools[name] = {
            "handler": handler,
            "description": description,
        }

    def get_tool_list(self) -> List[Dict[str, Any]]:
        """Get list of available tools.

        Returns:
            List of tool definitions
        """
        return [
            {
                "name": name,
                "description": info["description"],
            }
            for name, info in self.tools.items()
        ]

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming JSON-RPC request.

        Args:
            request: JSON-RPC request

        Returns:
            JSON-RPC response
        """
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "result": {"tools": self.get_tool_list()},
                "id": request_id,
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if tool_name not in self.tools:
                return {
                    "jsonrpc": "2.0",
                    "error": {"code": -32601, "message": f"Tool not found: {tool_name}"},
                    "id": request_id,
                }

            try:
                handler = self.tools[tool_name]["handler"]
                result = await handler(**arguments)
                return {
                    "jsonrpc": "2.0",
                    "result": result,
                    "id": request_id,
                }
            except Exception as e:
                logger.error(f"Tool execution error: {e}", exc_info=True)
                return {
                    "jsonrpc": "2.0",
                    "error": {"code": -32603, "message": "Internal error"},
                    "id": request_id,
                }

        else:
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32601, "message": f"Method not found: {method}"},
                "id": request_id,
            }

    async def run(self) -> None:
        """Run the MCP server (stdin/stdout loop)."""
        while True:
            line = sys.stdin.readline()
            if not line:
                break

            try:
                request = json.loads(line)
                response = await self.handle_request(request)
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {"code": -32700, "message": f"Parse error: {str(e)}"},
                    "id": None,
                }
                sys.stdout.write(json.dumps(error_response) + "\n")
                sys.stdout.flush()
