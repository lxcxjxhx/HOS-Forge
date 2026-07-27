"""Personality CLI 命令实现。"""

from pathlib import Path

from rich.console import Console
from rich.table import Table

from hosforge.personalities import PersonalityLoader


class PersonalityCommand:
    """Personality 命令实现。"""

    def __init__(self):
        self.console = Console()

    def list(self):
        """列出可用的 Personality。"""
        # 使用 PersonalityLoader 自动加载 examples/personalities 目录
        try:
            loader = PersonalityLoader()
            personality_names = loader.list_personalities()
        except Exception as e:
            self.console.print(f"[red]加载 Personality 失败: {e}[/red]")
            return

        if not personality_names:
            self.console.print("[yellow]未找到可用的 Personality[/yellow]")
            return

        personalities = []
        for name in personality_names:
            try:
                personality = loader.get_personality(name)
                personalities.append({
                    "name": personality.name,
                    "role": personality.role,
                    "description": personality.description,
                    "skills": len(personality.skills),
                    "tools": len(personality.tools),
                })
            except Exception as e:
                self.console.print(f"[yellow]警告: 无法加载 {name}: {e}[/yellow]")

        if not personalities:
            self.console.print("[yellow]未找到可用的 Personality[/yellow]")
            return

        # 创建表格
        table = Table(title="可用 Personality")
        table.add_column("名称", style="green")
        table.add_column("角色")
        table.add_column("技能数", justify="right")
        table.add_column("工具数", justify="right")
        table.add_column("描述")

        for p in personalities:
            table.add_row(
                p["name"],
                p["role"],
                str(p["skills"]),
                str(p["tools"]),
                p["description"],
            )

        self.console.print(table)
