"""MCP configuration management."""

import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field


@dataclass
class MCPServerConfig:
    """Configuration for a single MCP server."""
    name: str
    description: str = ""
    tools: List[str] = field(default_factory=list)
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPConfig:
    """Complete MCP configuration."""
    servers: List[MCPServerConfig] = field(default_factory=list)
    global_config: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_yaml_file(cls, file_path: Union[str, Path]) -> 'MCPConfig':
        """Load MCP configuration from YAML file.

        Args:
            file_path: Path to YAML configuration file

        Returns:
            MCPConfig instance

        Raises:
            FileNotFoundError: If file doesn't exist
            yaml.YAMLError: If YAML is invalid
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"MCP config file not found: {file_path}")

        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPConfig':
        """Create MCPConfig from dictionary.

        Args:
            data: Configuration dictionary

        Returns:
            MCPConfig instance
        """
        servers = []
        for server_data in data.get('servers', []):
            server = MCPServerConfig(
                name=server_data.get('name', 'unnamed'),
                description=server_data.get('description', ''),
                tools=server_data.get('tools', []),
                enabled=server_data.get('enabled', True),
                config=server_data.get('config', {}),
            )
            servers.append(server)

        return cls(
            servers=servers,
            global_config=data.get('global_config', {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Configuration dictionary
        """
        return {
            'servers': [
                {
                    'name': s.name,
                    'description': s.description,
                    'tools': s.tools,
                    'enabled': s.enabled,
                    'config': s.config,
                }
                for s in self.servers
            ],
            'global_config': self.global_config,
        }

    def get_server(self, name: str) -> Optional[MCPServerConfig]:
        """Get server configuration by name.

        Args:
            name: Server name

        Returns:
            MCPServerConfig if found, None otherwise
        """
        for server in self.servers:
            if server.name == name:
                return server
        return None

    def get_enabled_servers(self) -> List[MCPServerConfig]:
        """Get list of enabled servers.

        Returns:
            List of enabled MCPServerConfig instances
        """
        return [s for s in self.servers if s.enabled]

    def add_server(self, server: MCPServerConfig) -> None:
        """Add a server configuration.

        Args:
            server: Server configuration to add
        """
        self.servers.append(server)

    def remove_server(self, name: str) -> bool:
        """Remove a server configuration.

        Args:
            name: Server name to remove

        Returns:
            True if removed, False if not found
        """
        for i, server in enumerate(self.servers):
            if server.name == name:
                del self.servers[i]
                return True
        return False

    def save_to_yaml(self, file_path: Union[str, Path]) -> None:
        """Save configuration to YAML file.

        Args:
            file_path: Path to save YAML file
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, allow_unicode=True)
