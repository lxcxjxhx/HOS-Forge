"""
HOS-Silly-Mock: 配置定义 — 4 层检测的详细配置和默认值。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MockDetectionOptions:
    """MOCK 模式检测配置"""
    check_catch_fallback: bool = True
    check_unannotated_data: bool = True
    check_naming_convention: bool = True
    large_data_threshold: int = 3


@dataclass
class RegexDetectionOptions:
    """Regex 检测配置"""
    check_json_parsing: bool = True
    check_html_parsing: bool = True
    check_xml_parsing: bool = True
    check_url_parsing: bool = True


@dataclass
class BindingOptions:
    """Reality Binding 检测配置"""
    check_source: bool = True
    check_sink: bool = True
    check_transform_input: bool = True


@dataclass
class SilentFailureOptions:
    """Silent Failure 检测配置"""
    check_empty_catch: bool = True
    check_missing_error_path: bool = True
    check_no_io_system: bool = True


@dataclass
class EnforcementConfig:
    """整体引擎配置"""
    mock: MockDetectionOptions = field(default_factory=MockDetectionOptions)
    regex: RegexDetectionOptions = field(default_factory=RegexDetectionOptions)
    binding: BindingOptions = field(default_factory=BindingOptions)
    silent: SilentFailureOptions = field(default_factory=SilentFailureOptions)
    score_threshold: int = 50
    allow_test_exemption: bool = True
    test_exemption_marker: str = '@silly-mock:allow'
    allowed_mock_markers: list[str] = field(default_factory=lambda: [
        'MOCK_MODE: TRUE',
        'MOCK_MODE:TRUE',
        '@silly-mock:allow',
    ])


DEFAULT_CONFIG = EnforcementConfig()
