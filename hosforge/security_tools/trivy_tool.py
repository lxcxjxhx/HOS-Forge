"""
HOS-Forge Trivy Tool — 容器和文件系统漏洞扫描工具适配器。

集成 Trivy 进行容器镜像、文件系统、Git 仓库的漏洞扫描。
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
        - 文件系统依赖检查
        - Git 仓库扫描
        - 基础设施即代码 (IaC) 扫描
        - SBOM 生成

    使用示例:
        tool = TrivyTool()
        result = await tool.run("nginx:latest", scan_type="image")
        result = await tool.run("/path/to/project", scan_type="fs")
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
        tc = shutil.which(self._trivy_path)
        self._available = tc is not None
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
                severity: 严重级别过滤 (UNKNOWN/LOW/MEDIUM/HIGH/CRITICAL)
                ignore_unfixed: 忽略未修复漏洞
                exit_code: 退出码 (0=成功, 1=发现漏洞)
                output_format: 输出格式 (json/table/sarif/cyclonedx/spdx)
                timeout: 超时秒数 (默认 300)
                scanners: 扫描器列表 (vuln/config/secret/license)
                skip_dirs: 跳过目录列表
                skip_files: 跳过文件列表
                cache_dir: 缓存目录
                offline_scan: 离线扫描模式

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
        severity: str = kwargs.get("severity", "MEDIUM,HIGH,CRITICAL")
        ignore_unfixed: bool = kwargs.get("ignore_unfixed", False)
        exit_code: int = kwargs.get("exit_code", 0)
        output_format: str = kwargs.get("output_format", "json")
        timeout: int = kwargs.get("timeout", 300)
        scanners: list[str] = kwargs.get("scanners", ["vuln"])
        skip_dirs: list[str] = kwargs.get("skip_dirs", [])
        skip_files: list[str] = kwargs.get("skip_files", [])
        cache_dir: str = kwargs.get("cache_dir", "")
        offline_scan: bool = kwargs.get("offline_scan", False)

        cmd = [self._trivy_path]

        # 扫描类型子命令
        scan_commands = {
            "image": "image",
            "fs": "fs",
            "repo": "repository",
            "config": "config",
            "sbom": "sbom",
        }
        cmd.append(scan_commands.get(scan_type, "image"))

        # 严重级别过滤
        cmd.extend(["--severity", severity])

        # 忽略未修复漏洞
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
        elif output_format == "spdx":
            cmd.append("--format")
            cmd.append("spdx-json")

        # 扫描器
        if scanners and scan_type in ["fs", "repo", "config"]:
            cmd.extend(["--scanners", ",".join(scanners)])

        # 跳过目录
        for skip_dir in skip_dirs:
            cmd.extend(["--skip-dirs", skip_dir])

        # 跳过文件
        for skip_file in skip_files:
            cmd.extend(["--skip-files", skip_file])

        # 缓存目录
        if cache_dir:
            cmd.extend(["--cache-dir", cache_dir])

        # 离线扫描
        if offline_scan:
            cmd.append("--offline-scan")

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

            findings: list[dict[str, Any]] = []
            if output_format == "json" and output.strip():
                try:
                    data = json.loads(output)
                    findings = self._parse_trivy_result(data)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse Trivy JSON output")

            # Trivy 返回码: 0 = 成功, 1 = 发现漏洞 (如果设置了 --exit-code 1)
            success = process.returncode in (0, exit_code)
            error_msg = ""
            if process.returncode not in (0, exit_code):
                error_msg = stderr_text or f"Trivy exited with code {process.returncode}"

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

    def _parse_trivy_result(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """解析 Trivy JSON 输出为结构化发现列表"""
        findings: list[dict[str, Any]] = []

        # Trivy 输出结构: Results 数组
        for result in data.get("Results", []):
            target = result.get("Target", "")
            result_class = result.get("Class", "")
            result_type = result.get("Type", "")

            # 遍历漏洞
            for vuln in result.get("Vulnerabilities", []):
                findings.append(
                    {
                        "target": target,
                        "class": result_class,
                        "type": result_type,
                        "vuln_id": vuln.get("VulnerabilityID", ""),
                        "pkg_name": vuln.get("PkgName", ""),
                        "installed_version": vuln.get("InstalledVersion", ""),
                        "fixed_version": vuln.get("FixedVersion", ""),
                        "severity": vuln.get("Severity", "UNKNOWN"),
                        "title": vuln.get("Title", ""),
                        "description": vuln.get("Description", ""),
                        "primary_url": vuln.get("PrimaryURL", ""),
                        "references": vuln.get("References", []),
                    }
                )

            # 遍历配置问题 (IaC)
            for misconf in result.get("Misconfigurations", []):
                findings.append(
                    {
                        "target": target,
                        "class": result_class,
                        "type": result_type,
                        "vuln_id": misconf.get("ID", ""),
                        "title": misconf.get("Title", ""),
                        "description": misconf.get("Description", ""),
                        "severity": misconf.get("Severity", "UNKNOWN"),
                        "primary_url": misconf.get("PrimaryURL", ""),
                        "references": misconf.get("References", []),
                        "cause_metadata": misconf.get("CauseMetadata", {}),
                    }
                )

            # 遍历密钥泄露
            for secret in result.get("Secrets", []):
                findings.append(
                    {
                        "target": target,
                        "class": result_class,
                        "type": result_type,
                        "vuln_id": secret.get("RuleID", ""),
                        "title": secret.get("Title", ""),
                        "description": secret.get("Match", ""),
                        "severity": secret.get("Severity", "UNKNOWN"),
                        "start_line": secret.get("StartLine", 0),
                        "end_line": secret.get("EndLine", 0),
                    }
                )

        return findings
