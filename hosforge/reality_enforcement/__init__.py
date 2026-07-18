"""
HOS-Forge Reality Enforcement Layer — HOS-Silly-Mock Python 引擎。

反假数据/反正则滥用/反沉默失败的"真实强制执行层"。

4 层防御:
    Layer 1: Mock Exposure   — MOCK 显性化强制
    Layer 2: Regex Blocker   — 结构化数据 Regex 禁止
    Layer 3: Reality Binding — 变量 Source→Transform→Sink 强制
    Layer 4: Silent Failure  — 沉默失败检测
"""

from hosforge.reality_enforcement.config import EnforcementConfig, DEFAULT_CONFIG
from hosforge.reality_enforcement.types import (
    Finding,
    LayerId,
    FindingType,
    RiskLevel,
    SourceTransformSink,
    EnforcementResult,
)
from hosforge.reality_enforcement.engine import (
    enforce,
    enforce_text,
    analyze_lines,
)
from hosforge.reality_enforcement.scorer import build_result, calculate_reality_score
from hosforge.reality_enforcement.detectors.mock_detector import (
    detect_mock_leakage,
    has_mock_annotation,
    has_mock_name,
    is_catch_to_mock,
    is_large_static_data,
)
from hosforge.reality_enforcement.detectors.regex_detector import (
    detect_regex_abuse,
    contains_regex_literal,
    is_structural_context,
)
from hosforge.reality_enforcement.detectors.reality_binder import (
    detect_reality_binding,
    trace_variable,
    has_io,
)
from hosforge.reality_enforcement.detectors.silent_failure import (
    detect_silent_failure,
    is_empty_catch,
    has_error_path,
    is_no_io_system,
)

__all__ = [
    'EnforcementConfig',
    'DEFAULT_CONFIG',
    'Finding',
    'LayerId',
    'FindingType',
    'RiskLevel',
    'SourceTransformSink',
    'EnforcementResult',
    'enforce',
    'enforce_text',
    'analyze_lines',
    'build_result',
    'calculate_reality_score',
    'detect_mock_leakage',
    'has_mock_annotation',
    'has_mock_name',
    'is_catch_to_mock',
    'is_large_static_data',
    'detect_regex_abuse',
    'contains_regex_literal',
    'is_structural_context',
    'detect_reality_binding',
    'trace_variable',
    'has_io',
    'detect_silent_failure',
    'is_empty_catch',
    'has_error_path',
    'is_no_io_system',
]
