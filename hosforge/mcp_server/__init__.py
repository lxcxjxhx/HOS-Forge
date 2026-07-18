"""
HOS MCP Server — HOS-Forge MCP 协议服务层。

将 HOS-Forge 所有信息安全能力包装为 MCP (Model Context Protocol) 服务，
使任何 MCP 客户端 (Claude Code / Cursor / 自定义 Agent) 均可调用。

暴露的能力:
    - 安全工具: Nmap, Semgrep, Nuclei, BurpSuite
    - 安全 Agent: Audit, Attack, Defense
    - 知识库: CVE/CWE 查询, RAG 检索
    - 报告: 漏洞报告生成

MCP 工具列表:
    - hos_nmap_scan          — 端口扫描
    - hos_semgrep_scan       — 代码审计
    - hos_nuclei_scan        — 漏洞扫描
    - hos_burp_scan          — Burp Suite 扫描
    - hos_cve_query          — CVE 查询
    - hos_cwe_query          — CWE 查询
    - hos_vuln_explain       — 漏洞解释
    - hos_pentest_run        — 渗透测试
    - hos_report_generate    — 报告生成
"""

__version__ = '0.1.0'
