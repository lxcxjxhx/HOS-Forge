"""
HOS-Silly-Mock: Reality Score Calculator (Python)

综合多维度的检测结果，计算 Reality Score (0-100) 和各项风险评估等级。
"""

from __future__ import annotations

from hosforge.reality_enforcement.types import (
    Finding,
    EnforcementResult,
    RiskLevel,
    Dimensions,
    Summary,
    LayerId,
)

# 各层权重
LAYER_WEIGHTS = {
    LayerId.MOCK: 0.35,
    LayerId.REGEX: 0.20,
    LayerId.BINDING: 0.25,
    LayerId.SILENT: 0.20,
}

# 每级严重程度的扣分
SEVERITY_PENALTIES = {
    RiskLevel.CRITICAL: 25,
    RiskLevel.HIGH: 15,
    RiskLevel.MEDIUM: 8,
    RiskLevel.LOW: 3,
    RiskLevel.INFO: 1,
}

# 最大扣分上限（每层）
MAX_LAYER_PENALTY = 60


def calculate_reality_score(findings: list[Finding]) -> int:
    """
    从 findings 计算 Reality Score (0-100)。

    Args:
        findings: 检测发现列表

    Returns:
        int: Reality Score (0-100)
    """
    if not findings:
        return 100

    # 按层分组
    by_layer: dict[LayerId, list[Finding]] = {}
    for f in findings:
        if f.layer not in by_layer:
            by_layer[f.layer] = []
        by_layer[f.layer].append(f)

    total_score = 100

    for layer, layer_findings in by_layer.items():
        weight = LAYER_WEIGHTS.get(layer, 0.15)
        layer_penalty = 0

        for f in layer_findings:
            layer_penalty += SEVERITY_PENALTIES.get(f.severity, 1)

        layer_penalty = min(layer_penalty, MAX_LAYER_PENALTY)
        total_score -= layer_penalty * weight

    return max(0, min(100, round(total_score)))


def calc_mock_leakage_risk(score: int) -> RiskLevel:
    """计算 Mock Leakage 风险等级"""
    if score <= 30:
        return RiskLevel.CRITICAL
    if score <= 50:
        return RiskLevel.HIGH
    if score <= 70:
        return RiskLevel.MEDIUM
    if score <= 85:
        return RiskLevel.LOW
    return RiskLevel.INFO


def calc_regex_abuse_risk(findings: list[Finding]) -> RiskLevel:
    """计算 Regex Abuse 风险等级"""
    regex_findings = [f for f in findings if f.layer == LayerId.REGEX]
    critical_count = sum(1 for f in regex_findings if f.severity == RiskLevel.CRITICAL)
    high_count = sum(1 for f in regex_findings if f.severity == RiskLevel.HIGH)

    if critical_count > 0:
        return RiskLevel.CRITICAL
    if high_count > 0:
        return RiskLevel.HIGH
    if len(regex_findings) >= 3:
        return RiskLevel.MEDIUM
    if regex_findings:
        return RiskLevel.LOW
    return RiskLevel.INFO


def has_silent_failure(findings: list[Finding]) -> str:
    """判断是否有 Silent Failure"""
    silent = [f for f in findings if f.layer == LayerId.SILENT]
    has_critical = any(f.severity in (RiskLevel.CRITICAL, RiskLevel.HIGH) for f in silent)
    return 'YES' if has_critical else 'NO'


def binding_passed(findings: list[Finding]) -> str:
    """判断 Reality Binding 是否通过"""
    binding = [f for f in findings if f.layer == LayerId.BINDING]
    has_unbound = any(f.type.value == 'unbound-variable' for f in binding)
    return 'FAIL' if has_unbound else 'PASS'


def calc_summary(findings: list[Finding]) -> Summary:
    """计算统计摘要"""
    errors = sum(
        1 for f in findings
        if f.severity in (RiskLevel.CRITICAL, RiskLevel.HIGH)
    )
    warnings = sum(
        1 for f in findings
        if f.severity in (RiskLevel.MEDIUM, RiskLevel.LOW)
    )
    info = sum(1 for f in findings if f.severity == RiskLevel.INFO)

    return Summary(
        total_findings=len(findings),
        errors=errors,
        warnings=warnings,
        info=info,
    )


def build_result(findings: list[Finding]) -> EnforcementResult:
    """
    从 findings 生成完整的 EnforcementResult。
    """
    score = calculate_reality_score(findings)
    summary = calc_summary(findings)

    return EnforcementResult(
        passed=score >= 50,
        reality_score=score,
        dimensions=Dimensions(
            data_authenticity=max(0, 100 - len([f for f in findings if f.layer == LayerId.MOCK]) * 12),
            mock_leakage_risk=calc_mock_leakage_risk(score),
            regex_abuse_risk=calc_regex_abuse_risk(findings),
            silent_failure_risk=has_silent_failure(findings),
            reality_binding=binding_passed(findings),
        ),
        findings=findings,
        summary=summary,
    )
