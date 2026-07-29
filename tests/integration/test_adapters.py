"""IDE 适配器集成测试。

测试 VSCode、Cursor、Claude Code 适配器的输入输出格式转换和命令注册。
"""

import pytest
from unittest.mock import Mock

from hosforge.adapters.base_adapter import IDEAdapter, AdapterConfig
from hosforge.adapters.vscode_adapter import VSCodeAdapter
from hosforge.adapters.cursor_adapter import CursorAdapter
from hosforge.adapters.claude_code_adapter import ClaudeCodeAdapter


class TestVSCodeAdapter:
    """测试 VSCode 适配器。"""

    def test_adapter_name(self):
        """测试适配器名称。"""
        config = AdapterConfig(
            adapter_name="vscode",
            version="1.0.0",
            config={},
        )
        adapter = VSCodeAdapter(config)
        assert adapter.name == "vscode"

    def test_format_input_basic(self):
        """测试基本输入格式化。"""
        config = AdapterConfig(
            adapter_name="vscode",
            version="1.0.0",
            config={},
        )
        adapter = VSCodeAdapter(config)
        
        result = adapter.format_input(
            command="hos.skill.run",
            args={"skill_name": "test_skill", "param1": "value1"},
        )
        
        assert isinstance(result, dict)
        assert "command" in result
        assert result["command"] == "hos.skill.run"

    def test_format_output_success(self):
        """测试成功结果格式化。"""
        config = AdapterConfig(
            adapter_name="vscode",
            version="1.0.0",
            config={},
        )
        adapter = VSCodeAdapter(config)
        
        result = adapter.format_output({
            "success": True,
            "data": {"findings": []},
        })
        
        assert isinstance(result, dict)

    def test_format_output_error(self):
        """测试错误结果格式化。"""
        config = AdapterConfig(
            adapter_name="vscode",
            version="1.0.0",
            config={},
        )
        adapter = VSCodeAdapter(config)
        
        result = adapter.format_output({
            "success": False,
            "error": "Something went wrong",
        })
        
        assert isinstance(result, dict)

    def test_register_commands(self):
        """测试命令注册。"""
        config = AdapterConfig(
            adapter_name="vscode",
            version="1.0.0",
            config={},
        )
        adapter = VSCodeAdapter(config)
        
        commands = adapter.register_commands()
        assert isinstance(commands, list)


class TestCursorAdapter:
    """测试 Cursor 适配器。"""

    def test_adapter_name(self):
        """测试适配器名称。"""
        config = AdapterConfig(
            adapter_name="cursor",
            version="1.0.0",
            config={},
        )
        adapter = CursorAdapter(config)
        assert adapter.name == "cursor"

    def test_format_input_basic(self):
        """测试基本输入格式化。"""
        config = AdapterConfig(
            adapter_name="cursor",
            version="1.0.0",
            config={},
        )
        adapter = CursorAdapter(config)
        
        result = adapter.format_input(
            command="@hos skill list",
            args={},
        )
        
        assert isinstance(result, dict)
        assert "command" in result

    def test_format_output_success(self):
        """测试成功结果格式化。"""
        config = AdapterConfig(
            adapter_name="cursor",
            version="1.0.0",
            config={},
        )
        adapter = CursorAdapter(config)
        
        result = adapter.format_output({
            "success": True,
            "data": {"skills": []},
        })
        
        assert isinstance(result, dict)

    def test_register_commands(self):
        """测试命令注册。"""
        config = AdapterConfig(
            adapter_name="cursor",
            version="1.0.0",
            config={},
        )
        adapter = CursorAdapter(config)
        
        commands = adapter.register_commands()
        assert isinstance(commands, list)


class TestClaudeCodeAdapter:
    """测试 Claude Code 适配器。"""

    def test_adapter_name(self):
        """测试适配器名称。"""
        config = AdapterConfig(
            adapter_name="claude_code",
            version="1.0.0",
            config={},
        )
        adapter = ClaudeCodeAdapter(config)
        assert adapter.name == "claude_code"

    def test_format_input_basic(self):
        """测试基本输入格式化。"""
        config = AdapterConfig(
            adapter_name="claude_code",
            version="1.0.0",
            config={},
        )
        adapter = ClaudeCodeAdapter(config)
        
        result = adapter.format_input(
            command="/hos-skill-info",
            args={"skill_name": "github_integration"},
        )
        
        assert isinstance(result, dict)
        assert "command" in result

    def test_format_output_success(self):
        """测试成功结果格式化。"""
        config = AdapterConfig(
            adapter_name="claude_code",
            version="1.0.0",
            config={},
        )
        adapter = ClaudeCodeAdapter(config)
        
        result = adapter.format_output({
            "success": True,
            "data": {"name": "test_skill"},
        })
        
        assert isinstance(result, dict)

    def test_register_commands(self):
        """测试命令注册。"""
        config = AdapterConfig(
            adapter_name="claude_code",
            version="1.0.0",
            config={},
        )
        adapter = ClaudeCodeAdapter(config)
        
        commands = adapter.register_commands()
        assert isinstance(commands, list)


class TestAdapterConfig:
    """测试适配器配置。"""

    def test_adapter_config_creation(self):
        """测试创建适配器配置。"""
        config = AdapterConfig(
            adapter_name="test_adapter",
            version="2.0.0",
            config={"key": "value"},
        )
        
        assert config.adapter_name == "test_adapter"
        assert config.version == "2.0.0"
        assert config.config["key"] == "value"

    def test_adapter_config_with_empty_config(self):
        """测试空配置。"""
        config = AdapterConfig(
            adapter_name="test_adapter",
            version="1.0.0",
            config={},
        )
        
        assert config.config == {}
