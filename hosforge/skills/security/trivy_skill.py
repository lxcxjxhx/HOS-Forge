"""Trivy 漏洞扫描 Skill，封装 trivy 命令行工具调用。"""

import json
import subprocess
from typing import Any, Dict, List, Optional

from hosforge.skills.base_skill import Skill


class TrivyScanSkill(Skill):
    """使用 Trivy 进行漏洞扫描的 Skill。

    通过调用 trivy 命令行工具对指定目标执行漏洞扫描，
    解析 JSON 格式输出并返回结构化的漏洞列表。
    """

    def __init__(self) -> None:
        super().__init__(
            name="trivy_scan",
            description="使用 Trivy 进行漏洞扫描",
            parameters={
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "扫描目标 (镜像名、文件路径或仓库地址)",
                    },
                    "scan_type": {
                        "type": "string",
                        "description": "扫描类型: image, fs, repo",
                        "enum": ["image", "fs", "repo"],
                    },
                    "severity": {
                        "type": "string",
                        "description": "过滤严重级别 (UNKNOWN, LOW, MEDIUM, HIGH, CRITICAL)",
                    },
                },
                "required": ["target"],
            },
        )

    def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """执行 trivy 扫描并返回解析后的结果。

        Args:
            **kwargs: 包含 target, scan_type, severity 的参数。

        Returns:
            包含 vulnerabilities 列表和统计信息的字典。

        Raises:
            FileNotFoundError: trivy 命令不可用。
            subprocess.TimeoutExpired: 扫描超时。
        """
        target: str = kwargs["target"]
        scan_type: Optional[str] = kwargs.get("scan_type", "image")
        severity: Optional[str] = kwargs.get("severity")

        cmd: List[str] = ["trivy", scan_type, "--format", "json", "--quiet", target]

        if severity:
            cmd.extend(["--severity", severity])

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,
                check=False,
            )
        except FileNotFoundError as exc:
            raise FileNotFoundError("trivy 命令未找到，请确认已安装 trivy 并加入 PATH") from exc

        if proc.returncode not in (0, 1):
            raise subprocess.CalledProcessError(proc.returncode, cmd, proc.stdout, proc.stderr)

        try:
            output = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            raise ValueError(f"无法解析 trivy JSON 输出: {exc}") from exc

        vulnerabilities: List[Dict[str, Any]] = []
        for result in output.get("Results", []):
            for vuln in result.get("Vulnerabilities", []):
                vulnerabilities.append(vuln)

        return {
            "vulnerabilities": vulnerabilities,
            "total": len(vulnerabilities),
            "target": target,
            "scan_type": scan_type,
        }
