"""
HOS MCP Adapter — 外部 MCP 服务适配器基类。

提供统一接口将第三方 MCP 服务桥接到 HOS-Forge 工具体系。
支持 stdio 和 SSE 两种 MCP 传输协议。
"""

from __future__ import annotations

import abc
import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class MCPToolSchema:
    """外部 MCP 工具的模式定义"""
    name: str = ''
    description: str = ''
    input_schema: dict[str, Any] = field(default_factory=dict)


class MCPAdapter(abc.ABC):
    """
    外部 MCP 服务适配器基类。

    子类必须实现:
        - connect() — 连接到外部 MCP 服务
        - call_tool(name, args) — 调用外部工具
        - disconnect() — 断开连接
    """

    def __init__(self, service_name: str):
        self.service_name = service_name
        self._connected = False
        self._tools: list[MCPToolSchema] = []
        self.logger = logging.getLogger(f'MCPAdapter[{service_name}]')

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def tools(self) -> list[MCPToolSchema]:
        return self._tools

    @abc.abstractmethod
    async def connect(self) -> bool:
        """连接到外部 MCP 服务"""
        ...

    @abc.abstractmethod
    async def call_tool(self, name: str, args: dict[str, Any]) -> Any:
        """调用外部 MCP 工具"""
        ...

    @abc.abstractmethod
    async def disconnect(self) -> None:
        """断开连接"""
        ...

    async def list_tools(self) -> list[MCPToolSchema]:
        """列出外部服务支持的工具"""
        return self._tools


class StdioMCPAdapter(MCPAdapter):
    """
    stdio 传输协议的 MCP 适配器。

    通过子进程与 MCP 服务通信 (适用于 Claude Desktop 模式)。
    """

    def __init__(self, service_name: str, command: str, args: list[str] | None = None):
        super().__init__(service_name)
        self._command = command
        self._args = args or []
        self._process: asyncio.subprocess.Process | None = None
        self._pending: dict[str, asyncio.Future] = {}

    async def connect(self) -> bool:
        try:
            self._process = await asyncio.create_subprocess_exec(
                self._command, *self._args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            self._connected = True
            self.logger.info('Connected via stdio: %s %s', self._command, ' '.join(self._args))
            return True
        except FileNotFoundError:
            self.logger.error('Command not found: %s', self._command)
            return False
        except Exception as e:
            self.logger.error('Connection failed: %s', e)
            return False

    async def call_tool(self, name: str, args: dict[str, Any]) -> Any:
        if not self._connected or not self._process:
            raise ConnectionError(f'{self.service_name} not connected')

        request = {
            'jsonrpc': '2.0',
            'id': id(name),
            'method': 'tools/call',
            'params': {'name': name, 'arguments': args},
        }

        payload = json.dumps(request) + '\n'
        self._process.stdin.write(payload.encode())
        await self._process.stdin.drain()

        response = await asyncio.wait_for(
            self._process.stdout.readline(), timeout=60
        )
        result = json.loads(response.decode())
        return result.get('result', {})

    async def disconnect(self) -> None:
        if self._process:
            self._process.terminate()
            try:
                await asyncio.wait_for(self._process.wait(), timeout=5)
            except asyncio.TimeoutError:
                self._process.kill()
            self._connected = False
            self.logger.info('Disconnected')


class SSEHttpMCPAdapter(MCPAdapter):
    """
    SSE/HTTP 传输协议的 MCP 适配器。

    通过 HTTP 请求与 MCP 服务通信。
    """

    def __init__(self, service_name: str, base_url: str):
        super().__init__(service_name)
        self._base_url = base_url.rstrip('/')
        self._session = None

    async def connect(self) -> bool:
        try:
            import httpx
            self._session = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=30,
            )
            # 健康检查
            resp = await self._session.get('/health')
            self._connected = resp.status_code < 500
            if self._connected:
                self.logger.info('Connected via SSE: %s', self._base_url)
            return self._connected
        except Exception as e:
            self.logger.error('SSE connection failed: %s', e)
            return False

    async def call_tool(self, name: str, args: dict[str, Any]) -> Any:
        if not self._connected or not self._session:
            raise ConnectionError(f'{self.service_name} not connected')

        # 映射工具名到 HTTP 端点
        endpoint = f'/tools/{name}'

        resp = await self._session.post(
            endpoint,
            json={'arguments': args},
        )
        if resp.status_code == 200:
            return resp.json()
        else:
            raise RuntimeError(
                f'Tool call failed ({resp.status_code}): {resp.text}'
            )

    async def list_tools(self) -> list[MCPToolSchema]:
        if not self._connected or not self._session:
            return []

        try:
            resp = await self._session.get('/tools')
            if resp.status_code == 200:
                data = resp.json()
                self._tools = [
                    MCPToolSchema(
                        name=t.get('name', ''),
                        description=t.get('description', ''),
                        input_schema=t.get('inputSchema', {}),
                    )
                    for t in data.get('tools', [])
                ]
        except Exception:
            pass

        return self._tools

    async def disconnect(self) -> None:
        if self._session:
            await self._session.aclose()
            self._connected = False
            self.logger.info('Disconnected')
