"""
HOS-Forge Burp Suite Tool — Burp Suite API 集成适配器。

集成 Burp Suite REST API 进行流量分析和漏洞辅助。
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from hosforge.security_tools.base import BaseSecurityTool, SecurityToolResult

logger = logging.getLogger(__name__)


class BurpTool(BaseSecurityTool):
    """
    Burp Suite API 适配器。

    功能:
        - 抓取流量分析
        - 请求重放
        - 扫描队列管理
        - 漏洞报告导出

    使用示例:
        tool = BurpTool(base_url="http://localhost:1337", api_key="...")
        result = await tool.run("https://example.com")
    """

    def __init__(
        self,
        base_url: str = 'http://127.0.0.1:1337',
        api_key: str = '',
    ):
        super().__init__()
        self._base_url = base_url.rstrip('/')
        self._api_key = api_key
        self._client: httpx.AsyncClient | None = None
        self._available: bool | None = None

    @property
    def name(self) -> str:
        return 'burpsuite'

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {'Content-Type': 'application/json'}
            if self._api_key:
                headers['Authorization'] = f'Bearer {self._api_key}'
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                headers=headers,
                timeout=30,
            )
        return self._client

    async def validate(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            client = await self._get_client()
            resp = await client.get('/health')
            self._available = resp.status_code == 200
        except Exception:
            self._available = False
        return self._available

    async def run(self, target: str, **kwargs: Any) -> SecurityToolResult:
        """
        通过 Burp Suite 分析目标。

        Args:
            target: 目标 URL
            **kwargs:
                action: 操作类型 (scan/proxy/replay/report)
                scope: 扫描范围
                scan_speed: 扫描速度 (fast/medium/thorough)

        Returns:
            SecurityToolResult: 分析结果
        """
        if not await self.validate():
            return SecurityToolResult(
                tool_name=self.name,
                success=False,
                error='Burp Suite API is not available',
            )

        action = kwargs.get('action', 'scan')
        client = await self._get_client()

        try:
            if action == 'scan':
                return await self._start_scan(client, target, kwargs)
            elif action == 'proxy':
                return await self._get_proxy_history(client, kwargs)
            elif action == 'replay':
                return await self._replay_request(client, kwargs)
            elif action == 'report':
                return await self._get_report(client, target)
            else:
                return SecurityToolResult(
                    tool_name=self.name,
                    success=False,
                    error=f'Unknown action: {action}',
                )

        except httpx.RequestError as e:
            return SecurityToolResult(
                tool_name=self.name,
                success=False,
                error=f'Burp API request failed: {e}',
            )
        except Exception as e:
            logger.exception('Burp tool failed')
            return SecurityToolResult(
                tool_name=self.name,
                success=False,
                error=str(e),
            )

    async def _start_scan(
        self,
        client: httpx.AsyncClient,
        target: str,
        kwargs: dict[str, Any],
    ) -> SecurityToolResult:
        """启动主动扫描"""
        scope = kwargs.get('scope', target)
        scan_speed = kwargs.get('scan_speed', 'medium')

        payload = {
            'urls': [scope],
            'scan_configurations': [
                {'name': f'{scan_speed}_scan'},
            ],
        }

        resp = await client.post('/api/v0/scan', json=payload)

        if resp.status_code in (200, 201):
            data = resp.json()
            return SecurityToolResult(
                tool_name=self.name,
                success=True,
                output=f'Scan created: {data.get("scan_id", "")}',
                raw_data={'scan_id': data.get('scan_id', ''), 'status': 'created'},
            )
        else:
            return SecurityToolResult(
                tool_name=self.name,
                success=False,
                error=f'Scan creation failed: {resp.text}',
            )

    async def _get_proxy_history(
        self,
        client: httpx.AsyncClient,
        kwargs: dict[str, Any],
    ) -> SecurityToolResult:
        """获取代理历史"""
        limit = kwargs.get('limit', 50)
        resp = await client.get(f'/api/v0/proxy/history?limit={limit}')

        if resp.status_code == 200:
            data = resp.json()
            entries = [
                {
                    'url': item.get('url', ''),
                    'method': item.get('method', ''),
                    'status': item.get('status', 0),
                    'length': item.get('length', 0),
                    'mime_type': item.get('mime_type', ''),
                }
                for item in data.get('messages', [])
            ]
            return SecurityToolResult(
                tool_name=self.name,
                success=True,
                raw_data={'proxy_history': entries},
            )

        return SecurityToolResult(
            tool_name=self.name,
            success=False,
            error=f'Failed to get proxy history: {resp.text}',
        )

    async def _replay_request(
        self,
        client: httpx.AsyncClient,
        kwargs: dict[str, Any],
    ) -> SecurityToolResult:
        """重放请求"""
        request_data = kwargs.get('request', '')
        if not request_data:
            return SecurityToolResult(
                tool_name=self.name,
                success=False,
                error='No request data provided',
            )

        resp = await client.post(
            '/api/v0/proxy/send',
            json={'request': request_data},
        )

        if resp.status_code == 200:
            data = resp.json()
            return SecurityToolResult(
                tool_name=self.name,
                success=True,
                raw_data={
                    'status_code': data.get('status_code', 0),
                    'response': data.get('response', '')[:500],
                },
            )

        return SecurityToolResult(
            tool_name=self.name,
            success=False,
            error=f'Replay failed: {resp.text}',
        )

    async def _get_report(
        self,
        client: httpx.AsyncClient,
        target: str,
    ) -> SecurityToolResult:
        """获取扫描报告"""
        resp = await client.get(f'/api/v0/scan/{target}/report')

        if resp.status_code == 200:
            return SecurityToolResult(
                tool_name=self.name,
                success=True,
                output=resp.text,
                raw_data={'format': 'html'},
            )

        return SecurityToolResult(
            tool_name=self.name,
            success=False,
            error=f'Report fetch failed: {resp.text}',
        )

    async def close(self) -> None:
        """关闭 HTTP 客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None
