"""MCP Server 集成测试。

测试 MCP Server 的启动、工具注册、端点访问和错误处理。
"""

from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from hosforge.mcp_server.server import create_app
from hosforge.skills.base_skill import Skill, SkillResult
from hosforge.skills.registry import SkillRegistry


class TestMCPServerStartup:
    """测试 MCP Server 启动。"""

    def test_create_app_success(self):
        """测试成功创建 FastAPI 应用。"""
        app = create_app()
        assert app is not None
        assert app.title == "HOS-Forge MCP Server"

    def test_app_has_health_endpoint(self):
        """测试应用包含健康检查端点。"""
        app = create_app()
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200

    def test_app_has_skills_endpoint(self):
        """测试应用包含 skills 列表端点。"""
        app = create_app()
        client = TestClient(app)
        response = client.get("/skills")
        assert response.status_code == 200


class TestMCPServerToolRegistration:
    """测试 MCP Server 工具注册。"""

    def test_create_app_with_empty_registry(self):
        """测试空注册表时创建应用。"""
        registry = SkillRegistry()
        app = create_app(registry)

        # 应该不抛出异常
        assert app is not None

    def test_create_app_with_single_skill(self):
        """测试注册单个 Skill 为工具。"""
        registry = SkillRegistry()

        skill = Mock(spec=Skill)
        skill.name = "test_skill"
        skill.description = "Test skill"
        skill.parameters = {
            "type": "object",
            "properties": {
                "param1": {"type": "string"},
            },
            "required": ["param1"],
        }

        registry.register(skill)
        app = create_app(registry)

        # 验证工具已注册（通过 /skills 端点）
        client = TestClient(app)
        response = client.get("/skills")
        assert response.status_code == 200
        skills_data = response.json()
        assert any(s["name"] == "test_skill" for s in skills_data["skills"])

    def test_create_app_with_multiple_skills(self):
        """测试注册多个 Skills 为工具。"""
        registry = SkillRegistry()

        for i in range(3):
            skill = Mock(spec=Skill)
            skill.name = f"skill_{i}"
            skill.description = f"Test skill {i}"
            skill.parameters = {"type": "object", "properties": {}}
            registry.register(skill)

        app = create_app(registry)

        client = TestClient(app)
        response = client.get("/skills")
        skills_data = response.json()
        assert len(skills_data["skills"]) >= 3


class TestMCPServerEndpoints:
    """测试 MCP Server 端点。"""

    def test_health_endpoint_returns_status(self):
        """测试健康检查端点返回状态。"""
        app = create_app()
        client = TestClient(app)

        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"

    def test_health_endpoint_includes_skills_count(self):
        """测试健康检查端点包含 skills 数量。"""
        registry = SkillRegistry()

        skill = Mock(spec=Skill)
        skill.name = "test_skill"
        skill.description = "Test"
        skill.parameters = {"type": "object", "properties": {}}
        registry.register(skill)

        app = create_app(registry)

        client = TestClient(app)
        response = client.get("/health")
        data = response.json()

        assert "skills_count" in data
        assert data["skills_count"] >= 1

    def test_skills_endpoint_returns_list(self):
        """测试 skills 端点返回技能列表。"""
        registry = SkillRegistry()

        skill = Mock(spec=Skill)
        skill.name = "test_skill"
        skill.description = "Test skill"
        skill.parameters = {"type": "object", "properties": {}}
        registry.register(skill)

        app = create_app(registry)

        client = TestClient(app)
        response = client.get("/skills")
        assert response.status_code == 200

        skills_data = response.json()
        assert "skills" in skills_data
        assert isinstance(skills_data["skills"], list)
        assert len(skills_data["skills"]) > 0

    def test_skills_endpoint_includes_metadata(self):
        """测试 skills 端点包含元数据。"""
        registry = SkillRegistry()

        skill = Mock(spec=Skill)
        skill.name = "test_skill"
        skill.description = "Test description"
        skill.parameters = {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "Parameter 1"},
            },
        }
        registry.register(skill)

        app = create_app(registry)

        client = TestClient(app)
        response = client.get("/skills")
        skills_data = response.json()

        test_skill = next(s for s in skills_data["skills"] if s["name"] == "test_skill")
        assert "description" in test_skill


class TestMCPServerErrorHandling:
    """测试 MCP Server 错误处理。"""

    def test_invalid_endpoint_returns_404(self):
        """测试无效端点返回 404。"""
        app = create_app()
        client = TestClient(app)

        response = client.get("/invalid/endpoint")
        assert response.status_code == 404

    def test_skills_endpoint_with_no_skills(self):
        """测试无 skills 时的端点响应。"""
        registry = SkillRegistry()
        app = create_app(registry)
        client = TestClient(app)

        response = client.get("/skills")
        assert response.status_code == 200

        skills_data = response.json()
        assert "skills" in skills_data
        assert isinstance(skills_data["skills"], list)
