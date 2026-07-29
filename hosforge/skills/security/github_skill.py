"""GitHub 集成 Skill，封装 GitHub API 操作。"""

import json
import subprocess
from typing import Any, Dict, List, Optional

from hosforge.skills.base_skill import Skill


class GitHubIntegrationSkill(Skill):
    """GitHub 集成操作的 Skill。

    通过 gh CLI 工具执行 GitHub API 操作，
    包括创建 Issue、创建 PR 和列出 Issue 等。
    """

    VALID_ACTIONS = ("create_issue", "create_pr", "list_issues")

    def __init__(self) -> None:
        super().__init__(
            name="github_integration",
            description="GitHub 集成操作",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create_issue", "create_pr", "list_issues"],
                        "description": "要执行的 GitHub 操作",
                    },
                    "repo": {
                        "type": "string",
                        "description": "GitHub 仓库 (格式: owner/repo)",
                    },
                    "title": {
                        "type": "string",
                        "description": "Issue 或 PR 的标题",
                    },
                    "body": {
                        "type": "string",
                        "description": "Issue 或 PR 的正文内容",
                    },
                    "head": {
                        "type": "string",
                        "description": "PR 的源分支",
                    },
                    "base": {
                        "type": "string",
                        "description": "PR 的目标分支",
                    },
                    "labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Issue 的标签列表",
                    },
                    "state": {
                        "type": "string",
                        "enum": ["open", "closed", "all"],
                        "description": "列出 Issue 时的状态过滤",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "列出 Issue 时的最大返回数量",
                    },
                },
                "required": ["action", "repo"],
            },
        )

    def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """根据 action 参数执行对应的 GitHub 操作。

        Args:
            **kwargs: 包含 action, repo 及其他操作相关参数。

        Returns:
            包含操作结果的字典。

        Raises:
            ValueError: action 无效或缺少必要参数。
            FileNotFoundError: gh 命令不可用。
        """
        action: str = kwargs["action"]
        repo: str = kwargs["repo"]

        if action not in self.VALID_ACTIONS:
            raise ValueError(f"无效的 action '{action}'，可选值: {self.VALID_ACTIONS}")

        handler = {
            "create_issue": self._create_issue,
            "create_pr": self._create_pr,
            "list_issues": self._list_issues,
        }[action]

        return handler(repo=repo, **kwargs)

    def _create_issue(self, *, repo: str, **kwargs: Any) -> Dict[str, Any]:
        """创建 GitHub Issue。"""
        title: str = kwargs.get("title", "")
        body: str = kwargs.get("body", "")
        labels: Optional[List[str]] = kwargs.get("labels")

        if not title:
            raise ValueError("创建 Issue 需要提供 title 参数")

        cmd: List[str] = [
            "gh",
            "issue",
            "create",
            "--repo",
            repo,
            "--title",
            title,
            "--body",
            body,
        ]

        if labels:
            for label in labels:
                cmd.extend(["--label", label])

        result = self._run_gh(cmd)
        return {"action": "create_issue", "repo": repo, "output": result}

    def _create_pr(self, *, repo: str, **kwargs: Any) -> Dict[str, Any]:
        """创建 GitHub Pull Request。"""
        title: str = kwargs.get("title", "")
        body: str = kwargs.get("body", "")
        head: str = kwargs.get("head", "")
        base: str = kwargs.get("base", "")

        if not title:
            raise ValueError("创建 PR 需要提供 title 参数")
        if not head:
            raise ValueError("创建 PR 需要提供 head 参数")

        cmd: List[str] = [
            "gh",
            "pr",
            "create",
            "--repo",
            repo,
            "--title",
            title,
            "--body",
            body,
            "--head",
            head,
        ]

        if base:
            cmd.extend(["--base", base])

        result = self._run_gh(cmd)
        return {"action": "create_pr", "repo": repo, "output": result}

    def _list_issues(self, *, repo: str, **kwargs: Any) -> Dict[str, Any]:
        """列出 GitHub Issue。"""
        state: str = kwargs.get("state", "open")
        limit: int = kwargs.get("limit", 30)

        cmd: List[str] = [
            "gh",
            "issue",
            "list",
            "--repo",
            repo,
            "--state",
            state,
            "--limit",
            str(limit),
            "--json",
            "number,title,state,labels,createdAt",
        ]

        result = self._run_gh(cmd)
        try:
            issues = json.loads(result)
        except json.JSONDecodeError:
            issues = []

        return {
            "action": "list_issues",
            "repo": repo,
            "issues": issues,
            "total": len(issues),
        }

    @staticmethod
    def _run_gh(cmd: List[str]) -> str:
        """执行 gh 命令并返回 stdout。

        Args:
            cmd: 命令及参数列表。

        Returns:
            命令的 stdout 输出。

        Raises:
            FileNotFoundError: gh 命令不可用。
            subprocess.CalledProcessError: 命令执行失败。
        """
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
        except FileNotFoundError as exc:
            raise FileNotFoundError("gh 命令未找到，请确认已安装 GitHub CLI 并加入 PATH") from exc

        if proc.returncode != 0:
            raise subprocess.CalledProcessError(proc.returncode, cmd, proc.stdout, proc.stderr)

        return proc.stdout.strip()
