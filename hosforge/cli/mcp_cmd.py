"""MCP CLI 命令实现。"""

from pathlib import Path

from rich.console import Console
from rich.table import Table

from hosforge.mcp import MCPServerRegistry


class MCPCommand:
    """MCP 命令实现。"""

    def __init__(self):
        self.console = Console()

    def list(self):
        """列出可用的 MCP Server。"""
        registry = MCPServerRegistry()

        # 自动发现内置 MCP Server
        builtin_dir = Path(__file__).parent.parent / "mcp" / "servers"
        if builtin_dir.exists():
            for server_file in builtin_dir.glob("*_server.py"):
                server_name = server_file.stem.replace("_server", "")
                try:
                    registry.discover_server(server_name, str(server_file))
                except Exception as e:
                    self.console.print(f"[yellow]警告: 无法加载 {server_name}: {e}[/yellow]")

        servers = registry.list_servers()

        if not servers:
            self.console.print("[yellow]未找到可用的 MCP Server[/yellow]")
            return

        # 创建表格
        table = Table(title="可用 MCP Server")
        table.add_column("名称", style="cyan")
        table.add_column("状态", style="green")
        table.add_column("工具数", justify="right")
        table.add_column("描述")

        for server in servers:
            status = "已加载" if server.get("loaded") else "未加载"
            status_style = "green" if server.get("loaded") else "dim"

            table.add_row(
                server["name"],
                f"[{status_style}]{status}[/{status_style}]",
                str(server.get("tool_count", 0)),
                server.get("description", ""),
            )

        self.console.print(table)
