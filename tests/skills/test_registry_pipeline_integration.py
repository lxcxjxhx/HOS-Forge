"""测试 SkillRegistry 与 SkillPipeline 的集成。"""

import pytest
from typing import Any, Dict

from hosforge.skills.base_skill import Skill
from hosforge.skills.pipeline import ErrorStrategy, SkillPipeline
from hosforge.skills.registry import SkillRegistry


class MockSkill(Skill):
    """模拟 Skill 用于测试。"""

    def __init__(self, name: str, output: Dict[str, Any] = None):
        super().__init__(name=name, description=f"Mock skill: {name}")
        self._output = output or {"status": "success", "name": name}

    def execute(self, **kwargs) -> Dict[str, Any]:
        return self._output


class FailingSkill(Skill):
    """失败的 Skill 用于测试。"""

    def __init__(self, name: str = "failing"):
        super().__init__(name=name, description="Failing skill")

    def execute(self, **kwargs) -> Dict[str, Any]:
        raise RuntimeError("Intentional failure")


class TestSkillRegistryPipelineIntegration:
    """测试 SkillRegistry 与管线集成。"""

    def test_register_pipeline(self):
        """测试注册管线。"""
        registry = SkillRegistry()
        pipeline = SkillPipeline("test_pipeline", "Test pipeline")
        
        registry.register_pipeline(pipeline)
        
        assert registry.get_pipeline("test_pipeline") is pipeline

    def test_unregister_pipeline(self):
        """测试注销管线。"""
        registry = SkillRegistry()
        pipeline = SkillPipeline("test_pipeline", "Test pipeline")
        
        registry.register_pipeline(pipeline)
        registry.unregister_pipeline("test_pipeline")
        
        assert registry.get_pipeline("test_pipeline") is None

    def test_list_pipelines(self):
        """测试列出所有管线。"""
        registry = SkillRegistry()
        pipeline1 = SkillPipeline("pipeline1", "First pipeline")
        pipeline2 = SkillPipeline("pipeline2", "Second pipeline")
        
        registry.register_pipeline(pipeline1)
        registry.register_pipeline(pipeline2)
        
        pipelines = registry.list_pipelines()
        assert len(pipelines) == 2
        assert pipeline1 in pipelines
        assert pipeline2 in pipelines

    def test_execute_pipeline_success(self):
        """测试成功执行管线。"""
        registry = SkillRegistry()
        
        # 创建管线
        pipeline = SkillPipeline("test_pipeline", "Test pipeline")
        skill1 = MockSkill("skill1", {"step": 1, "value": "first"})
        skill2 = MockSkill("skill2", {"step": 2, "value": "second"})
        
        pipeline.add_step(skill1)
        pipeline.add_step(skill2)
        
        registry.register_pipeline(pipeline)
        
        # 执行管线
        result = registry.execute_pipeline("test_pipeline", {"initial": "data"})
        
        assert result["success"] is True
        assert len(result["step_results"]) == 2
        assert result["step_results"][0]["step_name"] == "skill1"
        assert result["step_results"][0]["success"] is True
        assert result["step_results"][1]["step_name"] == "skill2"
        assert result["step_results"][1]["success"] is True
        assert result["final_output"]["step"] == 2

    def test_execute_pipeline_not_found(self):
        """测试执行不存在的管线。"""
        registry = SkillRegistry()
        
        result = registry.execute_pipeline("nonexistent", {})
        
        assert result["success"] is False
        assert "not found" in result["error"]

    def test_execute_pipeline_with_failure(self):
        """测试执行包含失败步骤的管线。"""
        registry = SkillRegistry()
        
        pipeline = SkillPipeline("test_pipeline", "Test pipeline")
        skill1 = MockSkill("skill1", {"step": 1})
        failing_skill = FailingSkill("failing")
        skill3 = MockSkill("skill3", {"step": 3})
        
        pipeline.add_step(skill1)
        pipeline.add_step(failing_skill)
        pipeline.add_step(skill3)
        
        registry.register_pipeline(pipeline)
        
        result = registry.execute_pipeline("test_pipeline", {})
        
        assert result["success"] is False
        assert len(result["step_results"]) == 2  # 只执行到失败步骤
        assert result["step_results"][0]["success"] is True
        assert result["step_results"][1]["success"] is False
        assert "Intentional failure" in result["error"]

    def test_execute_pipeline_with_input_mapping(self):
        """测试执行带输入映射的管线。"""
        registry = SkillRegistry()
        
        pipeline = SkillPipeline("test_pipeline", "Test pipeline")
        skill1 = MockSkill("skill1", {"output_value": 42})
        skill2 = MockSkill("skill2", {"final": "result"})
        
        pipeline.add_step(skill1)
        pipeline.add_step(skill2, input_mapping={"input_value": "output_value"})
        
        registry.register_pipeline(pipeline)
        
        result = registry.execute_pipeline("test_pipeline", {})
        
        assert result["success"] is True
        assert len(result["step_results"]) == 2

    def test_execute_pipeline_with_condition(self):
        """测试执行带条件的管线。"""
        registry = SkillRegistry()
        
        pipeline = SkillPipeline("test_pipeline", "Test pipeline")
        skill1 = MockSkill("skill1", {"should_continue": True})
        skill2 = MockSkill("skill2", {"result": "executed"})
        
        pipeline.add_step(skill1)
        pipeline.add_step(skill2, condition=lambda ctx: ctx.get("should_continue", False))
        
        registry.register_pipeline(pipeline)
        
        result = registry.execute_pipeline("test_pipeline", {})
        
        assert result["success"] is True
        assert len(result["step_results"]) == 2
        assert result["step_results"][1]["success"] is True

    def test_execute_pipeline_with_error_strategy(self):
        """测试执行带错误策略的管线。"""
        registry = SkillRegistry()
        
        pipeline = SkillPipeline("test_pipeline", "Test pipeline")
        skill1 = MockSkill("skill1", {"step": 1})
        failing_skill = FailingSkill("failing")
        skill3 = MockSkill("skill3", {"step": 3})
        
        pipeline.add_step(skill1)
        pipeline.add_step(failing_skill, error_strategy=ErrorStrategy.SKIP)
        pipeline.add_step(skill3)
        
        registry.register_pipeline(pipeline)
        
        result = registry.execute_pipeline("test_pipeline", {})
        
        assert result["success"] is True
        assert len(result["step_results"]) == 3
        assert result["step_results"][0]["success"] is True
        assert result["step_results"][1]["success"] is False
        assert result["step_results"][2]["success"] is True

    def test_mixed_skills_and_pipelines(self):
        """测试同时管理 skills 和 pipelines。"""
        registry = SkillRegistry()
        
        # 注册 skills
        skill1 = MockSkill("standalone_skill")
        registry.register(skill1)
        
        # 注册 pipelines
        pipeline1 = SkillPipeline("pipeline1", "First pipeline")
        pipeline2 = SkillPipeline("pipeline2", "Second pipeline")
        registry.register_pipeline(pipeline1)
        registry.register_pipeline(pipeline2)
        
        # 验证
        assert registry.get("standalone_skill") is skill1
        assert registry.get_pipeline("pipeline1") is pipeline1
        assert registry.get_pipeline("pipeline2") is pipeline2
        assert len(registry.list_skills()) == 1
        assert len(registry.list_pipelines()) == 2
