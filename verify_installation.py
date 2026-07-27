#!/usr/bin/env python3
"""
HOS-Forge 端到端安装验证脚本

验证安装流程、CLI命令和基本功能是否正常工作。
"""

import sys
import subprocess
import shutil
from pathlib import Path


def run_command(cmd: list[str], check: bool = True) -> tuple[bool, str]:
    """运行命令并返回结果。"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            check=check,
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, f"Command failed: {e}\n{e.stderr}"
    except FileNotFoundError:
        return False, f"Command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return False, "Command timed out"


def check_python_version() -> bool:
    """检查Python版本是否满足要求（>=3.12）。"""
    print("✓ 检查Python版本...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 12):
        print(f"  ✗ Python版本过低: {version.major}.{version.minor} (需要 >= 3.12)")
        return False
    print(f"  ✓ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_pip_available() -> bool:
    """检查pip是否可用。"""
    print("\n✓ 检查pip...")
    success, output = run_command([sys.executable, "-m", "pip", "--version"], check=False)
    if success:
        print(f"  ✓ {output.strip()}")
        return True
    else:
        print("  ✗ pip不可用")
        return False


def check_hos_installed() -> bool:
    """检查hos命令是否已安装。"""
    print("\n✓ 检查hos命令...")
    hos_path = shutil.which("hos")
    if hos_path:
        print(f"  ✓ hos已安装: {hos_path}")
        return True
    else:
        print("  ✗ hos命令未找到")
        return False


def check_hos_version() -> bool:
    """检查hos版本。"""
    print("\n✓ 检查hos版本...")
    success, output = run_command(["hos", "--version"], check=False)
    if success:
        print(f"  ✓ {output.strip()}")
        return True
    else:
        print(f"  ✗ 无法获取版本: {output}")
        return False


def check_hos_help() -> bool:
    """检查hos帮助信息。"""
    print("\n✓ 检查hos帮助...")
    success, output = run_command(["hos", "--help"], check=False)
    if success and "taskflow" in output:
        print("  ✓ 帮助信息正常")
        return True
    else:
        print("  ✗ 帮助信息异常")
        return False


def check_taskflow_list() -> bool:
    """检查taskflow list命令。"""
    print("\n✓ 检查taskflow list...")
    success, output = run_command(["hos", "taskflow", "list"], check=False)
    if success:
        print("  ✓ taskflow list命令正常")
        return True
    else:
        print(f"  ✗ taskflow list失败: {output}")
        return False


def check_taskflow_validate() -> bool:
    """检查taskflow validate命令。"""
    print("\n✓ 检查taskflow validate...")
    demo_workflow = Path(__file__).parent / "examples" / "workflows" / "demo_quick_scan.yaml"
    if not demo_workflow.exists():
        print(f"  ⚠ 演示工作流不存在: {demo_workflow}")
        return False

    success, output = run_command(
        ["hos", "taskflow", "validate", str(demo_workflow)],
        check=False
    )
    if success and "验证通过" in output:
        print("  ✓ taskflow validate命令正常")
        return True
    else:
        print(f"  ✗ taskflow validate失败: {output}")
        return False


def check_taskflow_dry_run() -> bool:
    """检查taskflow run --dry-run命令。"""
    print("\n✓ 检查taskflow run --dry-run...")
    demo_workflow = Path(__file__).parent / "examples" / "workflows" / "demo_quick_scan.yaml"
    if not demo_workflow.exists():
        print(f"  ⚠ 演示工作流不存在: {demo_workflow}")
        return False

    success, output = run_command(
        ["hos", "taskflow", "run", str(demo_workflow), "--dry-run"],
        check=False
    )
    if success and "验证通过" in output:
        print("  ✓ taskflow run --dry-run命令正常")
        return True
    else:
        print(f"  ✗ taskflow run --dry-run失败: {output}")
        return False


def check_python_imports() -> bool:
    """检查核心模块是否可导入。"""
    print("\n✓ 检查Python模块导入...")
    modules = [
        "hosforge.taskflow",
        "hosforge.taskflow.schema",
        "hosforge.taskflow.parser",
        "hosforge.taskflow.executor",
        "hosforge.taskflow.registry",
        "hosforge.security_agents.base",
        "hosforge.security_tools.base",
    ]

    all_ok = True
    for module in modules:
        try:
            __import__(module)
            print(f"  ✓ {module}")
        except ImportError as e:
            print(f"  ✗ {module}: {e}")
            all_ok = False

    return all_ok


def main():
    """主函数。"""
    print("=" * 60)
    print("HOS-Forge 端到端安装验证")
    print("=" * 60)

    checks = [
        ("Python版本", check_python_version),
        ("pip可用", check_pip_available),
        ("hos命令", check_hos_installed),
        ("hos版本", check_hos_version),
        ("hos帮助", check_hos_help),
        ("taskflow list", check_taskflow_list),
        ("taskflow validate", check_taskflow_validate),
        ("taskflow dry-run", check_taskflow_dry_run),
        ("Python模块", check_python_imports),
    ]

    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"  ✗ 检查失败: {e}")
            results.append((name, False))

    # 打印总结
    print("\n" + "=" * 60)
    print("验证结果总结")
    print("=" * 60)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {status} - {name}")

    print(f"\n总计: {passed}/{total} 项检查通过")

    if passed == total:
        print("\n🎉 所有检查通过！HOS-Forge安装成功！")
        return 0
    else:
        print(f"\n⚠ {total - passed} 项检查失败，请检查安装")
        return 1


if __name__ == "__main__":
    sys.exit(main())
