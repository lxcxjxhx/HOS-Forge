"""HOS-Forge CLI 主入口。"""

import argparse
import sys
from pathlib import Path

from .taskflow_cmd import TaskflowCommand
from .personality_cmd import PersonalityCommand
from .mcp_cmd import MCPCommand


def main():
    """HOS-Forge CLI 主函数。"""
    parser = argparse.ArgumentParser(
        prog="hos",
        description="HOS-Forge: AI Native Cybersecurity Engineering Platform",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 2.0.0",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # taskflow 子命令
    taskflow_parser = subparsers.add_parser("taskflow", help="Taskflow Engine commands")
    taskflow_subparsers = taskflow_parser.add_subparsers(dest="subcommand")

    # taskflow run
    run_parser = taskflow_subparsers.add_parser("run", help="Run a workflow")
    run_parser.add_argument("workflow", type=str, help="Path to workflow YAML file")
    run_parser.add_argument("--checkpoint", action="store_true", help="Enable checkpoint/resume")
    run_parser.add_argument("--resume", type=str, help="Resume from checkpoint ID")

    # taskflow list
    taskflow_subparsers.add_parser("list", help="List available workflows")

    # personality 子命令
    personality_parser = subparsers.add_parser("personality", help="Personality system commands")
    personality_subparsers = personality_parser.add_subparsers(dest="subcommand")

    # personality list
    personality_subparsers.add_parser("list", help="List available personalities")

    # mcp 子命令
    mcp_parser = subparsers.add_parser("mcp", help="MCP Hub commands")
    mcp_subparsers = mcp_parser.add_subparsers(dest="subcommand")

    # mcp list
    mcp_subparsers.add_parser("list", help="List available MCP servers")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    # 分发命令
    if args.command == "taskflow":
        cmd = TaskflowCommand()
        if args.subcommand == "run":
            cmd.run(args.workflow, checkpoint=args.checkpoint, resume=args.resume)
        elif args.subcommand == "list":
            cmd.list()
        else:
            taskflow_parser.print_help()

    elif args.command == "personality":
        cmd = PersonalityCommand()
        if args.subcommand == "list":
            cmd.list()
        else:
            personality_parser.print_help()

    elif args.command == "mcp":
        cmd = MCPCommand()
        if args.subcommand == "list":
            cmd.list()
        else:
            mcp_parser.print_help()


if __name__ == "__main__":
    main()
