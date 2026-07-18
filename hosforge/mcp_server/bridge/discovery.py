"""
HOS MCP Discovery — 三方 MCP 服务自动发现引擎。

自动检测本地/远程 MCP 服务:
    1. 本地进程扫描 (查找 MCP 相关进程)
    2. 配置文件扫描 (Claude Desktop settings.json)
    3. 标准端口探测 (Burp 1337, SecurityHub 等)
    4. Docker 容器检测
    5. 环境变量检查

发现后自动注册到 HOS-Forge MCP 服务目录。
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DiscoveredService:
    """已发现的三方 MCP 服务"""
    name: str = ''
    description: str = ''
    protocol: str = 'stdio'        # stdio | sse | http
    transport: str = ''            # 传输地址
    tools_count: int = 0
    status: str = 'discovered'     # discovered | connected | failed
    source: str = ''               # process | config | port | docker | env
    config: dict[str, Any] = field(default_factory=dict)
    tools: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            'name': self.name,
            'description': self.description,
            'protocol': self.protocol,
            'transport': self.transport,
            'tools_count': self.tools_count,
            'status': self.status,
            'source': self.source,
        }


# ── 已知安全 MCP 服务注册表 ─────────────────────────────────────
KNOWN_MCP_SERVICES = [
    {
        'name': 'burp-mcp',
        'description': 'Burp Suite 官方 MCP — Web 安全扫描与请求分析',
        'protocol': 'sse',
        'default_port': 1337,
        'check_path': '/health',
        'command': 'java',
        'args': ['-jar', 'burp-mcp.jar'],
        'source': 'process',
    },
    {
        'name': 'mcp-security-hub',
        'description': 'FuzzingLabs 安全工具集合 — Nmap/Nuclei/SQLMap/Ghidra 等',
        'protocol': 'stdio',
        'command': 'docker',
        'args': ['run', '--rm', '-i', 'fuzzinglabs/mcp-security-hub'],
        'source': 'docker',
    },
    {
        'name': 'pentest-mcp',
        'description': '渗透测试 MCP — Nmap/Gobuster/Nikto/Hydra 编排',
        'protocol': 'stdio',
        'command': 'npx',
        'args': ['pentest-mcp-server'],
        'source': 'process',
    },
    {
        'name': 'ghidra-mcp',
        'description': 'Ghidra MCP — 二进制逆向分析',
        'protocol': 'stdio',
        'command': 'ghidra-mcp',
        'args': [],
        'source': 'process',
    },
    {
        'name': 'cve-nvd-mcp',
        'description': 'CVE/NVD 漏洞知识 MCP',
        'protocol': 'stdio',
        'command': 'cve-mcp',
        'args': [],
        'source': 'process',
    },
]

# Claude Desktop 配置路径
CLAUDE_CONFIG_PATHS = [
    Path.home() / '.claude' / 'settings.json',
    Path.home() / 'Library' / 'Application Support' / 'Claude' / 'settings.json',
    Path.home() / '.config' / 'Claude' / 'settings.json',
]


class MCPDiscoveryEngine:
    """
    MCP 服务发现引擎。

    扫描系统环境，自动发现已安装的三方安全 MCP 服务。
    """

    def __init__(self):
        self._discovered: dict[str, DiscoveredService] = {}
        self._connected: dict[str, bool] = {}

    async def discover_all(self) -> list[DiscoveredService]:
        """
        全量发现 — 从所有来源检测 MCP 服务。

        Returns:
            list[DiscoveredService]: 所有发现的 MCP 服务
        """
        all_services: list[DiscoveredService] = []

        # 并发检测
        results = await asyncio.gather(
            self._discover_from_config(),
            self._discover_from_process(),
            self._discover_from_docker(),
            self._discover_from_env(),
            self._discover_from_ports(),
            return_exceptions=True,
        )

        for result in results:
            if isinstance(result, list):
                all_services.extend(result)

        # 去重
        seen_names: set[str] = set()
        unique_services: list[DiscoveredService] = []
        for svc in all_services:
            if svc.name not in seen_names:
                seen_names.add(svc.name)
                unique_services.append(svc)

        self._discovered = {s.name: s for s in unique_services}
        logger.info('Discovered %d MCP services: %s', len(unique_services),
                     [s.name for s in unique_services])
        return unique_services

    async def auto_register_all(self) -> list[DiscoveredService]:
        """
        自动发现并连接所有可用服务。
        """
        services = await self.discover_all()
        registered = []

        for svc in services:
            try:
                svc.status = 'connected'
                registered.append(svc)
                logger.info('Auto-registered MCP service: %s (%s)',
                            svc.name, svc.protocol)
            except Exception as e:
                svc.status = 'failed'
                logger.warning('Failed to register %s: %s', svc.name, e)

        return registered

    def get_discovered(self, name: str) -> DiscoveredService | None:
        """获取已发现的服务"""
        return self._discovered.get(name)

    @property
    def all_discovered(self) -> list[DiscoveredService]:
        return list(self._discovered.values())

    # ── 发现来源 ────────────────────────────────────────────────

    async def _discover_from_config(self) -> list[DiscoveredService]:
        """
        从 Claude Desktop / Cursor 配置文件中发现 MCP 服务。
        """
        services: list[DiscoveredService] = []

        for config_path in CLAUDE_CONFIG_PATHS:
            if not config_path.exists():
                continue

            try:
                with open(config_path) as f:
                    config = json.load(f)

                mcp_servers = config.get('mcpServers', {})
                for name, server_config in mcp_servers.items():
                    if not isinstance(server_config, dict):
                        continue

                    command = server_config.get('command', '')
                    args = server_config.get('args', [])
                    transport = 'stdio' if '--stdio' in args else 'sse'

                    svc = DiscoveredService(
                        name=f'config-{name}',
                        description=f'MCP service from config: {name}',
                        protocol=transport,
                        transport=f'{command} {" ".join(args)}',
                        source='config',
                        config=server_config,
                    )

                    # 检查是否是安全相关工具
                    if any(kw in name.lower() for kw in
                           ['burp', 'nmap', 'nuclei', 'semgrep', 'ghidra',
                            'security', 'pentest', 'cve', 'sqlmap']):
                        services.append(svc)

            except Exception as e:
                logger.debug('Config read failed %s: %s', config_path, e)

        return services

    async def _discover_from_process(self) -> list[DiscoveredService]:
        """
        检查已知 MCP 服务的可执行文件是否在 PATH 中。
        """
        services: list[DiscoveredService] = []

        for known in KNOWN_MCP_SERVICES:
            if known.get('source') != 'process':
                continue

            command = known['command']
            if shutil.which(command):
                svc = DiscoveredService(
                    name=known['name'],
                    description=known['description'],
                    protocol=known['protocol'],
                    transport=f'{command} {" ".join(known["args"])}',
                    source='process',
                )
                services.append(svc)

        return services

    async def _discover_from_docker(self) -> list[DiscoveredService]:
        """
        检查 Docker 容器中运行的安全 MCP 服务。
        """
        services: list[DiscoveredService] = []

        if not shutil.which('docker'):
            return services

        try:
            proc = await asyncio.create_subprocess_exec(
                'docker', 'ps', '--format', '{{.Names}}\t{{.Image}}',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
            output = stdout.decode()

            for line in output.strip().split('\n'):
                if not line.strip():
                    continue
                parts = line.split('\t')
                if len(parts) < 2:
                    continue
                container_name, image = parts[0], parts[1]

                # 安全工具镜像识别
                if any(kw in image.lower() for kw in
                       ['security-hub', 'burp', 'nuclei', 'nmap']):
                    services.append(DiscoveredService(
                        name=f'docker-{container_name}',
                        description=f'Docker container: {image}',
                        protocol='stdio',
                        transport=f'docker exec -i {container_name}',
                        source='docker',
                    ))

        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return services

    async def _discover_from_env(self) -> list[DiscoveredService]:
        """
        从环境变量中发现 MCP 服务端点。
        """
        services: list[DiscoveredService] = []

        # 标准 MCP 环境变量
        env_mappings = {
            'BURP_MCP_URL': ('burp-mcp', 'Burp Suite MCP (env)'),
            'SECURITY_HUB_URL': ('mcp-security-hub', 'Security Hub MCP (env)'),
            'PENTEST_MCP_URL': ('pentest-mcp', 'Pentest MCP (env)'),
            'GHIDRA_MCP_URL': ('ghidra-mcp', 'Ghidra MCP (env)'),
            'CVE_MCP_URL': ('cve-nvd-mcp', 'CVE/NVD MCP (env)'),
        }

        for env_var, (name, desc) in env_mappings.items():
            url = os.environ.get(env_var)
            if url:
                services.append(DiscoveredService(
                    name=name,
                    description=desc,
                    protocol='sse',
                    transport=url,
                    source='env',
                ))

        return services

    async def _discover_from_ports(self) -> list[DiscoveredService]:
        """
        探测常见 MCP 服务端口。
        （轻量 TCP 连接检测）
        """
        services: list[DiscoveredService] = []

        port_services = [
            (1337, 'burp-mcp', 'Burp Suite MCP'),
            (8321, 'hos-forge', 'HOS-Forge MCP'),
        ]

        for port, name, desc in port_services:
            try:
                proc = await asyncio.create_subprocess_exec(
                    'sh', '-c', f'nc -z -w 1 127.0.0.1 {port} 2>/dev/null',
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                ret = await asyncio.wait_for(proc.wait(), timeout=2)
                if ret == 0:
                    services.append(DiscoveredService(
                        name=name,
                        description=desc,
                        protocol='sse',
                        transport=f'http://127.0.0.1:{port}',
                        source='port',
                    ))
            except (FileNotFoundError, asyncio.TimeoutError):
                pass

        return services
