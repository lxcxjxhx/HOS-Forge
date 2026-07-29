"""
HOS-Forge Trivy Tool — 容器和依赖漏洞扫描工具适配器。

集成 Trivy 进行容器镜像、文件系统、依赖项的漏洞扫描。
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


class TrivyTool(BaseSecurityTool):
    """
    Trivy 漏洞扫描工具适配器。

    功能:
        - 容器镜像漏洞扫描
        - 文件系统依赖检测
        - IaC 配置扫描
        - SBOM 生成

    使用示例:
        tool = TrivyTool()
        result = await tool.run("alpine:3.14", scan_type="image")
    """

    def __init__(self, trivy_path: str = "trivy"):
        super().__init__()
        self._trivy_path = trivy_path
        self._available: bool | None = None

    @property
    def name(self) -> str:
        return "trivy"

    async def validate(self) -> bool:
        """检查 Trivy 是否可用"""
        if self._available is not None:
            return self._available
        tv = shutil.which(self._trivy_path)
        self._available = tv is not None
        if not self._available:
            logger.warning("Trivy not found at: %s", self._trivy_path)
        return self._available

    async def run(self, target: str, **kwargs: Any) -> SecurityToolResult:
        """
        执行 Trivy 扫描。

        Args:
            target: 目标 (镜像名/路径/URL)
            **kwargs:
                scan_type: 扫描类型 (image/fs/repo/config)
                severity: 严重级别过滤 (UNKNOWN,LOW,MEDIUM,HIGH,CRITICAL)
                ignore_unfixed: 忽略未修复漏洞
                exit_code: 退出码 (0=所有, 1=有漏洞)
                output_format: 输出格式 (json/table/sarif/cyclonedx)
                timeout: 超时秒数 (默认 300)
                cache_dir: 缓存目录
                skip_dirs: 跳过目录列表
                scanners: 扫描器列表 (vuln,config,secret)

        Returns:
            SecurityToolResult: 扫描结果
        """
        if not await self.validate():
            return SecurityToolResult(
                tool_name=self.name,
                success=False,
                error="Trivy is not installed or not found in PATH",
            )

        scan_type: str = kwargs.get("scan_type", "image")
        severity: str = kwargs.get("severity", "UNKNOWN,LOW,MEDIUM,HIGH,CRITICAL")
        ignore_unfixed: bool = kwargs.get("ignore_unfixed", False)
        exit_code: int = kwargs.get("exit_code", 0)
        output_format: str = kwargs.get("output_format", "json")
        timeout: int = kwargs.get("timeout", 300)
        cache_dir: str = kwargs.get("cache_dir", "")
        skip_dirs: list[str] = kwargs.get("skip_dirs", [])
        scanners: list[str] = kwargs.get("scanners", ["vuln"])

        cmd = [self._trivy_path]

        # 扫描类型
        if scan_type == "image":
            cmd.append("image")
        elif scan_type == "fs":
            cmd.append("fs")
        elif scan_type == "repo":
            cmd.append("repo")
        elif scan_type == "config":
            cmd.append("config")
        else:
            cmd.append("image")

        # 严重级别
        cmd.extend(["--severity", severity])

        # 忽略未修复
        if ignore_unfixed:
            cmd.append("--ignore-unfixed")

        # 退出码
        cmd.extend(["--exit-code", str(exit_code)])

        # 输出格式
        if output_format == "json":
            cmd.append("--format")
            cmd.append("json")
        elif output_format == "sarif":
            cmd.append("--format")
            cmd.append("sarif")
        elif output_format == "cyclonedx":
            cmd.append("--format")
            cmd.append("cyclonedx")
        else:
            cmd.append("--format")
            cmd.append("table")

        # 缓存目录
        if cache_dir:
            cmd.extend(["--cache-dir", cache_dir])

        # 跳过目录
        for skip_dir in skip_dirs:
            cmd.extend(["--skip-dirs", skip_dir])

        # 扫描器
        if scanners:
            cmd.extend(["--scanners", ",".join(scanners)])

        # 目标
        cmd.append(target)

        logger.info("Trivy command: %s", " ".join(cmd[:6]) + " ...")

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
                    f"Trivy scan timed out after {timeout}s",
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

            vulnerabilities: list[dict[str, Any]] = []
            if output_format == "json" and output.strip():
                try:
                    data = json.loads(output)
                    vulnerabilities = self._parse_trivy_results(data)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse Trivy JSON output")

            # Trivy 返回码: 0=成功, 1=有漏洞(当exit_code=1时)
            success = process.returncode == 0 or (process.returncode == 1 and exit_code == 1)
            error_msg = ""
            if process.returncode not in (0, 1):
                error_msg = stderr_text or "Trivy encountered an error"

            return SecurityToolResult(
                tool_name=self.name,
                success=success,
                output=output,
                error=error_msg,
                raw_data={
                    "vulnerabilities": vulnerabilities,
                    "exit_code": process.returncode,
                    "stderr": stderr_text,
                },
            )

        except FileNotFoundError as e:
            error = ToolNotFoundError(
                f"Trivy not found at: {self._trivy_path}",
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
                "Trivy execution failed",
                tool_name=self.name,
                cause=e,
            )
            logger.exception(str(error))
            return SecurityToolResult(
                tool_name=self.name,
                success=False,
                error=str(error),
            )

    def _parse_trivy_results(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """解析 Trivy JSON 输出为结构化漏洞列表"""
        vulnerabilities: list[dict[str, Any]] = []

        # Trivy 输出格式: {"Results": [...]}
        results = data.get("Results", [])

        for result in results:
            target = result.get("Target", "")
            vulns = result.get("Vulnerabilities", [])

            for vuln in vulns:
                vulnerabilities.append(
                    {
                        "vuln_id": vuln.get("VulnerabilityID", ""),
                        "pkg_name": vuln.get("PkgName", ""),
                        "installed_version": vuln.get("InstalledVersion", ""),
                        "fixed_version": vuln.get("FixedVersion", ""),
                        "severity": vuln.get("Severity", "UNKNOWN"),
                        "title": vuln.get("Title", ""),
                        "description": vuln.get("Description", ""),
                        "references": vuln.get("References", []),
                        "target": target,
                    }
                )

        return vulnerabilities
