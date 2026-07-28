"""Adapter registry for managing IDE adapters."""

from typing import Optional

from hosforge.adapters.base_adapter import IDEAdapter


class AdapterRegistry:
    """Registry for managing IDE adapters.
    
    Provides methods to register, unregister, and retrieve adapters,
    as well as routing commands to the appropriate adapter.
    """
    
    def __init__(self) -> None:
        """Initialize the adapter registry."""
        self._adapters: dict[str, IDEAdapter] = {}
    
    def register(self, adapter: IDEAdapter) -> None:
        """Register an IDE adapter.
        
        Args:
            adapter: The adapter instance to register
            
        Raises:
            ValueError: If an adapter with the same name is already registered
        """
        if adapter.name in self._adapters:
            raise ValueError(f"Adapter '{adapter.name}' is already registered")
        self._adapters[adapter.name] = adapter
    
    def unregister(self, adapter_name: str) -> None:
        """Unregister an IDE adapter by name.
        
        Args:
            adapter_name: Name of the adapter to unregister
            
        Raises:
            KeyError: If no adapter with the given name is registered
        """
        if adapter_name not in self._adapters:
            raise KeyError(f"Adapter '{adapter_name}' is not registered")
        del self._adapters[adapter_name]
    
    def get(self, adapter_name: str) -> IDEAdapter:
        """Get an IDE adapter by name.
        
        Args:
            adapter_name: Name of the adapter
            
        Returns:
            The adapter instance
            
        Raises:
            KeyError: If no adapter with the given name is registered
        """
        if adapter_name not in self._adapters:
            raise KeyError(f"Adapter '{adapter_name}' is not registered")
        return self._adapters[adapter_name]
    
    def list_adapters(self) -> list[IDEAdapter]:
        """List all registered adapters.
        
        Returns:
            List of all registered adapter instances
        """
        return list(self._adapters.values())
    
    def get_adapter_for_command(self, command: str) -> Optional[IDEAdapter]:
        """Find the adapter that supports a given command.
        
        Args:
            command: Command name to look up
            
        Returns:
            The first adapter that supports the command, or None if not found
        """
        for adapter in self._adapters.values():
            if command in adapter.supported_commands:
                return adapter
        return None
