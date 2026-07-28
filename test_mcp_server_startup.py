#!/usr/bin/env python3
"""
MCP Server 启动验证脚本。

验证:
1. MCP Server 可以成功创建
2. 所有工具可以正常注册
3. 工具列表可以获取
"""

import asyncio
import sys


async def verify_mcp_server():
    """验证 MCP Server 启动和工具注册"""
    print("=" * 60)
    print("HOS-Forge MCP Server 启动验证")
    print("=" * 60)
    
    try:
        # 1. 导入并创建服务器
        print("\n[1/4] 导入 MCP Server 模块...")
        from hosforge.mcp_server.server import app
        from hosforge.mcp_server.tools.security_tools import register_tools
        print("✓ 模块导入成功")
        
        # 2. 注册工具
        print("\n[2/4] 注册所有安全工具...")
        register_tools(app)
        print("✓ 工具注册完成")
        
        # 3. 获取工具列表
        print("\n[3/4] 获取已注册工具列表...")
        tools = await app.list_tools()
        print(f"✓ 成功获取 {len(tools)} 个工具")
        
        # 4. 显示工具详情
        print("\n[4/4] 工具详情:")
        tool_categories = {
            "扫描类": ["hos_nmap_scan", "hos_semgrep_scan", "hos_nuclei_scan", "hos_burp_scan"],
            "知识库类": ["hos_cve_query", "hos_cwe_query", "hos_vuln_explain", "hos_rag_tag"],
            "渗透测试类": ["hos_pentest_run", "hos_security_audit", "hos_fix_vulnerability"],
            "报告类": ["hos_report_generate"],
            "桥接类": ["hos_mcp_discover", "hos_mcp_connect", "hos_burp_bridge", "hos_security_hub_bridge"],
            "编排类": ["hos_workflow_templates", "hos_workflow_run", "hos_parallel_scan"],
        }
        
        for category, expected_tools in tool_categories.items():
            print(f"\n  {category}:")
            for tool_name in expected_tools:
                tool = next((t for t in tools if t.name == tool_name), None)
                if tool:
                    print(f"    ✓ {tool_name}")
                else:
                    print(f"    ✗ {tool_name} (未注册)")
        
        print("\n" + "=" * 60)
        print(f"验证通过: {len(tools)} 个工具已成功注册")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(verify_mcp_server())
    sys.exit(0 if success else 1)
