"""Nuclei 漏洞扫描 Skill，封装 nuclei 命令行工具调用。"""

import json
import subprocess
from typing import Any, Dict, List, Optional

from hosforge.skills.base_skill import Skill, SkillResult


class NucleiScanSkill(Skill):
    """使用 Nuclei 进行漏洞扫描的 Skill。

    通过调用 nuclei 命令行工具对目标执行漏洞扫描，
    解析 JSON 格式输出并返回结构化的扫描结果。
    """

    def __init__(self) -> None:
        super().__init__(
            name="nuclei_scan",
            description="使用 Nuclei 进行漏洞扫描",
            parameters={
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "扫描目标 URL 或 IP",
                    },
                    "templates": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "要使用的 nuclei 模板列表",
                    },
                    "severity": {
                        "type": "string",
                        "description": "过滤严重级别 (info, low, medium, high, critical)",
                    },
                },
                "required": ["target"],
            },
        )

    def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """执行 nuclei 扫描并返回解析后的结果。

        Args:
            **kwargs: 包含 target, templates, severity 的参数。

        Returns:
            包含 findings 列表和统计信息的字典。

        Raises:
            FileNotFoundError: nuclei 命令不可用。
            subprocess.TimeoutExpired: 扫描超时。
        """
        target: str = kwargs["target"]
        templates: Optional[List[str]] = kwargs.get("templates")
        severity: Optional[str] = kwargs.get("severity")

        cmd: List[str] = ["nuclei", "-target", target, "-json", "-silent"]

        if templates:
            for tpl in templates:
                cmd.extend(["-t", tpl])

        if severity:
            cmd.extend(["-severity", severity])

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,
                check=False,
            )
        except FileNotFoundError as exc:
            raise FileNotFoundError(
                "nuclei 命令未找到，请确认已安装 nuclei 并加入 PATH"
            ) from exc

        if proc.returncode not in (0, 1):
            raise subprocess.CalledProcessError(
                proc.returncode, cmd, proc.stdout, proc.stderr
            )

        findings: List[Dict[str, Any]] = []
        for line in proc.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                findings.append(json.loads(line))
            except json.JSONDecodeError:
                continue

        return {
            "findings": findings,
            "total": len(findings),
            "target": target,
        }
