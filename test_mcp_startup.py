"""
测试MCP Server启动和工具注册（不实际执行工具）
"""
import asyncio
import sys
from hosforge.mcp_server.server import app
from hosforge.mcp_server.tools.security_tools import register_tools


async def test_mcp_server():
    """测试MCP Server功能"""
    print("=" * 60)
    print("HOS-Forge MCP Server 启动测试")
    print("=" * 60)
    
    # 注册工具
    register_tools(app)
    print(f"\n✓ 工具注册完成")
    
    # 列出所有工具
    tools = await app.list_tools()
    print(f"\n✓ 已注册 {len(tools)} 个MCP工具:")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description[:50]}...")
    
    # 验证工具调用接口存在（不实际执行）
    print(f"\n✓ 验证工具调用接口...")
    tool_names = [t.name for t in tools]
    
    expected_tools = [
        "hos_nmap_scan",
        "hos_semgrep_scan",
        "hos_nuclei_scan",
        "hos_cve_query",
        "hos_cwe_query",
        "hos_pentest_run",
        "hos_report_generate",
        "hos_workflow_run",
    ]
    
    for name in expected_tools:
        if name in tool_names:
            print(f"  ✓ {name}")
        else:
            print(f"  ✗ {name} (missing)")
    
    print("\n" + "=" * 60)
    print("MCP Server 启动测试完成")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    try:
        asyncio.run(test_mcp_server())
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
