"""
HOS-Silly-Mock — Layer 3: 真实连接强制器 (Reality Binding Layer)

强制每个变量必须绑定 source → transform → sink 三元组。
追踪数据流：检查 source（从哪里来）→ transform（如何转换）→ sink（用到哪里去）
"""

from __future__ import annotations

import re
from hosforge.reality_enforcement.types import Finding, LayerId, FindingType, RiskLevel, SourceTransformSink
from hosforge.reality_enforcement.config import EnforcementConfig, DEFAULT_CONFIG

# 常见 source 关键词（数据来源）
SOURCE_KEYWORDS = [
    'fetch', 'axios', 'request', 'get', 'post', 'put', 'delete',
    'query', 'find', 'findOne', 'findMany', 'findAll',
    'readFile', 'readdir', 'readFileSync',
    'from', 'fromAsync', 'of',
    'getItem', 'getJSON', 'getString',
    'select', 'selectAll', 'selectFrom',
    'listen', 'on', 'subscribe',
    'connect', 'pool', 'client',
    'import', 'require', 'load',
    'input', 'args', 'params', 'query',
    'req.', 'request.', 'event.', 'message.',
    'open(', 'openAsync(',
]

# 常见 sink 关键词（数据最终用途）
SINK_KEYWORDS = [
    'render', 'display', 'show', 'print', 'log',
    'writeFile', 'writeFileSync', 'appendFile',
    'send', 'response', 'res.', 'reply',
    'save', 'store', 'set', 'update', 'upsert',
    'emit', 'publish', 'broadcast',
    'return ', 'yield ',
    'setItem', 'setState',
    'insert', 'insertOne', 'insertMany',
    'create', 'createOne', 'createMany',
    'appendChild', 'innerHTML', 'textContent',
    'output', 'export', 'console.',
]

# 常见 transform 关键词
TRANSFORM_KEYWORDS = [
    'map', 'filter', 'reduce', 'flat', 'flatMap',
    'sort', 'reverse', 'slice', 'splice',
    'concat', 'join', 'split',
    'trim', 'toLowerCase', 'toUpperCase',
    'replace', 'replaceAll',
    'parse', 'stringify',
    'encode', 'decode',
    'format', 'normalize',
    'transform', 'convert',
    'validate', 'sanitize', 'clean',
]

# I/O 相关关键词
IO_KEYWORDS = [
    'fetch', 'axios', 'request',
    'readFile', 'writeFile', 'readdir', 'access',
    'connect', 'query', 'execute',
    'listen', 'createServer',
    'open', 'close',
    'stream', 'pipe',
    'import', 'require', 'load',
    'console.', 'process.',
    'socket', 'websocket', 'ws.',
]


def extract_assigned_var(line: str) -> str | None:
    """提取赋值语句的左侧变量名"""
    decl = re.match(r'^(?:const|let|var)\s+(\w+)\s*=', line)
    if decl:
        return decl.group(1)
    assign = re.match(r'^(\w+)\s*=\s*(?!>)', line)
    if assign:
        return assign.group(1)
    return None


def has_source(line: str) -> bool:
    """检查赋值语句的右侧是否有 source 来源"""
    rhs = re.sub(r'^(?:const|let|var)\s+\w+\s*=\s*', '', line)
    return any(kw in rhs for kw in SOURCE_KEYWORDS)


def has_sink(line: str) -> bool:
    """检查行内是否有 sink 用途"""
    return any(kw in line for kw in SINK_KEYWORDS)


def has_io(line: str) -> bool:
    """检查是否为 I/O 操作"""
    return any(kw in line for kw in IO_KEYWORDS)


def trace_variable(
    var_name: str,
    def_line: int,
    lines: list[str],
) -> SourceTransformSink:
    """
    检查一个变量是否有完整的 source → transform → sink。
    """
    result = SourceTransformSink(name=var_name)

    if def_line >= len(lines):
        return result

    def_line_content = lines[def_line]
    result.source = def_line_content.strip() if has_source(def_line_content) else None

    transforms: list[str] = []
    sink_lines: list[str] = []

    for i in range(def_line + 1, min(def_line + 20, len(lines))):
        line = lines[i]
        if not line or line.strip().startswith('//'):
            continue

        # 检查 transform
        is_transform = any(
            f'.{kw}(' in line
            for kw in TRANSFORM_KEYWORDS
        )
        if is_transform and var_name in line:
            transforms.append(line.strip())

        # 检查 sink
        if var_name in line and has_sink(line):
            sink_lines.append(line.strip())

        # 遇到新变量声明则停止
        if re.match(r'^(?:const|let|var)\s+\w+\s*=', line.strip()) and line != def_line_content:
            break

    result.transforms = transforms
    result.sink = sink_lines[0] if sink_lines else None
    result.complete = bool(result.source) and bool(result.sink)

    return result


def detect_reality_binding(
    file: str,
    lines: list[str],
    config: EnforcementConfig = DEFAULT_CONFIG,
) -> list[Finding]:
    """
    Layer 3 检测入口 — Reality Binding 检测。

    检查每个变量是否有完整的 source → transform → sink 链路。
    """
    findings: list[Finding] = []
    opts = config.binding

    if not opts.check_source and not opts.check_sink:
        return findings

    traced_vars: set[str] = set()
    simple_value_pattern = re.compile(
        r'^(?:const|let|var)\s+\w+\s*=\s*(?:true|false|null|undefined|\d+|\'[^\']*\'|"[^"]*")\s*;?$'
    )
    func_pattern = re.compile(
        r'^(?:const|let|var)\s+\w+\s*=\s*(?:async\s+)?(?:\(|function)'
    )

    for i, line in enumerate(lines):
        trimmed = line.strip()
        if trimmed.startswith('//') or not trimmed or trimmed.startswith('*'):
            continue

        var_name = extract_assigned_var(trimmed)
        if not var_name or var_name in traced_vars:
            continue

        # 跳过简单值类型赋值
        if simple_value_pattern.match(trimmed):
            continue
        # 跳过函数声明
        if func_pattern.match(trimmed):
            continue

        trace = trace_variable(var_name, i, lines)
        traced_vars.add(var_name)

        if not trace.complete:
            if not trace.source and opts.check_source:
                findings.append(Finding(
                    layer=LayerId.BINDING,
                    type=FindingType.UNBOUND_VARIABLE,
                    severity=RiskLevel.MEDIUM,
                    file=file,
                    line=i + 1,
                    message=f'Variable "{var_name}" has no identifiable data source (no source binding)',
                    snippet=trimmed[:100] + '...' if len(trimmed) > 100 else trimmed,
                    suggestion=(
                        f'Ensure "{var_name}" gets its value from an API call, '
                        'I/O operation, or function parameter'
                    ),
                ))
            elif not trace.sink and opts.check_sink:
                findings.append(Finding(
                    layer=LayerId.BINDING,
                    type=FindingType.UNBOUND_VARIABLE,
                    severity=RiskLevel.LOW,
                    file=file,
                    line=i + 1,
                    message=f'Variable "{var_name}" has a source but no identifiable sink (unused data)',
                    snippet=trimmed[:100] + '...' if len(trimmed) > 100 else trimmed,
                    suggestion=(
                        f'Either use "{var_name}" in a render/response/save operation, '
                        'or verify it is intentionally unused'
                    ),
                ))

    return findings
