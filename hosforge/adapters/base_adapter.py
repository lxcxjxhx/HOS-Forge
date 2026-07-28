"""Base adapter module for IDE integration."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class AdapterConfig:
    """Configuration for an IDE adapter.
    
    Attributes:
        adapter_name: Name of the adapter
        version: Version string
        config: Additional configuration dictionary
    """
    adapter_name: str
    version: str
    config: dict[str, Any]


class IDEAdapter(ABC):
    """Abstract base class for IDE adapters.
    
    IDE adapters handle the conversion between HOS-Forge's internal
    command format and IDE-specific formats.
    
    Attributes:
        name: Name of the adapter
        supported_commands: List of command names this adapter supports
    """
    
    def __init__(self, config: AdapterConfig) -> None:
        """Initialize the adapter with configuration.
        
        Args:
            config: Adapter configuration
        """
        self._config = config
        self._supported_commands: list[str] = []
    
    @property
    def name(self) -> str:
        """Get the adapter name."""
        return self._config.adapter_name
    
    @property
    def supported_commands(self) -> list[str]:
        """Get the list of supported commands."""
        return self._supported_commands
    
    @abstractmethod
    def format_input(self, command: str, args: dict[str, Any]) -> dict[str, Any]:
        """Format input command and arguments for the IDE.
        
        Args:
            command: Command name
            args: Command arguments
            
        Returns:
            Formatted input dictionary for the IDE
        """
        pass
    
    @abstractmethod
    def format_output(self, result: dict[str, Any]) -> dict[str, Any]:
        """Format output result for the IDE.
        
        Args:
            result: Result dictionary from command execution
            
        Returns:
            Formatted output dictionary for the IDE
        """
        pass
    
    @abstractmethod
    def register_commands(self) -> list[dict[str, Any]]:
        """Register commands supported by this adapter.
        
        Returns:
            List of command definitions
        """
        pass
