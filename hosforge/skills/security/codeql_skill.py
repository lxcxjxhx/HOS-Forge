"""CodeQL 安全分析 Skill，封装 codeql 命令行工具调用。"""

import json
import subprocess
from typing import Any, Dict, List, Optional

from hosforge.skills.base_skill import Skill, SkillResult


class CodeQLScanSkill(Skill):
    """使用 CodeQL 进行安全分析的 Skill。

    通过调用 codeql 命令行工具对指定数据库执行查询，
    解析 SARIF 格式输出并返回结构化的安全告警列表。
    """

    def __init__(self) -> None:
        super().__init__(
            name="codeql_scan",
            description="使用 CodeQL 进行安全分析",
            parameters={
                "type": "object",
                "properties": {
                    "database": {
                        "type": "string",
                        "description": "CodeQL 数据库路径",
                    },
                    "query_suite": {
                        "type": "string",
                        "description": "查询套件路径或名称 (如 security-extended)",
                    },
                    "language": {
                        "type": "string",
                        "description": "查询语言 (如 javascript, python, java)",
                    },
                },
                "required": ["database"],
            },
        )

    def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """执行 codeql 分析并返回解析后的结果。

        Args:
            **kwargs: 包含 database, query_suite, language 的参数。

        Returns:
            包含 alerts 列表和统计信息的字典。

        Raises:
            FileNotFoundError: codeql 命令不可用。
            subprocess.TimeoutExpired: 扫描超时。
        """
        database: str = kwargs["database"]
        query_suite: Optional[str] = kwargs.get("query_suite")
        language: Optional[str] = kwargs.get("language")

        cmd: List[str] = [
            "codeql", "database", "analyze",
            "--format", "sarif-latest",
            "--output", "-",
        ]

        if query_suite:
            cmd.append(query_suite)
        elif language:
            cmd.append(f"{language}-security-extended")

        cmd.append(database)

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800,
                check=False,
            )
        except FileNotFoundError as exc:
            raise FileNotFoundError(
                "codeql 命令未找到，请确认已安装 codeql 并加入 PATH"
            ) from exc

        if proc.returncode not in (0, 1):
            raise subprocess.CalledProcessError(
                proc.returncode, cmd, proc.stdout, proc.stderr
            )

        try:
            sarif = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            raise ValueError(f"无法解析 CodeQL SARIF 输出: {exc}") from exc

        alerts: List[Dict[str, Any]] = []
        for run in sarif.get("runs", []):
            for result in run.get("results", []):
                alert = {
                    "rule_id": result.get("ruleId"),
                    "message": result.get("message", {}).get("text"),
                    "level": result.get("level"),
                    "locations": result.get("locations", []),
                }
                alerts.append(alert)

        return {
            "alerts": alerts,
            "total": len(alerts),
            "database": database,
        }
