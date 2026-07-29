"""MCP Server HTTP 服务实现。

提供动态加载 Skills、转换为 MCP tools 以及健康检查端点。
"""

from typing import Any, Dict

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
        return {"skills": [{"name": s.name, "description": s.description} for s in skills]}

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
    async def execute_tool(tool_name: str, arguments: Dict[str, Any] | None = None) -> JSONResponse:
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
    """CLI 入口 — 启动 HOS MCP Server"""
    import logging
    import sys

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger(__name__)

    # 帮助信息
    if "--help" in sys.argv or "-h" in sys.argv:
        print("HOS-Forge MCP Server v0.1.0")
        print("")
        print("用法:")
        print("  hos-mcp                   启动 HTTP 模式 (:8321)")
        print("  hos-mcp --port 8321       指定端口")
        print("  hos-mcp --stdio           启动 stdio 模式 (Claude Desktop)")
        print("  hos-mcp --verify          验证工具注册并退出")
        print("")
        print("Claude Desktop 注册:")
        print('  "mcpServers": {')
        print('    "hos-forge": {')
        print('      "command": "hos-mcp",')
        print('      "args": ["--stdio"]')
        print("    }")
        print("  }")
        return

    # 创建应用
    app = create_app()

    # 注册工具
    try:
        from hosforge.mcp_server.tools import register_tools

        register_tools(app)
        logger.info("All HOS-Forge MCP tools registered successfully")
    except Exception as e:
        logger.error("Failed to register tools: %s", e)
        sys.exit(1)

    # 验证模式
    if "--verify" in sys.argv:
        import asyncio

        async def verify():
            tools = await app.list_tools()
            print(f"✓ {len(tools)} tools registered successfully")
            return True

        success = asyncio.run(verify())
        sys.exit(0 if success else 1)

    # 启动服务器
    try:
        if "--stdio" in sys.argv:
            logger.info("HOS MCP Server starting in stdio mode")
            app.run(transport="stdio")
        else:
            port = 8321
            for i, arg in enumerate(sys.argv):
                if arg == "--port" and i + 1 < len(sys.argv):
                    port = int(sys.argv[i + 1])
            logger.info("HOS MCP Server starting on port %s", port)
            import asyncio

            asyncio.run(app.run_http_async(host="0.0.0.0", port=port))
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error("Server error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
