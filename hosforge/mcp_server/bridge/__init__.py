"""
HOS MCP Bridge — 三方 MCP 桥接层。

自动发现、连接、桥接外部安全 MCP 服务:
    - Burp Suite MCP (PortSwigger 官方)
    - mcp-security-hub (FuzzingLabs 全工具集合)
    - pentestMCP (渗透测试流程自动化)
    - Ghidra MCP (二进制分析)
    - CVE/NVD MCP (漏洞知识)

架构:
    Discovery → Connection → Translation → Registration

使外部 MCP 工具如同 HOS-Forge 原生工具一样被调用。
"""

from hosforge.mcp_server.bridge.discovery import MCPDiscoveryEngine, DiscoveredService
from hosforge.mcp_server.bridge.adapter import MCPAdapter, MCPToolSchema

__all__ = [
    'MCPDiscoveryEngine',
    'DiscoveredService',
    'MCPAdapter',
    'MCPToolSchema',
]
