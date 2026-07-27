#!/usr/bin/env python3
"""
HOS-Forge 端到端演示脚本

演示如何使用 HOS-Forge 的 Taskflow Engine 执行安全扫描工作流。
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from hosforge.taskflow import WorkflowParser, WorkflowExecutor
from rich.console import Console

console = Console()


async def demo_basic_workflow():
    """演示基本工作流执行。"""
    console.print("\n[bold cyan]=== HOS-Forge Taskflow 演示 ===[/bold cyan]\n")

    # 1. 加载演示工作流
    demo_workflow = Path(__file__).parent / "examples" / "workflows" / "demo_quick_scan.yaml"
    console.print(f"[blue]加载工作流:[/blue] {demo_workflow}")

    parser = WorkflowParser()
    schema = parser.parse_file(str(demo_workflow))
    workflow = schema.workflow

    console.print(f"[green]工作流名称:[/green] {workflow.name}")
    console.print(f"[dim]{workflow.description}[/dim]")
    console.print(f"[blue]任务数量:[/blue] {len(workflow.tasks)}\n")

    # 2. 显示任务列表
    console.print("[bold]任务列表:[/bold]")
    for i, task in enumerate(workflow.tasks, 1):
        console.print(f"  {i}. [cyan]{task.name}[/cyan]")
        console.print(f"     Agent: {', '.join(task.agent)}")
        console.print(f"     Tools: {', '.join(task.tools) if task.tools else 'None'}")
        console.print(f"     依赖: {', '.join(task.depends_on) if task.depends_on else 'None'}")
        console.print(f"     [dim]{task.description}[/dim]\n")

    # 3. 执行工作流
    console.print("[yellow]开始执行工作流...[/yellow]\n")
    executor = WorkflowExecutor(workflow, enable_checkpoint=False)

    try:
        result = await executor.execute()

        # 4. 显示结果
        console.print("\n[bold green]工作流执行完成[/bold green]\n")

        if "task_results" in result:
            console.print("[bold]任务执行结果:[/bold]")
            for task_name, task_result in result["task_results"].items():
                status = task_result.get("status", "unknown")
                duration = task_result.get("duration", 0)
                status_icon = "✓" if status == "completed" else "✗"
                status_color = "green" if status == "completed" else "red"

                console.print(
                    f"  [{status_color}]{status_icon}[/{status_color}] "
                    f"[cyan]{task_name}[/cyan] - "
                    f"[{status_color}]{status}[/{status_color}] - "
                    f"[dim]{duration:.2f}s[/dim]"
                )

        console.print("\n[bold green]✓ 演示完成[/bold green]\n")

    except Exception as e:
        console.print(f"\n[red]执行失败: {e}[/red]\n")
        return 1

    return 0


async def demo_registry():
    """演示 Agent/Tool Registry 功能。"""
    console.print("\n[bold cyan]=== Agent/Tool Registry 演示 ===[/bold cyan]\n")

    from hosforge.taskflow.registry import (
        list_available_agents,
        list_available_tools,
        get_agent,
        get_tool,
    )

    # 1. 列出可用的 Agent
    console.print("[bold]可用的 Agent:[/bold]")
    agents = list_available_agents()
    for agent_name in agents:
        console.print(f"  • [green]{agent_name}[/green]")

    # 2. 列出可用的 Tool
    console.print("\n[bold]可用的 Tool:[/bold]")
    tools = list_available_tools()
    for tool_name in tools:
        console.print(f"  • [yellow]{tool_name}[/yellow]")

    # 3. 演示实例化 Agent
    console.print("\n[bold]实例化 Agent 演示:[/bold]")
    try:
        audit_agent = get_agent("sast_agent")
        console.print(f"  ✓ 成功创建 sast_agent: {audit_agent.name}")
    except Exception as e:
        console.print(f"  ✗ 创建 sast_agent 失败: {e}")

    # 4. 演示实例化 Tool
    console.print("\n[bold]实例化 Tool 演示:[/bold]")
    try:
        semgrep_tool = get_tool("semgrep")
        console.print(f"  ✓ 成功创建 semgrep tool: {semgrep_tool.name}")
    except Exception as e:
        console.print(f"  ✗ 创建 semgrep tool 失败: {e}")

    console.print("\n[bold green]✓ Registry 演示完成[/bold green]\n")
    return 0


def main():
    """主函数。"""
    console.print("\n[bold]HOS-Forge 端到端演示[/bold]\n")
    console.print("本演示将展示以下功能:")
    console.print("  1. Taskflow Engine 工作流执行")
    console.print("  2. Agent/Tool Registry 功能")
    console.print()

    # 运行演示
    exit_code = 0

    try:
        # 演示 1: Registry 功能
        exit_code += asyncio.run(demo_registry())

        # 演示 2: 基本工作流
        exit_code += asyncio.run(demo_basic_workflow())

    except KeyboardInterrupt:
        console.print("\n[yellow]演示被用户中断[/yellow]\n")
        return 1
    except Exception as e:
        console.print(f"\n[red]演示失败: {e}[/red]\n")
        return 1

    if exit_code == 0:
        console.print("[bold green]🎉 所有演示完成！[/bold green]\n")
    else:
        console.print(f"[yellow]⚠ 部分演示失败 (exit_code={exit_code})[/yellow]\n")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
