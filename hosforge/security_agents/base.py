"""
HOS-Forge Base Security Agent — 安全Agent基类定义。

所有安全Agent继承自 BaseSecurityAgent，
提供统一的漏洞发现/修复接口。
"""

from __future__ import annotations

import abc
import enum
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


class Severity(enum.Enum):
    """漏洞严重程度"""
    CRITICAL = 'critical'
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'
    INFO = 'info'


@dataclass
class SecurityVulnerability:
    """安全漏洞数据结构"""
    id: str = ''
    name: str = ''
    description: str = ''
    severity: Severity = Severity.INFO
    cwe_id: str = ''          # e.g. CWE-89
    cve_id: str = ''          # e.g. CVE-2024-XXXXX
    file_path: str = ''       # 漏洞所在文件
    line_number: int = 0      # 行号
    code_snippet: str = ''    # 相关代码片段
    remediation: str = ''     # 修复建议
    references: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'severity': self.severity.value,
            'cwe_id': self.cwe_id,
            'cve_id': self.cve_id,
            'file_path': self.file_path,
            'line_number': self.line_number,
            'code_snippet': self.code_snippet,
            'remediation': self.remediation,
            'references': self.references,
        }


@dataclass
class SecurityFinding:
    """安全分析结果——可包含多个漏洞"""
    target: str = ''                    # 分析目标 (file/module/project)
    agent_name: str = ''                # 执行Agent名称
    vulnerabilities: list[SecurityVulnerability] = field(default_factory=list)
    summary: str = ''
    scan_duration_ms: int = 0
    success: bool = True
    error_message: str = ''

    def to_dict(self) -> dict[str, Any]:
        return {
            'target': self.target,
            'agent_name': self.agent_name,
            'summary': self.summary,
            'success': self.success,
            'error_message': self.error_message,
            'vulnerabilities': [v.to_dict() for v in self.vulnerabilities],
            'vulnerability_count': len(self.vulnerabilities),
            'by_severity': {
                level: sum(1 for v in self.vulnerabilities if v.severity == level)
                for level in Severity
            },
        }


@dataclass
class SecurityAgentConfig:
    """安全Agent配置"""
    name: str = ''
    description: str = ''
    enabled: bool = True
    max_vulnerabilities: int = 50
    min_severity: Severity = Severity.LOW
    model: str = ''                       # LLM model override
    custom_rules_path: str = ''           # 自定义规则路径
    extra: dict[str, Any] = field(default_factory=dict)


class BaseSecurityAgent(abc.ABC):
    """
    所有HOS-Forge安全Agent的抽象基类。

    子类必须实现:
        - analyze(target) -> SecurityFinding
        - name 属性
    """

    def __init__(self, config: SecurityAgentConfig | None = None):
        self.config = config or SecurityAgentConfig(name=self.__class__.__name__)
        logger.info(
            'Initialized security agent: %s (enabled=%s)',
            self.name, self.config.enabled,
        )

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Agent 标识名称"""
        ...

    @abc.abstractmethod
    async def analyze(self, target: str, **kwargs: Any) -> SecurityFinding:
        """
        对目标执行安全分析。

        Args:
            target: 分析目标，可以是文件路径、代码片段、项目目录等
            **kwargs: 额外参数

        Returns:
            SecurityFinding: 分析结果
        """
        ...

    async def fix(self, vulnerability: SecurityVulnerability) -> str:
        """
        生成修复代码。

        Args:
            vulnerability: 待修复的漏洞

        Returns:
            str: 修复后的代码/补丁
        """
        raise NotImplementedError(
            f'{self.name} does not support auto-fix'
        )

    async def validate_fix(
        self,
        original: str,
        fixed: str,
    ) -> bool:
        """
        验证修复是否有效且未引入新问题。

        Args:
            original: 原始代码
            fixed: 修复后的代码

        Returns:
            bool: 修复是否有效
        """
        raise NotImplementedError(
            f'{self.name} does not support fix validation'
        )
