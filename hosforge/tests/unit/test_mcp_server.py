"""
MCP Server 单元测试。

通过子进程方式测试 MCP Server 启动和工具注册，
避免 hosforge/mcp/ 与 fastmcp 依赖的 mcp 包命名冲突。
"""

import os
import subprocess
import sys
from pathlib import Path

# 获取项目根目录（hosforge/ 的父目录）
PROJECT_ROOT = str(Path(__file__).parent.parent.parent.parent)

MCP_VERIFY_SCRIPT = """
import sys
import asyncio
sys.path.insert(0, "{project_root}")

from hosforge.mcp_server.server import app
from hosforge.mcp_server.tools.security_tools import register_tools

async def verify():
    register_tools(app)
    tools = await app.list_tools()
    print(f"TOOLS_COUNT={{len(tools)}}")
    for t in tools:
        print(f"TOOL={{t.name}}")

asyncio.run(verify())
"""


class TestMCPServerStartup:
    """MCP Server 启动测试套件（子进程方式）"""

    def test_mcp_server_tools_registration(self):
        """测试 MCP Server 工具注册（通过子进程避免 import 冲突）"""
        script = MCP_VERIFY_SCRIPT.format(project_root=PROJECT_ROOT)
        env = os.environ.copy()
        env["PYTHONPATH"] = PROJECT_ROOT + os.pathsep + env.get("PYTHONPATH", "")

        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
        )
        assert result.returncode == 0, f"MCP Server startup failed:\n{result.stderr}"

        # 解析输出
        output = result.stdout
        tools_count = None
        tool_names = []
        for line in output.strip().split("\n"):
            if line.startswith("TOOLS_COUNT="):
                tools_count = int(line.split("=")[1])
            elif line.startswith("TOOL="):
                tool_names.append(line.split("=")[1])

        # 验证工具数量
        assert tools_count is not None, "Could not parse tools count"
        assert tools_count >= 19, f"Expected at least 19 tools, got {tools_count}"

        # 验证关键工具存在
        expected_tools = {
            "hos_nmap_scan",
            "hos_semgrep_scan",
            "hos_nuclei_scan",
            "hos_burp_scan",
            "hos_cve_query",
            "hos_cwe_query",
            "hos_report_generate",
            "hos_mcp_discover",
            "hos_workflow_run",
            "hos_workflow_templates",
            "hos_parallel_scan",
        }
        actual_tools = set(tool_names)
        for expected in expected_tools:
            assert expected in actual_tools, f"Expected tool {expected} not found in {actual_tools}"

    def test_mcp_server_help(self):
        """测试 MCP Server --help 输出"""
        env = os.environ.copy()
        env["PYTHONPATH"] = PROJECT_ROOT + os.pathsep + env.get("PYTHONPATH", "")

        result = subprocess.run(
            [sys.executable, "-m", "hosforge.mcp_server.server", "--help"],
            capture_output=True,
            text=True,
            timeout=15,
            env=env,
        )
        assert result.returncode == 0, f"Help failed:\n{result.stderr}"
        assert "HOS-Forge MCP Server" in result.stdout
        assert "--stdio" in result.stdout
        assert "--verify" in result.stdout

    def test_mcp_server_verify_mode(self):
        """测试 MCP Server --verify 模式"""
        env = os.environ.copy()
        env["PYTHONPATH"] = PROJECT_ROOT + os.pathsep + env.get("PYTHONPATH", "")

        result = subprocess.run(
            [sys.executable, "-m", "hosforge.mcp_server.server", "--verify"],
            capture_output=True,
            text=True,
            timeout=15,
            env=env,
        )
        assert result.returncode == 0, f"Verify failed:\n{result.stderr}"
        assert "tools registered successfully" in result.stdout
