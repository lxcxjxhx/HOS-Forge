"""
HOS-Silly-Mock — Layer 4: 沉默失败检测器 (Silent Failure Detector)

检测"完整但不真实"的系统：完整逻辑链但无真实 I/O、无错误处理、无 throw。
这是最关键的一层 — 检测 AI 制造的 silent demo system。
"""

from __future__ import annotations

import re
from hosforge.reality_enforcement.types import Finding, LayerId, FindingType, RiskLevel
from hosforge.reality_enforcement.config import EnforcementConfig, DEFAULT_CONFIG
from hosforge.reality_enforcement.detectors.reality_binder import has_io

# 错误处理关键词
ERROR_HANDLING_KEYWORDS = [
    'try', 'catch', 'throw', 'reject',
    'error', 'Error', 'err',
    'finally',
    '.catch(', '.then(',
    'onerror', 'onError',
    'recovery', 'retry', 'fallback',
    'warn', 'warning',
    'rejectWith', 'fail',
    'status !=', 'statusCode !=', 'code !=',
    'ok !=', 'ok =',
]


def is_empty_catch(lines: list[str], catch_line_idx: int) -> bool:
    """
    检查 catch 块是否为空（沉默失败）。
    """
    for i in range(catch_line_idx, min(catch_line_idx + 5, len(lines))):
        trimmed = lines[i].strip()
        # catch { } 在一行
        if re.match(r'^\}?\s*catch\s*(?:\([^)]*\))?\s*\{\s*\}$', trimmed):
            return True
        # catch 后直接是 }
        if trimmed == '}' and i == catch_line_idx + 1:
            return True
        # 跳过 { } 和 catch 行
        if trimmed in ('{', '}'):
            continue
        if re.match(r'^\}?\s*catch\s*(?:\([^)]*\))?\s*\{?\s*$', trimmed):
            continue
        # catch 块内只有注释或 console.log
        if trimmed and not trimmed.startswith('//') and not trimmed.startswith('*') and 'console.' not in trimmed:
            if trimmed in ('{', '}'):
                continue
            if not trimmed.strip():
                continue
            return False  # 有实际代码
    return True  # 没有找到实际代码


def find_matching_brace(lines: list[str], start_idx: int) -> int:
    """
    查找匹配的闭合大括号。
    """
    brace_count = 0
    started = False

    for i in range(start_idx, len(lines)):
        line = lines[i]
        for ch in line:
            if ch == '{':
                brace_count += 1
                started = True
            elif ch == '}':
                brace_count -= 1
        if started and brace_count == 0:
            return i

    return -1


def has_error_path(lines: list[str], func_start_idx: int) -> bool:
    """
    检查函数是否缺乏错误路径。
    """
    end_brace = find_matching_brace(lines, func_start_idx)
    if end_brace == -1:
        return False

    for i in range(func_start_idx, end_brace + 1):
        if any(kw in lines[i] for kw in ERROR_HANDLING_KEYWORDS):
            return True

    return False


def is_no_io_system(lines: list[str]) -> bool:
    """
    检查是否为"无 I/O 的完整系统"。
    """
    io_lines = [l for l in lines if has_io(l)]
    return len(io_lines) == 0


def detect_silent_failure(
    file: str,
    lines: list[str],
    config: EnforcementConfig = DEFAULT_CONFIG,
) -> list[Finding]:
    """
    Layer 4 检测入口 — Silent Failure 检测。

    检查:
        - 空 catch 块
        - 有 I/O 但无 error handling 的函数
        - 完整的"无 I/O"系统（最危险）
    """
    findings: list[Finding] = []
    opts = config.silent

    if not opts.check_empty_catch and not opts.check_missing_error_path and not opts.check_no_io_system:
        return findings

    # 检查空 catch 块
    if opts.check_empty_catch:
        for i, line in enumerate(lines):
            trimmed = line.strip()
            is_catch_line = trimmed.startswith('catch') or bool(re.match(r'^\}?\s*catch\s*\(', trimmed))
            if is_catch_line:
                if is_empty_catch(lines, i):
                    # 检查是否有 MOCK_MODE 豁免
                    prev_lines = lines[max(0, i - 3):i]
                    has_exemption = any('MOCK_MODE' in l or '@silly-mock' in l for l in prev_lines)
                    if not has_exemption:
                        findings.append(Finding(
                            layer=LayerId.SILENT,
                            type=FindingType.MISSING_ERROR_HANDLING,
                            severity=RiskLevel.HIGH,
                            file=file,
                            line=i + 1,
                            message='Empty catch block — error is silently swallowed',
                            snippet=lines[i].strip(),
                            suggestion='Add error handling: log the error, throw a meaningful exception, or implement recovery logic',
                        ))

    # 检查缺失 error path 的函数
    if opts.check_missing_error_path:
        for i, line in enumerate(lines):
            trimmed = line.strip()
            is_async_func = bool(
                re.match(r'^(?:async\s+)?(?:def|function)\s+\w+\s*\(', trimmed)
                or re.match(r'^(?:const|let|var)\s+\w+\s*=\s*(?:async\s+)?(?:def|function|lambda)\s*\(', trimmed)
                or re.match(r'^(?:const|let|var)\s+\w+\s*=\s*(?:async\s+)?\([^)]*\)\s*(?:=>|:)\s*\{', trimmed)
            )
            if not is_async_func:
                continue

            end_idx = find_matching_brace(lines, i)
            if end_idx == -1:
                continue

            func_lines = lines[i:end_idx + 1]
            has_real_io = any(has_io(l) for l in func_lines)

            if len(func_lines) < 5:
                continue
            if not has_real_io:
                continue

            if not has_error_path(lines, i):
                findings.append(Finding(
                    layer=LayerId.SILENT,
                    type=FindingType.SILENT_FAILURE,
                    severity=RiskLevel.HIGH,
                    file=file,
                    line=i + 1,
                    message='Function performs I/O but has no error handling path',
                    snippet=trimmed[:100] + '...' if len(trimmed) > 100 else trimmed,
                    suggestion='Add try-catch, error logging, and explicit error recovery or re-throw',
                ))

    # 检查"无 I/O 的完整系统"
    if opts.check_no_io_system and len(lines) >= 20:
        has_any_io = any(has_io(l) for l in lines)
        has_error_handling = any(
            any(kw in l for kw in ERROR_HANDLING_KEYWORDS)
            for l in lines
        )

        if not has_any_io and has_error_handling:
            func_count = sum(
                1 for l in lines
                if re.match(r'^(?:async\s+)?(?:def|function)\s+\w+\s*\(', l.strip())
                or re.match(r'^(?:const|let|var)\s+\w+\s*=\s*(?:async\s+)?\(', l.strip())
            )
            if func_count >= 2:
                findings.append(Finding(
                    layer=LayerId.SILENT,
                    type=FindingType.SILENT_FAILURE,
                    severity=RiskLevel.CRITICAL,
                    file=file,
                    line=1,
                    message='Potential silent fake system: complete logic chain with no I/O operations',
                    snippet=f'File has {func_count} function(s), error handling present, but 0 I/O operations',
                    suggestion='Add real data sources (API calls, file reads, database queries) or halt generation and request system boundary clarification',
                ))

        if not has_any_io and not has_error_handling and len(lines) >= 30:
            findings.append(Finding(
                layer=LayerId.SILENT,
                type=FindingType.SILENT_FAILURE,
                severity=RiskLevel.CRITICAL,
                file=file,
                line=1,
                message='⚠ SILENT MOCK SYSTEM DETECTED: no I/O, no error handling, but complete logic',
                snippet='Complete system with no external dependencies and no error paths',
                suggestion='HALT: This system has no connection to reality. Request real system boundaries before proceeding.',
            ))

    return findings
