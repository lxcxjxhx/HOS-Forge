"""Adapter and MCP integration tests.

Tests MCPClient, AdapterMCPBridge, and integration with IDE adapters.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Any, Dict

import httpx

from hosforge.adapters.mcp_client import MCPClient
from hosforge.adapters.adapter_mcp_bridge import AdapterMCPBridge
from hosforge.adapters.base_adapter import IDEAdapter, AdapterConfig
from hosforge.adapters.vscode_adapter import VSCodeAdapter
from hosforge.adapters.cursor_adapter import CursorAdapter


class TestMCPClient:
    """Test MCPClient class."""

    def test_connect_success(self):
        """Test successful connection to MCP Server."""
        client = MCPClient()

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            client.connect("http://localhost:8000")

            assert client.is_connected
            assert client.server_url == "http://localhost:8000"
            mock_client.get.assert_called_once_with("/health")

    def test_connect_with_trailing_slash(self):
        """Test connection normalizes URL by removing trailing slash."""
        client = MCPClient()

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            client.connect("http://localhost:8000/")

            assert client.server_url == "http://localhost:8000"

    def test_connect_failure(self):
        """Test connection failure raises exception."""
        client = MCPClient()

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get.side_effect = httpx.ConnectError("Connection refused")
            mock_client_class.return_value = mock_client

            with pytest.raises(httpx.ConnectError):
                client.connect("http://localhost:8000")

            assert not client.is_connected

    def test_disconnect(self):
        """Test disconnect closes client and clears state."""
        client = MCPClient()

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            client.connect("http://localhost:8000")
            assert client.is_connected

            client.disconnect()
            assert not client.is_connected
            assert client.server_url is None
            mock_client.close.assert_called_once()

    def test_list_tools_success(self):
        """Test listing tools from server."""
        client = MCPClient()

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                "tools": [
                    {"name": "tool1", "description": "Tool 1", "inputSchema": {}},
                    {"name": "tool2", "description": "Tool 2", "inputSchema": {}},
                ]
            }
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            client.connect("http://localhost:8000")
            tools = client.list_tools()

            assert len(tools) == 2
            assert tools[0]["name"] == "tool1"
            assert tools[1]["name"] == "tool2"

    def test_list_tools_not_connected(self):
        """Test list_tools raises error when not connected."""
        client = MCPClient()

        with pytest.raises(RuntimeError, match="Not connected"):
            client.list_tools()

    def test_call_tool_success(self):
        """Test calling a tool successfully."""
        client = MCPClient()

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                "content": [{"type": "text", "text": "success"}],
                "isError": False,
            }
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            client.connect("http://localhost:8000")
            result = client.call_tool("test_tool", {"arg1": "value1"})

            assert result["isError"] is False
            assert "success" in result["content"][0]["text"]
            mock_client.post.assert_called_once()

    def test_call_tool_not_connected(self):
        """Test call_tool raises error when not connected."""
        client = MCPClient()

        with pytest.raises(RuntimeError, match="Not connected"):
            client.call_tool("test_tool", {})

    def test_health_check_success(self):
        """Test health check returns status."""
        client = MCPClient()

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"status": "ok", "skills_count": 5}
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            client.connect("http://localhost:8000")
            health = client.health_check()

            assert health["status"] == "ok"
            assert health["skills_count"] == 5


class TestAdapterMCPBridge:
    """Test AdapterMCPBridge class."""

    def test_execute_via_mcp_success(self):
        """Test successful execution through MCP."""
        mock_client = MagicMock(spec=MCPClient)
        mock_client.call_tool.return_value = {
            "content": [{"type": "text", "text": '{"result": "test"}'}],
            "isError": False,
        }

        bridge = AdapterMCPBridge(mock_client)
        adapter = VSCodeAdapter()

        result = bridge.execute_via_mcp(
            adapter, "hos.skill.run", {"skill_name": "test"}
        )

        assert result["status"] == "success"
        assert "data" in result
        mock_client.call_tool.assert_called_once()

    def test_execute_via_mcp_error(self):
        """Test execution with MCP error."""
        mock_client = MagicMock(spec=MCPClient)
        mock_client.call_tool.return_value = {
            "content": [{"type": "text", "text": "Tool not found"}],
            "isError": True,
        }

        bridge = AdapterMCPBridge(mock_client)
        adapter = VSCodeAdapter()

        result = bridge.execute_via_mcp(
            adapter, "hos.skill.run", {"skill_name": "nonexistent"}
        )

        assert result["status"] == "error"
        assert "error" in result["data"]

    def test_execute_via_mcp_with_cursor_adapter(self):
        """Test execution with Cursor adapter."""
        mock_client = MagicMock(spec=MCPClient)
        mock_client.call_tool.return_value = {
            "content": [{"type": "text", "text": '{"findings": 0}'}],
            "isError": False,
        }

        bridge = AdapterMCPBridge(mock_client)
        adapter = CursorAdapter()

        result = bridge.execute_via_mcp(adapter, "@hos scan", {"target": "."})

        assert "content" in result
        assert "metadata" in result
        assert result["metadata"]["format"] == "markdown"

    def test_start_mcp_server_for_adapter(self):
        """Test starting MCP server subprocess."""
        bridge = AdapterMCPBridge()
        adapter = VSCodeAdapter()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_popen.return_value = mock_process

            process = bridge.start_mcp_server_for_adapter(adapter, port=9000)

            assert process == mock_process
            mock_popen.assert_called_once()

    def test_mcp_result_to_adapter_format_success_json(self):
        """Test converting MCP result with JSON content."""
        bridge = AdapterMCPBridge()

        mcp_result = {
            "content": [{"type": "text", "text": '{"key": "value"}'}],
            "isError": False,
        }

        adapter_format = bridge._mcp_result_to_adapter_format(mcp_result)

        assert adapter_format["status"] == "success"
        assert adapter_format["data"]["key"] == "value"

    def test_mcp_result_to_adapter_format_success_text(self):
        """Test converting MCP result with plain text content."""
        bridge = AdapterMCPBridge()

        mcp_result = {
            "content": [{"type": "text", "text": "Plain text result"}],
            "isError": False,
        }

        adapter_format = bridge._mcp_result_to_adapter_format(mcp_result)

        assert adapter_format["status"] == "success"
        assert adapter_format["data"]["result"] == "Plain text result"

    def test_mcp_result_to_adapter_format_error(self):
        """Test converting MCP error result."""
        bridge = AdapterMCPBridge()

        mcp_result = {
            "content": [{"type": "text", "text": "Error occurred"}],
            "isError": True,
        }

        adapter_format = bridge._mcp_result_to_adapter_format(mcp_result)

        assert adapter_format["status"] == "error"
        assert adapter_format["data"]["error"] == "Error occurred"


class TestIntegrationWithDifferentAdapters:
    """Test integration with different IDE adapters."""

    def test_vscode_adapter_integration(self):
        """Test full integration with VSCode adapter."""
        mock_client = MagicMock(spec=MCPClient)
        mock_client.call_tool.return_value = {
            "content": [{"type": "text", "text": '{"skills": []}'}],
            "isError": False,
        }

        bridge = AdapterMCPBridge(mock_client)
        adapter = VSCodeAdapter()

        result = bridge.execute_via_mcp(
            adapter, "hos.skill.list", {}
        )

        assert result["status"] == "success"
        assert "data" in result

    def test_cursor_adapter_integration(self):
        """Test full integration with Cursor adapter."""
        mock_client = MagicMock(spec=MCPClient)
        mock_client.call_tool.return_value = {
            "content": [{"type": "text", "text": '{"status": "scanning"}'}],
            "isError": False,
        }

        bridge = AdapterMCPBridge(mock_client)
        adapter = CursorAdapter()

        result = bridge.execute_via_mcp(
            adapter, "@hos nuclei", {"target": "/path"}
        )

        assert "content" in result
        assert "metadata" in result
        assert result["metadata"]["adapter"] == "cursor"

    def test_multiple_tool_calls(self):
        """Test multiple sequential tool calls."""
        mock_client = MagicMock(spec=MCPClient)
        mock_client.call_tool.side_effect = [
            {
                "content": [{"type": "text", "text": '{"tool": "first"}'}],
                "isError": False,
            },
            {
                "content": [{"type": "text", "text": '{"tool": "second"}'}],
                "isError": False,
            },
        ]

        bridge = AdapterMCPBridge(mock_client)
        adapter = VSCodeAdapter()

        result1 = bridge.execute_via_mcp(adapter, "hos.skill.list", {})
        result2 = bridge.execute_via_mcp(adapter, "hos.skill.info", {"name": "test"})

        assert result1["status"] == "success"
        assert result2["status"] == "success"
        assert mock_client.call_tool.call_count == 2
