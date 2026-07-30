"""Pipeline 条件分支功能测试。"""

from typing import Any, Dict

import pytest

from hosforge.skills.base_skill import Skill
from hosforge.skills.pipeline import ConditionEvaluator, SkillPipeline


# ---------------------------------------------------------------------------
# 辅助 Skill
# ---------------------------------------------------------------------------

class _DoubleSkill(Skill):
    def __init__(self) -> None:
        super().__init__(name="double", description="double the value")

    def execute(self, **kwargs) -> Dict[str, Any]:
        value = kwargs.get("value", 0)
        return {"value": value * 2}


class _AddTenSkill(Skill):
    def __init__(self) -> None:
        super().__init__(name="add_ten", description="add ten")

    def execute(self, **kwargs) -> Dict[str, Any]:
        value = kwargs.get("value", 0)
        return {"value": value + 10}


class TestConditionEvaluator:
    """条件评估器测试。"""

    def setup_method(self):
        self.evaluator = ConditionEvaluator()

    # -------------------------------------------------------------------------
    # 基础操作符测试
    # -------------------------------------------------------------------------

    def test_equal_operator(self):
        """测试 == 操作符。"""
        condition = {"field": "status", "operator": "==", "value": "success"}
        assert self.evaluator.evaluate(condition, {"status": "success"}) is True
        assert self.evaluator.evaluate(condition, {"status": "failed"}) is False

    def test_not_equal_operator(self):
        """测试 != 操作符。"""
        condition = {"field": "status", "operator": "!=", "value": "failed"}
        assert self.evaluator.evaluate(condition, {"status": "success"}) is True
        assert self.evaluator.evaluate(condition, {"status": "failed"}) is False

    def test_greater_than_operator(self):
        """测试 > 操作符。"""
        condition = {"field": "count", "operator": ">", "value": 10}
        assert self.evaluator.evaluate(condition, {"count": 15}) is True
        assert self.evaluator.evaluate(condition, {"count": 5}) is False
        assert self.evaluator.evaluate(condition, {"count": 10}) is False

    def test_less_than_operator(self):
        """测试 < 操作符。"""
        condition = {"field": "count", "operator": "<", "value": 10}
        assert self.evaluator.evaluate(condition, {"count": 5}) is True
        assert self.evaluator.evaluate(condition, {"count": 15}) is False

    def test_greater_equal_operator(self):
        """测试 >= 操作符。"""
        condition = {"field": "count", "operator": ">=", "value": 10}
        assert self.evaluator.evaluate(condition, {"count": 10}) is True
        assert self.evaluator.evaluate(condition, {"count": 15}) is True
        assert self.evaluator.evaluate(condition, {"count": 5}) is False

    def test_less_equal_operator(self):
        """测试 <= 操作符。"""
        condition = {"field": "count", "operator": "<=", "value": 10}
        assert self.evaluator.evaluate(condition, {"count": 10}) is True
        assert self.evaluator.evaluate(condition, {"count": 5}) is True
        assert self.evaluator.evaluate(condition, {"count": 15}) is False

    def test_in_operator(self):
        """测试 in 操作符。"""
        condition = {"field": "status", "operator": "in", "value": ["success", "pending"]}
        assert self.evaluator.evaluate(condition, {"status": "success"}) is True
        assert self.evaluator.evaluate(condition, {"status": "failed"}) is False

    def test_not_in_operator(self):
        """测试 not in 操作符。"""
        condition = {"field": "status", "operator": "not in", "value": ["failed", "error"]}
        assert self.evaluator.evaluate(condition, {"status": "success"}) is True
        assert self.evaluator.evaluate(condition, {"status": "failed"}) is False

    def test_contains_operator(self):
        """测试 contains 操作符。"""
        condition = {"field": "message", "operator": "contains", "value": "error"}
        assert self.evaluator.evaluate(condition, {"message": "An error occurred"}) is True
        assert self.evaluator.evaluate(condition, {"message": "Success"}) is False

    def test_startswith_operator(self):
        """测试 startswith 操作符。"""
        condition = {"field": "filename", "operator": "startswith", "value": "test_"}
        assert self.evaluator.evaluate(condition, {"filename": "test_file.py"}) is True
        assert self.evaluator.evaluate(condition, {"filename": "file_test.py"}) is False

    def test_endswith_operator(self):
        """测试 endswith 操作符。"""
        condition = {"field": "filename", "operator": "endswith", "value": ".py"}
        assert self.evaluator.evaluate(condition, {"filename": "test.py"}) is True
        assert self.evaluator.evaluate(condition, {"filename": "test.js"}) is False

    # -------------------------------------------------------------------------
    # 嵌套字段访问测试
    # -------------------------------------------------------------------------

    def test_nested_field_access(self):
        """测试嵌套字段访问。"""
        condition = {"field": "output.status", "operator": "==", "value": "success"}
        context = {"output": {"status": "success", "data": [1, 2, 3]}}
        assert self.evaluator.evaluate(condition, context) is True

    def test_deep_nested_field_access(self):
        """测试深层嵌套字段访问。"""
        condition = {"field": "result.data.value", "operator": ">", "value": 100}
        context = {"result": {"data": {"value": 150}}}
        assert self.evaluator.evaluate(condition, context) is True

    def test_missing_field_returns_none(self):
        """测试缺失字段返回 None。"""
        condition = {"field": "missing.field", "operator": "==", "value": None}
        assert self.evaluator.evaluate(condition, {}) is True

    # -------------------------------------------------------------------------
    # 逻辑组合测试
    # -------------------------------------------------------------------------

    def test_and_logic(self):
        """测试 and 逻辑组合。"""
        condition = {
            "and": [
                {"field": "status", "operator": "==", "value": "success"},
                {"field": "count", "operator": ">", "value": 10}
            ]
        }
        context = {"status": "success", "count": 15}
        assert self.evaluator.evaluate(condition, context) is True

        context_fail = {"status": "success", "count": 5}
        assert self.evaluator.evaluate(condition, context_fail) is False

    def test_or_logic(self):
        """测试 or 逻辑组合。"""
        condition = {
            "or": [
                {"field": "status", "operator": "==", "value": "success"},
                {"field": "status", "operator": "==", "value": "pending"}
            ]
        }
        assert self.evaluator.evaluate(condition, {"status": "success"}) is True
        assert self.evaluator.evaluate(condition, {"status": "pending"}) is True
        assert self.evaluator.evaluate(condition, {"status": "failed"}) is False

    def test_not_logic(self):
        """测试 not 逻辑组合。"""
        condition = {
            "not": {"field": "status", "operator": "==", "value": "failed"}
        }
        assert self.evaluator.evaluate(condition, {"status": "success"}) is True
        assert self.evaluator.evaluate(condition, {"status": "failed"}) is False

    def test_complex_nested_logic(self):
        """测试复杂嵌套逻辑。"""
        condition = {
            "and": [
                {"field": "status", "operator": "==", "value": "success"},
                {
                    "or": [
                        {"field": "count", "operator": ">", "value": 100},
                        {"field": "priority", "operator": "==", "value": "high"}
                    ]
                }
            ]
        }
        context1 = {"status": "success", "count": 150, "priority": "low"}
        assert self.evaluator.evaluate(condition, context1) is True

        context2 = {"status": "success", "count": 50, "priority": "high"}
        assert self.evaluator.evaluate(condition, context2) is True

        context3 = {"status": "success", "count": 50, "priority": "low"}
        assert self.evaluator.evaluate(condition, context3) is False

    # -------------------------------------------------------------------------
    # Callable 条件测试
    # -------------------------------------------------------------------------

    def test_callable_condition_true(self):
        """测试 callable 条件返回 True。"""
        condition = lambda ctx: ctx.get("status") == "success"
        assert self.evaluator.evaluate(condition, {"status": "success"}) is True

    def test_callable_condition_false(self):
        """测试 callable 条件返回 False。"""
        condition = lambda ctx: ctx.get("status") == "success"
        assert self.evaluator.evaluate(condition, {"status": "failed"}) is False

    def test_callable_with_complex_logic(self):
        """测试 callable 复杂逻辑。"""
        def complex_condition(ctx):
            return ctx.get("count", 0) > 10 and ctx.get("status") == "active"

        assert self.evaluator.evaluate(complex_condition, {"count": 15, "status": "active"}) is True
        assert self.evaluator.evaluate(complex_condition, {"count": 5, "status": "active"}) is False

    # -------------------------------------------------------------------------
    # 字符串表达式测试
    # -------------------------------------------------------------------------

    def test_string_expression_equal(self):
        """测试字符串表达式 == 。"""
        condition = "status == 'success'"
        assert self.evaluator.evaluate(condition, {"status": "success"}) is True
        assert self.evaluator.evaluate(condition, {"status": "failed"}) is False

    def test_string_expression_not_equal(self):
        """测试字符串表达式 != 。"""
        condition = "status != 'failed'"
        assert self.evaluator.evaluate(condition, {"status": "success"}) is True
        assert self.evaluator.evaluate(condition, {"status": "failed"}) is False

    def test_string_expression_greater_than(self):
        """测试字符串表达式 > 。"""
        condition = "count > 10"
        assert self.evaluator.evaluate(condition, {"count": 15}) is True
        assert self.evaluator.evaluate(condition, {"count": 5}) is False

    def test_string_expression_and(self):
        """测试字符串表达式 and 。"""
        condition = "status == 'success' and count > 10"
        assert self.evaluator.evaluate(condition, {"status": "success", "count": 15}) is True
        assert self.evaluator.evaluate(condition, {"status": "success", "count": 5}) is False

    def test_string_expression_or(self):
        """测试字符串表达式 or 。"""
        condition = "status == 'success' or status == 'pending'"
        assert self.evaluator.evaluate(condition, {"status": "success"}) is True
        assert self.evaluator.evaluate(condition, {"status": "pending"}) is True
        assert self.evaluator.evaluate(condition, {"status": "failed"}) is False

    def test_string_expression_not(self):
        """测试字符串表达式 not 。"""
        condition = "not status == 'failed'"
        assert self.evaluator.evaluate(condition, {"status": "success"}) is True
        assert self.evaluator.evaluate(condition, {"status": "failed"}) is False

    def test_string_expression_nested_field(self):
        """测试字符串表达式嵌套字段。"""
        condition = "output.status == 'success'"
        context = {"output": {"status": "success"}}
        assert self.evaluator.evaluate(condition, context) is True

    def test_string_expression_boolean_value(self):
        """测试字符串表达式布尔值。"""
        condition = "enabled == true"
        assert self.evaluator.evaluate(condition, {"enabled": True}) is True
        assert self.evaluator.evaluate(condition, {"enabled": False}) is False

    def test_string_expression_numeric_comparison(self):
        """测试字符串表达式数值比较。"""
        condition = "score >= 90"
        assert self.evaluator.evaluate(condition, {"score": 95}) is True
        assert self.evaluator.evaluate(condition, {"score": 85}) is False

    def test_string_expression_in_operator(self):
        """测试字符串表达式 in 操作符。"""
        condition = "status in ['success', 'pending']"
        assert self.evaluator.evaluate(condition, {"status": "success"}) is True
        assert self.evaluator.evaluate(condition, {"status": "pending"}) is True
        assert self.evaluator.evaluate(condition, {"status": "failed"}) is False

    def test_string_expression_not_in_operator(self):
        """测试字符串表达式 not in 操作符。"""
        condition = "status not in ['failed', 'error']"
        assert self.evaluator.evaluate(condition, {"status": "success"}) is True
        assert self.evaluator.evaluate(condition, {"status": "failed"}) is False

    def test_string_with_and_in_value(self):
        """测试值中包含 and 关键词的引号感知分割。"""
        condition = "message == 'x and y' and status == 'ok'"
        context = {"message": "x and y", "status": "ok"}
        assert self.evaluator.evaluate(condition, context) is True

    def test_string_with_or_in_value(self):
        """测试值中包含 or 关键词的引号感知分割。"""
        condition = "message == 'x or y' or status == 'ok'"
        context = {"message": "x or y", "status": "fail"}
        assert self.evaluator.evaluate(condition, context) is True

    def test_string_expression_field_starting_with_not(self):
        """测试字段名以 not 开头（如 note）不会被误判为 not 逻辑。"""
        condition = "note == 'hello'"
        assert self.evaluator.evaluate(condition, {"note": "hello"}) is True
        assert self.evaluator.evaluate(condition, {"note": "world"}) is False

    # -------------------------------------------------------------------------
    # 边界情况测试
    # -------------------------------------------------------------------------

    def test_none_condition_returns_true(self):
        """测试 None 条件返回 True。"""
        assert self.evaluator.evaluate(None, {}) is True

    def test_unsupported_operator_raises_error(self):
        """测试不支持的操作符抛出错误。"""
        condition = {"field": "status", "operator": "invalid_op", "value": "success"}
        with pytest.raises(ValueError, match="Unsupported operator"):
            self.evaluator.evaluate(condition, {"status": "success"})

    def test_invalid_string_expression_raises_error(self):
        """测试无效的字符串表达式抛出错误。"""
        condition = "invalid expression without operator"
        with pytest.raises(ValueError, match="Cannot parse condition expression"):
            self.evaluator.evaluate(condition, {})


class TestPipelineConditionalExecution:
    """管线条件执行测试。"""

    def test_dict_condition_skips_step(self):
        """测试字典条件跳过步骤。"""
        pipeline = SkillPipeline("test")
        pipeline.add_step(_DoubleSkill())
        pipeline.add_step(
            _AddTenSkill(),
            condition={"field": "value", "operator": ">", "value": 100}
        )

        result = pipeline.execute({"value": 3})
        # double(3)=6, 6 < 100 所以 add_ten 被跳过
        assert result.success is True
        assert result.final_output == {"value": 6}
        assert result.step_results[1].skipped is True

    def test_dict_condition_executes_step(self):
        """测试字典条件执行步骤。"""
        pipeline = SkillPipeline("test")
        pipeline.add_step(_DoubleSkill())
        pipeline.add_step(
            _AddTenSkill(),
            condition={"field": "value", "operator": ">", "value": 5}
        )

        result = pipeline.execute({"value": 3})
        # double(3)=6 > 5 所以 add_ten 执行 -> 16
        assert result.success is True
        assert result.final_output == {"value": 16}
        assert result.step_results[1].skipped is False

    def test_string_condition_skips_step(self):
        """测试字符串条件跳过步骤。"""
        pipeline = SkillPipeline("test")
        pipeline.add_step(_DoubleSkill())
        pipeline.add_step(
            _AddTenSkill(),
            condition="value > 100"
        )

        result = pipeline.execute({"value": 3})
        assert result.success is True
        assert result.final_output == {"value": 6}
        assert result.step_results[1].skipped is True

    def test_string_condition_executes_step(self):
        """测试字符串条件执行步骤。"""
        pipeline = SkillPipeline("test")
        pipeline.add_step(_DoubleSkill())
        pipeline.add_step(
            _AddTenSkill(),
            condition="value > 5"
        )

        result = pipeline.execute({"value": 3})
        assert result.success is True
        assert result.final_output == {"value": 16}

    def test_callable_condition_backward_compatibility(self):
        """测试 callable 条件向后兼容。"""
        pipeline = SkillPipeline("test")
        pipeline.add_step(_DoubleSkill())
        pipeline.add_step(
            _AddTenSkill(),
            condition=lambda ctx: ctx.get("value", 0) > 100
        )

        result = pipeline.execute({"value": 3})
        assert result.success is True
        assert result.final_output == {"value": 6}
        assert result.step_results[1].skipped is True

    def test_multiple_conditional_steps(self):
        """测试多个条件步骤。"""
        pipeline = SkillPipeline("test")
        pipeline.add_step(_DoubleSkill())
        pipeline.add_step(
            _AddTenSkill(),
            condition={"field": "value", "operator": ">", "value": 5}
        )
        pipeline.add_step(
            _DoubleSkill(),
            condition={"field": "value", "operator": "<", "value": 10}
        )

        result = pipeline.execute({"value": 3})
        # double(3)=6, 6>5 所以 add_ten 执行 -> 16, 16<10 为 False 所以第二个 double 被跳过
        assert result.success is True
        assert result.final_output == {"value": 16}
        assert result.step_results[1].skipped is False
        assert result.step_results[2].skipped is True

    def test_condition_error_stops_pipeline(self):
        """测试条件评估错误停止管线。"""
        pipeline = SkillPipeline("test")
        pipeline.add_step(_DoubleSkill())
        pipeline.add_step(
            _AddTenSkill(),
            condition={"field": "value", "operator": "invalid_op", "value": 10}
        )

        result = pipeline.execute({"value": 3})
        assert result.success is False
        assert "Condition check failed" in result.error
        assert len(result.step_results) == 2
        assert result.step_results[1].success is False
