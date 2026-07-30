"""SkillPipeline 单元测试。"""

from typing import Any, Dict
from unittest.mock import MagicMock

import pytest

from hosforge.skills.base_skill import Skill
from hosforge.skills.pipeline import (
    PipelineResult,
    SkillPipeline,
    StepResult,
)


# ---------------------------------------------------------------------------
# 辅助用 concrete skill 实现
# ---------------------------------------------------------------------------

class _DoubleSkill(Skill):
    """将输入数值乘 2。"""

    def __init__(self) -> None:
        super().__init__(name="double", description="double the value")

    def execute(self, **kwargs) -> Dict[str, Any]:
        value = kwargs.get("value", 0)
        return {"value": value * 2}


class _AddTenSkill(Skill):
    """将输入数值加 10。"""

    def __init__(self) -> None:
        super().__init__(name="add_ten", description="add ten")

    def execute(self, **kwargs) -> Dict[str, Any]:
        value = kwargs.get("value", 0)
        return {"value": value + 10}


class _ToStringSkill(Skill):
    """将数值转为字符串。"""

    def __init__(self) -> None:
        super().__init__(name="to_string", description="convert to string")

    def execute(self, **kwargs) -> Dict[str, Any]:
        value = kwargs.get("value", "")
        return {"result": str(value)}


class _FailingSkill(Skill):
    """总是抛出异常的 skill。"""

    def __init__(self) -> None:
        super().__init__(name="failing", description="always fails")

    def execute(self, **kwargs) -> Dict[str, Any]:
        raise RuntimeError("intentional failure")


# ---------------------------------------------------------------------------
# 测试用例
# ---------------------------------------------------------------------------

class TestSkillPipelineLinearExecution:
    """测试线性管线执行（3 个 skill 串联）。"""

    def test_three_step_pipeline(self):
        """double(5) -> add_ten -> to_string  => '20'"""
        pipeline = SkillPipeline(name="calc")
        pipeline.add_step(_DoubleSkill())
        pipeline.add_step(_AddTenSkill())
        pipeline.add_step(_ToStringSkill())

        result = pipeline.execute({"value": 5})

        assert result.success is True
        assert result.final_output == {"result": "20"}
        assert len(result.step_results) == 3
        assert result.error is None

    def test_step_results_contain_all_steps(self):
        pipeline = (
            SkillPipeline(name="chain")
            .add_step(_DoubleSkill())
            .add_step(_AddTenSkill())
            .add_step(_ToStringSkill())
        )

        result = pipeline.execute({"value": 3})

        names = [sr.step_name for sr in result.step_results]
        assert names == ["double", "add_ten", "to_string"]
        # double(3)=6, add_ten(6)=16
        assert result.step_results[0].output == {"value": 6}
        assert result.step_results[1].output == {"value": 16}
        assert result.step_results[2].output == {"result": "16"}

    def test_pipeline_propagates_data(self):
        """验证前一步的输出自动成为下一步的输入。"""
        pipeline = SkillPipeline(name="propagate").add_step(_DoubleSkill()).add_step(
            _DoubleSkill()
        )

        result = pipeline.execute({"value": 4})
        # 4 -> 8 -> 16
        assert result.final_output == {"value": 16}


class TestSkillPipelineInputMapping:
    """测试数据传递和字段映射。"""

    def test_input_mapping_renames_fields(self):
        """将 value 映射为 number。"""

        class _SquareSkill(Skill):
            def __init__(self) -> None:
                super().__init__(name="square", description="square")

            def execute(self, **kwargs) -> Dict[str, Any]:
                n = kwargs.get("number", 0)
                return {"result": n * n}

        pipeline = (
            SkillPipeline(name="mapped")
            .add_step(_DoubleSkill())
            .add_step(_SquareSkill(), input_mapping={"number": "value"})
        )

        result = pipeline.execute({"value": 3})
        # double(3)=6, square(number=6)=36
        assert result.success is True
        assert result.final_output == {"result": 36}

    def test_mapping_ignores_missing_source(self):
        """映射中源字段不存在时，目标字段不会出现在输入中。"""
        pipeline = SkillPipeline(name="map_missing").add_step(
            _DoubleSkill(), input_mapping={"value": "nonexistent"}
        )

        result = pipeline.execute({"value": 5})
        # value 缺失 -> _DoubleSkill 使用默认 0 -> 0*2=0
        assert result.success is True
        assert result.final_output == {"value": 0}

    def test_map_input_helper(self):
        pipeline = SkillPipeline(name="helper_test")
        output = {"a": 1, "b": 2, "c": 3}
        mapped = pipeline._map_input(output, {"x": "a", "y": "c", "z": "missing"})
        assert mapped == {"x": 1, "y": 3}


class TestSkillPipelineEdgeCases:
    """测试空管线和单步骤管线。"""

    def test_empty_pipeline(self):
        pipeline = SkillPipeline(name="empty")
        result = pipeline.execute({"value": 42})

        assert result.success is True
        assert result.step_results == []
        assert result.final_output == {"value": 42}

    def test_single_step_pipeline(self):
        pipeline = SkillPipeline(name="single").add_step(_DoubleSkill())
        result = pipeline.execute({"value": 7})

        assert result.success is True
        assert result.final_output == {"value": 14}
        assert len(result.step_results) == 1
        assert result.step_results[0].step_name == "double"

    def test_initial_input_not_mutated(self):
        pipeline = SkillPipeline(name="immut").add_step(_DoubleSkill())
        original = {"value": 5}
        pipeline.execute(original)
        assert original == {"value": 5}


class TestSkillPipelineErrorHandling:
    """测试管线错误处理。"""

    def test_step_failure_stops_pipeline(self):
        pipeline = (
            SkillPipeline(name="fail")
            .add_step(_DoubleSkill())
            .add_step(_FailingSkill())
            .add_step(_AddTenSkill())
        )

        result = pipeline.execute({"value": 3})

        assert result.success is False
        assert "failing" in result.error
        # 只有前两步有结果（第三步未执行）
        assert len(result.step_results) == 2
        assert result.step_results[1].success is False

    def test_error_handler_recovers(self):
        def handler(exc, current_input):
            return {"value": 0}

        pipeline = (
            SkillPipeline(name="recover")
            .add_step(_FailingSkill(), error_handler=handler)
            .add_step(_DoubleSkill())
        )

        result = pipeline.execute({"value": 5})
        # failing 被 handler 恢复为 value=0, double(0)=0
        assert result.success is True
        assert result.final_output == {"value": 0}


class TestSkillPipelineCondition:
    """测试条件执行。"""

    def test_condition_skips_step(self):
        pipeline = (
            SkillPipeline(name="cond")
            .add_step(_DoubleSkill())
            .add_step(
                _AddTenSkill(),
                condition=lambda inp: inp.get("value", 0) > 100,
            )
        )

        result = pipeline.execute({"value": 3})
        # double(3)=6, 6<100 所以 add_ten 被跳过
        assert result.success is True
        assert result.final_output == {"value": 6}
        assert result.step_results[1].skipped is True

    def test_condition_allows_step(self):
        pipeline = (
            SkillPipeline(name="cond2")
            .add_step(_DoubleSkill())
            .add_step(
                _AddTenSkill(),
                condition=lambda inp: inp.get("value", 0) > 0,
            )
        )

        result = pipeline.execute({"value": 3})
        # double(3)=6 > 0, add_ten 执行 -> 16
        assert result.success is True
        assert result.final_output == {"value": 16}


class TestPipelineResultDataclass:
    """测试数据类结构。"""

    def test_step_result_defaults(self):
        sr = StepResult(step_name="x", success=True)
        assert sr.output == {}
        assert sr.error is None
        assert sr.skipped is False

    def test_pipeline_result_defaults(self):
        pr = PipelineResult(success=True)
        assert pr.step_results == []
        assert pr.final_output == {}
        assert pr.error is None


class TestAddStepChaining:
    """测试 add_step 链式调用。"""

    def test_chaining_returns_self(self):
        pipeline = SkillPipeline(name="chain")
        returned = pipeline.add_step(_DoubleSkill())
        assert returned is pipeline

    def test_full_chain(self):
        pipeline = (
            SkillPipeline(name="full_chain")
            .add_step(_DoubleSkill())
            .add_step(_AddTenSkill())
        )
        assert len(pipeline.steps) == 2
