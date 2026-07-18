"""
HOS-Forge Audit Agent — 安全审计Agent。

负责SAST代码审计、CWE/CVE分析、漏洞定位。
"""

from __future__ import annotations

import logging
from typing import Any

from hosforge.security_agents.base import (
    BaseSecurityAgent,
    SecurityAgentConfig,
    SecurityFinding,
    SecurityVulnerability,
    Severity,
)

logger = logging.getLogger(__name__)


class AuditAgent(BaseSecurityAgent):
    """
    Security Audit Agent — 代码安全审计Agent。

    能力:
        - SAST 静态应用安全测试
        - CWE 漏洞分类映射
        - 敏感信息泄露检测
        - 不安全配置检测
        - OWASP Top 10 检查
    """

    def __init__(self, config: SecurityAgentConfig | None = None):
        super().__init__(config or SecurityAgentConfig(
            name='AuditAgent',
            description='代码安全审计 Agent — SAST / CWE 分析 / 漏洞定位',
        ))
        # 内置规则引擎规则
        self._builtin_rules: list[dict[str, Any]] = self._load_default_rules()

    @property
    def name(self) -> str:
        return 'AuditAgent'

    async def analyze(self, target: str, **kwargs: Any) -> SecurityFinding:
        """
        对目标执行安全审计。

        结合规则引擎和AI分析识别安全漏洞。

        Args:
            target: 分析目标 (文件路径/代码片段/项目目录)
            **kwargs: 额外参数
                mode: 'quick' | 'full' (默认 full)
                rules: 自定义规则列表
        """
        mode = kwargs.get('mode', 'full')
        custom_rules = kwargs.get('rules', [])

        finding = SecurityFinding(
            target=target,
            agent_name=self.name,
        )

        logger.info(
            'AuditAgent analyzing target=%s mode=%s',
            target, mode,
        )

        # 规则引擎分析
        all_rules = self._builtin_rules + list(custom_rules)
        for rule in all_rules:
            if self.config.min_severity.value > rule.get('severity', Severity.LOW).value:
                continue

            if len(finding.vulnerabilities) >= self.config.max_vulnerabilities:
                logger.warning('Max vulnerabilities reached, stopping analysis')
                break

            try:
                vuln = await self._apply_rule(rule, target)
                if vuln:
                    finding.vulnerabilities.append(vuln)
            except Exception as e:
                logger.error('Rule evaluation failed: %s', e)

        finding.summary = (
            f'AuditAgent 发现 {len(finding.vulnerabilities)} 个潜在安全问题 '
            f'(模式: {mode})'
        )
        finding.scan_duration_ms = 0  # 实际应记录耗时

        logger.info('Audit complete: %d findings', len(finding.vulnerabilities))
        return finding

    async def _apply_rule(
        self,
        rule: dict[str, Any],
        target: str,
    ) -> SecurityVulnerability | None:
        """
        应用单个规则到目标。

        实际实现将调用 HOS-Sec-Engine 或 AI 模型进行分析。
        当前为基础占位实现。
        """
        rule_name = rule.get('name', 'unknown')
        logger.debug('Applying rule: %s to %s', rule_name, target)

        # TODO: 集成 HOS-Sec-Engine 实际分析
        # 当前返回占位结果
        return None

    def _load_default_rules(self) -> list[dict[str, Any]]:
        """加载内置安全审计规则"""
        return [
            # SQL注入检测
            {
                'id': 'R001',
                'name': 'SQL Injection Detection',
                'description': '检测潜在的SQL注入风险',
                'severity': Severity.CRITICAL,
                'cwe': 'CWE-89',
                'patterns': [
                    r"execute\(.*\+.*\)",
                    r"cursor\.execute\(.*f['\"]",
                    r"raw_input.*sql",
                ],
            },
            # XSS检测
            {
                'id': 'R002',
                'name': 'Cross-Site Scripting (XSS)',
                'description': '检测反射型/存储型XSS',
                'severity': Severity.HIGH,
                'cwe': 'CWE-79',
                'patterns': [
                    r"innerHTML\s*=",
                    r"document\.write\(.*request",
                    r"mark_safe\(",
                ],
            },
            # 命令注入
            {
                'id': 'R003',
                'name': 'Command Injection',
                'description': '检测OS命令注入风险',
                'severity': Severity.CRITICAL,
                'cwe': 'CWE-78',
                'patterns': [
                    r"os\.system\(.*\+",
                    r"subprocess\.call\(.*\+",
                    r"eval\(.*request",
                ],
            },
            # 路径遍历
            {
                'id': 'R004',
                'name': 'Path Traversal',
                'description': '检测路径遍历漏洞',
                'severity': Severity.HIGH,
                'cwe': 'CWE-22',
                'patterns': [
                    r"open\(.*\.\./",
                    r"\.\.\/.*open\(",
                ],
            },
            # 弱密码硬编码
            {
                'id': 'R005',
                'name': 'Hardcoded Credentials',
                'description': '检测硬编码密码/密钥',
                'severity': Severity.CRITICAL,
                'cwe': 'CWE-798',
                'patterns': [
                    r"password\s*=\s*['\"][^'\"]{3,}['\"]",
                    r"api_key\s*=\s*['\"][^'\"]{8,}['\"]",
                    r"secret\s*=\s*['\"][^'\"]{8,}['\"]",
                ],
            },
            # SSRF
            {
                'id': 'R006',
                'name': 'Server-Side Request Forgery',
                'description': '检测SSRF风险',
                'severity': Severity.HIGH,
                'cwe': 'CWE-918',
                'patterns': [
                    r"requests\.get\(.*request\.get\(",
                    r"urlopen\(.*request\.",
                ],
            },
            # 不安全的反序列化
            {
                'id': 'R007',
                'name': 'Insecure Deserialization',
                'description': '检测不安全的反序列化',
                'severity': Severity.HIGH,
                'cwe': 'CWE-502',
                'patterns': [
                    r"pickle\.loads\(",
                    r"yaml\.load\(.*Loader",
                    r"eval\(.*input",
                ],
            },
        ]
