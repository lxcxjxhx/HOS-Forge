"""
HOS-Forge Semgrep Tool — SAST 代码安全扫描工具适配器。

集成 Semgrep 进行静态代码分析、安全规则检测。
"""

from __future__ import annotations

import asyncio
import json
import logging
import shutil
from typing import Any

from hosforge.security_tools.base import BaseSecurityTool, SecurityToolResult

logger = logging.getLogger(__name__)


class SemgrepTool(BaseSecurityTool):
    """
    Semgrep SAST 工具适配器。

    功能:
        - 代码安全扫描
        - 自定义规则执行
        - CI/CD 集成输出

    使用示例:
        tool = SemgrepTool()
        result = await tool.run("/path/to/project", rules=["python", "javascript"])
    """

    def __init__(self, semgrep_path: str = 'semgrep'):
        super().__init__()
        self._semgrep_path = semgrep_path
        self._available: bool | None = None

    @property
    def name(self) -> str:
        return 'semgrep'

    async def validate(self) -> bool:
        """检查 Semgrep 是否可用"""
        if self._available is not None:
            return self._available
        sg = shutil.which(self._semgrep_path)
        self._available = sg is not None
        return self._available

    async def run(self, target: str, **kwargs: Any) -> SecurityToolResult:
        """
        执行 Semgrep 扫描。

        Args:
            target: 项目路径
            **kwargs:
                rules: 规则列表 (默认 ["p/default"])
                config: 配置路径
                languages: 语言过滤器
                severity: 最低严重级别
                output_format: 输出格式 (json/sarif/text)

        Returns:
            SecurityToolResult: 扫描结果
        """
        if not await self.validate():
            return SecurityToolResult(
                tool_name=self.name,
                success=False,
                error='Semgrep is not installed',
            )

        rules = kwargs.get('rules', ['p/default'])
        config = kwargs.get('config', '')
        languages = kwargs.get('languages', [])
        severity = kwargs.get('severity', 'info')
        output_format = kwargs.get('output_format', 'json')

        cmd = [self._semgrep_path, 'scan']

        # 规则配置
        if config:
            cmd.extend(['--config', config])
        else:
            for rule in rules:
                cmd.extend(['--config', rule])

        # 语言过滤
        if languages:
            cmd.extend(['--lang', ','.join(languages)])

        # 最低严重级别
        cmd.extend(['--severity', severity.upper()])

        # 输出格式
        if output_format == 'json':
            cmd.append('--json')
        elif output_format == 'sarif':
            cmd.append('--sarif')

        # 目标路径
        cmd.append(target)

        # 强制颜色输出
        cmd.append('--force-color')

        logger.info('Semgrep command: %s', ' '.join(cmd[:4]) + ' ...')

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=120,
                )
            except asyncio.TimeoutError:
                process.kill()
                return SecurityToolResult(
                    tool_name=self.name,
                    success=False,
                    error='Semgrep scan timed out after 120s',
                )

            output = stdout.decode()

            findings = []
            if output_format == 'json' and output.strip():
                try:
                    data = json.loads(output)
                    findings = self._parse_semgrep_results(data)
                except json.JSONDecodeError:
                    pass

            return SecurityToolResult(
                tool_name=self.name,
                success=process.returncode in (0, 1),  # 1 = findings found
                output=output,
                raw_data={'findings': findings},
            )

        except FileNotFoundError:
            return SecurityToolResult(
                tool_name=self.name,
                success=False,
                error='Semgrep not found',
            )

    def _parse_semgrep_results(self, data: dict) -> list[dict]:
        """解析 Semgrep JSON 输出"""
        findings = []
        for result in data.get('results', []):
            findings.append({
                'check_id': result.get('check_id', ''),
                'path': result.get('path', ''),
                'start_line': result.get('start', {}).get('line', 0),
                'end_line': result.get('end', {}).get('line', 0),
                'message': result.get('extra', {}).get('message', ''),
                'severity': result.get('extra', {}).get('severity', 'INFO'),
                'cwe': result.get('extra', {}).get('metadata', {}).get('cwe', ''),
                'cve': result.get('extra', {}).get('metadata', {}).get('cve', ''),
            })
        return findings
