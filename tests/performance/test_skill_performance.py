"""性能测试 - 验证系统在高负载场景下的性能表现。

测试内容包括：
1. 大量 Skill 注册性能
2. 并发执行性能
3. MCP Server 并发请求处理
4. Skill 动态加载性能
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict

import pytest

from hosforge.skills import Skill, SkillLoader, SkillRegistry


class PerformanceTestSkill(Skill):
    """用于性能测试的简单 Skill 实现"""

    def __init__(self, name: str):
        super().__init__(
            name=name,
            description=f"Performance test skill {name}",
            parameters={"type": "object", "properties": {"value": {"type": "integer"}}},
        )

    def execute(self, **kwargs) -> Dict[str, Any]:
        """简单的执行逻辑"""
        value = kwargs.get("value", 0)
        return {"result": value * 2, "skill": self.name}


class TestSkillRegistrationPerformance:
    """测试大量 Skill 注册的性能"""

    def test_register_1000_skills_performance(self):
        """测试注册 1000 个 skills 的性能

        验证标准：< 1秒
        """
        registry = SkillRegistry()
        num_skills = 1000

        start_time = time.perf_counter()

        for i in range(num_skills):
            skill = PerformanceTestSkill(f"skill_{i}")
            registry.register(skill)

        end_time = time.perf_counter()
        duration = end_time - start_time

        # 验证性能指标
        assert duration < 1.0, f"注册 {num_skills} 个 skills 耗时 {duration:.3f}秒，超过 1秒阈值"

        # 验证注册结果
        skills = registry.list_skills()
        assert len(skills) == num_skills, f"期望 {num_skills} 个 skills，实际 {len(skills)} 个"

        print(f"\n性能指标: 注册 {num_skills} 个 skills 耗时 {duration:.3f}秒")

    def test_register_10000_skills_performance(self):
        """测试注册 10000 个 skills 的性能

        验证标准：< 10秒
        """
        registry = SkillRegistry()
        num_skills = 10000

        start_time = time.perf_counter()

        for i in range(num_skills):
            skill = PerformanceTestSkill(f"skill_{i}")
            registry.register(skill)

        end_time = time.perf_counter()
        duration = end_time - start_time

        # 验证性能指标
        assert duration < 10.0, f"注册 {num_skills} 个 skills 耗时 {duration:.3f}秒，超过 10秒阈值"

        # 验证注册结果
        skills = registry.list_skills()
        assert len(skills) == num_skills

        print(f"\n性能指标: 注册 {num_skills} 个 skills 耗时 {duration:.3f}秒")

    def test_skill_lookup_performance(self):
        """测试 Skill 查找性能

        验证标准：10000 次查找 < 0.5秒
        """
        registry = SkillRegistry()
        num_skills = 1000

        # 注册 skills
        for i in range(num_skills):
            skill = PerformanceTestSkill(f"skill_{i}")
            registry.register(skill)

        start_time = time.perf_counter()

        # 执行查找
        for i in range(num_skills):
            skill = registry.get(f"skill_{i}")
            assert skill is not None

        end_time = time.perf_counter()
        duration = end_time - start_time

        # 验证性能指标
        assert duration < 0.5, f"1000 次查找耗时 {duration:.3f}秒，超过 0.5秒阈值"

        print(f"\n性能指标: 1000 次 skill 查找耗时 {duration:.3f}秒")


class TestConcurrentExecutionPerformance:
    """测试并发执行性能"""

    @pytest.mark.timeout(10)
    def test_concurrent_skill_execution_10_threads(self):
        """测试 10 个并发 skill 执行

        验证标准：< 5秒
        """
        registry = SkillRegistry()
        num_skills = 10

        # 注册 skills
        for i in range(num_skills):
            skill = PerformanceTestSkill(f"skill_{i}")
            registry.register(skill)

        start_time = time.perf_counter()

        # 并发执行
        with ThreadPoolExecutor(max_workers=num_skills) as executor:
            futures = []
            for i in range(num_skills):
                future = executor.submit(registry.execute_skill, f"skill_{i}", value=i)
                futures.append(future)

            # 收集结果
            results = []
            for future in as_completed(futures):
                result = future.result()
                results.append(result)

        end_time = time.perf_counter()
        duration = end_time - start_time

        # 验证性能指标
        assert duration < 5.0, f"10 个并发执行耗时 {duration:.3f}秒，超过 5秒阈值"

        # 验证所有执行成功
        assert len(results) == num_skills
        for result in results:
            assert result.success is True

        print(f"\n性能指标: 10 个并发 skill 执行耗时 {duration:.3f}秒")

    @pytest.mark.timeout(30)
    def test_concurrent_skill_execution_100_threads(self):
        """测试 100 个并发 skill 执行

        验证标准：< 15秒
        """
        registry = SkillRegistry()
        num_skills = 100

        # 注册 skills
        for i in range(num_skills):
            skill = PerformanceTestSkill(f"skill_{i}")
            registry.register(skill)

        start_time = time.perf_counter()

        # 并发执行
        with ThreadPoolExecutor(max_workers=num_skills) as executor:
            futures = []
            for i in range(num_skills):
                future = executor.submit(registry.execute_skill, f"skill_{i}", value=i)
                futures.append(future)

            # 收集结果
            results = []
            for future in as_completed(futures):
                result = future.result()
                results.append(result)

        end_time = time.perf_counter()
        duration = end_time - start_time

        # 验证性能指标
        assert duration < 15.0, f"100 个并发执行耗时 {duration:.3f}秒，超过 15秒阈值"

        # 验证所有执行成功
        assert len(results) == num_skills
        for result in results:
            assert result.success is True

        print(f"\n性能指标: 100 个并发 skill 执行耗时 {duration:.3f}秒")


class TestMCPServerConcurrentRequests:
    """测试 MCP Server 并发请求处理能力"""

    @pytest.mark.timeout(10)
    def test_mcp_server_concurrent_requests(self):
        """测试 MCP Server 处理并发请求的能力

        验证标准：10 个并发请求 < 5秒
        """
        from hosforge.mcp_server.skill_bridge import MCPToolExecutor

        registry = SkillRegistry()
        num_skills = 10

        # 注册 skills
        for i in range(num_skills):
            skill = PerformanceTestSkill(f"tool_{i}")
            registry.register(skill)

        executor = MCPToolExecutor(registry)

        start_time = time.perf_counter()

        # 并发执行 MCP tool 调用
        with ThreadPoolExecutor(max_workers=num_skills) as thread_executor:
            futures = []
            for i in range(num_skills):
                future = thread_executor.submit(executor.execute, f"tool_{i}", {"value": i})
                futures.append(future)

            # 收集结果
            results = []
            for future in as_completed(futures):
                result = future.result()
                results.append(result)

        end_time = time.perf_counter()
        duration = end_time - start_time

        # 验证性能指标
        assert duration < 5.0, f"10 个并发 MCP 请求耗时 {duration:.3f}秒，超过 5秒阈值"

        # 验证所有请求成功
        assert len(results) == num_skills
        for result in results:
            assert result["isError"] is False

        print(f"\n性能指标: 10 个并发 MCP 请求耗时 {duration:.3f}秒")


class TestSkillLoadingPerformance:
    """测试 Skill 动态加载性能"""

    def test_skill_loader_performance(self):
        """测试 SkillLoader 加载性能

        验证标准：加载 100 个 skills < 2秒
        """
        import os
        import tempfile
        from pathlib import Path

        # 创建临时目录和测试 skill 文件
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # 生成 100 个 skill 文件
            num_skills = 100
            for i in range(num_skills):
                skill_file = temp_path / f"skill_{i}.py"
                skill_content = f"""
from hosforge.skills import Skill
from typing import Any, Dict

class Skill_{i}(Skill):
    def __init__(self):
        super().__init__(
            name="skill_{i}",
            description="Test skill {i}",
            parameters={{"type": "object", "properties": {{"value": {{"type": "integer"}}}}}}
        )
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        return {{"result": {i}}}
"""
                skill_file.write_text(skill_content, encoding="utf-8")

            # 测试加载性能
            loader = SkillLoader()

            start_time = time.perf_counter()
            skills = loader.load_from_directory(str(temp_path))
            end_time = time.perf_counter()

            duration = end_time - start_time

            # 验证性能指标
            assert duration < 2.0, f"加载 {num_skills} 个 skills 耗时 {duration:.3f}秒，超过 2秒阈值"

            # 验证加载结果
            assert len(skills) == num_skills, f"期望 {num_skills} 个 skills，实际 {len(skills)} 个"

            print(f"\n性能指标: 加载 {num_skills} 个 skills 耗时 {duration:.3f}秒")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
