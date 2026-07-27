"""MCP client for unified tool invocation."""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MCPClient:
    """Client for invoking MCP tools."""
    
    def __init__(self, registry=None):
        """Initialize MCP client.
        
        Args:
            registry: MCPServerRegistry instance for tool discovery
        """
        self.registry = registry
        self._connections: Dict[str, Any] = {}
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Call an MCP tool.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool execution result
            
        Raises:
            ValueError: If tool not found
            RuntimeError: If tool execution fails
        """
        if not self.registry:
            raise RuntimeError("No registry configured")
        
        # Find which server provides this tool
        server_name = self.registry.find_server_for_tool(tool_name)
        if not server_name:
            raise ValueError(f"Tool not found: {tool_name}")
        
        # Get server info
        server_info = self.registry.get_server(server_name)
        if not server_info:
            raise RuntimeError(f"Server not found: {server_name}")
        
        # Simulate tool execution (in real implementation, this would connect to actual MCP server)
        logger.info(f"Calling tool {tool_name} on server {server_name} with args: {arguments}")
        
        # Mock response
        return {
            "tool": tool_name,
            "server": server_name,
            "arguments": arguments or {},
            "status": "success",
            "result": f"Mock result for {tool_name}",
        }
    
    async def call_tool_batch(
        self,
        calls: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Call multiple MCP tools in batch.
        
        Args:
            calls: List of call specifications, each with 'tool' and optional 'arguments'
            
        Returns:
            List of results in same order as calls
        """
        tasks = []
        for call in calls:
            tool_name = call.get("tool")
            arguments = call.get("arguments", {})
            if tool_name:
                tasks.append(self.call_tool(tool_name, arguments))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "tool": calls[i].get("tool"),
                    "status": "error",
                    "error": str(result),
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools.
        
        Returns:
            List of tool information dictionaries
        """
        if not self.registry:
            return []
        
        tools = []
        for server_info in self.registry.list_servers():
            server_name = server_info["name"]
            for tool_name in self.registry.get_tools_for_server(server_name):
                tools.append({
                    "name": tool_name,
                    "server": server_name,
                })
        
        return tools
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all registered servers.
        
        Returns:
            Health check results
        """
        if not self.registry:
            return {"status": "no_registry"}
        
        results = {}
        for server_info in self.registry.list_servers():
            server_name = server_info["name"]
            # Mock health check
            results[server_name] = {
                "status": "healthy",
                "tool_count": server_info["tool_count"],
            }
        
        return {
            "status": "ok",
            "servers": results,
        }
    
    def close(self) -> None:
        """Close all connections."""
        self._connections.clear()
        logger.info("MCP client connections closed")
