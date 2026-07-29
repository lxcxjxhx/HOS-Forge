"""HOS-LS 安全扫描 Skill，封装 HOS-LS 引擎调用。"""

import json
import subprocess
from typing import Any, Dict, List, Optional

from hosforge.skills.base_skill import Skill


class HOSLSScanSkill(Skill):
    """使用 HOS-LS 引擎进行安全扫描的 Skill。

    通过调用 hos-ls 命令行工具对指定目标执行安全扫描，
    解析 JSON 格式输出并返回结构化的安全告警列表。
    """

    def __init__(self) -> None:
        super().__init__(
            name="hosls_scan",
            description="使用 HOS-LS 引擎进行安全扫描",
            parameters={
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "扫描目标（文件路径、目录或 URL）",
                    },
                    "scan_type": {
                        "type": "string",
                        "description": "扫描类型（如 vulnerability, malware, config）",
                        "default": "vulnerability",
                    },
                    "severity": {
                        "type": "string",
                        "description": "最低严重级别过滤（critical, high, medium, low）",
                    },
                    "output_format": {
                        "type": "string",
                        "description": "输出格式（json, sarif, text）",
                        "default": "json",
                    },
                },
                "required": ["target"],
            },
        )

    def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """执行 HOS-LS 扫描并返回解析后的结果。

        Args:
            **kwargs: 包含 target, scan_type, severity, output_format 的参数。

        Returns:
            包含 alerts 列表和统计信息的字典。

        Raises:
            FileNotFoundError: hos-ls 命令不可用。
            subprocess.TimeoutExpired: 扫描超时。
        """
        target: str = kwargs["target"]
        scan_type: str = kwargs.get("scan_type", "vulnerability")
        severity: Optional[str] = kwargs.get("severity")
        output_format: str = kwargs.get("output_format", "json")

        cmd: List[str] = [
            "hos-ls",
            "scan",
            "--target",
            target,
            "--type",
            scan_type,
            "--format",
            output_format,
        ]

        if severity:
            cmd.extend(["--severity", severity])

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800,
                check=False,
            )
        except FileNotFoundError as exc:
            raise FileNotFoundError("hos-ls 命令未找到，请确认已安装 HOS-LS 并加入 PATH") from exc

        if proc.returncode not in (0, 1):
            raise subprocess.CalledProcessError(proc.returncode, cmd, proc.stdout, proc.stderr)

        try:
            results = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            raise ValueError(f"无法解析 HOS-LS 输出: {exc}") from exc

        alerts: List[Dict[str, Any]] = []
        for finding in results.get("findings", []):
            alert = {
                "rule_id": finding.get("rule_id"),
                "message": finding.get("description"),
                "severity": finding.get("severity"),
                "location": finding.get("location"),
                "cwe": finding.get("cwe"),
            }
            alerts.append(alert)

        return {
            "alerts": alerts,
            "total": len(alerts),
            "target": target,
            "scan_type": scan_type,
        }
