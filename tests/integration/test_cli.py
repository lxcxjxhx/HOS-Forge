"""CLI 集成测试。

测试命令行界面的参数解析、命令执行和输出格式。
"""

import pytest
from unittest.mock import Mock, patch
import argparse

from hosforge.cli.main import (
    create_parser,
    parse_skill_args,
    format_skill_list_table,
    format_skill_list_json,
    format_skill_info_table,
    format_skill_info_json,
    cmd_skill_list,
    cmd_skill_info,
    cmd_skill_run,
)
from hosforge.skills.base_skill import Skill


class TestCLIParser:
    """测试命令行参数解析器。"""

    def test_create_parser(self):
        """测试创建解析器。"""
        parser = create_parser()
        assert parser is not None
        assert parser.prog == "hos"

    def test_parse_skill_list_command(self):
        """测试解析 skill list 命令。"""
        parser = create_parser()
        args = parser.parse_args(["skill", "list"])
        
        assert args.command == "skill"
        assert args.skill_command == "list"
        assert args.format == "table"

    def test_parse_skill_list_with_json_format(self):
        """测试解析带 JSON 格式的 skill list 命令。"""
        parser = create_parser()
        args = parser.parse_args(["skill", "list", "--format", "json"])
        
        assert args.command == "skill"
        assert args.skill_command == "list"
        assert args.format == "json"

    def test_parse_skill_info_command(self):
        """测试解析 skill info 命令。"""
        parser = create_parser()
        args = parser.parse_args(["skill", "info", "github_integration"])
        
        assert args.command == "skill"
        assert args.skill_command == "info"
        assert args.skill_name == "github_integration"

    def test_parse_skill_run_command(self):
        """测试解析 skill run 命令。"""
        parser = create_parser()
        args = parser.parse_args([
            "skill", "run", "nuclei_scan",
            "target=https://example.com",
            "severity=high",
        ])
        
        assert args.command == "skill"
        assert args.skill_command == "run"
        assert args.skill_name == "nuclei_scan"
        assert len(args.args) == 2


class TestParseSkillArgs:
    """测试 skill 参数解析。"""

    def test_parse_empty_args(self):
        """测试解析空参数。"""
        result = parse_skill_args([])
        assert result == {}

    def test_parse_single_arg(self):
        """测试解析单个参数。"""
        result = parse_skill_args(["key=value"])
        assert result == {"key": "value"}

    def test_parse_multiple_args(self):
        """测试解析多个参数。"""
        result = parse_skill_args([
            "target=https://example.com",
            "severity=high",
            "timeout=600",
        ])
        
        assert result["target"] == "https://example.com"
        assert result["severity"] == "high"
        assert result["timeout"] == 600  # JSON 解析会将数字转换为 int

    def test_parse_json_value(self):
        """测试解析 JSON 值。"""
        result = parse_skill_args(['data={"key": "value"}'])
        assert result["data"] == {"key": "value"}

    def test_parse_json_array(self):
        """测试解析 JSON 数组。"""
        result = parse_skill_args(['items=[1, 2, 3]'])
        assert result["items"] == [1, 2, 3]

    def test_parse_invalid_format(self):
        """测试解析无效格式。"""
        with pytest.raises(ValueError, match="Invalid argument format"):
            parse_skill_args(["invalid_arg"])


class TestFormatSkillList:
    """测试 skill 列表格式化。"""

    def test_format_empty_list_table(self):
        """测试格式化空列表为表格。"""
        result = format_skill_list_table([])
        assert result == "No skills registered."

    def test_format_empty_list_json(self):
        """测试格式化空列表为 JSON。"""
        result = format_skill_list_json([])
        assert result == "[]"

    def test_format_single_skill_table(self):
        """测试格式化单个 skill 为表格。"""
        skill = Mock(spec=Skill)
        skill.name = "test_skill"
        skill.description = "Test description"
        skill.parameters = {
            "type": "object",
            "properties": {
                "param1": {"type": "string"},
            },
        }
        
        result = format_skill_list_table([skill])
        assert "test_skill" in result
        assert "Test description" in result

    def test_format_single_skill_json(self):
        """测试格式化单个 skill 为 JSON。"""
        skill = Mock(spec=Skill)
        skill.name = "test_skill"
        skill.description = "Test description"
        skill.parameters = {"type": "object", "properties": {}}
        
        result = format_skill_list_json([skill])
        assert '"name": "test_skill"' in result
        assert '"description": "Test description"' in result


class TestFormatSkillInfo:
    """测试 skill 详细信息格式化。"""

    def test_format_skill_info_table(self):
        """测试格式化 skill 信息为表格。"""
        skill = Mock(spec=Skill)
        skill.name = "test_skill"
        skill.description = "Test description"
        skill.parameters = {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "Parameter 1",
                },
            },
            "required": ["param1"],
        }
        
        result = format_skill_info_table(skill)
        assert "test_skill" in result
        assert "Test description" in result
        assert "param1" in result

    def test_format_skill_info_json(self):
        """测试格式化 skill 信息为 JSON。"""
        skill = Mock(spec=Skill)
        skill.name = "test_skill"
        skill.description = "Test description"
        skill.parameters = {"type": "object", "properties": {}}
        
        result = format_skill_info_json(skill)
        assert '"name": "test_skill"' in result
        assert '"description": "Test description"' in result


class TestCLICommands:
    """测试 CLI 命令执行。"""

    @patch("hosforge.cli.main.create_default_registry")
    def test_cmd_skill_list_table(self, mock_create_registry, capsys):
        """测试 skill list 命令（表格格式）。"""
        mock_registry = Mock()
        mock_skill = Mock(spec=Skill)
        mock_skill.name = "test_skill"
        mock_skill.description = "Test"
        mock_skill.parameters = {"type": "object", "properties": {}}
        mock_registry.list_skills.return_value = [mock_skill]
        mock_create_registry.return_value = mock_registry
        
        args = argparse.Namespace(format="table")
        result = cmd_skill_list(args)
        
        assert result == 0
        captured = capsys.readouterr()
        assert "test_skill" in captured.out

    @patch("hosforge.cli.main.create_default_registry")
    def test_cmd_skill_list_json(self, mock_create_registry, capsys):
        """测试 skill list 命令（JSON 格式）。"""
        mock_registry = Mock()
        mock_skill = Mock(spec=Skill)
        mock_skill.name = "test_skill"
        mock_skill.description = "Test"
        mock_skill.parameters = {"type": "object", "properties": {}}
        mock_registry.list_skills.return_value = [mock_skill]
        mock_create_registry.return_value = mock_registry
        
        args = argparse.Namespace(format="json")
        result = cmd_skill_list(args)
        
        assert result == 0
        captured = capsys.readouterr()
        assert '"name": "test_skill"' in captured.out

    @patch("hosforge.cli.main.create_default_registry")
    def test_cmd_skill_info_success(self, mock_create_registry, capsys):
        """测试 skill info 命令成功。"""
        mock_registry = Mock()
        mock_skill = Mock(spec=Skill)
        mock_skill.name = "test_skill"
        mock_skill.description = "Test"
        mock_skill.parameters = {"type": "object", "properties": {}}
        mock_registry.get.return_value = mock_skill
        mock_create_registry.return_value = mock_registry
        
        args = argparse.Namespace(skill_name="test_skill", format="table")
        result = cmd_skill_info(args)
        
        assert result == 0

    @patch("hosforge.cli.main.create_default_registry")
    def test_cmd_skill_info_not_found(self, mock_create_registry, capsys):
        """测试 skill info 命令（skill 不存在）。"""
        mock_registry = Mock()
        mock_registry.get.return_value = None
        mock_create_registry.return_value = mock_registry
        
        args = argparse.Namespace(skill_name="nonexistent", format="table")
        result = cmd_skill_info(args)
        
        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err.lower()

    @patch("hosforge.cli.main.create_default_registry")
    def test_cmd_skill_run_success(self, mock_create_registry, capsys):
        """测试 skill run 命令成功。"""
        from hosforge.skills.base_skill import SkillResult
        
        mock_registry = Mock()
        mock_registry.execute_skill.return_value = SkillResult(
            success=True,
            data={"result": "success"},
        )
        mock_create_registry.return_value = mock_registry
        
        args = argparse.Namespace(
            skill_name="test_skill",
            args=["param1=value1"],
        )
        result = cmd_skill_run(args)
        
        assert result == 0
        captured = capsys.readouterr()
        assert "Success" in captured.out

    @patch("hosforge.cli.main.create_default_registry")
    def test_cmd_skill_run_failure(self, mock_create_registry, capsys):
        """测试 skill run 命令失败。"""
        from hosforge.skills.base_skill import SkillResult
        
        mock_registry = Mock()
        mock_registry.execute_skill.return_value = SkillResult(
            success=False,
            error="Execution failed",
        )
        mock_create_registry.return_value = mock_registry
        
        args = argparse.Namespace(
            skill_name="test_skill",
            args=[],
        )
        result = cmd_skill_run(args)
        
        assert result == 1
        captured = capsys.readouterr()
        assert "Execution failed" in captured.err
