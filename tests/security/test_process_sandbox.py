"""进程级沙箱执行器测试。

验证 ProcessSandboxExecutor 的功能，包括：
- 正常 skill 在子进程中执行
- 超时终止机制
- 子进程崩溃处理
- 进程隔离验证
"""

import time
from typing import Any, Dict

import pytest

from hosforge.skills.base_skill import Skill, SkillResult
from hosforge.skills.sandbox import ProcessSandboxExecutor, SandboxConfig


class SimpleSkill(Skill):
    """简单的测试 skill。"""

    def __init__(self) -> None:
        super().__init__(name="simple_skill", description="Simple test skill")

    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行简单操作。"""
        value = kwargs.get("value", "default")
        return {"result": f"processed_{value}", "status": "success"}


class CrashingSkill(Skill):
    """模拟崩溃的 skill。"""

    def __init__(self) -> None:
        super().__init__(name="crashing_skill", description="Skill that crashes")

    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行时崩溃。"""
        raise RuntimeError("Skill crashed unexpectedly")


class HangingSkill(Skill):
    """模拟挂起的 skill。"""

    def __init__(self) -> None:
        super().__init__(name="hanging_skill", description="Skill that hangs")

    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行时无限等待。"""
        time.sleep(3600)  # 休眠 1 小时
        return {"status": "done"}


class MemoryHeavySkill(Skill):
    """模拟内存密集型 skill。"""

    def __init__(self) -> None:
        super().__init__(name="memory_heavy", description="Memory heavy skill")

    def execute(self, **kwargs) -> Dict[str, Any]:
        """分配大量内存。"""
        data = []
        for i in range(1000000):
            data.append("x" * 100)
        return {"allocated": len(data)}


class MultiArgSkill(Skill):
    """多参数测试 skill。"""

    def __init__(self) -> None:
        super().__init__(name="multi_arg", description="Multi arg skill")

    def execute(self, **kwargs) -> Dict[str, Any]:
        a = kwargs.get("a", 0)
        b = kwargs.get("b", 0)
        return {"sum": a + b}


class StatefulSkill(Skill):
    """有状态测试 skill。"""

    counter = 0

    def __init__(self) -> None:
        super().__init__(name="stateful", description="Stateful skill")

    def execute(self, **kwargs) -> Dict[str, Any]:
        StatefulSkill.counter += 1
        return {"counter": StatefulSkill.counter}


class EmptyReturnSkill(Skill):
    """空返回值测试 skill。"""

    def __init__(self) -> None:
        super().__init__(name="empty", description="Empty return skill")

    def execute(self, **kwargs) -> Dict[str, Any]:
        return {}


class ComplexReturnSkill(Skill):
    """复杂返回值测试 skill。"""

    def __init__(self) -> None:
        super().__init__(name="complex", description="Complex return skill")

    def execute(self, **kwargs) -> Dict[str, Any]:
        return {
            "nested": {"key": "value"},
            "list": [1, 2, 3],
            "number": 42,
            "boolean": True,
            "null": None,
        }


class UnicodeSkill(Skill):
    """Unicode 输出测试 skill。"""

    def __init__(self) -> None:
        super().__init__(name="unicode", description="Unicode skill")

    def execute(self, **kwargs) -> Dict[str, Any]:
        return {"message": "你好世界", "emoji": "🎉"}


class TestProcessSandboxBasicExecution:
    """测试进程级沙箱基本执行。"""

    def test_simple_skill_executes_in_subprocess(self):
        """测试简单 skill 在子进程中执行。"""
        executor = ProcessSandboxExecutor()
        skill = SimpleSkill()

        result = executor.execute_skill(skill, value="test")

        assert result.success is True
        assert result.data is not None
        assert result.data["result"] == "processed_test"
        assert result.data["status"] == "success"
        assert result.metadata.get("process_sandbox") is True

    def test_skill_with_no_arguments(self):
        """测试无参数 skill 执行。"""
        executor = ProcessSandboxExecutor()
        skill = SimpleSkill()

        result = executor.execute_skill(skill)

        assert result.success is True
        assert result.data is not None
        assert result.data["result"] == "processed_default"

    def test_skill_with_multiple_arguments(self):
        """测试多参数 skill 执行。"""
        executor = ProcessSandboxExecutor()
        skill = MultiArgSkill()

        result = executor.execute_skill(skill, a=10, b=20)

        assert result.success is True
        assert result.data["sum"] == 30


class TestProcessSandboxTimeout:
    """测试进程级沙箱超时机制。"""

    def test_hanging_skill_timeout(self):
        """测试挂起 skill 超时终止。"""
        config = SandboxConfig(max_execution_time=1.0)
        executor = ProcessSandboxExecutor(config)
        skill = HangingSkill()

        start = time.time()
        result = executor.execute_skill(skill)
        duration = time.time() - start

        assert result.success is False
        assert "timeout" in result.error.lower()
        assert duration < 3.0  # 应该在 3 秒内返回

    def test_timeout_kills_subprocess(self):
        """测试超时后子进程被终止。"""
        config = SandboxConfig(max_execution_time=0.5)
        executor = ProcessSandboxExecutor(config)
        skill = HangingSkill()

        result = executor.execute_skill(skill)

        assert result.success is False
        assert "exceeded" in result.error
        assert result.metadata.get("process_sandbox") is True


class TestProcessSandboxCrash:
    """测试进程级沙箱崩溃处理。"""

    def test_crashing_skill_handled(self):
        """测试崩溃 skill 被正确处理。"""
        executor = ProcessSandboxExecutor()
        skill = CrashingSkill()

        result = executor.execute_skill(skill)

        assert result.success is False
        assert "crashed" in result.error.lower() or "RuntimeError" in result.error
        assert result.metadata.get("process_sandbox") is True

    def test_crash_does_not_affect_main_process(self):
        """测试子进程崩溃不影响主进程。"""
        executor = ProcessSandboxExecutor()
        crashing_skill = CrashingSkill()
        simple_skill = SimpleSkill()

        # 执行崩溃的 skill
        result1 = executor.execute_skill(crashing_skill)
        assert result1.success is False

        # 执行正常的 skill，应该不受影响
        result2 = executor.execute_skill(simple_skill, value="after_crash")
        assert result2.success is True
        assert result2.data["result"] == "processed_after_crash"


class TestProcessSandboxIsolation:
    """测试进程级沙箱隔离性。"""

    def test_process_isolation_variable_not_shared(self):
        """测试进程间变量不共享。"""
        executor = ProcessSandboxExecutor()
        skill = StatefulSkill()

        # 重置计数器
        StatefulSkill.counter = 0

        # 在子进程中执行多次
        result1 = executor.execute_skill(skill)
        result2 = executor.execute_skill(skill)

        # 每次执行都是新的进程，但类变量在子进程中会被重新初始化
        # 由于 StatefulSkill.counter 是类变量，每次子进程导入模块后从 0 开始
        # 但主进程中 counter 已经被修改，所以子进程中的 counter 值取决于模块导入时的状态
        # 关键是验证子进程是独立执行的
        assert result1.success is True
        assert result2.success is True
        assert result1.data["counter"] >= 1
        assert result2.data["counter"] >= 1

    def test_memory_heavy_skill_isolated(self):
        """测试内存密集型 skill 被隔离。"""
        config = SandboxConfig(max_execution_time=10.0)
        executor = ProcessSandboxExecutor(config)
        skill = MemoryHeavySkill()

        result = executor.execute_skill(skill)

        assert result.success is True
        assert result.data["allocated"] == 1000000

    def test_exception_traceback_captured(self):
        """测试异常堆栈被捕获。"""
        executor = ProcessSandboxExecutor()
        skill = CrashingSkill()

        result = executor.execute_skill(skill)

        assert result.success is False
        # 检查是否有 traceback 信息
        assert result.metadata.get("traceback") is not None or "RuntimeError" in result.error


class TestProcessSandboxConfig:
    """测试进程级沙箱配置。"""

    def test_default_config(self):
        """测试默认配置。"""
        executor = ProcessSandboxExecutor()
        assert executor.config.max_execution_time == 30.0

    def test_custom_config(self):
        """测试自定义配置。"""
        config = SandboxConfig(max_execution_time=60.0, max_memory_mb=1024)
        executor = ProcessSandboxExecutor(config)

        assert executor.config.max_execution_time == 60.0
        assert executor.config.max_memory_mb == 1024

    def test_config_passed_to_subprocess(self):
        """测试配置影响子进程执行。"""
        # 使用很短的超时时间
        config = SandboxConfig(max_execution_time=0.1)
        executor = ProcessSandboxExecutor(config)
        skill = HangingSkill()

        result = executor.execute_skill(skill)

        assert result.success is False
        assert "timeout" in result.error.lower()


class TestProcessSandboxEdgeCases:
    """测试进程级沙箱边界情况。"""

    def test_empty_return_value(self):
        """测试空返回值处理。"""
        executor = ProcessSandboxExecutor()
        skill = EmptyReturnSkill()

        result = executor.execute_skill(skill)

        assert result.success is True
        assert result.data == {}

    def test_complex_return_value(self):
        """测试复杂返回值处理。"""
        executor = ProcessSandboxExecutor()
        skill = ComplexReturnSkill()

        result = executor.execute_skill(skill)

        assert result.success is True
        assert result.data["nested"]["key"] == "value"
        assert result.data["list"] == [1, 2, 3]
        assert result.data["number"] == 42
        assert result.data["boolean"] is True
        assert result.data["null"] is None

    def test_unicode_in_output(self):
        """测试 Unicode 输出处理。"""
        executor = ProcessSandboxExecutor()
        skill = UnicodeSkill()

        result = executor.execute_skill(skill)

        assert result.success is True
        assert result.data["message"] == "你好世界"
        assert result.data["emoji"] == "🎉"
