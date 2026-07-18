"""
HOS MCP Server — 主服务器入口。

基于 FastMCP 实现，将所有 HOS-Forge 安全工具暴露为 MCP 端点。
支持任何 MCP 客户端 (Claude Desktop/Code, Cursor, LangChain, 等) 调用。

启动方式:
    # 直接运行
    python -m hosforge.mcp_server.server

    # 作为 MCP Server 注册 (settings.json)
    {
        "mcpServers": {
            "hos-forge": {
                "command": "python",
                "args": ["-m", "hosforge.mcp_server.server"]
            }
        }
    }

    # 在代码中调用
    from hosforge.mcp_server.server import app
    result = await app.call_tool("hos_nmap_scan", {"target": "example.com"})
"""

from __future__ import annotations

import logging
import sys
from typing import Any

from fastmcp import FastMCP

from hosforge.mcp_server.tools.security_tools import register_tools
from hosforge.mcp_server.bridge.discovery import MCPDiscoveryEngine
from hosforge.mcp_server.orchestrator import MCPOrchestrator

logger = logging.getLogger(__name__)

# 创建 MCP 服务器
app = FastMCP(
    'HOS-Forge Security Server',
    description='HOS-Forge: AI Native Information Security IDE — MCP 安全工具服务',
    version='0.1.0',
)


@app.get('/health', description='健康检查')
async def health() -> dict[str, Any]:
    """服务器健康检查"""
    return {
        'status': 'ok',
        'service': 'HOS-Forge MCP Server',
        'version': '0.1.0',
    }


@app.get('/capabilities', description='获取所有可用能力列表')
async def capabilities() -> dict[str, list[dict[str, str]]]:
    """获取服务器支持的所有工具能力"""
    return {
        'tools': [
            {'name': t.name, 'description': t.description}
            for t in app._tool_manager.list_tools()
        ],
    }


@app.get('/bridge/discover', description='发现外部 MCP 安全服务')
async def bridge_discover() -> dict[str, list[dict]]:
    """自动发现系统中可用的外部安全 MCP 服务"""
    engine = MCPDiscoveryEngine()
    services = await engine.discover_all()
    return {
        'services': [s.to_dict() for s in services],
        'count': len(services),
    }


@app.get('/workflows', description='列出可用工作流模板')
async def list_workflows() -> dict[str, dict]:
    """列出所有预定义的安全工作流"""
    return MCPOrchestrator.list_templates()


def serve(host: str = '0.0.0.0', port: int = 8321) -> None:
    """
    启动 MCP HTTP 服务。

    Args:
        host: 监听地址
        port: 监听端口 (默认 8321 = 安全风信子)
    """
    logger.info('HOS MCP Server starting on %s:%s', host, port)
    app.run(host=host, port=port)


def main() -> None:
    """CLI 入口"""
    register_tools(app)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    )
    logger.info('HOS MCP Server initializing...')

    if '--stdio' in sys.argv:
        # stdio 模式 (用于 Claude Desktop/Code)
        app.run(transport='stdio')
    else:
        # HTTP 模式 (默认)
        app.run(transport='sse', host='0.0.0.0', port=8321)


if __name__ == '__main__':
    main()
