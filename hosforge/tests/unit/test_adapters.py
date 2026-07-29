"""IDE adapter unit tests."""

from typing import Any

import pytest

from hosforge.adapters import AdapterConfig, AdapterRegistry, IDEAdapter


class ConcreteAdapter(IDEAdapter):
    """Concrete adapter implementation for testing."""

    def __init__(self, config: AdapterConfig) -> None:
        """Initialize the adapter."""
        super().__init__(config)
        self._supported_commands = ["test_command", "another_command"]

    def format_input(self, command: str, args: dict[str, Any]) -> dict[str, Any]:
        """Format input for testing."""
        return {"command": command, "args": args, "adapter": self.name}

    def format_output(self, result: dict[str, Any]) -> dict[str, Any]:
        """Format output for testing."""
        return {"status": "success", "data": result, "adapter": self.name}

    def register_commands(self) -> list[dict[str, Any]]:
        """Register commands for testing."""
        return [
            {"name": "test_command", "description": "A test command"},
            {"name": "another_command", "description": "Another test command"},
        ]


class TestIDEAdapter:
    """Test IDEAdapter base class."""

    def test_adapter_initialization(self):
        """Test adapter instantiation."""
        config = AdapterConfig(adapter_name="test_adapter", version="1.0.0", config={"key": "value"})
        adapter = ConcreteAdapter(config)

        assert adapter.name == "test_adapter"
        assert adapter._config.version == "1.0.0"
        assert adapter._config.config == {"key": "value"}

    def test_supported_commands(self):
        """Test supported commands property."""
        config = AdapterConfig(adapter_name="test_adapter", version="1.0.0", config={})
        adapter = ConcreteAdapter(config)

        assert "test_command" in adapter.supported_commands
        assert "another_command" in adapter.supported_commands
        assert len(adapter.supported_commands) == 2

    def test_format_input(self):
        """Test input formatting."""
        config = AdapterConfig(adapter_name="test_adapter", version="1.0.0", config={})
        adapter = ConcreteAdapter(config)

        result = adapter.format_input("test_command", {"arg1": "value1"})

        assert result["command"] == "test_command"
        assert result["args"] == {"arg1": "value1"}
        assert result["adapter"] == "test_adapter"

    def test_format_output(self):
        """Test output formatting."""
        config = AdapterConfig(adapter_name="test_adapter", version="1.0.0", config={})
        adapter = ConcreteAdapter(config)

        result = adapter.format_output({"data": "test_result"})

        assert result["status"] == "success"
        assert result["data"] == {"data": "test_result"}
        assert result["adapter"] == "test_adapter"

    def test_register_commands(self):
        """Test command registration."""
        config = AdapterConfig(adapter_name="test_adapter", version="1.0.0", config={})
        adapter = ConcreteAdapter(config)

        commands = adapter.register_commands()

        assert len(commands) == 2
        assert commands[0]["name"] == "test_command"
        assert commands[1]["name"] == "another_command"


class TestAdapterRegistry:
    """Test AdapterRegistry."""

    def test_register_adapter(self):
        """Test registering an adapter."""
        registry = AdapterRegistry()
        config = AdapterConfig(adapter_name="test_adapter", version="1.0.0", config={})
        adapter = ConcreteAdapter(config)

        registry.register(adapter)

        assert registry.get("test_adapter") is adapter

    def test_register_duplicate_adapter(self):
        """Test registering duplicate adapter raises error."""
        registry = AdapterRegistry()
        config = AdapterConfig(adapter_name="test_adapter", version="1.0.0", config={})
        adapter1 = ConcreteAdapter(config)
        adapter2 = ConcreteAdapter(config)

        registry.register(adapter1)

        with pytest.raises(ValueError, match="already registered"):
            registry.register(adapter2)

    def test_unregister_adapter(self):
        """Test unregistering an adapter."""
        registry = AdapterRegistry()
        config = AdapterConfig(adapter_name="test_adapter", version="1.0.0", config={})
        adapter = ConcreteAdapter(config)

        registry.register(adapter)
        registry.unregister("test_adapter")

        with pytest.raises(KeyError, match="not registered"):
            registry.get("test_adapter")

    def test_unregister_nonexistent_adapter(self):
        """Test unregistering non-existent adapter raises error."""
        registry = AdapterRegistry()

        with pytest.raises(KeyError, match="not registered"):
            registry.unregister("nonexistent")

    def test_get_adapter(self):
        """Test getting an adapter by name."""
        registry = AdapterRegistry()
        config = AdapterConfig(adapter_name="test_adapter", version="1.0.0", config={})
        adapter = ConcreteAdapter(config)

        registry.register(adapter)
        retrieved = registry.get("test_adapter")

        assert retrieved is adapter

    def test_get_nonexistent_adapter(self):
        """Test getting non-existent adapter raises error."""
        registry = AdapterRegistry()

        with pytest.raises(KeyError, match="not registered"):
            registry.get("nonexistent")

    def test_list_adapters(self):
        """Test listing all adapters."""
        registry = AdapterRegistry()
        config1 = AdapterConfig(adapter_name="adapter1", version="1.0.0", config={})
        config2 = AdapterConfig(adapter_name="adapter2", version="1.0.0", config={})
        adapter1 = ConcreteAdapter(config1)
        adapter2 = ConcreteAdapter(config2)

        registry.register(adapter1)
        registry.register(adapter2)

        adapters = registry.list_adapters()

        assert len(adapters) == 2
        assert adapter1 in adapters
        assert adapter2 in adapters

    def test_get_adapter_for_command(self):
        """Test getting adapter for a specific command."""
        registry = AdapterRegistry()
        config = AdapterConfig(adapter_name="test_adapter", version="1.0.0", config={})
        adapter = ConcreteAdapter(config)

        registry.register(adapter)

        result = registry.get_adapter_for_command("test_command")
        assert result is adapter

    def test_get_adapter_for_unsupported_command(self):
        """Test getting adapter for unsupported command returns None."""
        registry = AdapterRegistry()
        config = AdapterConfig(adapter_name="test_adapter", version="1.0.0", config={})
        adapter = ConcreteAdapter(config)

        registry.register(adapter)

        result = registry.get_adapter_for_command("unsupported_command")
        assert result is None

    def test_command_routing_with_multiple_adapters(self):
        """Test command routing with multiple adapters."""
        registry = AdapterRegistry()

        config1 = AdapterConfig(adapter_name="adapter1", version="1.0.0", config={})
        adapter1 = ConcreteAdapter(config1)

        config2 = AdapterConfig(adapter_name="adapter2", version="1.0.0", config={})
        adapter2 = ConcreteAdapter(config2)
        adapter2._supported_commands = ["unique_command"]

        registry.register(adapter1)
        registry.register(adapter2)

        # Test routing to adapter1
        result1 = registry.get_adapter_for_command("test_command")
        assert result1 is adapter1

        # Test routing to adapter2
        result2 = registry.get_adapter_for_command("unique_command")
        assert result2 is adapter2
