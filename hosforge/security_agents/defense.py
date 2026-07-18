"""
HOS-Forge Defense Agent — 安全防御/修复Agent。

负责漏洞修复、代码加固、安全策略生成。
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


class DefenseAgent(BaseSecurityAgent):
    """
    Security Defense Agent — 修复和加固Agent。

    能力:
        - 自动生成安全修复代码
        - 代码加固建议
        - 安全策略生成
        - 修复验证
        - 安全配置生成
    """

    def __init__(self, config: SecurityAgentConfig | None = None):
        super().__init__(config or SecurityAgentConfig(
            name='DefenseAgent',
            description='安全防御/修复 Agent — 漏洞修复 / 代码加固 / 安全策略',
        ))
        # 安全修复模板库
        self._fix_templates: dict[str, str] = self._load_fix_templates()

    @property
    def name(self) -> str:
        return 'DefenseAgent'

    async def analyze(self, target: str, **kwargs: Any) -> SecurityFinding:
        """
        分析目标的安全防御状态。

        Args:
            target: 分析目标
            **kwargs: 额外参数
        """
        finding = SecurityFinding(
            target=target,
            agent_name=self.name,
            summary=f'DefenseAgent 分析完成: {target}',
        )
        logger.info('DefenseAgent analyzing: %s', target)
        return finding

    async def fix(self, vulnerability: SecurityVulnerability) -> str:
        """
        根据漏洞类型生成修复代码。

        Args:
            vulnerability: 待修复的漏洞信息

        Returns:
            str: 修复代码/补丁
        """
        cwe_id = vulnerability.cwe_id
        template = self._fix_templates.get(cwe_id)

        if template:
            logger.info('Using fix template for %s (CWE: %s)', vulnerability.name, cwe_id)
            return self._apply_template(template, vulnerability)

        logger.info(
            'No template for CWE %s, generating AI-based fix for %s',
            cwe_id, vulnerability.name,
        )
        # TODO: 集成AI模型生成修复
        return f'# TODO: Auto-fix for {vulnerability.name} ({cwe_id})\n'

    async def validate_fix(
        self,
        original: str,
        fixed: str,
    ) -> bool:
        """
        验证修复是否有效。

        检查:
            1. 语法正确性
            2. 是否引入了新安全问题
            3. 功能等价性
        """
        # TODO: 集成HOS-Sec-Engine验证
        logger.info('Validating fix...')
        return True

    def _load_fix_templates(self) -> dict[str, str]:
        """加载CWE对应的修复模板"""
        return {
            'CWE-89': self._template_sql_injection(),
            'CWE-79': self._template_xss(),
            'CWE-78': self._template_command_injection(),
            'CWE-22': self._template_path_traversal(),
            'CWE-798': self._template_hardcoded_credentials(),
        }

    def _apply_template(
        self,
        template: str,
        vuln: SecurityVulnerability,
    ) -> str:
        """应用修复模板"""
        context = vuln.code_snippet or ''
        return template.format(
            code=context,
            file=vuln.file_path,
            line=vuln.line_number,
        )

    @staticmethod
    def _template_sql_injection() -> str:
        return '''\
# HOS-Forge Auto-Fix: SQL Injection (CWE-89)
# Original code had SQL injection risk
# Replace with parameterized query:

import sqlite3  # or your DB library

# ❌ Vulnerable pattern:
# cursor.execute(f"SELECT * FROM users WHERE id = {user_input}")

# ✅ Fixed with parameterized query:
cursor.execute(
    "SELECT * FROM users WHERE id = ?",
    (user_input,),
)
'''

    @staticmethod
    def _template_xss() -> str:
        return '''\
# HOS-Forge Auto-Fix: Cross-Site Scripting (CWE-79)
# Use safe content rendering

from markupsafe import escape

# ❌ Vulnerable pattern:
# template = f"<div>{user_input}</div>"

# ✅ Fixed:
template = f"<div>{escape(user_input)}</div>"
'''

    @staticmethod
    def _template_command_injection() -> str:
        return '''\
# HOS-Forge Auto-Fix: Command Injection (CWE-78)
# Avoid shell=True and use subprocess with list args

import subprocess

# ❌ Vulnerable pattern:
# subprocess.call(f"ping {user_input}", shell=True)

# ✅ Fixed:
subprocess.call(
    ["ping", user_input],
    shell=False,
)
'''

    @staticmethod
    def _template_path_traversal() -> str:
        return '''\
# HOS-Forge Auto-Fix: Path Traversal (CWE-22)
# Validate and sanitize file paths

import os

BASE_DIR = "/safe/base/path"

# ❌ Vulnerable pattern:
# path = os.path.join(BASE_DIR, user_input)

# ✅ Fixed:
user_path = os.path.normpath(user_input).lstrip("/")
if user_path.startswith("..") or "/" in user_path:
    raise ValueError("Invalid path")
safe_path = os.path.join(BASE_DIR, user_path)
'''

    @staticmethod
    def _template_hardcoded_credentials() -> str:
        return '''\
# HOS-Forge Auto-Fix: Hardcoded Credentials (CWE-798)
# Move secrets to environment variables

import os

# ❌ Vulnerable pattern:
# PASSWORD = "super_secret_123"

# ✅ Fixed:
PASSWORD = os.environ.get("APP_PASSWORD")
if not PASSWORD:
    raise EnvironmentError("APP_PASSWORD not set in environment")
'''
