"""
HOS-Forge — AI Native Security Platform

基于 OpenHands 二次开发的 AI 原生安全平台。

用法:
    python -m hosforge [command]

命令:
    mcp         启动 HOS MCP Server (默认 :8321)
"""

from __future__ import annotations

import sys

from hosforge.__init__ import __version__


def main() -> None:
    """HOS-Forge CLI 主入口"""
    args = sys.argv[1:]

    if not args:
        print(f"HOS-Forge v{__version__}")
        print("AI Native Security Platform")
        print()
        print("用法:")
        print("  python -m hosforge mcp [--port PORT] [--stdio]")
        print()
        print("快速开始:")
        print("  python -m hosforge mcp              # 启动 MCP Server")
        sys.exit(0)

    command = args[0]
    cmd_args = args[1:]

    if command == "mcp":
        from hosforge.mcp_server.server import main as mcp_main

        sys.argv = ["hos-mcp"] + cmd_args
        mcp_main()

    else:
        print(f"未知命令: {command}")
        print("使用 python -m hosforge --help 查看可用命令")
        sys.exit(1)


if __name__ == "__main__":
    main()
