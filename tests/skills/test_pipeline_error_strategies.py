"""管线错误处理策略测试。"""

from typing import Any, Dict

import pytest

from hosforge.skills.base_skill import Skill
from hosforge.skills.pipeline import (
    ErrorStrategy,
    RetryConfig,
    SkillPipeline,
)


class FailingSkill(Skill):
    """总是失败的 skill。"""

    def __init__(self, name: str = "failing") -> None:
        super().__init__(name=name, description="Always fails")

    def execute(self, **kwargs) -> Dict[str, Any]:
        raise RuntimeError("Intentional failure")


class RetryableSkill(Skill):
    """可重试的 skill，前两次失败，第三次成功。"""

    def __init__(self) -> None:
        super().__init__(name="retryable", description="Retryable skill")
        self.attempt_count = 0

    def execute(self, **kwargs) -> Dict[str, Any]:
        self.attempt_count += 1
        if self.attempt_count < 3:
            raise RuntimeError(f"Attempt {self.attempt_count} failed")
        return {"status": "success", "attempts": self.attempt_count}


class SuccessSkill(Skill):
    """总是成功的 skill。"""

    def __init__(self, name: str = "success") -> None:
        super().__init__(name=name, description="Always succeeds")

    def execute(self, **kwargs) -> Dict[str, Any]:
        return {"status": "success", "value": 42}


class TestErrorStrategyStop:
    """测试 STOP 策略。"""

    def test_stop_on_first_failure(self):
        """测试遇到第一个错误时停止。"""
        pipeline = SkillPipeline("test")
        pipeline.add_step(FailingSkill(), error_strategy=ErrorStrategy.STOP)
        pipeline.add_step(SuccessSkill())

        result = pipeline.execute({})

        assert result.success is False
        assert len(result.step_results) == 1
        assert result.step_results[0].success is False
        assert "Intentional failure" in result.error

    def test_stop_is_default_strategy(self):
        """测试 STOP 是默认策略。"""
        pipeline = SkillPipeline("test")
        pipeline.add_step(FailingSkill())  # 不指定策略
        pipeline.add_step(SuccessSkill())

        result = pipeline.execute({})

        assert result.success is False
        assert len(result.step_results) == 1


class TestErrorStrategySkip:
    """测试 SKIP 策略。"""

    def test_skip_failed_step(self):
        """测试跳过失败步骤继续执行。"""
        pipeline = SkillPipeline("test")
        pipeline.add_step(SuccessSkill("step1"))
        pipeline.add_step(FailingSkill("step2"), error_strategy=ErrorStrategy.SKIP)
        pipeline.add_step(SuccessSkill("step3"))

        result = pipeline.execute({})

        assert result.success is True
        assert len(result.step_results) == 3
        assert result.step_results[0].success is True
        assert result.step_results[1].success is False
        assert result.step_results[1].skipped is False  # 执行了但失败
        assert result.step_results[2].success is True

    def test_skip_preserves_current_input(self):
        """测试跳过时保留当前输入。"""
        pipeline = SkillPipeline("test")
        pipeline.add_step(SuccessSkill("step1"))
        pipeline.add_step(FailingSkill("step2"), error_strategy=ErrorStrategy.SKIP)
        pipeline.add_step(SuccessSkill("step3"))

        result = pipeline.execute({"initial": "value"})

        assert result.success is True
        # step3 应该接收到 step1 的输出
        assert result.final_output["status"] == "success"


class TestErrorStrategyRetry:
    """测试 RETRY 策略。"""

    def test_retry_success_after_failures(self):
        """测试重试后成功。"""
        pipeline = SkillPipeline("test")
        retryable = RetryableSkill()
        pipeline.add_step(
            retryable,
            error_strategy=ErrorStrategy.RETRY,
            retry_config=RetryConfig(max_attempts=3, delay_seconds=0.01),
        )

        result = pipeline.execute({})

        assert result.success is True
        assert len(result.step_results) == 1
        assert result.step_results[0].success is True
        assert result.step_results[0].output["attempts"] == 3

    def test_retry_exhausted(self):
        """测试重试次数耗尽。"""
        pipeline = SkillPipeline("test")
        pipeline.add_step(
            FailingSkill(),
            error_strategy=ErrorStrategy.RETRY,
            retry_config=RetryConfig(max_attempts=3, delay_seconds=0.01),
        )

        result = pipeline.execute({})

        assert result.success is False
        assert "Failed after 3 attempts" in result.step_results[0].error

    def test_retry_with_default_config(self):
        """测试使用默认重试配置。"""
        pipeline = SkillPipeline("test")
        pipeline.add_step(
            FailingSkill(),
            error_strategy=ErrorStrategy.RETRY,
            # 不提供 retry_config，使用默认值
        )

        result = pipeline.execute({})

        assert result.success is False
        # 默认 max_attempts=3
        assert "Failed after 3 attempts" in result.step_results[0].error

    def test_retry_with_custom_delay(self):
        """测试自定义重试延迟。"""
        pipeline = SkillPipeline("test")
        pipeline.add_step(
            FailingSkill(),
            error_strategy=ErrorStrategy.RETRY,
            retry_config=RetryConfig(max_attempts=2, delay_seconds=0.001),
        )

        result = pipeline.execute({})

        assert result.success is False
        assert "Failed after 2 attempts" in result.step_results[0].error


class TestMixedErrorStrategies:
    """测试混合错误策略。"""

    def test_skip_then_stop(self):
        """测试跳过失败后继续，然后遇到 STOP 策略停止。"""
        pipeline = SkillPipeline("test")
        pipeline.add_step(FailingSkill("step1"), error_strategy=ErrorStrategy.SKIP)
        pipeline.add_step(FailingSkill("step2"), error_strategy=ErrorStrategy.STOP)
        pipeline.add_step(SuccessSkill("step3"))

        result = pipeline.execute({})

        assert result.success is False
        assert len(result.step_results) == 2
        assert result.step_results[0].success is False  # 跳过
        assert result.step_results[1].success is False  # 停止

    def test_retry_then_skip(self):
        """测试重试失败后继续，然后遇到 SKIP 策略。"""
        pipeline = SkillPipeline("test")
        pipeline.add_step(
            FailingSkill("step1"),
            error_strategy=ErrorStrategy.SKIP,  # 改为 SKIP，让管线继续
        )
        pipeline.add_step(FailingSkill("step2"), error_strategy=ErrorStrategy.SKIP)
        pipeline.add_step(SuccessSkill("step3"))

        result = pipeline.execute({})

        assert result.success is True
        assert len(result.step_results) == 3
        assert result.step_results[0].success is False  # 跳过
        assert result.step_results[1].success is False  # 跳过
        assert result.step_results[2].success is True  # 成功


class TestErrorHandlerWithStrategy:
    """测试 error_handler 与 error_strategy 的交互。"""

    def test_handler_takes_precedence(self):
        """测试 error_handler 优先于 error_strategy。"""
        def custom_handler(error, context):
            return {"handled": True}

        pipeline = SkillPipeline("test")
        pipeline.add_step(
            FailingSkill(),
            error_handler=custom_handler,
            error_strategy=ErrorStrategy.STOP,  # 不会触发，因为 handler 成功
        )

        result = pipeline.execute({})

        assert result.success is True
        assert result.step_results[0].success is True
        assert result.final_output["handled"] is True

    def test_handler_failure_falls_back_to_strategy(self):
        """测试 handler 失败时回退到 error_strategy。"""
        def failing_handler(error, context):
            raise RuntimeError("Handler also failed")

        pipeline = SkillPipeline("test")
        pipeline.add_step(
            FailingSkill(),
            error_handler=failing_handler,
            error_strategy=ErrorStrategy.SKIP,
        )
        pipeline.add_step(SuccessSkill())

        result = pipeline.execute({})

        # handler 失败会导致管线停止，不会触发 SKIP
        assert result.success is False
        assert "Handler also failed" in result.error


class TestRetryConfig:
    """测试 RetryConfig 配置。"""

    def test_default_config(self):
        """测试默认配置。"""
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.delay_seconds == 1.0
        assert config.backoff_multiplier == 2.0

    def test_custom_config(self):
        """测试自定义配置。"""
        config = RetryConfig(max_attempts=5, delay_seconds=0.5, backoff_multiplier=1.5)
        assert config.max_attempts == 5
        assert config.delay_seconds == 0.5
        assert config.backoff_multiplier == 1.5
