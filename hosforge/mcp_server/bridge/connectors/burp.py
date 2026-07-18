"""
HOS MCP Connector — Burp Suite MCP 连接器。

桥接 PortSwigger 官方 Burp MCP Server:
    https://github.com/PortSwigger/mcp-server

能力:
    - 查看 Proxy History
    - 分析 HTTP 请求/响应
    - 修改请求参数
    - 辅助漏洞判断
    - 主动扫描

连接方式:
    1. SSE: Burp MCP Server 默认端口 1337
    2. Stdio: java -jar burp-mcp.jar
"""

from __future__ import annotations

import logging
from typing import Any

from hosforge.mcp_server.bridge.adapter import SSEHttpMCPAdapter

logger = logging.getLogger(__name__)


class BurpConnector:
    """
    Burp Suite MCP 连接器。

    封装 Burp MCP 的常用操作，供 HOS-Forge Agent 调用。

    使用示例:
        connector = BurpConnector(base_url="http://127.0.0.1:1337")
        await connector.connect()
        history = await connector.get_proxy_history()
        summary = await connector.analyze_request(target)
    """

    def __init__(self, base_url: str = 'http://127.0.0.1:1337'):
        self._adapter = SSEHttpMCPAdapter(
            service_name='burp-mcp',
            base_url=base_url,
        )
        self._connected = False

    async def connect(self) -> bool:
        """连接到 Burp MCP 服务"""
        ok = await self._adapter.connect()
        self._connected = ok
        return ok

    async def get_proxy_history(self, limit: int = 50) -> list[dict[str, Any]]:
        """
        获取 Burp Proxy 历史记录。

        Args:
            limit: 返回条数

        Returns:
            list[dict]: 历史请求列表
        """
        if not self._connected:
            raise ConnectionError('Burp MCP not connected')

        result = await self._adapter.call_tool('get_proxy_history', {
            'limit': limit,
        })
        return result.get('messages', [])

    async def analyze_request(self, request_data: str) -> dict[str, Any]:
        """
        分析 HTTP 请求。

        Args:
            request_data: 原始 HTTP 请求数据

        Returns:
            dict: 分析结果 (参数/路径/Cookie/Header 等)
        """
        if not self._connected:
            raise ConnectionError('Burp MCP not connected')

        result = await self._adapter.call_tool('analyze_request', {
            'request': request_data,
        })
        return result

    async def send_to_repeater(self, request_data: str) -> dict[str, Any]:
        """
        发送请求到 Repeater 进行重放。

        Args:
            request_data: 原始 HTTP 请求

        Returns:
            dict: 响应结果
        """
        if not self._connected:
            raise ConnectionError('Burp MCP not connected')

        result = await self._adapter.call_tool('send_to_repeater', {
            'request': request_data,
        })
        return result

    async def start_scan(self, url: str) -> dict[str, Any]:
        """
        启动主动扫描。

        Args:
            url: 目标 URL

        Returns:
            dict: 扫描任务信息
        """
        if not self._connected:
            raise ConnectionError('Burp MCP not connected')

        result = await self._adapter.call_tool('start_scan', {
            'url': url,
        })
        return result

    async def get_scan_issues(self, scan_id: str) -> list[dict[str, Any]]:
        """
        获取扫描发现的问题。

        Args:
            scan_id: 扫描任务 ID

        Returns:
            list[dict]: 安全问题列表
        """
        if not self._connected:
            raise ConnectionError('Burp MCP not connected')

        result = await self._adapter.call_tool('get_scan_issues', {
            'scan_id': scan_id,
        })
        return result.get('issues', [])

    async def disconnect(self) -> None:
        """断开连接"""
        await self._adapter.disconnect()
        self._connected = False
