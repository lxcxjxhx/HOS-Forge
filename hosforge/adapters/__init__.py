"""IDE adapters for HOS-Forge."""

from hosforge.adapters.adapter_registry import AdapterRegistry
from hosforge.adapters.base_adapter import AdapterConfig, IDEAdapter
from hosforge.adapters.claude_code_adapter import ClaudeCodeAdapter
from hosforge.adapters.cursor_adapter import CursorAdapter

__all__ = ["IDEAdapter", "AdapterConfig", "AdapterRegistry", "CursorAdapter", "ClaudeCodeAdapter"]
