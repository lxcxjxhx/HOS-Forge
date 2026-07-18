"""
HOS-Silly-Mock — Layer 1: MOCK显性化强制器 (Mock Exposure Layer)

检测所有未经显式标注的 mock 数据。
任何 mock 必须标注 ⚠ MOCK_MODE: TRUE + reason 才被认为是合法的。
"""

from __future__ import annotations

import re
from hosforge.reality_enforcement.types import Finding, LayerId, FindingType, RiskLevel
from hosforge.reality_enforcement.config import EnforcementConfig, DEFAULT_CONFIG

# Mock 关键词列表
MOCK_INDICATORS = [
    'mock', 'fake', 'dummy', 'sample', 'demo', 'testData',
    'test_data', 'placeholder', 'stub', 'fixture',
]

# Catch → Mock 模式检测
CATCH_MOCK_PATTERNS = [
    re.compile(r'\.catch\s*\(\s*\(?\s*\)?\s*=>\s*\['),
    re.compile(r'\.catch\s*\(\s*\(?\s*\)?\s*=>\s*\d+'),
    re.compile(r'\.catch\s*\(\s*\(?\w*\)?\s*=>\s*\('),
]


def has_mock_annotation(line: str, markers: list[str] | None = None) -> bool:
    """
    检测单行是否包含 MOCK_MODE 标注。
    """
    if markers is None:
        markers = DEFAULT_CONFIG.allowed_mock_markers
    return any(m in line for m in markers)


def has_mock_name(variable_name: str) -> bool:
    """
    检测变量名是否暗示 mock。
    """
    name_lower = variable_name.lower()
    return any(indicator.lower() in name_lower for indicator in MOCK_INDICATORS)


def is_catch_to_mock(line: str) -> bool:
    """
    检查 catch → fallback 模式是否产生 mock。
    """
    return any(p.search(line) for p in CATCH_MOCK_PATTERNS)


def is_large_static_data(lines: list[str], start_idx: int, threshold: int) -> bool:
    """
    检测是否为大型静态数据（多行数组/对象）。
    """
    if start_idx >= len(lines):
        return False

    start = lines[start_idx].strip()
    # 检查是否为数组或对象字面量的开始
    is_array = bool(re.match(r'^(const|let|var)\s+\w+\s*=\s*\[\s*$', start))
    is_object = bool(re.match(r'^(const|let|var)\s+\w+\s*=\s*\{\s*$', start))

    if not is_array and not is_object:
        return False

    brace_count = 0
    line_count = 0
    in_string = False
    char_prev = ''

    for i in range(start_idx, len(lines)):
        line = lines[i]
        for ch in line:
            if ch in ('"', "'", '`'):
                if not in_string:
                    in_string = True
                elif char_prev != '\\':
                    in_string = False
            if not in_string:
                if ch in ('{', '['):
                    brace_count += 1
                if ch in ('}', ']'):
                    brace_count -= 1
            char_prev = ch

        line_count += 1
        if brace_count == 0 and line_count > 1:
            break
        if line_count > threshold * 2:
            return True

    return line_count > threshold


def detect_mock_leakage(
    file: str,
    lines: list[str],
    config: EnforcementConfig = DEFAULT_CONFIG,
) -> list[Finding]:
    """
    Layer 1 检测入口 — MOCK 泄漏检测。

    检查:
        - 无标注的 catch→fallback mock 数据
        - 变量名含 mock 关键词且有大型静态数据
        - 未标注的大型静态数据结构
    """
    findings: list[Finding] = []
    in_block_comment = False
    has_annotation_in_scope = False
    opts = config.mock

    for i, line in enumerate(lines):
        trimmed = line.strip()

        # 追踪块注释中的 MOCK_MODE 标注
        if trimmed.startswith('/*'):
            in_block_comment = True
            if has_mock_annotation(trimmed, config.allowed_mock_markers):
                has_annotation_in_scope = True
        if in_block_comment:
            if has_mock_annotation(trimmed, config.allowed_mock_markers):
                has_annotation_in_scope = True
            if '*/' in trimmed:
                in_block_comment = False
                continue
            continue

        # 单行注释检查标注
        if trimmed.startswith('//') and has_mock_annotation(trimmed, config.allowed_mock_markers):
            has_annotation_in_scope = True

        # 跳过测试豁免标记
        if config.allow_test_exemption and config.test_exemption_marker in trimmed:
            has_annotation_in_scope = True
            continue

        # 检查 catch → fallback 模式
        if opts.check_catch_fallback and is_catch_to_mock(trimmed):
            if not has_annotation_in_scope:
                findings.append(Finding(
                    layer=LayerId.MOCK,
                    type=FindingType.MOCK_LEAKAGE,
                    severity=RiskLevel.HIGH,
                    file=file,
                    line=i + 1,
                    message='Catch block falls back to mock data without MOCK_MODE annotation',
                    snippet=trimmed[:80] + '...' if len(trimmed) > 80 else trimmed,
                    suggestion=(
                        'Add /**\n * MOCK_MODE: TRUE\n * reason: <explain why mock is needed>\n */ '
                        'before this catch block'
                    ),
                ))
            continue

        # 检查变量名中的 mock 关键词
        if opts.check_naming_convention:
            var_match = re.match(r'^(const|let|var)\s+(\w+)\s*=', trimmed)
            if var_match:
                var_name = var_match.group(2)
                if has_mock_name(var_name) and not has_annotation_in_scope:
                    has_large_data = False
                    if trimmed.endswith('{') or trimmed.endswith('['):
                        has_large_data = is_large_static_data(lines, i, opts.large_data_threshold)
                    elif i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line.startswith('[') or next_line.startswith('{'):
                            has_large_data = is_large_static_data(lines, i + 1, opts.large_data_threshold)

                    if has_large_data:
                        findings.append(Finding(
                            layer=LayerId.MOCK,
                            type=FindingType.MOCK_LEAKAGE,
                            severity=RiskLevel.MEDIUM,
                            file=file,
                            line=i + 1,
                            message=f'Variable "{var_name}" has mock-indicating name with large static data',
                            snippet=trimmed,
                            suggestion=(
                                f'Add MOCK_MODE annotation or rename "{var_name}" if it is real data'
                            ),
                        ))

        # 检查未标注的大型静态数据
        if opts.check_unannotated_data and not has_annotation_in_scope:
            if is_large_static_data(lines, i, opts.large_data_threshold):
                var_match = re.match(r'^(const|let|var)\s+(\w+)\s*=\s*[\[{]\s*$', lines[i])
                if var_match:
                    findings.append(Finding(
                        layer=LayerId.MOCK,
                        type=FindingType.MOCK_LEAKAGE,
                        severity=RiskLevel.LOW,
                        file=file,
                        line=i + 1,
                        message=f'Large static data structure without MOCK_MODE annotation: {var_match.group(2)}',
                        snippet=var_match.group(0),
                        suggestion=(
                            'If this is mock data, add /**\n * MOCK_MODE: TRUE\n * reason: ...\n */ before it'
                        ),
                    ))

        # 重置标注作用域
        if not trimmed.startswith('//') and not in_block_comment:
            if not trimmed or trimmed.endswith(';') or trimmed.endswith('}') or trimmed.endswith(')'):
                has_annotation_in_scope = False

    return findings
