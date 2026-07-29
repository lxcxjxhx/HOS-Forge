"""Skill 注册表性能基准测试。

测试大量 skill 下的注册表性能，包括：
- 注册和注销性能
- 查找性能
- 执行性能
- 内存使用
"""

import time
from typing import Any, Dict

import pytest

from hosforge.skills.base_skill import Skill
from hosforge.skills.registry import SkillRegistry


class BenchmarkSkill(Skill):
    """用于基准测试的 skill。"""

    def __init__(self, name: str) -> None:
        super().__init__(
            name=name,
            description=f"Benchmark skill {name}",
            parameters={
                "type": "object",
                "properties": {
                    "input": {"type": "string"},
                },
                "required": ["input"],
            },
        )

    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行简单操作。"""
        return {"result": f"processed {kwargs.get('input', '')}"}


class TestSkillRegistryPerformance:
    """测试 skill 注册表性能。"""

    def test_register_100_skills(self):
        """测试注册 100 个 skills 的性能。"""
        registry = SkillRegistry()
        start = time.time()

        for i in range(100):
            skill = BenchmarkSkill(f"skill_{i}")
            registry.register(skill)

        duration = time.time() - start
        assert duration < 1.0, f"注册 100 个 skills 耗时 {duration:.3f}s，超过 1s"
        assert len(registry.list_skills()) == 100

    def test_register_1000_skills(self):
        """测试注册 1000 个 skills 的性能。"""
        registry = SkillRegistry()
        start = time.time()

        for i in range(1000):
            skill = BenchmarkSkill(f"skill_{i}")
            registry.register(skill)

        duration = time.time() - start
        assert duration < 5.0, f"注册 1000 个 skills 耗时 {duration:.3f}s，超过 5s"
        assert len(registry.list_skills()) == 1000

    def test_get_skill_from_1000(self):
        """测试从 1000 个 skills 中查找的性能。"""
        registry = SkillRegistry()

        # 注册 1000 个 skills
        for i in range(1000):
            skill = BenchmarkSkill(f"skill_{i}")
            registry.register(skill)

        # 测试查找性能
        start = time.time()
        for _ in range(1000):
            skill = registry.get("skill_500")
            assert skill is not None
        duration = time.time() - start

        # 1000 次查找应该在 0.1s 内完成
        assert duration < 0.1, f"1000 次查找耗时 {duration:.3f}s，超过 0.1s"

    def test_execute_skill_from_1000(self):
        """测试从 1000 个 skills 中执行的性能。"""
        registry = SkillRegistry()

        # 注册 1000 个 skills
        for i in range(1000):
            skill = BenchmarkSkill(f"skill_{i}")
            registry.register(skill)

        # 测试执行性能
        start = time.time()
        for _ in range(100):
            result = registry.execute_skill("skill_500", input="test")
            assert result.success
        duration = time.time() - start

        # 100 次执行应该在 1s 内完成
        assert duration < 1.0, f"100 次执行耗时 {duration:.3f}s，超过 1s"

    def test_unregister_100_skills(self):
        """测试注销 100 个 skills 的性能。"""
        registry = SkillRegistry()

        # 注册 100 个 skills
        for i in range(100):
            skill = BenchmarkSkill(f"skill_{i}")
            registry.register(skill)

        # 测试注销性能
        start = time.time()
        for i in range(100):
            registry.unregister(f"skill_{i}")
        duration = time.time() - start

        assert duration < 0.5, f"注销 100 个 skills 耗时 {duration:.3f}s，超过 0.5s"
        assert len(registry.list_skills()) == 0

    def test_list_skills_1000(self):
        """测试列出 1000 个 skills 的性能。"""
        registry = SkillRegistry()

        # 注册 1000 个 skills
        for i in range(1000):
            skill = BenchmarkSkill(f"skill_{i}")
            registry.register(skill)

        # 测试列出性能
        start = time.time()
        skills = registry.list_skills()
        duration = time.time() - start

        assert duration < 0.1, f"列出 1000 个 skills 耗时 {duration:.3f}s，超过 0.1s"
        assert len(skills) == 1000

    def test_concurrent_registration(self):
        """测试并发注册性能。"""
        import threading

        registry = SkillRegistry()
        errors = []

        def register_skills(start_idx: int, count: int):
            try:
                for i in range(count):
                    skill = BenchmarkSkill(f"skill_{start_idx + i}")
                    registry.register(skill)
            except Exception as e:
                errors.append(e)

        # 启动 10 个线程，每个注册 100 个 skills
        threads = []
        start = time.time()
        for t in range(10):
            thread = threading.Thread(target=register_skills, args=(t * 100, 100))
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()
        duration = time.time() - start

        assert len(errors) == 0, f"并发注册出错: {errors}"
        # 注意：由于字典不是线程安全的，实际数量可能少于 1000
        # 这里只验证性能
        assert duration < 2.0, f"并发注册 1000 个 skills 耗时 {duration:.3f}s，超过 2s"


class TestSkillRegistryMemoryUsage:
    """测试 skill 注册表内存使用。"""

    def test_memory_usage_100_skills(self):
        """测试 100 个 skills 的内存使用。"""
        import sys

        registry = SkillRegistry()

        # 注册 100 个 skills
        for i in range(100):
            skill = BenchmarkSkill(f"skill_{i}")
            registry.register(skill)

        # 估算内存使用（粗略）
        memory_estimate = sys.getsizeof(registry)
        for skill in registry.list_skills():
            memory_estimate += sys.getsizeof(skill)

        # 应该小于 1MB
        assert memory_estimate < 1_000_000, f"内存使用 {memory_estimate} 字节，超过 1MB"

    def test_memory_usage_1000_skills(self):
        """测试 1000 个 skills 的内存使用。"""
        import sys

        registry = SkillRegistry()

        # 注册 1000 个 skills
        for i in range(1000):
            skill = BenchmarkSkill(f"skill_{i}")
            registry.register(skill)

        # 估算内存使用（粗略）
        memory_estimate = sys.getsizeof(registry)
        for skill in registry.list_skills():
            memory_estimate += sys.getsizeof(skill)

        # 应该小于 10MB
        assert memory_estimate < 10_000_000, f"内存使用 {memory_estimate} 字节，超过 10MB"


class TestSkillRegistryOptimization:
    """测试 skill 注册表优化。"""

    def test_skill_caching(self):
        """测试 skill 缓存机制。"""
        registry = SkillRegistry()

        # 注册 skill
        skill = BenchmarkSkill("cached_skill")
        registry.register(skill)

        # 多次获取应该返回同一实例
        skill1 = registry.get("cached_skill")
        skill2 = registry.get("cached_skill")
        assert skill1 is skill2

    def test_lazy_loading_simulation(self):
        """模拟延迟加载。"""
        registry = SkillRegistry()

        # 注册大量 skills
        for i in range(100):
            skill = BenchmarkSkill(f"skill_{i}")
            registry.register(skill)

        # 只获取部分 skills
        start = time.time()
        for i in range(10):
            skill = registry.get(f"skill_{i}")
            assert skill is not None
        duration = time.time() - start

        # 获取 10 个 skills 应该非常快
        assert duration < 0.01, f"获取 10 个 skills 耗时 {duration:.3f}s"
