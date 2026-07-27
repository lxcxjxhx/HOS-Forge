"""
HOS-Forge Nuclei Tool — 自动化漏洞扫描工具适配器。

集成 Nuclei 进行基于模板的漏洞扫描。
"""

from __future__ import annotations

import asyncio
import json
import shutil
from typing import Any

from hosforge.exceptions import ToolExecutionError, ToolNotFoundError, ToolTimeoutError
from hosforge.logging_config import get_logger
from hosforge.security_tools.base import BaseSecurityTool, SecurityToolResult

logger = get_logger(__name__)


class NucleiTool(BaseSecurityTool):
    """
    Nuclei 漏洞扫描工具适配器。

    功能:
        - 基于模板的漏洞扫描
        - CVE 检测
        - 配置错误检测
        - 多协议支持 (HTTP/DNS/SSL)

    使用示例:
        tool = NucleiTool()
        result = await tool.run("https://example.com", tags=["cve", "misconfig"])
    """

    def __init__(self, nuclei_path: str = "nuclei"):
        super().__init__()
        self._nuclei_path = nuclei_path
        self._available: bool | None = None

    @property
    def name(self) -> str:
        return "nuclei"

    async def validate(self) -> bool:
        """检查 Nuclei 是否可用"""
        if self._available is not None:
            return self._available
        nc = shutil.which(self._nuclei_path)
        self._available = nc is not None
        if not self._available:
            logger.warning("Nuclei not found at: %s", self._nuclei_path)
        return self._available

    async def run(self, target: str, **kwargs: Any) -> SecurityToolResult:
        """
        执行 Nuclei 扫描。

        Args:
            target: 目标 URL/IP
            **kwargs:
                tags: 模板标签过滤 (默认 ["cve","misconfiguration"])
                templates: 指定模板路径或目录
                severity: 最低严重级别 (info/low/medium/high/critical)
                rate_limit: 请求速率 (默认 150)
                timeout: 超时秒数 (默认 180)
                concurrency: 并发数 (默认 25)
                retries: 重试次数 (默认 1)
                output_format: 输出格式 (json/text)
                exclude_tags: 排除的标签列表
                include_tags: 包含的标签列表

        Returns:
            SecurityToolResult: 扫描结果
        """
        if not await self.validate():
            return SecurityToolResult(
                tool_name=self.name,
                success=False,
                error="Nuclei is not installed or not found in PATH",
            )

        tags: list[str] = kwargs.get("tags", ["cve", "misconfiguration"])
        templates: str = kwargs.get("templates", "")
        severity: str = kwargs.get("severity", "low")
        rate_limit: int = kwargs.get("rate_limit", 150)
        timeout: int = kwargs.get("timeout", 180)
        concurrency: int = kwargs.get("concurrency", 25)
        retries: int = kwargs.get("retries", 1)
        output_format: str = kwargs.get("output_format", "json")
        exclude_tags: list[str] = kwargs.get("exclude_tags", [])
        include_tags: list[str] = kwargs.get("include_tags", [])

        cmd = [self._nuclei_path]

        # 输出格式
        if output_format == "json":
            cmd.append("-json")

        # 模板选择
        if templates:
            cmd.extend(["-t", templates])
        elif tags:
            cmd.extend(["-tags", ",".join(tags)])

        # 严重级别过滤
        cmd.extend(["-severity", severity])

        # 速率限制
        cmd.extend(["-rl", str(rate_limit)])

        # 并发控制
        cmd.extend(["-c", str(concurrency)])

        # 重试次数
        cmd.extend(["-retries", str(retries)])

        # 排除标签
        if exclude_tags:
            cmd.extend(["-etags", ",".join(exclude_tags)])

        # 包含标签
        if include_tags:
            cmd.extend(["-tags", ",".join(include_tags)])

        # 目标
        cmd.extend(["-u", target])

        logger.info("Nuclei scan: target=%s tags=%s severity=%s", target, tags, severity)

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
            except asyncio.TimeoutError as e:
                process.kill()
                error = ToolTimeoutError(
                    f"Nuclei scan timed out after {timeout}s",
                    timeout_seconds=timeout,
                    tool_name=self.name,
                    cause=e,
                )
                logger.error(str(error))
                return SecurityToolResult(
                    tool_name=self.name,
                    success=False,
                    error=str(error),
                )

            output = stdout.decode()
            stderr_text = stderr.decode() if stderr else ""

            findings: list[dict[str, Any]] = []
            if output_format == "json" and output.strip():
                findings = self._parse_nuclei_output(output)

            # Nuclei 返回码: 0 = 成功, 1 = 发现漏洞
            success = process.returncode in (0, 1)
            error_msg = ""
            if process.returncode not in (0, 1):
                error_msg = stderr_text or f"Nuclei exited with code {process.returncode}"

            return SecurityToolResult(
                tool_name=self.name,
                success=success,
                output=output,
                error=error_msg,
                raw_data={
                    "findings": findings,
                    "exit_code": process.returncode,
                    "stderr": stderr_text,
                },
            )

        except FileNotFoundError as e:
            error = ToolNotFoundError(
                f"Nuclei not found at: {self._nuclei_path}",
                tool_name=self.name,
                cause=e,
            )
            logger.error(str(error))
            return SecurityToolResult(
                tool_name=self.name,
                success=False,
                error=str(error),
            )
        except Exception as e:
            error = ToolExecutionError(
                "Nuclei execution failed",
                tool_name=self.name,
                cause=e,
            )
            logger.exception(str(error))
            return SecurityToolResult(
                tool_name=self.name,
                success=False,
                error=str(error),
            )

    def _parse_nuclei_output(self, output: str) -> list[dict[str, Any]]:
        """解析 Nuclei JSON 输出（每行一个 JSON）"""
        findings: list[dict[str, Any]] = []
        for line in output.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                info = data.get("info", {})
                classification = info.get("classification", {})

                findings.append(
                    {
                        "template_id": data.get("template-id", ""),
                        "name": info.get("name", ""),
                        "severity": info.get("severity", "unknown"),
                        "type": data.get("type", ""),
                        "host": data.get("host", ""),
                        "matched_at": data.get("matched-at", ""),
                        "description": info.get("description", ""),
                        "cve_ids": classification.get("cve-id", []),
                        "cwe_ids": classification.get("cwe-id", []),
                        "cvss_metrics": classification.get("cvss-metrics", ""),
                        "curl_command": data.get("curl-command", ""),
                        "timestamp": data.get("timestamp", ""),
                        "matcher_name": data.get("matcher-name", ""),
                    }
                )
            except json.JSONDecodeError:
                logger.warning("Failed to parse Nuclei JSON line: %s", line[:100])
                continue
        return findings
