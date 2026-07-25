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

    def __init__(self, semgrep_path: str = "semgrep"):
        super().__init__()
        self._semgrep_path = semgrep_path
        self._available: bool | None = None

    @property
    def name(self) -> str:
        return "semgrep"

    async def validate(self) -> bool:
        """检查 Semgrep 是否可用"""
        if self._available is not None:
            return self._available
        sg = shutil.which(self._semgrep_path)
        self._available = sg is not None
        if not self._available:
            logger.warning("Semgrep not found at: %s", self._semgrep_path)
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
                severity: 最低严重级别 (info/warning/error)
                output_format: 输出格式 (json/sarif/text)
                timeout: 超时秒数 (默认 300)
                exclude: 排除的文件/目录模式列表
                max_target_bytes: 最大目标文件大小 (bytes)
                metrics: 是否发送匿名指标

        Returns:
            SecurityToolResult: 扫描结果
        """
        if not await self.validate():
            return SecurityToolResult(
                tool_name=self.name,
                success=False,
                error="Semgrep is not installed or not found in PATH",
            )

        rules: list[str] = kwargs.get("rules", ["p/default"])
        config: str = kwargs.get("config", "")
        languages: list[str] = kwargs.get("languages", [])
        severity: str = kwargs.get("severity", "info")
        output_format: str = kwargs.get("output_format", "json")
        timeout: int = kwargs.get("timeout", 300)
        exclude: list[str] = kwargs.get("exclude", [])
        max_target_bytes: int = kwargs.get("max_target_bytes", 1000000)
        metrics: str = kwargs.get("metrics", "off")

        cmd = [self._semgrep_path, "scan"]

        # 规则配置
        if config:
            cmd.extend(["--config", config])
        else:
            for rule in rules:
                cmd.extend(["--config", rule])

        # 语言过滤
        if languages:
            cmd.extend(["--lang", ",".join(languages)])

        # 最低严重级别
        cmd.extend(["--severity", severity.upper()])

        # 输出格式
        if output_format == "json":
            cmd.append("--json")
        elif output_format == "sarif":
            cmd.append("--sarif")

        # 排除模式
        for pattern in exclude:
            cmd.extend(["--exclude", pattern])

        # 最大目标文件大小
        cmd.extend(["--max-target-bytes", str(max_target_bytes)])

        # 指标
        cmd.extend(["--metrics", metrics])

        # 不发送匿名指标
        cmd.append("--no-git-ignore")

        # 目标路径
        cmd.append(target)

        # 强制颜色输出（仅在非 JSON 格式时使用）
        if output_format != "json":
            cmd.append("--force-color")

        logger.info("Semgrep command: %s", " ".join(cmd[:6]) + " ...")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                return SecurityToolResult(
                    tool_name=self.name,
                    success=False,
                    error=f"Semgrep scan timed out after {timeout}s",
                )

            output = stdout.decode()
            stderr_text = stderr.decode() if stderr else ""

            findings: list[dict[str, Any]] = []
            errors: list[dict[str, Any]] = []
            if output_format == "json" and output.strip():
                try:
                    data = json.loads(output)
                    findings = self._parse_semgrep_results(data)
                    errors = self._parse_semgrep_errors(data)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse Semgrep JSON output")

            # Semgrep 返回码: 0 = 无发现, 1 = 有发现, 2 = 错误
            success = process.returncode in (0, 1)
            error_msg = ""
            if process.returncode == 2:
                error_msg = stderr_text or "Semgrep encountered an error"

            return SecurityToolResult(
                tool_name=self.name,
                success=success,
                output=output,
                error=error_msg,
                raw_data={
                    "findings": findings,
                    "errors": errors,
                    "exit_code": process.returncode,
                    "stderr": stderr_text,
                },
            )

        except FileNotFoundError:
            return SecurityToolResult(
                tool_name=self.name,
                success=False,
                error=f"Semgrep not found at: {self._semgrep_path}",
            )
        except Exception as e:
            logger.exception("Semgrep execution failed")
            return SecurityToolResult(
                tool_name=self.name,
                success=False,
                error=str(e),
            )

    def _parse_semgrep_results(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """解析 Semgrep JSON 输出为结构化发现列表"""
        findings: list[dict[str, Any]] = []
        for result in data.get("results", []):
            extra = result.get("extra", {})
            metadata = extra.get("metadata", {})
            findings.append(
                {
                    "check_id": result.get("check_id", ""),
                    "path": result.get("path", ""),
                    "start_line": result.get("start", {}).get("line", 0),
                    "end_line": result.get("end", {}).get("line", 0),
                    "start_col": result.get("start", {}).get("col", 0),
                    "end_col": result.get("end", {}).get("col", 0),
                    "message": extra.get("message", ""),
                    "severity": extra.get("severity", "INFO"),
                    "fingerprint": extra.get("fingerprint", ""),
                    "metadata": {
                        "cwe": metadata.get("cwe", []),
                        "cve": metadata.get("cve", ""),
                        "owasp": metadata.get("owasp", ""),
                        "references": metadata.get("references", []),
                        "category": metadata.get("category", ""),
                    },
                }
            )
        return findings

    def _parse_semgrep_errors(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """解析 Semgrep JSON 输出中的错误信息"""
        errors: list[dict[str, Any]] = []
        for err in data.get("errors", []):
            errors.append(
                {
                    "type": err.get("type", ""),
                    "level": err.get("level", ""),
                    "path": err.get("location", {}).get("path", ""),
                    "message": err.get("message", ""),
                }
            )
        return errors
