"""Skill 抽象层单元测试。"""

from typing import Any, Dict

import pytest

from hosforge.skills import Skill, SkillRegistry, SkillResult


class ConcreteSkill(Skill):
    """用于测试的具体 Skill 实现。"""

    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行简单的加法操作。"""
        a = kwargs.get("a", 0)
        b = kwargs.get("b", 0)
        return {"result": a + b}


class TestSkillBase:
    """测试 Skill 基类。"""

    def test_skill_initialization(self):
        """测试 Skill 实例化。"""
        skill = ConcreteSkill(
            name="test_skill",
            description="A test skill",
            parameters={
                "type": "object",
                "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
                "required": ["a", "b"],
            },
        )

        assert skill.name == "test_skill"
        assert skill.description == "A test skill"
        assert "a" in skill.parameters["properties"]
        assert "b" in skill.parameters["properties"]

    def test_skill_default_parameters(self):
        """测试 Skill 默认参数。"""
        skill = ConcreteSkill(name="test", description="test")
        assert skill.parameters == {}

    def test_validate_input_valid(self):
        """测试输入验证 - 有效输入。"""
        skill = ConcreteSkill(
            name="test",
            description="test",
            parameters={
                "type": "object",
                "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
                "required": ["a", "b"],
            },
        )

        assert skill.validate_input(a=1, b=2) is True

    def test_validate_input_missing_required(self):
        """测试输入验证 - 缺少必填参数。"""
        skill = ConcreteSkill(
            name="test",
            description="test",
            parameters={
                "type": "object",
                "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
                "required": ["a", "b"],
            },
        )

        assert skill.validate_input(a=1) is False

    def test_validate_input_wrong_type(self):
        """测试输入验证 - 类型错误。"""
        skill = ConcreteSkill(
            name="test",
            description="test",
            parameters={"type": "object", "properties": {"a": {"type": "integer"}}, "required": ["a"]},
        )

        assert skill.validate_input(a="not an int") is False

    def test_validate_input_no_schema(self):
        """测试输入验证 - 无 schema 定义。"""
        skill = ConcreteSkill(name="test", description="test")
        assert skill.validate_input(anything="goes") is True

    def test_execute(self):
        """测试 Skill 执行。"""
        skill = ConcreteSkill(name="test", description="test")
        result = skill.execute(a=5, b=3)
        assert result == {"result": 8}


class TestSkillResult:
    """测试 SkillResult 数据类。"""

    def test_skill_result_success(self):
        """测试成功的 SkillResult。"""
        result = SkillResult(success=True, data={"key": "value"})
        assert result.success is True
        assert result.data == {"key": "value"}
        assert result.error is None
        assert result.metadata == {}

    def test_skill_result_failure(self):
        """测试失败的 SkillResult。"""
        result = SkillResult(success=False, error="Something went wrong")
        assert result.success is False
        assert result.data is None
        assert result.error == "Something went wrong"

    def test_skill_result_with_metadata(self):
        """测试带元数据的 SkillResult。"""
        result = SkillResult(success=True, data="test", metadata={"duration": 1.5})
        assert result.metadata == {"duration": 1.5}


class TestSkillRegistry:
    """测试 SkillRegistry。"""

    def test_register_skill(self):
        """测试注册 Skill。"""
        registry = SkillRegistry()
        skill = ConcreteSkill(name="test", description="test")
        registry.register(skill)

        assert registry.get("test") is skill

    def test_unregister_skill(self):
        """测试注销 Skill。"""
        registry = SkillRegistry()
        skill = ConcreteSkill(name="test", description="test")
        registry.register(skill)
        registry.unregister("test")

        assert registry.get("test") is None

    def test_get_skill(self):
        """测试获取 Skill。"""
        registry = SkillRegistry()
        skill = ConcreteSkill(name="test", description="test")
        registry.register(skill)

        retrieved = registry.get("test")
        assert retrieved is skill

    def test_get_nonexistent_skill(self):
        """测试获取不存在的 Skill。"""
        registry = SkillRegistry()
        assert registry.get("nonexistent") is None

    def test_list_skills(self):
        """测试列出所有 Skill。"""
        registry = SkillRegistry()
        skill1 = ConcreteSkill(name="skill1", description="desc1")
        skill2 = ConcreteSkill(name="skill2", description="desc2")

        registry.register(skill1)
        registry.register(skill2)

        skills = registry.list_skills()
        assert len(skills) == 2
        assert skill1 in skills
        assert skill2 in skills

    def test_execute_skill_success(self):
        """测试成功执行 Skill。"""
        registry = SkillRegistry()
        skill = ConcreteSkill(name="adder", description="adds numbers")
        registry.register(skill)

        result = registry.execute_skill("adder", a=10, b=20)

        assert result.success is True
        assert result.data == {"result": 30}
        assert result.metadata == {"skill_name": "adder"}

    def test_execute_skill_not_found(self):
        """测试执行不存在的 Skill。"""
        registry = SkillRegistry()
        result = registry.execute_skill("nonexistent")

        assert result.success is False
        assert "not found" in result.error

    def test_execute_skill_invalid_input(self):
        """测试执行 Skill 时输入无效参数。"""
        registry = SkillRegistry()
        skill = ConcreteSkill(
            name="test",
            description="test",
            parameters={"type": "object", "properties": {"a": {"type": "integer"}}, "required": ["a"]},
        )
        registry.register(skill)

        result = registry.execute_skill("test")  # missing required 'a'

        assert result.success is False
        assert "Invalid input" in result.error

    def test_execute_skill_exception(self):
        """测试执行 Skill 时发生异常。"""

        class FailingSkill(Skill):
            def execute(self, **kwargs):
                raise ValueError("Intentional failure")

        registry = SkillRegistry()
        skill = FailingSkill(name="failing", description="fails")
        registry.register(skill)

        result = registry.execute_skill("failing")

        assert result.success is False
        assert "Intentional failure" in result.error
        assert result.metadata == {"skill_name": "failing"}
