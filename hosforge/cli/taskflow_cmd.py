"""Taskflow CLI 命令实现。"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table

from hosforge.taskflow import WorkflowParser, WorkflowExecutor

console = Console()


class TaskflowCommand:
    """Taskflow 命令实现。"""

    def __init__(self):
        self.console = Console()

    def run(self, workflow_path: str, checkpoint: bool = False, resume: Optional[str] = None, dry_run: bool = False):
        """运行工作流。

        Args:
            workflow_path: 工作流 YAML 文件路径
            checkpoint: 是否启用 checkpoint
            resume: 从指定 checkpoint 恢复
            dry_run: 仅验证不执行
        """
        path = Path(workflow_path)
        if not path.exists():
            self.console.print(f"[red]错误: 工作流文件不存在: {workflow_path}[/red]")
            sys.exit(1)

        if not path.suffix in (".yaml", ".yml"):
            self.console.print(f"[red]错误: 工作流文件必须是 YAML 格式: {workflow_path}[/red]")
            sys.exit(1)

        try:
            # 解析工作流
            self.console.print(f"[blue]解析工作流: {workflow_path}[/blue]")
            parser = WorkflowParser()
            schema = parser.parse_file(str(path))
            workflow = schema.workflow

            # 显示工作流信息
            self.console.print(f"\n[green]工作流名称: {workflow.name}[/green]")
            self.console.print(f"[dim]{workflow.description}[/dim]")
            self.console.print(f"[blue]任务数量: {len(workflow.tasks)}[/blue]\n")

            # 如果是 dry-run，只验证不执行
            if dry_run:
                self.console.print("[green]✓ 工作流验证通过[/green]")
                self.console.print("[dim]Dry-run 模式，未实际执行[/dim]")
                return

            # 执行工作流
            executor = WorkflowExecutor(workflow, enable_checkpoint=checkpoint)

            if resume:
                self.console.print(f"[blue]从 checkpoint 恢复: {resume}[/blue]")
                executor.load_checkpoint(resume)

            self.console.print("[yellow]开始执行工作流...[/yellow]\n")

            # 运行异步执行
            result = asyncio.run(executor.execute())

            # 显示结果
            self._print_result(result)

        except Exception as e:
            self.console.print(f"[red]执行失败: {e}[/red]")
            sys.exit(1)

    def validate(self, workflow_path: str):
        """验证工作流文件。

        Args:
            workflow_path: 工作流 YAML 文件路径
        """
        path = Path(workflow_path)
        if not path.exists():
            self.console.print(f"[red]错误: 工作流文件不存在: {workflow_path}[/red]")
            sys.exit(1)

        if not path.suffix in (".yaml", ".yml"):
            self.console.print(f"[red]错误: 工作流文件必须是 YAML 格式: {workflow_path}[/red]")
            sys.exit(1)

        try:
            # 解析工作流
            parser = WorkflowParser()
            schema = parser.parse_file(str(path))
            workflow = schema.workflow

            # 验证成功
            self.console.print(f"[green]✓ 工作流验证通过: {workflow_path}[/green]")
            self.console.print(f"\n[green]工作流名称: {workflow.name}[/green]")
            self.console.print(f"[dim]{workflow.description}[/dim]")
            self.console.print(f"[blue]任务数量: {len(workflow.tasks)}[/blue]\n")

            # 显示任务列表
            table = Table(title="任务列表")
            table.add_column("任务名称", style="cyan")
            table.add_column("Agent", style="green")
            table.add_column("Tools", style="yellow")
            table.add_column("依赖", style="magenta")

            for task in workflow.tasks:
                table.add_row(
                    task.name,
                    ", ".join(task.agent) if task.agent else "-",
                    ", ".join(task.tools) if task.tools else "-",
                    ", ".join(task.depends_on) if task.depends_on else "-",
                )

            self.console.print(table)

        except Exception as e:
            self.console.print(f"[red]验证失败: {e}[/red]")
            sys.exit(1)

    def list(self):
        """列出可用的工作流。"""
        # 查找内置工作流目录
        builtin_dir = Path(__file__).parent.parent / "taskflow" / "workflows"

        if not builtin_dir.exists():
            self.console.print("[yellow]未找到内置工作流目录[/yellow]")
            return

        workflows = []
        for yaml_file in builtin_dir.glob("*.yaml"):
            try:
                parser = WorkflowParser()
                schema = parser.parse_file(str(yaml_file))
                workflow = schema.workflow
                workflows.append({
                    "name": workflow.name,
                    "description": workflow.description,
                    "tasks": len(workflow.tasks),
                    "file": yaml_file.name,
                })
            except Exception as e:
                self.console.print(f"[yellow]警告: 无法解析 {yaml_file.name}: {e}[/yellow]")

        if not workflows:
            self.console.print("[yellow]未找到可用的工作流[/yellow]")
            return

        # 创建表格
        table = Table(title="可用工作流")
        table.add_column("文件名", style="cyan")
        table.add_column("名称", style="green")
        table.add_column("任务数", justify="right")
        table.add_column("描述")

        for wf in workflows:
            table.add_row(
                wf["file"],
                wf["name"],
                str(wf["tasks"]),
                wf["description"],
            )

        self.console.print(table)

    def _print_result(self, result: dict):
        """打印执行结果。"""
        self.console.print("\n[green]工作流执行完成[/green]")

        if "checkpoint_id" in result:
            self.console.print(f"[blue]Checkpoint ID: {result['checkpoint_id']}[/blue]")

        if "task_results" in result:
            table = Table(title="任务执行结果")
            table.add_column("任务", style="cyan")
            table.add_column("状态", style="green")
            table.add_column("耗时", justify="right")

            for task_name, task_result in result["task_results"].items():
                status = task_result.get("status", "unknown")
                duration = task_result.get("duration", 0)
                status_style = "green" if status == "completed" else "red"
                table.add_row(
                    task_name,
                    f"[{status_style}]{status}[/{status_style}]",
                    f"{duration:.2f}s",
                )

            self.console.print(table)
