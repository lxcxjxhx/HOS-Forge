"""MCP Server 与 Skill 桥接层单元测试。"""

import pytest
from typing import Any, Dict

from fastapi.testclient import TestClient

from hosforge.mcp_server.server import create_app
from hosforge.mcp_server.skill_bridge import MCPToolExecutor, SkillToMCPTool
from hosforge.skills import Skill, SkillRegistry


class DummySkill(Skill):
    """用于测试的简单 Skill。"""

    def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """返回简单的测试结果。"""
        return {"result": "success", "args": kwargs}


class FailingSkill(Skill):
    """用于测试执行失败的 Skill。"""

    def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """抛出异常模拟失败。"""
        raise ValueError("Intentional failure")


@pytest.fixture
def registry() -> SkillRegistry:
    """创建测试用的 SkillRegistry。"""
    reg = SkillRegistry()
    reg.register(
        DummySkill(
            name="dummy",
            description="A dummy skill for testing",
            parameters={
                "type": "object",
                "properties": {"value": {"type": "string"}},
                "required": [],
            },
        )
    )
    reg.register(
        FailingSkill(
            name="failing",
            description="A skill that always fails",
            parameters={"type": "object", "properties": {}, "required": []},
        )
    )
    return reg


@pytest.fixture
def app(registry: SkillRegistry):
    """创建测试用的 FastAPI 应用。"""
    return create_app(registry)


@pytest.fixture
def client(app):
    """创建测试用的 HTTP 客户端。"""
    return TestClient(app)


class TestSkillToMCPTool:
    """测试 SkillToMCPTool 类。"""

    def test_convert_basic_skill(self):
        """测试转换基本 Skill。"""
        skill = DummySkill(
            name="test_skill",
            description="Test description",
            parameters={"type": "object", "properties": {"x": {"type": "integer"}}},
        )
        tool_def = SkillToMCPTool.convert(skill)

        assert tool_def["name"] == "test_skill"
        assert tool_def["description"] == "Test description"
        assert tool_def["inputSchema"]["type"] == "object"
        assert "x" in tool_def["inputSchema"]["properties"]

    def test_convert_skill_without_parameters(self):
        """测试转换没有参数的 Skill。"""

        class ConcreteSkill(Skill):
            def execute(self, **kwargs):
                return {}

        skill = ConcreteSkill(name="no_params", description="No params")
        tool_def = SkillToMCPTool.convert(skill)

        assert tool_def["name"] == "no_params"
        assert tool_def["inputSchema"]["type"] == "object"
        assert tool_def["inputSchema"]["properties"] == {}

    def test_convert_all_skills(self):
        """测试批量转换多个 Skills。"""
        skills = [
            DummySkill(name="skill1", description="First"),
            DummySkill(name="skill2", description="Second"),
        ]
        tool_defs = SkillToMCPTool.convert_all(skills)

        assert len(tool_defs) == 2
        assert tool_defs[0]["name"] == "skill1"
        assert tool_defs[1]["name"] == "skill2"


class TestMCPToolExecutor:
    """测试 MCPToolExecutor 类。"""

    def test_execute_success(self, registry: SkillRegistry):
        """测试成功执行 tool。"""
        executor = MCPToolExecutor(registry)
        result = executor.execute("dummy", {"value": "test"})

        assert result["isError"] is False
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        assert "success" in result["content"][0]["text"]

    def test_execute_with_no_arguments(self, registry: SkillRegistry):
        """测试不带参数执行 tool。"""
        executor = MCPToolExecutor(registry)
        result = executor.execute("dummy")

        assert result["isError"] is False
        assert "success" in result["content"][0]["text"]

    def test_execute_skill_not_found(self, registry: SkillRegistry):
        """测试执行不存在的 tool。"""
        executor = MCPToolExecutor(registry)
        result = executor.execute("nonexistent")

        assert result["isError"] is True
        assert "not found" in result["content"][0]["text"].lower()

    def test_execute_skill_failure(self, registry: SkillRegistry):
        """测试执行失败的 tool。"""
        executor = MCPToolExecutor(registry)
        result = executor.execute("failing")

        assert result["isError"] is True
        assert "Intentional failure" in result["content"][0]["text"]


class TestHealthEndpoint:
    """测试健康检查端点。"""

    def test_health_check(self, client: TestClient):
        """测试 /health 端点。"""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ok"
        assert data["skills_count"] == 2

    def test_health_check_empty_registry(self):
        """测试空注册表的健康检查。"""
        empty_registry = SkillRegistry()
        app = create_app(empty_registry)
        client = TestClient(app)

        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["skills_count"] == 0


class TestSkillsEndpoint:
    """测试 skills 列表端点。"""

    def test_list_skills(self, client: TestClient):
        """测试 /skills 端点。"""
        response = client.get("/skills")
        assert response.status_code == 200

        data = response.json()
        assert "skills" in data
        assert len(data["skills"]) == 2

        skill_names = [s["name"] for s in data["skills"]]
        assert "dummy" in skill_names
        assert "failing" in skill_names


class TestToolsEndpoint:
    """测试 tools 相关端点。"""

    def test_list_tools(self, client: TestClient):
        """测试 /tools 端点。"""
        response = client.get("/tools")
        assert response.status_code == 200

        data = response.json()
        assert "tools" in data
        assert len(data["tools"]) == 2

        tool = data["tools"][0]
        assert "name" in tool
        assert "description" in tool
        assert "inputSchema" in tool

    def test_execute_tool_success(self, client: TestClient):
        """测试成功执行 tool。"""
        response = client.post(
            "/tools/dummy/execute", json={"arguments": {"value": "hello"}}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["isError"] is False
        assert "success" in data["content"][0]["text"]

    def test_execute_tool_not_found(self, client: TestClient):
        """测试执行不存在的 tool 返回 404。"""
        response = client.post("/tools/nonexistent/execute", json={})
        assert response.status_code == 404

    def test_execute_tool_failure(self, client: TestClient):
        """测试执行失败的 tool。"""
        response = client.post("/tools/failing/execute", json={})
        assert response.status_code == 200

        data = response.json()
        assert data["isError"] is True
        assert "Intentional failure" in data["content"][0]["text"]
