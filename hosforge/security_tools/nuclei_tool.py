"""
HOS-Forge Nuclei Tool — 自动化漏洞扫描工具适配器。

集成 Nuclei 进行基于模板的漏洞扫描。
"""

from __future__ import annotations

import asyncio
import json
import logging
import shutil
from typing import Any

from hosforge.security_tools.base import BaseSecurityTool, SecurityToolResult

logger = logging.getLogger(__name__)


class NucleiTool(BaseSecurityTool):
    """
    Nuclei 漏洞扫描工具适配器。

    功能:
        - 基于模板的漏洞扫描
        - CVE 检测
        - 配置错误检测
        - 多协议支持 (HTTP/DNS/SSL)

    使用示例:
        tool = NucleiTool()
        result = await tool.run("https://example.com", tags=["cve", "misconfig"])
    """

    def __init__(self, nuclei_path: str = 'nuclei'):
        super().__init__()
        self._nuclei_path = nuclei_path
        self._available: bool | None = None

    @property
    def name(self) -> str:
        return 'nuclei'

    async def validate(self) -> bool:
        if self._available is not None:
            return self._available
        nc = shutil.which(self._nuclei_path)
        self._available = nc is not None
        return self._available

    async def run(self, target: str, **kwargs: Any) -> SecurityToolResult:
        """
        执行 Nuclei 扫描。

        Args:
            target: 目标 URL/IP
            **kwargs:
                tags: 模板标签过滤 (默认 ["cve","misconfiguration"])
                templates: 指定模板路径
                severity: 最低严重级别
                rate_limit: 请求速率
                timeout: 超时秒数

        Returns:
            SecurityToolResult: 扫描结果
        """
        if not await self.validate():
            return SecurityToolResult(
                tool_name=self.name,
                success=False,
                error='Nuclei is not installed',
            )

        tags = kwargs.get('tags', ['cve', 'misconfiguration'])
        templates = kwargs.get('templates', '')
        severity = kwargs.get('severity', 'low')
        rate_limit = kwargs.get('rate_limit', 150)
        timeout = kwargs.get('timeout', 180)

        cmd = [self._nuclei_path, '-json']

        # 模板选择
        if templates:
            cmd.extend(['-t', templates])
        elif tags:
            cmd.extend(['-tags', ','.join(tags)])

        # 严重级别过滤
        cmd.extend(['-severity', severity])

        # 速率限制
        cmd.extend(['-rl', str(rate_limit)])

        # 目标
        cmd.extend(['-u', target])

        logger.info('Nuclei scan: target=%s tags=%s', target, tags)

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                return SecurityToolResult(
                    tool_name=self.name,
                    success=False,
                    error=f'Nuclei scan timed out after {timeout}s',
                )

            output = stdout.decode()
            findings = self._parse_nuclei_output(output)

            return SecurityToolResult(
                tool_name=self.name,
                success=process.returncode == 0,
                output=output,
                raw_data={'findings': findings},
            )

        except FileNotFoundError:
            return SecurityToolResult(
                tool_name=self.name,
                success=False,
                error='Nuclei not found',
            )

    def _parse_nuclei_output(self, output: str) -> list[dict]:
        """解析 Nuclei JSON 输出（每行一个 JSON）"""
        findings = []
        for line in output.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                findings.append({
                    'template_id': data.get('template-id', ''),
                    'name': data.get('info', {}).get('name', ''),
                    'severity': data.get('info', {}).get('severity', 'unknown'),
                    'type': data.get('type', ''),
                    'host': data.get('host', ''),
                    'matched_at': data.get('matched-at', ''),
                    'description': data.get('info', {}).get('description', ''),
                    'cve_ids': data.get('info', {}).get('classification', {}).get('cve-id', []),
                    'cwe_ids': data.get('info', {}).get('classification', {}).get('cwe-id', []),
                    'curl_command': data.get('curl-command', ''),
                })
            except json.JSONDecodeError:
                continue
        return findings
