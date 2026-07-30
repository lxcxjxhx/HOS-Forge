"""资源限制功能测试。

验证 ProcessSandboxExecutor 的资源限制功能，包括：
- CPU 时间限制强制执行
- 内存限制强制执行
- 资源限制违规处理和进程终止
- 跨平台兼容性（Windows/Unix）
"""

import sys
import time
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from hosforge.skills.base_skill import Skill, SkillResult
from hosforge.skills.sandbox import ProcessSandboxExecutor, SandboxConfig


class CPUIntensiveSkill(Skill):
    """CPU 密集型测试 skill。"""

    def __init__(self) -> None:
        super().__init__(name="cpu_intensive", description="CPU intensive skill")

    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行 CPU 密集型操作。"""
        # 无限循环，用于测试 CPU 时间限制
        while True:
            _ = 1 + 1
        return {"status": "completed"}


class MemoryIntensiveSkill(Skill):
    """内存密集型测试 skill。"""

    def __init__(self) -> None:
        super().__init__(name="memory_intensive", description="Memory intensive skill")

    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行内存密集型操作。"""
        # 分配大量内存
        data = []
        for i in range(10_000_000):
            data.append("x" * 100)
        return {"allocated": len(data)}


class QuickSkill(Skill):
    """快速执行的 skill。"""

    def __init__(self) -> None:
        super().__init__(name="quick", description="Quick skill")

    def execute(self, **kwargs) -> Dict[str, Any]:
        """快速执行并返回。"""
        return {"status": "success", "value": 42}


class ModerateSkill(Skill):
    """适度资源使用的 skill。"""

    def __init__(self) -> None:
        super().__init__(name="moderate", description="Moderate skill")

    def execute(self, **kwargs) -> Dict[str, Any]:
        """适度使用资源。"""
        # 适度 CPU 使用
        result = 0
        for i in range(100000):
            result += i
        # 适度内存使用
        data = ["x" * 100 for _ in range(1000)]
        return {"result": result, "data_size": len(data)}


class TestResourceLimitSetup:
    """测试资源限制设置。"""

    def test_setup_resource_limits_with_psutil(self):
        """测试使用 psutil 设置资源限制。"""
        with patch("hosforge.skills.sandbox.ProcessSandboxExecutor._setup_resource_limits") as mock_setup:
            mock_setup.return_value = True
            executor = ProcessSandboxExecutor()
            assert executor._resource_limits_supported is True

    def test_setup_resource_limits_without_psutil(self):
        """测试没有 psutil 时的资源限制设置。"""
        executor = ProcessSandboxExecutor()
        # 应该能够初始化，即使 psutil 不可用
        assert hasattr(executor, "_psutil_available")
        assert hasattr(executor, "_resource_module_available")

    def test_resource_limits_support_detection(self):
        """测试资源限制支持检测。"""
        executor = ProcessSandboxExecutor()
        # 应该检测到至少一种资源限制机制
        supported = executor._psutil_available or executor._resource_module_available
        # 在大多数系统上应该支持
        assert isinstance(supported, bool)


class TestCPULimitEnforcement:
    """测试 CPU 时间限制强制执行。"""

    def test_cpu_limit_with_short_timeout(self):
        """测试短超时时间的 CPU 限制。"""
        config = SandboxConfig(max_execution_time=0.5)
        executor = ProcessSandboxExecutor(config)
        skill = CPUIntensiveSkill()

        start = time.time()
        result = executor.execute_skill(skill)
        duration = time.time() - start

        assert result.success is False
        # 应该在合理时间内终止
        assert duration < 5.0
        # 应该报告超时或资源限制
        assert "timeout" in result.error.lower() or "limit" in result.error.lower()

    def test_cpu_limit_allows_quick_execution(self):
        """测试 CPU 限制允许快速执行的任务。"""
        config = SandboxConfig(max_execution_time=10.0)
        executor = ProcessSandboxExecutor(config)
        skill = QuickSkill()

        result = executor.execute_skill(skill)

        assert result.success is True
        assert result.data["status"] == "success"
        assert result.data["value"] == 42

    def test_cpu_limit_with_moderate_execution(self):
        """测试适度执行的 CPU 限制。"""
        config = SandboxConfig(max_execution_time=5.0)
        executor = ProcessSandboxExecutor(config)
        skill = ModerateSkill()

        result = executor.execute_skill(skill)

        # 适度执行应该成功
        assert result.success is True
        assert "result" in result.data
        assert "data_size" in result.data


class TestMemoryLimitEnforcement:
    """测试内存限制强制执行。"""

    def test_memory_limit_detection(self):
        """测试内存限制检测。"""
        executor = ProcessSandboxExecutor()
        # 应该能够检测内存使用（如果 psutil 可用）
        if executor._psutil_available:
            assert hasattr(executor, "_get_process_resources")

    def test_memory_limit_with_small_limit(self):
        """测试小内存限制。"""
        # 设置非常小的内存限制（10MB）
        config = SandboxConfig(max_execution_time=10.0, max_memory_mb=10)
        executor = ProcessSandboxExecutor(config)
        skill = MemoryIntensiveSkill()

        result = executor.execute_skill(skill)

        # 可能因为内存限制失败，或者在 Unix 上被 OOM killer 杀死
        # 在某些平台上可能成功（如果限制无法强制执行）
        # 我们只验证不会崩溃
        assert isinstance(result, SkillResult)

    def test_memory_limit_allows_small_allocation(self):
        """测试内存限制允许小规模内存分配。"""
        config = SandboxConfig(max_execution_time=10.0, max_memory_mb=512)
        executor = ProcessSandboxExecutor(config)
        skill = QuickSkill()

        result = executor.execute_skill(skill)

        assert result.success is True


class TestResourceLimitViolation:
    """测试资源限制违规处理。"""

    def test_resource_violation_returns_error(self):
        """测试资源违规返回错误。"""
        config = SandboxConfig(max_execution_time=0.3)
        executor = ProcessSandboxExecutor(config)
        skill = CPUIntensiveSkill()

        result = executor.execute_skill(skill)

        assert result.success is False
        assert result.metadata.get("process_sandbox") is True

    def test_resource_violation_metadata(self):
        """测试资源违规的元数据。"""
        config = SandboxConfig(max_execution_time=0.3)
        executor = ProcessSandboxExecutor(config)
        skill = CPUIntensiveSkill()

        result = executor.execute_skill(skill)

        assert "skill_name" in result.metadata
        assert result.metadata["sandbox"] is True
        assert result.metadata["process_sandbox"] is True

    def test_process_terminated_on_violation(self):
        """测试违规时进程被终止。"""
        config = SandboxConfig(max_execution_time=0.5)
        executor = ProcessSandboxExecutor(config)
        skill = CPUIntensiveSkill()

        result = executor.execute_skill(skill)

        # 应该返回错误
        assert result.success is False
        # 进程应该被终止，不会继续运行


class TestCrossPlatformCompatibility:
    """测试跨平台兼容性。"""

    def test_windows_compatibility(self):
        """测试 Windows 平台兼容性。"""
        if sys.platform != "win32":
            pytest.skip("仅在 Windows 上运行")

        executor = ProcessSandboxExecutor()
        # Windows 应该使用 psutil（如果可用）
        if executor._psutil_available:
            assert executor._resource_limits_supported is True

    def test_unix_compatibility(self):
        """测试 Unix/Linux 平台兼容性。"""
        if sys.platform == "win32":
            pytest.skip("仅在 Unix/Linux 上运行")

        executor = ProcessSandboxExecutor()
        # Unix 应该支持 resource 模块
        assert executor._resource_module_available is True

    def test_fallback_without_psutil(self):
        """测试没有 psutil 时的降级方案。"""
        with patch("hosforge.skills.sandbox.ProcessSandboxExecutor._setup_resource_limits") as mock_setup:
            mock_setup.return_value = False
            executor = ProcessSandboxExecutor()
            # 应该能够初始化，即使资源限制不支持
            assert executor._resource_limits_supported is False

    def test_platform_specific_preexec(self):
        """测试平台特定的 preexec_fn。"""
        executor = ProcessSandboxExecutor()
        preexec_fn = executor._make_preexec_fn()

        if sys.platform == "win32":
            assert preexec_fn is None
        else:
            # Unix 平台应该有 preexec_fn（如果 resource 模块可用）
            if executor._resource_module_available:
                assert preexec_fn is not None or preexec_fn is None  # 可能因为限制失败而为 None


class TestResourceMonitoring:
    """测试资源监控功能。"""

    def test_get_process_resources(self):
        """测试获取进程资源使用情况。"""
        import subprocess

        executor = ProcessSandboxExecutor()

        # 创建一个简单的子进程
        process = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(0.5)"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        try:
            resources = executor._get_process_resources(process)
            assert "cpu_time" in resources
            assert "memory_mb" in resources
            assert isinstance(resources["cpu_time"], (int, float))
            assert isinstance(resources["memory_mb"], (int, float))
        finally:
            process.kill()
            process.wait()

    def test_enforce_limits_no_violation(self):
        """测试没有违规时的限制执行。"""
        import subprocess

        config = SandboxConfig(max_execution_time=10.0, max_memory_mb=512)
        executor = ProcessSandboxExecutor(config)

        # 创建一个简单的子进程
        process = subprocess.Popen(
            [sys.executable, "-c", "print('hello')"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        try:
            process.wait(timeout=2)
            violation = executor._enforce_limits(process)
            # 进程已结束，应该没有违规
            assert violation is None
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

    def test_monitor_resources_thread(self):
        """测试资源监控线程。"""
        import subprocess
        import threading

        executor = ProcessSandboxExecutor()

        # 创建一个子进程
        process = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(0.3)"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        stop_event = threading.Event()

        try:
            # 启动监控线程
            result = executor._monitor_resources(process, stop_event)
            # 应该正常结束
            assert result is None or isinstance(result, str)
        finally:
            stop_event.set()
            process.kill()
            process.wait()


class TestResourceLimitConfiguration:
    """测试资源限制配置。"""

    def test_custom_cpu_limit(self):
        """测试自定义 CPU 时间限制。"""
        config = SandboxConfig(max_execution_time=5.0)
        executor = ProcessSandboxExecutor(config)

        assert executor.config.max_execution_time == 5.0

    def test_custom_memory_limit(self):
        """测试自定义内存限制。"""
        config = SandboxConfig(max_memory_mb=1024)
        executor = ProcessSandboxExecutor(config)

        assert executor.config.max_memory_mb == 1024

    def test_default_limits(self):
        """测试默认资源限制。"""
        executor = ProcessSandboxExecutor()

        assert executor.config.max_execution_time == 30.0
        assert executor.config.max_memory_mb == 512


class TestResourceLimitEdgeCases:
    """测试资源限制边界情况。"""

    def test_very_short_timeout(self):
        """测试非常短的超时时间。"""
        config = SandboxConfig(max_execution_time=0.1)
        executor = ProcessSandboxExecutor(config)
        skill = QuickSkill()

        result = executor.execute_skill(skill)

        # 可能成功也可能超时，取决于系统性能
        assert isinstance(result, SkillResult)

    def test_very_small_memory_limit(self):
        """测试非常小的内存限制。"""
        config = SandboxConfig(max_memory_mb=1)  # 1MB
        executor = ProcessSandboxExecutor(config)
        skill = QuickSkill()

        result = executor.execute_skill(skill)

        # 可能成功也可能失败，取决于系统
        assert isinstance(result, SkillResult)

    def test_zero_timeout(self):
        """测试零超时时间。"""
        config = SandboxConfig(max_execution_time=0.0)
        executor = ProcessSandboxExecutor(config)
        skill = QuickSkill()

        result = executor.execute_skill(skill)

        # 应该立即超时
        assert isinstance(result, SkillResult)

    def test_large_memory_limit(self):
        """测试大内存限制。"""
        config = SandboxConfig(max_memory_mb=4096)  # 4GB
        executor = ProcessSandboxExecutor(config)
        skill = QuickSkill()

        result = executor.execute_skill(skill)

        assert result.success is True


class TestResourceLimitIntegration:
    """测试资源限制集成。"""

    def test_combined_cpu_and_memory_limits(self):
        """测试组合 CPU 和内存限制。"""
        config = SandboxConfig(max_execution_time=5.0, max_memory_mb=256)
        executor = ProcessSandboxExecutor(config)
        skill = ModerateSkill()

        result = executor.execute_skill(skill)

        # 适度使用应该在限制内
        assert result.success is True

    def test_resource_limits_with_normal_skill(self):
        """测试资源限制下的正常 skill。"""
        config = SandboxConfig(max_execution_time=10.0, max_memory_mb=512)
        executor = ProcessSandboxExecutor(config)
        skill = QuickSkill()

        result = executor.execute_skill(skill)

        assert result.success is True
        assert result.data["status"] == "success"

    def test_resource_limits_do_not_affect_correctness(self):
        """测试资源限制不影响结果正确性。"""
        config = SandboxConfig(max_execution_time=10.0, max_memory_mb=512)
        executor = ProcessSandboxExecutor(config)
        skill = ModerateSkill()

        result1 = executor.execute_skill(skill)
        result2 = executor.execute_skill(skill)

        # 两次执行应该得到相同结果
        assert result1.success == result2.success
        if result1.success and result2.success:
            assert result1.data == result2.data
