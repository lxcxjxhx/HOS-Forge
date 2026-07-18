"""
HOS-Silly-Mock — Layer 2: Regex禁用反射器 (Regex Reflection Blocker)

检测正则表达式是否用于结构化数据解析（JSON/HTML/XML/CSV/URL）。
禁止 regex 用于结构化解析，强制使用标准解析器。
"""

from __future__ import annotations

import re
from hosforge.reality_enforcement.types import Finding, LayerId, FindingType, RiskLevel
from hosforge.reality_enforcement.config import EnforcementConfig, DEFAULT_CONFIG

# 结构化上下文的提示词
STRUCTURED_CONTEXT_INDICATORS = [
    'json', 'html', 'xml', 'csv', 'url',
    'querystring', 'query string', 'params', 'endpoint',
    'parse', 'serialize', 'tag', 'element',
    'div', 'span', 'soap', 'xsd',
    'json数据', 'html解析', 'xml解析', '日志解析',
]

# 高风险的 regex 模式
HIGH_RISK_REGEX_PATTERNS = [
    re.compile(r'["\']\w+["\']\s*:\s*["\'][^"\']*["\']'),  # JSON field
    re.compile(r'"name"\s*:'),
    re.compile(r'<[^>]*>'),
    re.compile(r'class=["\'][^"\']*["\']'),
    re.compile(r'id=["\'][^"\']*["\']'),
    re.compile(r'https?://'),
    re.compile(r'/api/'),
    re.compile(r'\?\w+='),
]

# Regex 字面量检测
REGEX_LITERAL_PATTERN = re.compile(r'(?<![=\/\w])/(?!\/)(?!\*)[^\n/]*/[gimsuyd]*')


def contains_regex_literal(line: str) -> bool:
    """检查行是否包含 regex 字面量"""
    return bool(REGEX_LITERAL_PATTERN.search(line))


def contains_new_regexp(line: str) -> bool:
    """检查行是否包含 new RegExp"""
    return 'new RegExp(' in line or 're.compile(' in line or 're.search(' in line or 're.match(' in line or 're.findall(' in line or 're.sub(' in line


def contains_regex_method(line: str) -> bool:
    """检查行是否包含 regex 方法调用"""
    return bool(re.search(r'\.(match|replace|split|exec|search)\s*\(', line))


def is_structural_context(line: str, prev_lines: list[str], next_lines: list[str]) -> bool:
    """检查行是否在结构化解析上下文中"""
    context = ' '.join([
        line.lower(),
        *[l.lower() for l in prev_lines[-3:]],
        *[l.lower() for l in next_lines[:2]],
    ])
    return any(indicator.lower() in context for indicator in STRUCTURED_CONTEXT_INDICATORS)


def is_high_risk_regex(line: str) -> bool:
    """检查 regex 模式是否高风险"""
    return any(p.search(line) for p in HIGH_RISK_REGEX_PATTERNS)


def suggest_replacement(line: str, context: str) -> str:
    """根据上下文推荐替代方案"""
    ctx_lower = context.lower()
    if 'json' in ctx_lower:
        return 'Use JSON.parse() + schema validation (e.g., Zod, pydantic) instead of regex'
    if 'html' in ctx_lower or '<' in line:
        return 'Use DOMParser / BeautifulSoup / lxml instead of regex for HTML parsing'
    if 'xml' in ctx_lower:
        return 'Use xml.etree / lxml / defusedxml instead of regex for XML parsing'
    if 'csv' in ctx_lower:
        return 'Use csv module / pandas instead of regex for CSV parsing'
    if 'url' in ctx_lower:
        return 'Use urllib.parse / URL constructor instead of regex'
    if 'log' in ctx_lower:
        return 'Use a structured log parser instead of regex'
    return 'Use a standard parser library specific to this data format instead of regex'


def detect_regex_abuse(
    file: str,
    lines: list[str],
    config: EnforcementConfig = DEFAULT_CONFIG,
) -> list[Finding]:
    """
    Layer 2 检测入口 — Regex 滥用检测。
    """
    findings: list[Finding] = []
    opts = config.regex

    any_enabled = opts.check_json_parsing or opts.check_html_parsing or opts.check_xml_parsing or opts.check_url_parsing
    if not any_enabled:
        return findings

    for i, line in enumerate(lines):
        trimmed = line.strip()
        # 跳过注释
        if trimmed.startswith('//') or trimmed.startswith('*') or trimmed.startswith('/*'):
            continue

        has_regex = contains_regex_literal(line) or contains_new_regexp(line) or contains_regex_method(line)
        if not has_regex:
            continue

        # 获取上下文
        prev_lines = lines[max(0, i - 3):i]
        next_lines = lines[i + 1:min(len(lines), i + 3)]
        context = ' '.join([line, *prev_lines, *next_lines])

        # 判断是否为结构化上下文
        if not is_structural_context(line, prev_lines, next_lines):
            continue

        # 判断配置
        ctx_lower = context.lower()
        is_json = 'json' in ctx_lower
        is_html = 'html' in ctx_lower or '<' in line
        is_xml = 'xml' in ctx_lower
        is_url = 'url' in ctx_lower

        if is_json and not opts.check_json_parsing:
            continue
        if is_html and not opts.check_html_parsing:
            continue
        if is_xml and not opts.check_xml_parsing:
            continue
        if is_url and not opts.check_url_parsing:
            continue

        severity = RiskLevel.HIGH if is_high_risk_regex(line) else RiskLevel.MEDIUM
        suggestion = suggest_replacement(line, context)

        data_type = 'JSON' if is_json else 'HTML' if is_html else 'XML' if is_xml else 'URL' if is_url else 'structured data'

        findings.append(Finding(
            layer=LayerId.REGEX,
            type=FindingType.REGEX_ABUSE,
            severity=severity,
            file=file,
            line=i + 1,
            message=f'Regex used for {data_type} parsing — use standard parser instead',
            snippet=line[:100] + '...' if len(line) > 100 else line,
            suggestion=suggestion,
        ))

    return findings
