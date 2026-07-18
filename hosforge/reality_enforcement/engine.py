"""
HOS-Silly-Mock: 4-Layer Enforcement Engine (Python)

主引擎 — 协调 4 层检测器，汇总结果，生成 Reality Score。
"""

from __future__ import annotations

from hosforge.reality_enforcement.types import EnforcementResult, Finding
from hosforge.reality_enforcement.config import EnforcementConfig, DEFAULT_CONFIG
from hosforge.reality_enforcement.scorer import build_result
from hosforge.reality_enforcement.detectors.mock_detector import detect_mock_leakage
from hosforge.reality_enforcement.detectors.regex_detector import detect_regex_abuse
from hosforge.reality_enforcement.detectors.reality_binder import detect_reality_binding
from hosforge.reality_enforcement.detectors.silent_failure import detect_silent_failure


def enforce(file_path: str, config: EnforcementConfig = DEFAULT_CONFIG) -> EnforcementResult:
    """
    分析单个文件。

    Args:
        file_path: 文件绝对路径
        config: 检测配置

    Returns:
        EnforcementResult: 检测结果
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    lines = content.splitlines()
    return analyze_lines(file_path, lines, config)


def enforce_text(
    lines: list[str],
    filename: str = '<anonymous>',
    config: EnforcementConfig = DEFAULT_CONFIG,
) -> EnforcementResult:
    """
    分析已分割的代码行数组。

    Args:
        lines: 代码行数组
        filename: 文件名（用于报告）
        config: 检测配置

    Returns:
        EnforcementResult: 检测结果
    """
    return analyze_lines(filename, lines, config)


def analyze_lines(
    file: str,
    lines: list[str],
    config: EnforcementConfig = DEFAULT_CONFIG,
) -> EnforcementResult:
    """
    核心分析逻辑 — 依次运行 4 层检测。
    """
    all_findings: list[Finding] = []

    # Layer 1: MOCK 显性化检测
    mock_findings = detect_mock_leakage(file, lines, config)
    all_findings.extend(mock_findings)

    # Layer 2: Regex 滥用检测
    regex_findings = detect_regex_abuse(file, lines, config)
    all_findings.extend(regex_findings)

    # Layer 3: Reality Binding 检测
    binding_findings = detect_reality_binding(file, lines, config)
    all_findings.extend(binding_findings)

    # Layer 4: Silent Failure 检测
    silent_findings = detect_silent_failure(file, lines, config)
    all_findings.extend(silent_findings)

    return build_result(all_findings)
