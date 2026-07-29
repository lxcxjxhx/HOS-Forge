"""End-to-end integration tests for HOS-Forge workflow.

This module tests complete workflows from CLI → Skill Registry → MCP Server → IDE Adapter,
verifying the entire system integration and error handling across all components.
"""

import json
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, Mock, patch

import pytest

from hosforge.adapters.adapter_mcp_bridge import AdapterMCPBridge
from hosforge.adapters.adapter_registry import AdapterRegistry
from hosforge.adapters.claude_code_adapter import ClaudeCodeAdapter
from hosforge.adapters.cursor_adapter import CursorAdapter
from hosforge.adapters.mcp_client import MCPClient
from hosforge.adapters.vscode_adapter import VSCodeAdapter
from hosforge.cli.main import (
    cmd_skill_info,
    cmd_skill_list,
    cmd_skill_run,
    create_default_registry,
)
from hosforge.cli.main import main as cli_main
from hosforge.cli.main import (
    parse_skill_args,
)
from hosforge.mcp_server.server import create_app
from hosforge.mcp_server.skill_bridge import MCPToolExecutor, SkillToMCPTool
from hosforge.skills.base_skill import Skill, SkillResult
from hosforge.skills.loader import SkillLoader
from hosforge.skills.registry import SkillRegistry


class TestCLIToSkillExecution:
    """Test CLI → Skill execution workflow."""

    def test_cli_skill_list_command(self, capsys):
        """Test CLI skill list command executes successfully."""
        exit_code = cli_main(["skill", "list"])
        captured = capsys.readouterr()

        assert exit_code == 0
        assert "github_integration" in captured.out or "No skills registered" in captured.out

    def test_cli_skill_list_json_format(self, capsys):
        """Test CLI skill list with JSON output format."""
        exit_code = cli_main(["skill", "list", "--format", "json"])
        captured = capsys.readouterr()

        assert exit_code == 0
        # Should be valid JSON
        data = json.loads(captured.out)
        assert isinstance(data, list)

    def test_cli_skill_info_command(self, capsys):
        """Test CLI skill info command for existing skill."""
        exit_code = cli_main(["skill", "info", "github_integration"])
        captured = capsys.readouterr()

        assert exit_code == 0
        assert "github_integration" in captured.out

    def test_cli_skill_info_nonexistent(self, capsys):
        """Test CLI skill info for non-existent skill returns error."""
        exit_code = cli_main(["skill", "info", "nonexistent_skill"])
        captured = capsys.readouterr()

        assert exit_code == 1
        assert "not found" in captured.err.lower()

    def test_cli_skill_run_with_mock(self, mock_skill, capsys):
        """Test CLI skill run command with mocked skill execution."""
        with patch("hosforge.cli.main.create_default_registry") as mock_create:
            mock_registry = Mock(spec=SkillRegistry)
            mock_registry.execute_skill.return_value = SkillResult(
                success=True,
                data={"result": "test output"},
            )
            mock_create.return_value = mock_registry

            exit_code = cli_main(["skill", "run", "mock_skill", "input=test"])
            captured = capsys.readouterr()

            assert exit_code == 0
            assert "Success" in captured.out
            mock_registry.execute_skill.assert_called_once()

    def test_cli_skill_run_failure(self, capsys):
        """Test CLI skill run command handles execution failure."""
        with patch("hosforge.cli.main.create_default_registry") as mock_create:
            mock_registry = Mock(spec=SkillRegistry)
            mock_registry.execute_skill.return_value = SkillResult(
                success=False,
                error="Execution failed",
            )
            mock_create.return_value = mock_registry

            exit_code = cli_main(["skill", "run", "test_skill", "param=value"])
            captured = capsys.readouterr()

            assert exit_code == 1
            assert "Error" in captured.err

    def test_parse_skill_args_valid(self):
        """Test parsing valid skill arguments."""
        args = ["key1=value1", "key2=value2", "key3=123"]
        result = parse_skill_args(args)

        assert result["key1"] == "value1"
        assert result["key2"] == "value2"
        assert result["key3"] == 123  # Should parse as int

    def test_parse_skill_args_json_array(self):
        """Test parsing skill arguments with JSON array."""
        args = ['labels=["bug", "urgent"]']
        result = parse_skill_args(args)

        assert result["labels"] == ["bug", "urgent"]

    def test_parse_skill_args_invalid_format(self):
        """Test parsing invalid skill argument format raises error."""
        args = ["invalid_arg_no_equals"]

        with pytest.raises(ValueError, match="Invalid argument format"):
            parse_skill_args(args)


class TestMCPServerIntegration:
    """Test MCP Server startup and tool invocation."""

    def test_mcp_server_health_check(self, mcp_app):
        """Test MCP Server health check endpoint."""
        from fastapi.testclient import TestClient

        client = TestClient(mcp_app)
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "skills_count" in data

    def test_mcp_server_list_skills(self, mcp_app):
        """Test MCP Server list skills endpoint."""
        from fastapi.testclient import TestClient

        client = TestClient(mcp_app)
        response = client.get("/skills")

        assert response.status_code == 200
        data = response.json()
        assert "skills" in data
        assert isinstance(data["skills"], list)

    def test_mcp_server_list_tools(self, mcp_app):
        """Test MCP Server list tools endpoint."""
        from fastapi.testclient import TestClient

        client = TestClient(mcp_app)
        response = client.get("/tools")

        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert isinstance(data["tools"], list)

        # Each tool should have name, description, inputSchema
        if data["tools"]:
            tool = data["tools"][0]
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool

    def test_mcp_server_execute_tool_success(self, mcp_app):
        """Test MCP Server tool execution success."""
        from fastapi.testclient import TestClient

        client = TestClient(mcp_app)

        # Execute nuclei_scan with valid parameters
        response = client.post("/tools/nuclei_scan/execute", json={"arguments": {"target": "https://example.com"}})

        assert response.status_code == 200
        data = response.json()
        # Should return MCP format result
        assert "content" in data or "isError" in data

    def test_mcp_server_execute_tool_not_found(self, mcp_app):
        """Test MCP Server tool execution with non-existent tool."""
        from fastapi.testclient import TestClient

        client = TestClient(mcp_app)

        response = client.post("/tools/nonexistent_tool/execute", json={"arguments": {}})

        assert response.status_code == 404

    def test_mcp_tool_conversion(self, github_skill):
        """Test Skill to MCP tool conversion."""
        mcp_tool = SkillToMCPTool.convert(github_skill)

        assert mcp_tool["name"] == "github_integration"
        assert "description" in mcp_tool
        assert "inputSchema" in mcp_tool
        assert mcp_tool["inputSchema"]["type"] == "object"

    def test_mcp_tool_executor_success(self, skill_registry):
        """Test MCP tool executor with successful execution."""
        executor = MCPToolExecutor(skill_registry)

        result = executor.execute("mock_skill", {"input": "test"})

        assert result["isError"] is False
        assert "content" in result
        assert len(result["content"]) > 0
        assert result["content"][0]["type"] == "text"

    def test_mcp_tool_executor_error(self, skill_registry):
        """Test MCP tool executor with error handling."""
        executor = MCPToolExecutor(skill_registry)

        result = executor.execute("error_skill", {"error_type": "value_error"})

        assert result["isError"] is True
        assert "content" in result
        assert "error" in result["content"][0]["text"].lower()

    def test_mcp_tool_executor_not_found(self, skill_registry):
        """Test MCP tool executor with non-existent skill."""
        executor = MCPToolExecutor(skill_registry)

        result = executor.execute("nonexistent_skill", {})

        assert result["isError"] is True
        assert "not found" in result["content"][0]["text"].lower()


class TestIDEAdapterIntegration:
    """Test IDE Adapter integration through MCP."""

    def test_vscode_adapter_command_formatting(self, vscode_adapter):
        """Test VSCode adapter formats commands correctly."""
        formatted = vscode_adapter.format_input("hos.skill.run", {"skill_name": "nuclei_scan", "target": "example.com"})

        assert formatted["command"] == "hos.skill.run"
        assert "args" in formatted
        assert formatted["args"]["skill_name"] == "nuclei_scan"

    def test_vscode_adapter_output_formatting(self, vscode_adapter):
        """Test VSCode adapter formats output correctly."""
        result = {"status": "success", "message": "Scan completed", "data": {"findings": 5}}

        formatted = vscode_adapter.format_output(result)

        assert formatted["status"] == "success"
        assert "data" in formatted

    def test_cursor_adapter_command_formatting(self, cursor_adapter):
        """Test Cursor adapter formats @mention commands correctly."""
        formatted = cursor_adapter.format_input("@hos nuclei", {"target": "example.com"})

        assert "command" in formatted
        assert "args" in formatted

    def test_cursor_adapter_output_formatting(self, cursor_adapter):
        """Test Cursor adapter formats output as Markdown."""
        result = {"status": "success", "message": "Scan completed", "data": {"findings": 5}}

        formatted = cursor_adapter.format_output(result)

        assert "content" in formatted
        assert "metadata" in formatted
        assert formatted["metadata"]["format"] == "markdown"
        assert "Success" in formatted["content"]

    def test_claude_adapter_command_formatting(self, claude_adapter):
        """Test Claude Code adapter formats slash commands correctly."""
        formatted = claude_adapter.format_input("/hos-nuclei", {"target": "example.com"})

        assert formatted["command"] == "nuclei"
        assert "args" in formatted

    def test_claude_adapter_output_formatting(self, claude_adapter):
        """Test Claude Code adapter formats output correctly."""
        result = {"status": "success", "message": "Scan completed", "data": {"findings": 5}}

        formatted = claude_adapter.format_output(result)

        assert "response" in formatted
        assert "tool_results" in formatted
        assert "data" in formatted

    def test_adapter_registry_routing(self, adapter_registry):
        """Test adapter registry routes commands to correct adapter."""
        # VSCode command
        vscode = adapter_registry.get_adapter_for_command("hos.skill.run")
        assert vscode is not None
        assert vscode.name == "vscode"

        # Cursor command
        cursor = adapter_registry.get_adapter_for_command("@hos nuclei")
        assert cursor is not None
        assert cursor.name == "cursor"

        # Claude command
        claude = adapter_registry.get_adapter_for_command("/hos-nuclei")
        assert claude is not None
        assert claude.name == "claude_code"

    def test_adapter_mcp_bridge_execution(self, adapter_mcp_bridge, vscode_adapter):
        """Test adapter MCP bridge executes commands through MCP."""
        adapter_mcp_bridge.mcp_client.call_tool.return_value = {
            "content": [{"type": "text", "text": '{"result": "success"}'}],
            "isError": False,
        }

        result = adapter_mcp_bridge.execute_via_mcp(vscode_adapter, "hos.skill.run", {"skill_name": "test"})

        assert result["status"] == "success"
        assert "data" in result

    def test_adapter_mcp_bridge_error_handling(self, adapter_mcp_bridge, vscode_adapter):
        """Test adapter MCP bridge handles MCP errors correctly."""
        adapter_mcp_bridge.mcp_client.call_tool.return_value = {
            "content": [{"type": "text", "text": "Tool execution failed"}],
            "isError": True,
        }

        result = adapter_mcp_bridge.execute_via_mcp(vscode_adapter, "hos.skill.run", {"skill_name": "test"})

        assert result["status"] == "error"
        assert "error" in result["data"]


class TestSkillDynamicLoading:
    """Test dynamic skill loading from directories."""

    def test_skill_loader_from_directory(self, skill_loader, sample_skills_dir):
        """Test loading skills from directory."""
        # Create a sample skill file
        sample_skill_code = """
from hosforge.skills.base_skill import Skill
from typing import Dict, Any

class SampleTestSkill(Skill):
    def __init__(self):
        super().__init__(
            name="sample_test",
            description="Sample test skill",
            parameters={"type": "object", "properties": {}}
        )
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        return {"result": "sample"}
"""
        sample_file = sample_skills_dir / "sample_skill.py"
        sample_file.write_text(sample_skill_code, encoding="utf-8")

        try:
            skills = skill_loader.load_from_directory(str(sample_skills_dir))

            assert len(skills) > 0
            skill_names = [s.name for s in skills]
            assert "sample_test" in skill_names
        finally:
            # Cleanup
            if sample_file.exists():
                sample_file.unlink()

    def test_skill_loader_nonexistent_directory(self, skill_loader):
        """Test loading from non-existent directory returns empty list."""
        skills = skill_loader.load_from_directory("/nonexistent/path")

        assert len(skills) == 0

    def test_skill_loader_from_module(self, skill_loader):
        """Test loading skills from Python module."""
        skills = skill_loader.load_from_module("hosforge.skills.security")

        assert len(skills) > 0
        skill_names = [s.name for s in skills]
        assert "github_integration" in skill_names
        assert "nuclei_scan" in skill_names
        assert "semgrep_scan" in skill_names

    def test_skill_loader_invalid_module(self, skill_loader):
        """Test loading from invalid module returns empty list."""
        skills = skill_loader.load_from_module("nonexistent.module")

        assert len(skills) == 0

    def test_skill_registry_integration(self, skill_loader):
        """Test loaded skills can be registered and executed."""
        skills = skill_loader.load_from_module("hosforge.skills.security")

        registry = SkillRegistry()
        for skill in skills:
            registry.register(skill)

        # Verify skills are registered
        registered = registry.list_skills()
        assert len(registered) == len(skills)

        # Verify can get specific skill
        github = registry.get("github_integration")
        assert github is not None
        assert github.name == "github_integration"


class TestErrorHandlingChain:
    """Test error handling across all components."""

    def test_skill_execution_error_propagation(self, skill_registry):
        """Test skill execution errors propagate correctly."""
        result = skill_registry.execute_skill("error_skill", error_type="value_error")

        assert result.success is False
        assert result.error is not None
        assert "value error" in result.error.lower()

    def test_skill_not_found_error(self, skill_registry):
        """Test non-existent skill returns error result."""
        result = skill_registry.execute_skill("nonexistent_skill")

        assert result.success is False
        assert "not found" in result.error.lower()

    def test_mcp_executor_error_handling(self, skill_registry):
        """Test MCP executor handles skill errors correctly."""
        executor = MCPToolExecutor(skill_registry)

        result = executor.execute("error_skill", {"error_type": "runtime_error"})

        assert result["isError"] is True
        assert "error" in result["content"][0]["text"].lower()

    def test_adapter_bridge_error_propagation(self, adapter_mcp_bridge, vscode_adapter):
        """Test adapter bridge propagates errors correctly."""
        adapter_mcp_bridge.mcp_client.call_tool.return_value = {
            "content": [{"type": "text", "text": "Internal error"}],
            "isError": True,
        }

        result = adapter_mcp_bridge.execute_via_mcp(vscode_adapter, "hos.skill.run", {"skill_name": "error_skill"})

        assert result["status"] == "error"

    def test_mcp_client_connection_error(self):
        """Test MCP client handles connection errors."""
        client = MCPClient()

        # Not connected, should raise error
        with pytest.raises(RuntimeError, match="Not connected"):
            client.call_tool("test", {})

    def test_cli_invalid_skill_args(self, capsys):
        """Test CLI handles invalid skill arguments."""
        exit_code = cli_main(["skill", "run", "test_skill", "invalid_arg"])
        captured = capsys.readouterr()

        assert exit_code == 1
        assert "Error" in captured.err

    def test_adapter_unsupported_command(self, vscode_adapter):
        """Test adapter rejects unsupported commands."""
        with pytest.raises(ValueError, match="Unsupported command"):
            vscode_adapter.format_input("unsupported.command", {})


class TestCompleteWorkflow:
    """Test complete end-to-end workflows."""

    def test_cli_to_skill_execution_workflow(self, capsys):
        """Test complete workflow: CLI → Registry → Skill execution."""
        # List skills
        exit_code = cli_main(["skill", "list", "--format", "json"])
        assert exit_code == 0

        captured = capsys.readouterr()
        skills = json.loads(captured.out)
        assert isinstance(skills, list)

    def test_mcp_server_workflow(self, mcp_app):
        """Test complete workflow: MCP Server → Tool listing → Execution."""
        from fastapi.testclient import TestClient

        client = TestClient(mcp_app)

        # Health check
        response = client.get("/health")
        assert response.status_code == 200

        # List tools
        response = client.get("/tools")
        assert response.status_code == 200
        tools = response.json()["tools"]

        # Execute a tool if available
        if tools:
            tool_name = tools[0]["name"]
            response = client.post(f"/tools/{tool_name}/execute", json={"arguments": {}})
            # Should return 200 or 404 (if tool requires specific args)
            assert response.status_code in [200, 404, 422]

    def test_adapter_to_mcp_workflow(self, adapter_mcp_bridge, vscode_adapter):
        """Test complete workflow: Adapter → MCP Bridge → Tool execution."""
        # Mock successful MCP response
        adapter_mcp_bridge.mcp_client.call_tool.return_value = {
            "content": [{"type": "text", "text": '{"status": "completed"}'}],
            "isError": False,
        }

        # Execute through adapter
        result = adapter_mcp_bridge.execute_via_mcp(vscode_adapter, "hos.skill.run", {"skill_name": "test"})

        assert result["status"] == "success"
        assert "data" in result

    def test_multi_adapter_workflow(self, adapter_registry):
        """Test workflow with multiple adapters handling same command type."""
        # All adapters should handle skill-related commands
        adapters = adapter_registry.list_adapters()

        assert len(adapters) >= 3

        # Each adapter should have supported commands
        for adapter in adapters:
            assert len(adapter.supported_commands) > 0

    def test_skill_loading_and_registration_workflow(self, skill_loader):
        """Test workflow: Load skills → Register → Execute."""
        # Load skills
        skills = skill_loader.load_from_module("hosforge.skills.security")
        assert len(skills) > 0

        # Register skills
        registry = SkillRegistry()
        for skill in skills:
            registry.register(skill)

        # Verify registration
        registered = registry.list_skills()
        assert len(registered) == len(skills)

        # Get specific skill
        github = registry.get("github_integration")
        assert github is not None

        # Verify skill metadata
        assert github.name == "github_integration"
        assert github.description
        assert github.parameters


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_skill_registry(self):
        """Test operations on empty skill registry."""
        registry = SkillRegistry()

        assert len(registry.list_skills()) == 0
        assert registry.get("any_skill") is None

        result = registry.execute_skill("any_skill")
        assert result.success is False

    def test_skill_with_no_parameters(self):
        """Test skill with no parameters defined."""

        class NoParamSkill(Skill):
            def __init__(self):
                super().__init__(name="no_param", description="No parameters", parameters=None)

            def execute(self, **kwargs):
                return {"result": "ok"}

        skill = NoParamSkill()
        registry = SkillRegistry()
        registry.register(skill)

        result = registry.execute_skill("no_param")
        assert result.success is True

    def test_mcp_tool_conversion_with_complex_schema(self):
        """Test MCP tool conversion with complex parameter schema."""

        class ComplexSkill(Skill):
            def __init__(self):
                super().__init__(
                    name="complex",
                    description="Complex parameters",
                    parameters={
                        "type": "object",
                        "properties": {
                            "string_param": {"type": "string"},
                            "int_param": {"type": "integer"},
                            "array_param": {"type": "array", "items": {"type": "string"}},
                            "object_param": {"type": "object", "properties": {"nested": {"type": "string"}}},
                        },
                        "required": ["string_param"],
                    },
                )

            def execute(self, **kwargs):
                return {"result": "complex"}

        skill = ComplexSkill()
        mcp_tool = SkillToMCPTool.convert(skill)

        assert mcp_tool["name"] == "complex"
        assert "inputSchema" in mcp_tool
        assert mcp_tool["inputSchema"]["type"] == "object"
        assert "properties" in mcp_tool["inputSchema"]

    def test_adapter_with_empty_result(self, vscode_adapter):
        """Test adapter handles empty result correctly."""
        result = vscode_adapter.format_output({})

        assert "status" in result
        assert "data" in result

    def test_concurrent_skill_execution(self, skill_registry):
        """Test concurrent skill execution (basic test)."""
        import threading

        results = []

        def execute_skill():
            result = skill_registry.execute_skill("mock_skill", input="test")
            results.append(result)

        threads = [threading.Thread(target=execute_skill) for _ in range(3)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 3
        assert all(r.success for r in results)
