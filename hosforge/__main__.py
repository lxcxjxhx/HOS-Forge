"""
HOS-Forge — AI Native Information Security IDE

基于 OpenHands 二次开发的 AI 原生信息安全 IDE。

用法:
    python -m hosforge [command]

命令:
    mcp         启动 HOS MCP Server (默认 :8321)
    dashboard   启动 Dashboard API 服务
    report      生成安全报告
    ci          执行 CI/CD 安全检查
"""

from __future__ import annotations

import sys

from hosforge.__init__ import __version__


def main() -> None:
    """HOS-Forge CLI 主入口"""
    args = sys.argv[1:]

    if not args:
        print(f'HOS-Forge v{__version__}')
        print('AI Native Information Security IDE')
        print()
        print('用法:')
        print('  python -m hosforge mcp [--port PORT] [--stdio]')
        print('  python -m hosforge dashboard [--port PORT]')
        print('  python -m hosforge report --input <data.json> --output <report.html>')
        print('  python -m hosforge ci <command> [args...]')
        print()
        print('快速开始:')
        print('  python -m hosforge mcp              # 启动 MCP Server')
        print('  python -m hosforge report --help    # 报告生成帮助')
        sys.exit(0)

    command = args[0]
    cmd_args = args[1:]

    if command == 'mcp':
        from hosforge.mcp_server.server import main as mcp_main
        sys.argv = ['hos-mcp'] + cmd_args
        mcp_main()

    elif command == 'dashboard':
        from hosforge.dashboard.cli import main as dash_main
        sys.argv = ['hos-dashboard'] + cmd_args
        dash_main()

    elif command == 'report':
        from hosforge.reporter.cli import main as report_main
        sys.argv = ['hos-report'] + cmd_args
        report_main()

    elif command == 'ci':
        from hosforge.ci.__main__ import main as ci_main
        sys.argv = ['hos-ci'] + cmd_args
        ci_main()

    else:
        print(f'未知命令: {command}')
        print('使用 python -m hosforge --help 查看可用命令')
        sys.exit(1)


if __name__ == '__main__':
    main()
