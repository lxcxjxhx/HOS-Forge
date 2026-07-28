"""IDE adapters for HOS-Forge."""

from hosforge.adapters.base_adapter import AdapterConfig, IDEAdapter
from hosforge.adapters.adapter_registry import AdapterRegistry
from hosforge.adapters.cursor_adapter import CursorAdapter
from hosforge.adapters.claude_code_adapter import ClaudeCodeAdapter

__all__ = ["IDEAdapter", "AdapterConfig", "AdapterRegistry", "CursorAdapter", "ClaudeCodeAdapter"]
