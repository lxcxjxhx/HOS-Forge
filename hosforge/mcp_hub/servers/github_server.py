"""GitHub MCP Server - GitHub API integration."""

import logging
import os
from typing import Any, Dict

from .base import BaseMCPServer

logger = logging.getLogger(__name__)


class GitHubServer(BaseMCPServer):
    """MCP server for GitHub API."""

    def __init__(self):
        """Initialize GitHub server."""
        super().__init__("github-server")
        self.register_tool(
            "create_issue",
            self.create_issue,
            "Create a GitHub issue"
        )
        self.register_tool(
            "create_pr",
            self.create_pr,
            "Create a GitHub pull request"
        )

    async def _get_github_client(self):
        """Get GitHub client using PyGithub."""
        try:
            from github import Github
        except ImportError:
            raise ImportError("PyGithub not installed. Run: pip install PyGithub")

        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise ValueError("GITHUB_TOKEN environment variable not set")

        return Github(token)

    async def create_issue(self, repo: str, title: str, body: str = "", **kwargs) -> Dict[str, Any]:
        """Create a GitHub issue.

        Args:
            repo: Repository in format 'owner/repo'
            title: Issue title
            body: Issue body

        Returns:
            Issue creation result
        """
        try:
            github = await self._get_github_client()
            repository = github.get_repo(repo)
            issue = repository.create_issue(title=title, body=body)

            logger.info(f"Created issue #{issue.number} in {repo}: {title}")
            return {
                "status": "success",
                "issue_number": issue.number,
                "issue_url": issue.html_url,
                "title": title,
                "repo": repo,
            }
        except ImportError as e:
            logger.error(f"PyGithub not installed: {e}")
            return {
                "status": "error",
                "message": f"GitHub client not available: {str(e)}"
            }
        except ValueError as e:
            logger.error(f"GitHub token not configured: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
        except Exception as e:
            logger.error(f"Failed to create issue: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to create issue: {str(e)}"
            }

    async def create_pr(self, repo: str, title: str, head: str, base: str = "main", body: str = "", **kwargs) -> Dict[str, Any]:
        """Create a GitHub pull request.

        Args:
            repo: Repository in format 'owner/repo'
            title: PR title
            head: Head branch
            base: Base branch
            body: PR body

        Returns:
            PR creation result
        """
        try:
            github = await self._get_github_client()
            repository = github.get_repo(repo)
            pr = repository.create_pull(title=title, body=body, head=head, base=base)

            logger.info(f"Created PR #{pr.number} in {repo}: {title}")
            return {
                "status": "success",
                "pr_number": pr.number,
                "pr_url": pr.html_url,
                "title": title,
                "repo": repo,
                "head": head,
                "base": base,
            }
        except ImportError as e:
            logger.error(f"PyGithub not installed: {e}")
            return {
                "status": "error",
                "message": f"GitHub client not available: {str(e)}"
            }
        except ValueError as e:
            logger.error(f"GitHub token not configured: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
        except Exception as e:
            logger.error(f"Failed to create PR: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to create PR: {str(e)}"
            }
