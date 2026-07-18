"""
HOS MCP Server — 主服务器入口。

基于 FastMCP 实现，将所有 HOS-Forge 安全工具暴露为 MCP 端点。
支持任何 MCP 客户端 (Claude Desktop/Code, Cursor, LangChain, 等) 调用。

启动方式:
    # HTTP 模式 (默认)
    python -m hosforge mcp

    # stdio 模式 (Claude Desktop/Code)
    python -m hosforge mcp --stdio

    # 代码中调用
    from hosforge.mcp_server.server import app
    result = await app.call_tool("hos_nmap_scan", {"target": "example.com"})

Claude Desktop 注册:
    {
        "mcpServers": {
            "hos-forge": {
                "command": "hos-mcp",
                "args": ["--stdio"]
            }
        }
    }
"""

from __future__ import annotations

import logging
import sys

from fastmcp import FastMCP

from hosforge.mcp_server.tools.security_tools import register_tools

logger = logging.getLogger(__name__)

# 创建 MCP 服务器
app = FastMCP(
    'HOS-Forge',
    version='0.1.0',
)


def main() -> None:
    """CLI 入口 — 启动 HOS MCP Server"""
    register_tools(app)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    )

    if '--help' in sys.argv or '-h' in sys.argv:
        print('HOS-Forge MCP Server v0.1.0')
        print('')
        print('用法:')
        print('  hos-mcp                   启动 HTTP 模式 (:8321)')
        print('  hos-mcp --port 8321       指定端口')
        print('  hos-mcp --stdio           启动 stdio 模式 (Claude Desktop)')
        print('')
        print('Claude Desktop 注册:')
        print('  "mcpServers": {')
        print('    "hos-forge": {')
        print('      "command": "hos-mcp",')
        print('      "args": ["--stdio"]')
        print('    }')
        print('  }')
        return

    if '--stdio' in sys.argv:
        logger.info('HOS MCP Server starting in stdio mode')
        app.run(transport='stdio')
    else:
        port = 8321
        for i, arg in enumerate(sys.argv):
            if arg == '--port' and i + 1 < len(sys.argv):
                port = int(sys.argv[i + 1])
        logger.info('HOS MCP Server starting on port %s', port)
        import asyncio
        asyncio.run(app.run_http_async(host='0.0.0.0', port=port))


if __name__ == '__main__':
    main()
