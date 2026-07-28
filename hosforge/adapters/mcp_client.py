"""MCP Client for connecting to MCP Server.

Provides HTTP client implementation for communicating with
HOS-Forge MCP Server endpoints.
"""

from typing import Any, Dict, List

import httpx


class MCPClient:
    """Client for interacting with MCP Server via HTTP.

    Connects to MCP Server to list available tools and execute them.
    Uses httpx for async-capable HTTP requests.

    Attributes:
        server_url: Base URL of the MCP Server
        timeout: Request timeout in seconds
    """

    def __init__(self, timeout: float = 30.0) -> None:
        """Initialize MCP client.

        Args:
            timeout: Request timeout in seconds
        """
        self._server_url: str | None = None
        self._timeout = timeout
        self._client: httpx.Client | None = None

    @property
    def server_url(self) -> str | None:
        """Get the connected server URL."""
        return self._server_url

    @property
    def is_connected(self) -> bool:
        """Check if client is connected to server."""
        return self._client is not None and self._server_url is not None

    def connect(self, server_url: str) -> None:
        """Connect to MCP Server.

        Args:
            server_url: Base URL of the MCP Server (e.g., "http://localhost:8000")

        Raises:
            httpx.ConnectError: If connection fails
            httpx.TimeoutException: If connection times out
        """
        # Remove trailing slash if present
        normalized_url = server_url.rstrip("/")
        temp_client = httpx.Client(
            base_url=normalized_url,
            timeout=self._timeout,
        )
        # Verify connection with health check
        response = temp_client.get("/health")
        response.raise_for_status()
        # Only set state after successful connection
        self._server_url = normalized_url
        self._client = temp_client

    def disconnect(self) -> None:
        """Disconnect from MCP Server.

        Closes the HTTP client and clears connection state.
        """
        if self._client is not None:
            self._client.close()
            self._client = None
        self._server_url = None

    def list_tools(self) -> List[Dict[str, Any]]:
        """Get all available MCP tools from server.

        Returns:
            List of tool definitions, each containing name, description,
            and inputSchema fields.

        Raises:
            RuntimeError: If not connected to server
            httpx.HTTPStatusError: If request fails
        """
        if not self.is_connected or self._client is None:
            raise RuntimeError("Not connected to MCP Server. Call connect() first.")

        response = self._client.get("/tools")
        response.raise_for_status()
        data = response.json()
        return data.get("tools", [])

    def call_tool(self, tool_name: str, arguments: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Call a specific MCP tool on the server.

        Args:
            tool_name: Name of the tool to execute
            arguments: Arguments to pass to the tool

        Returns:
            Tool execution result containing content and isError fields.

        Raises:
            RuntimeError: If not connected to server
            httpx.HTTPStatusError: If request fails (e.g., 404 for unknown tool)
        """
        if not self.is_connected or self._client is None:
            raise RuntimeError("Not connected to MCP Server. Call connect() first.")

        payload = {"arguments": arguments or {}}
        response = self._client.post(f"/tools/{tool_name}/execute", json=payload)
        response.raise_for_status()
        return response.json()

    def health_check(self) -> Dict[str, Any]:
        """Perform health check on the server.

        Returns:
            Health status dictionary containing status and skills_count.

        Raises:
            RuntimeError: If not connected to server
            httpx.HTTPStatusError: If health check fails
        """
        if not self.is_connected or self._client is None:
            raise RuntimeError("Not connected to MCP Server. Call connect() first.")

        response = self._client.get("/health")
        response.raise_for_status()
        return response.json()
