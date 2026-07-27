"""
HOS-Forge Nmap Tool — 网络扫描工具适配器。

集成 Nmap 进行端口扫描、服务识别、操作系统检测。
支持作为 MCP Server 供 Agent 调用。
"""

from __future__ import annotations

import asyncio
import re
import shutil
from typing import Any

from hosforge.exceptions import ToolExecutionError, ToolNotFoundError, ToolTimeoutError
from hosforge.logging_config import get_logger
from hosforge.security_tools.base import BaseSecurityTool, SecurityToolResult

logger = get_logger(__name__)


class NmapTool(BaseSecurityTool):
    """
    Nmap 网络扫描工具适配器。

    功能:
        - TCP/UDP 端口扫描
        - 服务版本检测
        - 操作系统识别
        - NSE 脚本扫描

    使用示例:
        tool = NmapTool()
        result = await tool.run("example.com", ports="22,80,443")
    """

    def __init__(self, nmap_path: str = "nmap"):
        super().__init__()
        self._nmap_path = nmap_path
        self._available: bool | None = None

    @property
    def name(self) -> str:
        return "nmap"

    async def validate(self) -> bool:
        """检查 Nmap 是否可用"""
        if self._available is not None:
            return self._available

        nmap = shutil.which(self._nmap_path)
        self._available = nmap is not None
        if not self._available:
            logger.warning("Nmap not found at: %s", self._nmap_path)
        return self._available

    async def run(self, target: str, **kwargs: Any) -> SecurityToolResult:
        """
        执行 Nmap 扫描。

        Args:
            target: 目标 IP/域名
            **kwargs:
                ports: 端口范围 (默认 "1-1024")
                scan_type: 扫描类型 (tcp_syn/tcp_connect/udp/ping/comprehensive)
                scripts: NSE 脚本列表
                os_detection: 是否检测操作系统
                service_detection: 是否检测服务版本
                timing: 时序模板 (T0-T5)
                extra_args: 额外 nmap 参数
                timeout: 超时秒数 (默认 300)

        Returns:
            SecurityToolResult: 扫描结果
        """
        if not await self.validate():
            return SecurityToolResult(
                tool_name=self.name,
                success=False,
                error="Nmap is not installed or not found in PATH",
            )

        ports = kwargs.get("ports", "1-1024")
        scan_type = kwargs.get("scan_type", "tcp_syn")
        scripts = kwargs.get("scripts", [])
        os_detection = kwargs.get("os_detection", False)
        service_detection = kwargs.get("service_detection", True)
        timing = kwargs.get("timing", "")
        extra_args = kwargs.get("extra_args", [])
        timeout = kwargs.get("timeout", 300)

        # 构建命令
        cmd = [self._nmap_path]

        # 扫描类型
        scan_flags = {
            "tcp_syn": ["-sS"],
            "tcp_connect": ["-sT"],
            "udp": ["-sU"],
            "ping": ["-sn"],
            "comprehensive": ["-sS", "-sV", "-sC", "-O"],
        }
        cmd.extend(scan_flags.get(scan_type, ["-sS"]))

        # 端口
        if ports and scan_type != "ping":
            cmd.extend(["-p", str(ports)])

        # 服务版本检测
        if service_detection and scan_type != "comprehensive":
            cmd.append("-sV")

        # 操作系统检测
        if os_detection and scan_type != "comprehensive":
            cmd.append("-O")

        # 时序模板
        if timing and re.match(r"^T[0-5]$", timing):
            cmd.append(f"-{timing}")

        # NSE 脚本
        if scripts:
            cmd.extend(["--script", ",".join(scripts)])

        # 输出格式 - XML 到 stdout
        cmd.extend(["-oX", "-"])

        # 额外参数
        if extra_args:
            cmd.extend(extra_args if isinstance(extra_args, list) else [extra_args])

        # 目标
        cmd.append(target)

        logger.info("Nmap command: %s", " ".join(cmd))

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
                    error=f"Nmap scan timed out after {timeout}s",
                )

            if process.returncode != 0:
                return SecurityToolResult(
                    tool_name=self.name,
                    success=False,
                    error=stderr.decode() if stderr else "Nmap returned non-zero exit code",
                    output=stdout.decode() if stdout else "",
                )

            output = stdout.decode()
            result = self._parse_nmap_output(output)

            return SecurityToolResult(
                tool_name=self.name,
                success=True,
                output=output,
                raw_data=result,
            )

        except FileNotFoundError as e:
            error = ToolNotFoundError(
                f"Nmap not found at: {self._nmap_path}",
                tool_name=self.name,
                cause=e,
            )
            logger.error(str(error))
            return SecurityToolResult(
                tool_name=self.name,
                success=False,
                error=str(error),
            )
        except asyncio.TimeoutError as e:
            error = ToolTimeoutError(
                f"Nmap scan timed out after {timeout}s",
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
        except Exception as e:
            error = ToolExecutionError(
                "Nmap execution failed",
                tool_name=self.name,
                cause=e,
            )
            logger.exception(str(error))
            return SecurityToolResult(
                tool_name=self.name,
                success=False,
                error=str(error),
            )

    def _parse_nmap_output(self, xml_output: str) -> dict[str, Any]:
        """
        解析 Nmap XML 输出为结构化数据。

        由于避免依赖外部 XML 解析库，采用基础解析。
        """
        result: dict[str, Any] = {
            "open_ports": [],
            "services": {},
            "banners": {},
            "os_guess": "",
            "host_status": "unknown",
            "scan_info": {},
        }

        # 基础 XML 解析
        if "<host>" in xml_output:
            # 提取 host status
            if '<status state="up"' in xml_output:
                result["host_status"] = "up"

            # 提取端口信息
            port_matches = re.findall(
                r'<port protocol="(\w+)" portid="(\d+)">.*?<state state="(\w+)".*?'
                r'(?:<service name="([^"]*)"|)',
                xml_output,
                re.DOTALL,
            )
            for _protocol, port, state, service in port_matches:
                if state == "open":
                    port_num = int(port)
                    result["open_ports"].append(port_num)
                    if service:
                        result["services"][port_num] = service

            # 提取操作系统信息
            os_matches = re.findall(
                r'<osmatch name="([^"]*)" accuracy="(\d+)"',
                xml_output,
            )
            if os_matches:
                result["os_guess"] = os_matches[0][0]

            # 提取扫描信息
            scan_matches = re.findall(
                r'<scaninfo type="(\w+)"',
                xml_output,
            )
            if scan_matches:
                result["scan_info"]["type"] = scan_matches[0]

        return result
