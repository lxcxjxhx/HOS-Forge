"""CLI skills 命令单元测试。"""

import json
import pytest
from typing import Any, Dict
from unittest.mock import patch, MagicMock
from io import StringIO

from hosforge.cli.main import (
    main,
    create_parser,
    parse_skill_args,
    format_skill_list_table,
    format_skill_list_json,
    format_skill_info_table,
    format_skill_info_json,
    _generate_skill_examples,
    create_default_registry,
)
from hosforge.skills import Skill, SkillResult, SkillRegistry


class ConcreteSkill(Skill):
    """用于测试的具体 Skill 实现。"""

    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行简单的操作并返回结果。"""
        return {"result": "success", "params": kwargs}


class TestParseSkillArgs:
    """测试 parse_skill_args 函数。"""

    def test_parse_empty_args(self):
        """测试解析空参数列表。"""
        result = parse_skill_args([])
        assert result == {}

    def test_parse_single_string_arg(self):
        """测试解析单个字符串参数。"""
        result = parse_skill_args(["key=value"])
        assert result == {"key": "value"}

    def test_parse_multiple_args(self):
        """测试解析多个参数。"""
        result = parse_skill_args(["key1=value1", "key2=value2", "key3=value3"])
        assert result == {
            "key1": "value1",
            "key2": "value2",
            "key3": "value3",
        }

    def test_parse_json_array_arg(self):
        """测试解析 JSON 数组参数。"""
        result = parse_skill_args(['labels=["bug","critical"]'])
        assert result == {"labels": ["bug", "critical"]}

    def test_parse_json_object_arg(self):
        """测试解析 JSON 对象参数。"""
        result = parse_skill_args(['config={"key":"value"}'])
        assert result == {"config": {"key": "value"}}

    def test_parse_json_number_arg(self):
        """测试解析 JSON 数字参数。"""
        result = parse_skill_args(["limit=10"])
        assert result == {"limit": 10}

    def test_parse_json_boolean_arg(self):
        """测试解析 JSON 布尔参数。"""
        result = parse_skill_args(["verbose=true"])
        assert result == {"verbose": True}

    def test_parse_invalid_format_raises_error(self):
        """测试解析无效格式参数时抛出异常。"""
        with pytest.raises(ValueError, match="Invalid argument format"):
            parse_skill_args(["invalid_arg"])

    def test_parse_arg_with_equals_in_value(self):
        """测试解析值中包含等号的参数。"""
        result = parse_skill_args(["query=a=b"])
        assert result == {"query": "a=b"}


class TestFormatSkillList:
    """测试 skill 列表格式化函数。"""

    def test_format_empty_list_table(self):
        """测试格式化空列表为表格。"""
        result = format_skill_list_table([])
        assert result == "No skills registered."

    def test_format_skill_list_table(self):
        """测试格式化 skill 列表为表格。"""
        skill1 = ConcreteSkill(name="test1", description="Test skill 1")
        skill2 = ConcreteSkill(name="test2", description="Test skill 2")

        result = format_skill_list_table([skill1, skill2])

        assert "test1" in result
        assert "test2" in result
        assert "Test skill 1" in result
        assert "Test skill 2" in result
        assert "Name" in result
        assert "Description" in result

    def test_format_skill_list_json(self):
        """测试格式化 skill 列表为 JSON。"""
        skill1 = ConcreteSkill(name="test1", description="Test skill 1")
        skill2 = ConcreteSkill(name="test2", description="Test skill 2")

        result = format_skill_list_json([skill1, skill2])
        data = json.loads(result)

        assert len(data) == 2
        assert data[0]["name"] == "test1"
        assert data[1]["name"] == "test2"
        assert data[0]["description"] == "Test skill 1"


class TestFormatSkillInfo:
    """测试 skill 详细信息格式化函数。"""

    def test_format_skill_info_table_no_params(self):
        """测试格式化无参数的 skill 信息为表格。"""
        skill = ConcreteSkill(name="test", description="Test skill")

        result = format_skill_info_table(skill)

        assert "Name: test" in result
        assert "Description: Test skill" in result
        assert "Parameters:" in result
        assert "No parameters defined." in result

    def test_format_skill_info_table_with_params(self):
        """测试格式化带参数的 skill 信息为表格。"""
        skill = ConcreteSkill(
            name="test",
            description="Test skill",
            parameters={
                "type": "object",
                "properties": {
                    "param1": {"type": "string", "description": "First parameter"},
                    "param2": {"type": "integer", "description": "Second parameter"},
                },
                "required": ["param1"],
            },
        )

        result = format_skill_info_table(skill)

        assert "Name: test" in result
        assert "param1: string (required)" in result
        assert "param2: integer" in result
        assert "First parameter" in result
        assert "Second parameter" in result

    def test_format_skill_info_json(self):
        """测试格式化 skill 信息为 JSON。"""
        skill = ConcreteSkill(
            name="test",
            description="Test skill",
            parameters={
                "type": "object",
                "properties": {"param1": {"type": "string"}},
            },
        )

        result = format_skill_info_json(skill)
        data = json.loads(result)

        assert data["name"] == "test"
        assert data["description"] == "Test skill"
        assert "parameters" in data
        assert "examples" in data


class TestGenerateSkillExamples:
    """测试 skill 示例生成函数。"""

    def test_generate_examples_github(self):
        """测试生成 GitHub skill 示例。"""
        skill = ConcreteSkill(name="github_integration", description="GitHub skill")
        examples = _generate_skill_examples(skill)

        assert len(examples) > 0
        assert any("github_integration" in ex for ex in examples)

    def test_generate_examples_semgrep(self):
        """测试生成 Semgrep skill 示例。"""
        skill = ConcreteSkill(name="semgrep_scan", description="Semgrep skill")
        examples = _generate_skill_examples(skill)

        assert len(examples) > 0
        assert any("semgrep_scan" in ex for ex in examples)

    def test_generate_examples_nuclei(self):
        """测试生成 Nuclei skill 示例。"""
        skill = ConcreteSkill(name="nuclei_scan", description="Nuclei skill")
        examples = _generate_skill_examples(skill)

        assert len(examples) > 0
        assert any("nuclei_scan" in ex for ex in examples)

    def test_generate_examples_generic_with_params(self):
        """测试生成通用 skill 示例（带参数）。"""
        skill = ConcreteSkill(
            name="custom_skill",
            description="Custom skill",
            parameters={
                "type": "object",
                "properties": {"param1": {"type": "string"}},
            },
        )
        examples = _generate_skill_examples(skill)

        assert len(examples) > 0
        assert any("custom_skill" in ex for ex in examples)

    def test_generate_examples_generic_no_params(self):
        """测试生成通用 skill 示例（无参数）。"""
        skill = ConcreteSkill(name="simple_skill", description="Simple skill")
        examples = _generate_skill_examples(skill)

        assert len(examples) > 0
        assert any("simple_skill" in ex for ex in examples)


class TestCreateDefaultRegistry:
    """测试创建默认 registry 函数。"""

    def test_create_default_registry(self):
        """测试创建默认 registry 并注册所有内置 skills。"""
        registry = create_default_registry()

        skills = registry.list_skills()
        skill_names = [s.name for s in skills]

        assert "github_integration" in skill_names
        assert "semgrep_scan" in skill_names
        assert "nuclei_scan" in skill_names
        assert len(skills) == 3


class TestCLICommands:
    """测试 CLI 命令执行。"""

    def test_main_no_args_shows_help(self, capsys):
        """测试无参数时显示帮助信息。"""
        exit_code = main([])
        assert exit_code == 0

        captured = capsys.readouterr()
        assert "usage:" in captured.out.lower() or "hos" in captured.out

    def test_skill_list_command_table(self, capsys):
        """测试 skill list 命令（表格格式）。"""
        exit_code = main(["skill", "list"])
        assert exit_code == 0

        captured = capsys.readouterr()
        assert "github_integration" in captured.out
        assert "semgrep_scan" in captured.out
        assert "nuclei_scan" in captured.out

    def test_skill_list_command_json(self, capsys):
        """测试 skill list 命令（JSON 格式）。"""
        exit_code = main(["skill", "list", "--format", "json"])
        assert exit_code == 0

        captured = capsys.readouterr()
        data = json.loads(captured.out)

        assert isinstance(data, list)
        assert len(data) == 3
        skill_names = [s["name"] for s in data]
        assert "github_integration" in skill_names

    def test_skill_info_command_existing_skill(self, capsys):
        """测试 skill info 命令（存在的 skill）。"""
        exit_code = main(["skill", "info", "github_integration"])
        assert exit_code == 0

        captured = capsys.readouterr()
        assert "github_integration" in captured.out
        assert "GitHub" in captured.out or "github" in captured.out.lower()

    def test_skill_info_command_nonexistent_skill(self, capsys):
        """测试 skill info 命令（不存在的 skill）。"""
        exit_code = main(["skill", "info", "nonexistent_skill"])
        assert exit_code == 1

        captured = capsys.readouterr()
        assert "not found" in captured.err.lower()

    def test_skill_info_command_json_format(self, capsys):
        """测试 skill info 命令（JSON 格式）。"""
        exit_code = main(["skill", "info", "semgrep_scan", "--format", "json"])
        assert exit_code == 0

        captured = capsys.readouterr()
        data = json.loads(captured.out)

        assert data["name"] == "semgrep_scan"
        assert "parameters" in data
        assert "examples" in data

    def test_skill_run_command_success(self, capsys):
        """测试 skill run 命令（成功执行）。"""
        # Mock execute_skill 以避免实际执行外部命令
        with patch.object(SkillRegistry, "execute_skill") as mock_execute:
            mock_execute.return_value = SkillResult(
                success=True,
                data={"result": "mocked"},
                metadata={"skill_name": "github_integration"},
            )

            exit_code = main([
                "skill", "run",
                "github_integration",
                "action=list_issues",
                "repo=test/repo",
            ])

            assert exit_code == 0
            captured = capsys.readouterr()
            assert "Success!" in captured.out
            assert "mocked" in captured.out

    def test_skill_run_command_failure(self, capsys):
        """测试 skill run 命令（执行失败）。"""
        with patch.object(SkillRegistry, "execute_skill") as mock_execute:
            mock_execute.return_value = SkillResult(
                success=False,
                error="Mocked error",
            )

            exit_code = main([
                "skill", "run",
                "nonexistent_skill",
            ])

            assert exit_code == 1
            captured = capsys.readouterr()
            assert "error" in captured.err.lower()

    def test_skill_run_command_invalid_args(self, capsys):
        """测试 skill run 命令（无效参数格式）。"""
        exit_code = main([
            "skill", "run",
            "github_integration",
            "invalid_arg_format",
        ])

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "error" in captured.err.lower()

    def test_taskflow_command(self, capsys):
        """测试 taskflow 命令（保留兼容性）。"""
        exit_code = main(["taskflow"])
        assert exit_code == 0

        captured = capsys.readouterr()
        assert "taskflow" in captured.out.lower()

    def test_validate_command(self, capsys):
        """测试 validate 命令（保留兼容性）。"""
        exit_code = main(["validate"])
        assert exit_code == 0

        captured = capsys.readouterr()
        assert "validate" in captured.out.lower()


class TestCreateParser:
    """测试命令行参数解析器创建。"""

    def test_create_parser(self):
        """测试创建解析器。"""
        parser = create_parser()
        assert parser is not None
        assert parser.prog == "hos"

    def test_parser_skill_list(self):
        """测试解析 skill list 命令。"""
        parser = create_parser()
        args = parser.parse_args(["skill", "list"])

        assert args.command == "skill"
        assert args.skill_command == "list"
        assert args.format == "table"

    def test_parser_skill_list_json(self):
        """测试解析 skill list 命令（JSON 格式）。"""
        parser = create_parser()
        args = parser.parse_args(["skill", "list", "--format", "json"])

        assert args.command == "skill"
        assert args.skill_command == "list"
        assert args.format == "json"

    def test_parser_skill_info(self):
        """测试解析 skill info 命令。"""
        parser = create_parser()
        args = parser.parse_args(["skill", "info", "test_skill"])

        assert args.command == "skill"
        assert args.skill_command == "info"
        assert args.skill_name == "test_skill"
        assert args.format == "table"

    def test_parser_skill_run(self):
        """测试解析 skill run 命令。"""
        parser = create_parser()
        args = parser.parse_args([
            "skill", "run",
            "test_skill",
            "key1=value1",
            "key2=value2",
        ])

        assert args.command == "skill"
        assert args.skill_command == "run"
        assert args.skill_name == "test_skill"
        assert args.args == ["key1=value1", "key2=value2"]

    def test_parser_taskflow(self):
        """测试解析 taskflow 命令。"""
        parser = create_parser()
        args = parser.parse_args(["taskflow", "arg1", "arg2"])

        assert args.command == "taskflow"
        assert args.taskflow_args == ["arg1", "arg2"]

    def test_parser_validate(self):
        """测试解析 validate 命令。"""
        parser = create_parser()
        args = parser.parse_args(["validate", "config.yaml"])

        assert args.command == "validate"
        assert args.validate_args == ["config.yaml"]


class TestIntegration:
    """集成测试，测试完整的命令执行流程。"""

    def test_full_workflow_list_info(self, capsys):
        """测试完整工作流：列出 skills 后查看详细信息。"""
        # 列出所有 skills
        exit_code = main(["skill", "list"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "github_integration" in captured.out

        # 查看特定 skill 的详细信息
        exit_code = main(["skill", "info", "github_integration"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "github_integration" in captured.out

    def test_full_workflow_with_json_format(self, capsys):
        """测试使用 JSON 格式的完整工作流。"""
        # JSON 格式列出 skills
        exit_code = main(["skill", "list", "--format", "json"])
        assert exit_code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert len(data) > 0

        # JSON 格式查看 skill 信息
        skill_name = data[0]["name"]
        exit_code = main(["skill", "info", skill_name, "--format", "json"])
        assert exit_code == 0
        captured = capsys.readouterr()
        info_data = json.loads(captured.out)
        assert info_data["name"] == skill_name
