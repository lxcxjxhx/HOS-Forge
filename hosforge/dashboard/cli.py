"""
HOS-Forge Dashboard CLI — 仪表盘命令行工具。

用法:
    hos-dashboard --port 8321
    hos-dashboard --help
"""

from __future__ import annotations

import sys


def main() -> None:
    """CLI 入口"""
    args = sys.argv[1:]

    if '--help' in args or '-h' in args:
        print('用法: hos-dashboard [--port PORT]')
        print('')
        print('选项:')
        print('  --port   HTTP 服务端口 (默认: 8321)')
        print('')
        print('启动仪表盘 API 服务后，访问:')
        print('  http://localhost:8321/api/hos/dashboard/overview')
        sys.exit(0)

    port = 8321
    for i, arg in enumerate(args):
        if arg == '--port' and i + 1 < len(args):
            port = int(args[i + 1])

    import uvicorn
    from fastapi import FastAPI
    from hosforge.dashboard.api import router

    app = FastAPI(title='HOS-Forge Dashboard')
    app.include_router(router)

    print(f'HOS-Forge Dashboard API running on http://0.0.0.0:{port}')
    uvicorn.run(app, host='0.0.0.0', port=port)
