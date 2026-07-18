"""
HOS MCP Connector — mcp-security-hub 连接器。

桥接 FuzzingLabs mcp-security-hub:
    https://github.com/FuzzingLabs/mcp-security-hub

涵盖能力:
    - Recon: Nmap/Subfinder/DNS/WHOIS
    - Web: Nuclei/SQLMap/OWASP ZAP
    - Binary: Ghidra
    - Password: Hashcat
    - Threat Intel: CVE/OSINT
    - Code: Semgrep

连接方式:
    - Docker: docker run --rm -i fuzzinglabs/mcp-security-hub
"""

from __future__ import annotations

import logging
from typing import Any

from hosforge.mcp_server.bridge.adapter import StdioMCPAdapter

logger = logging.getLogger(__name__)

# mcp-security-hub 的子工具清单
SECURITY_HUB_TOOLS = {
    'nmap': '🔍 Nmap 端口扫描 — 主机发现/端口扫描/服务识别',
    'subfinder': '🌐 子域名枚举 — 被动子域名收集',
    'dns_lookup': '📡 DNS 查询 — A/AAAA/MX/NS/TXT 记录',
    'whois_lookup': '📋 WHOIS 查询 — 域名注册信息',
    'nuclei_scan': '📡 Nuclei 漏洞扫描 — 模板化漏洞检测',
    'sqlmap_scan': '💉 SQLMap SQL 注入检测',
    'zap_scan': '🛡️ OWASP ZAP 主动扫描',
    'ghidra_analyze': '🔬 Ghidra 二进制分析',
    'hashcat_crack': '🔑 Hashcat 密码破解',
    'cve_search': '📖 CVE 漏洞搜索',
    'osint_email': '📧 邮箱 OSINT 搜集',
    'semgrep_scan': '🔬 Semgrep 代码审计',
    'gobuster_dir': '📁 目录爆破',
    'wpscan_scan': '🔍 WordPress 安全扫描',
}


class SecurityHubConnector:
    """
    mcp-security-hub 连接器。

    封装 FuzzingLabs 安全 MCP 工具集。

    使用示例:
        hub = SecurityHubConnector()
        await hub.connect()
        result = await hub.nmap_scan("example.com")
        cves = await hub.cve_search("apache")
    """

    def __init__(self):
        self._adapter = StdioMCPAdapter(
            service_name='mcp-security-hub',
            command='docker',
            args=['run', '--rm', '-i', 'fuzzinglabs/mcp-security-hub'],
        )
        self._connected = False

    async def connect(self) -> bool:
        """连接到 mcp-security-hub"""
        ok = await self._adapter.connect()
        self._connected = ok
        if ok:
            logger.info('Connected to mcp-security-hub')
        return ok

    async def nmap_scan(self, target: str, ports: str = '1-1024') -> dict[str, Any]:
        """
        Nmap 端口扫描。

        Args:
            target: 目标 IP/域名
            ports: 端口范围

        Returns:
            dict: 扫描结果
        """
        return await self._call('nmap', {
            'target': target,
            'ports': ports,
        })

    async def nuclei_scan(self, target: str, severity: str = 'medium') -> dict[str, Any]:
        """Nuclei 漏洞扫描"""
        return await self._call('nuclei_scan', {
            'target': target,
            'severity': severity,
        })

    async def sqlmap_scan(self, url: str, data: str = '') -> dict[str, Any]:
        """SQLMap SQL 注入检测"""
        return await self._call('sqlmap_scan', {
            'url': url,
            'data': data,
        })

    async def cve_search(self, keyword: str, limit: int = 20) -> dict[str, Any]:
        """CVE 漏洞搜索"""
        return await self._call('cve_search', {
            'keyword': keyword,
            'limit': limit,
        })

    async def ghidra_analyze(self, binary_path: str) -> dict[str, Any]:
        """Ghidra 二进制分析"""
        return await self._call('ghidra_analyze', {
            'path': binary_path,
        })

    async def subdomain_enum(self, domain: str) -> dict[str, Any]:
        """子域名枚举"""
        return await self._call('subfinder', {
            'domain': domain,
        })

    async def directory_bruteforce(self, url: str, wordlist: str = 'common') -> dict[str, Any]:
        """目录爆破"""
        return await self._call('gobuster_dir', {
            'url': url,
            'wordlist': wordlist,
        })

    async def semgrep_scan(self, path: str, rules: str = 'default') -> dict[str, Any]:
        """Semgrep 代码审计"""
        return await self._call('semgrep_scan', {
            'path': path,
            'rules': rules,
        })

    async def list_capabilities(self) -> dict[str, str]:
        """列出所有可用的安全工具能力"""
        return dict(SECURITY_HUB_TOOLS)

    async def disconnect(self) -> None:
        """断开连接"""
        await self._adapter.disconnect()
        self._connected = False

    async def _call(self, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        """调用 mcp-security-hub 的工具"""
        if not self._connected:
            raise ConnectionError('mcp-security-hub not connected')

        try:
            result = await self._adapter.call_tool(tool, args)
            return result
        except Exception as e:
            logger.error('%s call failed: %s', tool, e)
            return {'success': False, 'error': str(e)}
