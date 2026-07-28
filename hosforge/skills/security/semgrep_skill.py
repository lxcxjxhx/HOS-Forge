"""Semgrep 静态代码分析 Skill，封装 semgrep 命令行工具调用。"""

import json
import subprocess
from typing import Any, Dict, List, Optional

from hosforge.skills.base_skill import Skill, SkillResult


class SemgrepScanSkill(Skill):
    """使用 Semgrep 进行静态代码分析的 Skill。

    通过调用 semgrep 命令行工具对指定路径执行代码扫描，
    解析 JSON 格式输出并返回结构化的分析结果。
    """

    def __init__(self) -> None:
        super().__init__(
            name="semgrep_scan",
            description="使用 Semgrep 进行静态代码分析",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "要扫描的文件或目录路径",
                    },
                    "language": {
                        "type": "string",
                        "description": "限定扫描的编程语言",
                    },
                    "config": {
                        "type": "string",
                        "description": "Semgrep 规则配置 (如 'auto', 'p/default', 或配置文件路径)",
                    },
                },
                "required": ["path"],
            },
        )

    def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """执行 semgrep 扫描并返回解析后的结果。

        Args:
            **kwargs: 包含 path, language, config 的参数。

        Returns:
            包含 findings 列表和统计信息的字典。

        Raises:
            FileNotFoundError: semgrep 命令不可用。
            subprocess.TimeoutExpired: 扫描超时。
        """
        path: str = kwargs["path"]
        language: Optional[str] = kwargs.get("language")
        config: Optional[str] = kwargs.get("config")

        cmd: List[str] = ["semgrep", "--json", "--quiet"]

        if config:
            cmd.extend(["--config", config])
        else:
            cmd.extend(["--config", "auto"])

        if language:
            cmd.extend(["--lang", language])

        cmd.append(path)

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
                "semgrep 命令未找到，请确认已安装 semgrep 并加入 PATH"
            ) from exc

        if proc.returncode not in (0, 1):
            raise subprocess.CalledProcessError(
                proc.returncode, cmd, proc.stdout, proc.stderr
            )

        try:
            output = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            raise ValueError(f"无法解析 semgrep JSON 输出: {exc}") from exc

        results: List[Dict[str, Any]] = output.get("results", [])
        errors: List[Dict[str, Any]] = output.get("errors", [])

        return {
            "findings": results,
            "total": len(results),
            "errors": errors,
            "path": path,
        }
