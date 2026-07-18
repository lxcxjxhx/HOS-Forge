"""
HOS MCP Connectors — 特定外部 MCP 服务的连接器实现。

每个连接器封装一个外部安全 MCP 服务的接入逻辑:
    - BurpConnector: Burp Suite 官方 MCP (PortSwigger)
    - SecurityHubConnector: mcp-security-hub (FuzzingLabs)
    - PentestMCPConnector: pentestMCP 自动化渗透
"""

from hosforge.mcp_server.bridge.connectors.burp import BurpConnector
from hosforge.mcp_server.bridge.connectors.security_hub import SecurityHubConnector

__all__ = [
    'BurpConnector',
    'SecurityHubConnector',
]
