"""
HOS-Forge Nmap Tool — 网络扫描工具适配器。

集成 Nmap 进行端口扫描、服务识别、操作系统检测。
支持作为 MCP Server 供 Agent 调用。
"""

from __future__ import annotations

import asyncio
import json
import logging
import shutil
from typing import Any

from hosforge.security_tools.base import BaseSecurityTool, SecurityToolResult

logger = logging.getLogger(__name__)


class NmapTool(BaseSecurityTool):
    """
    Nmap 网络扫描工具适配器。

    功能:
        - TCP/UDP 端口扫描
        - 服务版本检测
        - 操作系统识别
        - NSE 脚本扫描

    使用示例:
        tool = NmapTool()
        result = await tool.run("example.com", ports="22,80,443")
    """

    def __init__(self, nmap_path: str = 'nmap'):
        super().__init__()
        self._nmap_path = nmap_path
        self._available: bool | None = None

    @property
    def name(self) -> str:
        return 'nmap'

    async def validate(self) -> bool:
        """检查 Nmap 是否可用"""
        if self._available is not None:
            return self._available

        nmap = shutil.which(self._nmap_path)
        self._available = nmap is not None
        if not self._available:
            logger.warning('Nmap not found at: %s', self._nmap_path)
        return self._available

    async def run(self, target: str, **kwargs: Any) -> SecurityToolResult:
        """
        执行 Nmap 扫描。

        Args:
            target: 目标 IP/域名
            **kwargs:
                ports: 端口范围 (默认 "1-1024")
                scan_type: 扫描类型 (tcp_syn/tcp_connect/udp)
                scripts: NSE 脚本列表
                os_detection: 是否检测操作系统
                service_detection: 是否检测服务版本
                extra_args: 额外 nmap 参数

        Returns:
            SecurityToolResult: 扫描结果
        """
        if not await self.validate():
            return SecurityToolResult(
                tool_name=self.name,
                success=False,
                error='Nmap is not installed or not found in PATH',
            )

        ports = kwargs.get('ports', '1-1024')
        scan_type = kwargs.get('scan_type', 'tcp_syn')
        scripts = kwargs.get('scripts', [])
        os_detection = kwargs.get('os_detection', False)
        service_detection = kwargs.get('service_detection', True)
        extra_args = kwargs.get('extra_args', [])

        # 构建命令
        cmd = [self._nmap_path]

        # 扫描类型
        scan_flags = {
            'tcp_syn': ['-sS'],
            'tcp_connect': ['-sT'],
            'udp': ['-sU'],
            'ping': ['-sn'],
            'comprehensive': ['-sS', '-sV', '-sC', '-O'],
        }
        cmd.extend(scan_flags.get(scan_type, ['-sS']))

        # 端口
        cmd.extend(['-p', str(ports)])

        # 服务版本检测
        if service_detection:
            cmd.append('-sV')

        # 操作系统检测
        if os_detection:
            cmd.append('-O')

        # NSE 脚本
        if scripts:
            cmd.extend(['--script', ','.join(scripts)])

        # 输出格式
        cmd.extend(['-oX', '-'])  # XML to stdout

        # 额外参数
        if extra_args:
            cmd.extend(extra_args if isinstance(extra_args, list) else [extra_args])

        # 目标
        cmd.append(target)

        # 超时
        timeout = kwargs.get('timeout', 300)

        logger.info('Nmap command: %s', ' '.join(cmd))

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
                    error=f'Nmap scan timed out after {timeout}s',
                )

            if process.returncode != 0:
                return SecurityToolResult(
                    tool_name=self.name,
                    success=False,
                    error=stderr.decode() if stderr else 'Nmap returned non-zero exit code',
                    output=stdout.decode() if stdout else '',
                )

            output = stdout.decode()
            result = self._parse_nmap_output(output)

            return SecurityToolResult(
                tool_name=self.name,
                success=True,
                output=output,
                raw_data=result,
            )

        except FileNotFoundError:
            return SecurityToolResult(
                tool_name=self.name,
                success=False,
                error=f'Nmap not found at: {self._nmap_path}',
            )
        except Exception as e:
            logger.exception('Nmap execution failed')
            return SecurityToolResult(
                tool_name=self.name,
                success=False,
                error=str(e),
            )

    def _parse_nmap_output(self, xml_output: str) -> dict[str, Any]:
        """
        解析 Nmap XML 输出为结构化数据。

        由于避免依赖外部 XML 解析库，采用基础解析。
        """
        result: dict[str, Any] = {
            'open_ports': [],
            'services': {},
            'banners': {},
            'os_guess': '',
            'host_status': 'unknown',
        }

        # 基础 XML 解析
        if '<host>' in xml_output:
            # 提取 host status
            if '<status state="up"' in xml_output:
                result['host_status'] = 'up'

            # 提取端口信息
            import re
            port_matches = re.findall(
                r'<port protocol="(\w+)" portid="(\d+)">.*?<state state="(\w+)".*?'
                r'(?:<service name="([^"]*)"|)',
                xml_output,
            )
            for protocol, port, state, service in port_matches:
                if state == 'open':
                    port_num = int(port)
                    result['open_ports'].append(port_num)
                    if service:
                        result['services'][port_num] = service

        return result
