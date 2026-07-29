"""
MCP Server 单元测试。

测试 MCP Server 的基本功能和工具注册。
"""

import pytest
from fastapi.testclient import TestClient

from hosforge.mcp_server.server import create_app
from hosforge.skills.registry import SkillRegistry


class TestMCPServerBasic:
    """MCP Server 基础测试"""

    def test_create_app(self):
        """测试创建 FastAPI 应用"""
        registry = SkillRegistry()
        app = create_app(registry)
        assert app is not None

    def test_health_endpoint(self):
        """测试健康检查端点"""
        registry = SkillRegistry()
        app = create_app(registry)
        client = TestClient(app)

        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("healthy", "ok")
        assert "skills_count" in data

    def test_skills_endpoint(self):
        """测试 skills 列表端点"""
        registry = SkillRegistry()
        app = create_app(registry)
        client = TestClient(app)

        response = client.get("/skills")
        assert response.status_code == 200
        data = response.json()
        assert "skills" in data
        assert isinstance(data["skills"], list)

    def test_tools_endpoint(self):
        """测试 tools 列表端点"""
        registry = SkillRegistry()
        app = create_app(registry)
        client = TestClient(app)

        response = client.get("/tools")
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert isinstance(data["tools"], list)
