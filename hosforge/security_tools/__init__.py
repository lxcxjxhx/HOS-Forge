"""
HOS-Forge Security Tools — 安全工具集成层。

集成外部安全工具为OpenHands Tool：
    - Semgrep SAST 引擎
    - Nmap 网络扫描
    - Burp Suite API 集成
    - Nuclei 漏洞扫描
    - Ghidra 逆向分析
"""

from hosforge.security_tools.base import BaseSecurityTool, SecurityToolResult
from hosforge.security_tools.nmap_tool import NmapTool
from hosforge.security_tools.semgrep_tool import SemgrepTool
from hosforge.security_tools.nuclei_tool import NucleiTool
from hosforge.security_tools.burp_tool import BurpTool

__all__ = [
    'BaseSecurityTool',
    'SecurityToolResult',
    'NmapTool',
    'SemgrepTool',
    'NucleiTool',
    'BurpTool',
]
