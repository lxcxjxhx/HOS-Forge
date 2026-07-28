"""MCP Server HTTP 服务实现。

提供动态加载 Skills、转换为 MCP tools 以及健康检查端点。
"""

from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from hosforge.mcp_server.skill_bridge import MCPToolExecutor, SkillToMCPTool
from hosforge.skills.registry import SkillRegistry
from hosforge.skills.security import (
    GitHubIntegrationSkill,
    NucleiScanSkill,
    SemgrepScanSkill,
)


def create_app(registry: SkillRegistry | None = None) -> FastAPI:
    """创建并配置 FastAPI 应用。

    Args:
        registry: 可选的 SkillRegistry 实例。如果为 None，将创建默认注册表并注册内置 skills。

    Returns:
        配置完成的 FastAPI 应用实例
    """
    if registry is None:
        registry = _create_default_registry()

    app = FastAPI(title="HOS-Forge MCP Server", version="1.0.0")
    executor = MCPToolExecutor(registry)

    @app.get("/health")
    async def health_check() -> Dict[str, Any]:
        """健康检查端点。

        Returns:
            包含状态和 skills 数量的字典
        """
        skills_count = len(registry.list_skills())
        return {"status": "ok", "skills_count": skills_count}

    @app.get("/skills")
    async def list_skills() -> Dict[str, Any]:
        """列出所有已注册的 skills。

        Returns:
            包含 skills 列表的字典
        """
        skills = registry.list_skills()
        return {
            "skills": [
                {"name": s.name, "description": s.description}
                for s in skills
            ]
        }

    @app.get("/tools")
    async def list_tools() -> Dict[str, Any]:
        """列出所有可用的 MCP tools。

        Returns:
            包含 MCP tool 定义的列表
        """
        skills = registry.list_skills()
        tools = SkillToMCPTool.convert_all(skills)
        return {"tools": tools}

    @app.post("/tools/{tool_name}/execute")
    async def execute_tool(
        tool_name: str, arguments: Dict[str, Any] | None = None
    ) -> JSONResponse:
        """执行指定的 MCP tool。

        Args:
            tool_name: tool 名称
            arguments: 传递给 tool 的参数

        Returns:
            MCP tool 执行结果

        Raises:
            HTTPException: 当 tool 不存在或执行失败时
        """
        skill = registry.get(tool_name)
        if skill is None:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

        result = executor.execute(tool_name, arguments)
        return JSONResponse(content=result)

    return app


def _create_default_registry() -> SkillRegistry:
    """创建默认的 SkillRegistry 并注册内置 skills。

    Returns:
        已注册内置 skills 的 SkillRegistry 实例
    """
    registry = SkillRegistry()
    registry.register(NucleiScanSkill())
    registry.register(SemgrepScanSkill())
    registry.register(GitHubIntegrationSkill())
    return registry


def main() -> None:
    """启动 MCP Server 的入口函数。"""
    import uvicorn

    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
