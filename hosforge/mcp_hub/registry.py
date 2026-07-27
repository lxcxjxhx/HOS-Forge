"""MCP Server registry for dynamic server management."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MCPServerRegistry:
    """Registry for managing MCP servers and their tools."""
    
    def __init__(self):
        """Initialize MCP server registry."""
        self._servers: Dict[str, Dict[str, Any]] = {}
    
    def register_server(
        self,
        name: str,
        description: str,
        tools: List[str],
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Register a new MCP server.
        
        Args:
            name: Server name
            description: Server description
            tools: List of tool names provided by this server
            config: Optional server configuration
        """
        self._servers[name] = {
            "name": name,
            "description": description,
            "tools": tools,
            "config": config or {},
        }
        logger.info(f"Registered MCP server: {name} with {len(tools)} tools")
    
    def unregister_server(self, name: str) -> bool:
        """Unregister an MCP server.
        
        Args:
            name: Server name to unregister
            
        Returns:
            True if server was unregistered, False if not found
        """
        if name in self._servers:
            del self._servers[name]
            logger.info(f"Unregistered MCP server: {name}")
            return True
        return False
    
    def get_server(self, name: str) -> Optional[Dict[str, Any]]:
        """Get server information by name.
        
        Args:
            name: Server name
            
        Returns:
            Server information dictionary or None if not found
        """
        return self._servers.get(name)
    
    def list_servers(self) -> List[Dict[str, Any]]:
        """List all registered servers.
        
        Returns:
            List of server information dictionaries
        """
        return [
            {
                "name": info["name"],
                "description": info["description"],
                "tool_count": len(info["tools"]),
            }
            for info in self._servers.values()
        ]
    
    def get_tools_for_server(self, name: str) -> List[str]:
        """Get list of tools for a specific server.
        
        Args:
            name: Server name
            
        Returns:
            List of tool names
        """
        server = self._servers.get(name)
        if server:
            return server["tools"]
        return []
    
    def get_all_tools(self) -> List[str]:
        """Get all tools from all registered servers.
        
        Returns:
            List of all tool names
        """
        tools = []
        for server_info in self._servers.values():
            tools.extend(server_info["tools"])
        return tools
    
    def is_tool_available(self, tool_name: str) -> bool:
        """Check if a tool is available in any registered server.
        
        Args:
            tool_name: Tool name to check
            
        Returns:
            True if tool is available, False otherwise
        """
        for server_info in self._servers.values():
            if tool_name in server_info["tools"]:
                return True
        return False
    
    def find_server_for_tool(self, tool_name: str) -> Optional[str]:
        """Find which server provides a specific tool.
        
        Args:
            tool_name: Tool name to find
            
        Returns:
            Server name if found, None otherwise
        """
        for server_info in self._servers.values():
            if tool_name in server_info["tools"]:
                return server_info["name"]
        return None
    
    def get_server_config(self, name: str) -> Optional[Dict[str, Any]]:
        """Get server configuration.
        
        Args:
            name: Server name
            
        Returns:
            Server configuration dictionary or None if not found
        """
        server = self._servers.get(name)
        if server:
            return server["config"]
        return None
    
    def update_server_config(self, name: str, config: Dict[str, Any]) -> bool:
        """Update server configuration.
        
        Args:
            name: Server name
            config: New configuration to merge
            
        Returns:
            True if updated, False if server not found
        """
        server = self._servers.get(name)
        if server:
            server["config"].update(config)
            return True
        return False
    
    def discover_server(self, name: str, server_path: str) -> None:
        """Discover and register a server from file path.
        
        Args:
            name: Server name
            server_path: Path to server file
        """
        # For now, just register with basic info
        # In real implementation, this would load the server and extract tools
        self.register_server(
            name=name,
            description=f"Discovered from {server_path}",
            tools=[],
            config={"path": server_path, "loaded": True}
        )
    
    def clear(self) -> None:
        """Clear all registered servers."""
        self._servers.clear()
        logger.info("Cleared all MCP server registrations")
