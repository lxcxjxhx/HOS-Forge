#!/usr/bin/env python3
"""HOS-Forge 命令行入口，提供 skill 子命令组和其他命令。"""

import argparse
import json
import sys
from typing import Any, Dict, List, Optional

from hosforge.skills import SkillRegistry
from hosforge.skills.marketplace import MarketplaceClient
from hosforge.skills.security import (
    GitHubIntegrationSkill,
    NucleiScanSkill,
    SemgrepScanSkill,
)


def create_default_registry() -> SkillRegistry:
    """创建并初始化默认的 SkillRegistry，注册所有内置 skills。

    Returns:
        初始化完成的 SkillRegistry 实例
    """
    registry = SkillRegistry()
    registry.register(GitHubIntegrationSkill())
    registry.register(SemgrepScanSkill())
    registry.register(NucleiScanSkill())
    return registry


def format_skill_list_table(skills: List[Any]) -> str:
    """将 skill 列表格式化为表格字符串。

    Args:
        skills: Skill 实例列表

    Returns:
        格式化后的表格字符串
    """
    if not skills:
        return "No skills registered."

    # 计算列宽
    name_width = max(len(s.name) for s in skills)
    name_width = max(name_width, 4)  # 最小宽度为 "Name" 的长度
    desc_width = 50  # 描述列固定宽度

    lines = []
    header = f"{'Name':<{name_width}}  {'Description':<{desc_width}}  Parameters"
    lines.append(header)
    lines.append("-" * len(header))

    for skill in skills:
        params = ", ".join(skill.parameters.get("properties", {}).keys())
        if len(params) > 30:
            params = params[:27] + "..."
        desc = skill.description[:desc_width]
        lines.append(f"{skill.name:<{name_width}}  {desc:<{desc_width}}  {params}")

    return "\n".join(lines)


def format_skill_list_json(skills: List[Any]) -> str:
    """将 skill 列表格式化为 JSON 字符串。

    Args:
        skills: Skill 实例列表

    Returns:
        格式化后的 JSON 字符串
    """
    data = []
    for skill in skills:
        data.append({
            "name": skill.name,
            "description": skill.description,
            "parameters": skill.parameters,
        })
    return json.dumps(data, indent=2, ensure_ascii=False)


def format_skill_info_json(skill: Any) -> str:
    """将 skill 详细信息格式化为 JSON 字符串。

    Args:
        skill: Skill 实例

    Returns:
        格式化后的 JSON 字符串
    """
    data = {
        "name": skill.name,
        "description": skill.description,
        "parameters": skill.parameters,
        "examples": _generate_skill_examples(skill),
    }
    return json.dumps(data, indent=2, ensure_ascii=False)


def format_skill_info_table(skill: Any) -> str:
    """将 skill 详细信息格式化为表格字符串。

    Args:
        skill: Skill 实例

    Returns:
        格式化后的表格字符串
    """
    lines = []
    lines.append(f"Name: {skill.name}")
    lines.append(f"Description: {skill.description}")
    lines.append("")
    lines.append("Parameters:")

    if skill.parameters:
        props = skill.parameters.get("properties", {})
        required = skill.parameters.get("required", [])

        if props:
            for param_name, param_info in props.items():
                param_type = param_info.get("type", "any")
                param_desc = param_info.get("description", "")
                is_required = " (required)" if param_name in required else ""
                lines.append(f"  - {param_name}: {param_type}{is_required}")
                if param_desc:
                    lines.append(f"    {param_desc}")
        else:
            lines.append("  No parameters defined.")
    else:
        lines.append("  No parameters defined.")

    lines.append("")
    lines.append("Examples:")
    examples = _generate_skill_examples(skill)
    for i, example in enumerate(examples, 1):
        lines.append(f"  {i}. {example}")

    return "\n".join(lines)


def _generate_skill_examples(skill: Any) -> List[str]:
    """为 skill 生成使用示例。

    Args:
        skill: Skill 实例

    Returns:
        示例字符串列表
    """
    examples = []

    if skill.name == "github_integration":
        examples = [
            "hos skill run github_integration action=create_issue repo=owner/repo title='Bug report'",
            "hos skill run github_integration action=list_issues repo=owner/repo state=open",
        ]
    elif skill.name == "semgrep_scan":
        examples = [
            "hos skill run semgrep_scan path=./src",
            "hos skill run semgrep_scan path=./src language=python config=auto",
        ]
    elif skill.name == "nuclei_scan":
        examples = [
            "hos skill run nuclei_scan target=https://example.com",
            "hos skill run nuclei_scan target=https://example.com severity=high",
        ]
    else:
        # 通用示例
        props = skill.parameters.get("properties", {})
        if props:
            params = " ".join(f"{k}=<value>" for k in list(props.keys())[:2])
            examples.append(f"hos skill run {skill.name} {params}")
        else:
            examples.append(f"hos skill run {skill.name}")

    return examples


def cmd_skill_list(args: argparse.Namespace) -> int:
    """执行 skill list 命令。

    Args:
        args: 解析后的命令行参数

    Returns:
        退出码（0 表示成功）
    """
    registry = create_default_registry()
    skills = registry.list_skills()

    if args.format == "json":
        print(format_skill_list_json(skills))
    else:
        print(format_skill_list_table(skills))

    return 0


def cmd_skill_info(args: argparse.Namespace) -> int:
    """执行 skill info 命令。

    Args:
        args: 解析后的命令行参数

    Returns:
        退出码（0 表示成功，1 表示 skill 不存在）
    """
    registry = create_default_registry()
    skill = registry.get(args.skill_name)

    if skill is None:
        print(f"Error: Skill '{args.skill_name}' not found.", file=sys.stderr)
        return 1

    if args.format == "json":
        print(format_skill_info_json(skill))
    else:
        print(format_skill_info_table(skill))

    return 0


def parse_skill_args(args: List[str]) -> Dict[str, Any]:
    """解析 skill 运行参数，将 key=value 格式转换为字典。

    Args:
        args: 参数列表，格式为 ["key1=value1", "key2=value2", ...]

    Returns:
        解析后的参数字典
    """
    result = {}
    for arg in args:
        if "=" not in arg:
            raise ValueError(f"Invalid argument format: {arg}. Expected key=value")
        key, value = arg.split("=", 1)

        # 尝试解析 JSON 值（支持数组、对象等）
        try:
            parsed_value = json.loads(value)
            result[key] = parsed_value
        except json.JSONDecodeError:
            # 如果不是 JSON，作为字符串处理
            result[key] = value

    return result


def cmd_skill_run(args: argparse.Namespace) -> int:
    """执行 skill run 命令。

    Args:
        args: 解析后的命令行参数

    Returns:
        退出码（0 表示成功，1 表示执行失败）
    """
    registry = create_default_registry()

    try:
        skill_args = parse_skill_args(args.args or [])
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    result = registry.execute_skill(args.skill_name, **skill_args)

    if result.success:
        print("Success!")
        if result.data:
            print(json.dumps(result.data, indent=2, ensure_ascii=False))
        return 0
    else:
        print(f"Error: {result.error}", file=sys.stderr)
        return 1


def cmd_taskflow(args: argparse.Namespace) -> int:
    """执行 taskflow 命令（保留兼容性）。

    Args:
        args: 解析后的命令行参数

    Returns:
        退出码
    """
    print("Taskflow command - not yet implemented")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """执行 validate 命令（保留兼容性）。

    Args:
        args: 解析后的命令行参数

    Returns:
        退出码
    """
    print("Validate command - not yet implemented")
    return 0


def cmd_skill_market_list(args: argparse.Namespace) -> int:
    """执行 skill market list 命令。

    Args:
        args: 解析后的命令行参数

    Returns:
        退出码
    """
    client = MarketplaceClient()
    skills = client.list_remote_skills()

    if args.format == "json":
        print(json.dumps([s.to_dict() for s in skills], indent=2, ensure_ascii=False))
    else:
        if not skills:
            print("No remote skills available.")
            return 0

        name_width = max(len(s.name) for s in skills)
        name_width = max(name_width, 4)
        desc_width = 50

        lines = []
        header = f"{'Name':<{name_width}}  {'Version':<10}  {'Description':<{desc_width}}  Downloads"
        lines.append(header)
        lines.append("-" * len(header))

        for skill in skills:
            version = skill.latest_version.version if skill.latest_version else "-"
            desc = skill.description[:desc_width]
            lines.append(f"{skill.name:<{name_width}}  {version:<10}  {desc:<{desc_width}}  {skill.download_count}")

        print("\n".join(lines))

    return 0


def cmd_skill_market_install(args: argparse.Namespace) -> int:
    """执行 skill market install 命令。

    Args:
        args: 解析后的命令行参数

    Returns:
        退出码
    """
    client = MarketplaceClient()
    result = client.install_skill(args.name, version=getattr(args, "version", None))

    if result["success"]:
        print(result["message"])
        return 0
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        return 1


def cmd_skill_market_uninstall(args: argparse.Namespace) -> int:
    """执行 skill market uninstall 命令。

    Args:
        args: 解析后的命令行参数

    Returns:
        退出码
    """
    client = MarketplaceClient()
    result = client.uninstall_skill(args.name)

    if result["success"]:
        print(result["message"])
        return 0
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        return 1


def cmd_skill_market_search(args: argparse.Namespace) -> int:
    """执行 skill market search 命令。

    Args:
        args: 解析后的命令行参数

    Returns:
        退出码
    """
    client = MarketplaceClient()
    skills = client.search_skills(args.query)

    if args.format == "json":
        print(json.dumps([s.to_dict() for s in skills], indent=2, ensure_ascii=False))
    else:
        if not skills:
            print(f"No skills found matching '{args.query}'.")
            return 0

        name_width = max(len(s.name) for s in skills)
        name_width = max(name_width, 4)
        desc_width = 50

        lines = []
        header = f"{'Name':<{name_width}}  {'Version':<10}  {'Description':<{desc_width}}  Rating"
        lines.append(header)
        lines.append("-" * len(header))

        for skill in skills:
            version = skill.latest_version.version if skill.latest_version else "-"
            desc = skill.description[:desc_width]
            rating = f"{skill.rating:.1f}" if skill.rating else "-"
            lines.append(f"{skill.name:<{name_width}}  {version:<10}  {desc:<{desc_width}}  {rating}")

        print("\n".join(lines))

    return 0


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器。

    Returns:
        配置完成的 ArgumentParser 实例
    """
    parser = argparse.ArgumentParser(
        prog="hos",
        description="HOS-Forge CLI - 安全工具集成和任务编排",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # skill 子命令组
    skill_parser = subparsers.add_parser("skill", help="Skill 管理命令")
    skill_subparsers = skill_parser.add_subparsers(dest="skill_command", help="Skill 子命令")

    # skill list
    list_parser = skill_subparsers.add_parser("list", help="列出所有已注册的 skills")
    list_parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="输出格式 (默认: table)",
    )

    # skill info
    info_parser = skill_subparsers.add_parser("info", help="显示指定 skill 的详细信息")
    info_parser.add_argument("skill_name", help="Skill 名称")
    info_parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="输出格式 (默认: table)",
    )

    # skill run
    run_parser = skill_subparsers.add_parser("run", help="执行指定 skill")
    run_parser.add_argument("skill_name", help="Skill 名称")
    run_parser.add_argument(
        "args",
        nargs="*",
        help="Skill 参数，格式: key=value",
    )

    # skill market 子命令组
    market_parser = skill_subparsers.add_parser("market", help="Skill 市场管理命令")
    market_subparsers = market_parser.add_subparsers(dest="market_command", help="Skill 市场子命令")

    # skill market list
    market_list_parser = market_subparsers.add_parser("list", help="列出所有可用的远程 skills")
    market_list_parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="输出格式 (默认: table)",
    )

    # skill market install
    market_install_parser = market_subparsers.add_parser("install", help="安装指定的远程 skill")
    market_install_parser.add_argument("name", help="Skill 名称")
    market_install_parser.add_argument("--version", help="指定版本（可选）")

    # skill market uninstall
    market_uninstall_parser = market_subparsers.add_parser("uninstall", help="卸载指定的远程 skill")
    market_uninstall_parser.add_argument("name", help="Skill 名称")

    # skill market search
    market_search_parser = market_subparsers.add_parser("search", help="搜索远程 skills")
    market_search_parser.add_argument("query", help="搜索关键词")
    market_search_parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="输出格式 (默认: table)",
    )

    # taskflow 命令（保留兼容性）
    taskflow_parser = subparsers.add_parser("taskflow", help="任务流管理")
    taskflow_parser.add_argument("taskflow_args", nargs="*", help="任务流参数")

    # validate 命令（保留兼容性）
    validate_parser = subparsers.add_parser("validate", help="验证配置或数据")
    validate_parser.add_argument("validate_args", nargs="*", help="验证参数")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """CLI 主入口函数。

    Args:
        argv: 命令行参数列表，None 表示使用 sys.argv

    Returns:
        退出码（0 表示成功）
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "skill":
        if args.skill_command is None:
            parser.parse_args(["skill", "--help"])
            return 0

        if args.skill_command == "list":
            return cmd_skill_list(args)
        elif args.skill_command == "info":
            return cmd_skill_info(args)
        elif args.skill_command == "run":
            return cmd_skill_run(args)
        elif args.skill_command == "market":
            if getattr(args, "market_command", None) is None:
                parser.parse_args(["skill", "market", "--help"])
                return 0
            if args.market_command == "list":
                return cmd_skill_market_list(args)
            elif args.market_command == "install":
                return cmd_skill_market_install(args)
            elif args.market_command == "uninstall":
                return cmd_skill_market_uninstall(args)
            elif args.market_command == "search":
                return cmd_skill_market_search(args)

    elif args.command == "taskflow":
        return cmd_taskflow(args)

    elif args.command == "validate":
        return cmd_validate(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
