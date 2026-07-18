"""
HOS-Forge CI CLI — 安全质量门禁命令行工具。

用法:
    python -m hosforge.ci check-reality [files...]
    python -m hosforge.ci check-sast [path]
    python -m hosforge.ci install-hook
    python -m hosforge.ci ci-scan
"""

from __future__ import annotations

import asyncio
import sys

from hosforge.ci.check import (
    generate_precommit_hook,
    run_reality_check,
    run_sast_scan,
)


def main() -> None:
    """CLI 入口"""
    if len(sys.argv) < 2:
        print('用法:')
        print('  python -m hosforge.ci check-reality [files...]')
        print('  python -m hosforge.ci check-sast [path]')
        print('  python -m hosforge.ci install-hook')
        print('  python -m hosforge.ci ci-scan')
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    if command == 'check-reality':
        result = asyncio.run(run_reality_check(args if args else None))
        print(f'Reality Check: {"✅ PASS" if result["passed"] else "❌ FAIL"}')
        print(f'Files scanned: {result["files_scanned"]}')

    elif command == 'check-sast':
        path = args[0] if args else '.'
        result = asyncio.run(run_sast_scan(path))
        print(f'SAST Scan: {"✅ PASS" if result["passed"] else "❌ FAIL"}')
        print(f'Findings: {result["findings"]}')

    elif command == 'install-hook':
        path = args[0] if args else '.git/hooks/pre-commit'
        generate_precommit_hook(path)
        print(f'Pre-commit hook installed: {path}')

    elif command == 'ci-scan':
        print('=== HOS-Forge CI Security Scan ===')
        reality = asyncio.run(run_reality_check())
        sast = asyncio.run(run_sast_scan())
        print(f'\nReality Score: {"✅" if reality["passed"] else "❌"} ')
        print(f'SAST Scan: {"✅" if sast["passed"] else "❌"} ({sast["findings"]} findings)')
        sys.exit(0 if (reality['passed'] and sast['passed']) else 1)

    else:
        print(f'Unknown command: {command}')
        sys.exit(1)


if __name__ == '__main__':
    main()
