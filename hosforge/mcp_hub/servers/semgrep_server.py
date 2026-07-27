"""Semgrep MCP Server - SAST integration."""

import logging
from typing import Any, Dict

from .base import BaseMCPServer

logger = logging.getLogger(__name__)


class SemgrepServer(BaseMCPServer):
    """MCP server for Semgrep SAST tool."""

    def __init__(self):
        """Initialize Semgrep server."""
        super().__init__("semgrep-server")
        self.register_tool(
            "run_semgrep",
            self.run_semgrep,
            "Run Semgrep static analysis on code"
        )

    async def run_semgrep(self, target_path: str, config: str = "auto", **kwargs) -> Dict[str, Any]:
        """Run Semgrep analysis.

        Args:
            target_path: Path to code to analyze
            config: Semgrep config to use (e.g., "auto", "p/default", "p/security")
            **kwargs: Additional arguments (rules, languages, severity, timeout, etc.)

        Returns:
            Analysis results with findings
        """
        try:
            from hosforge.security_tools.semgrep_tool import SemgrepTool
            
            tool = SemgrepTool()
            
            # Build tool arguments
            tool_kwargs = {}
            if config and config != "auto":
                tool_kwargs["config"] = config
            if "rules" in kwargs:
                tool_kwargs["rules"] = kwargs["rules"]
            if "languages" in kwargs:
                tool_kwargs["languages"] = kwargs["languages"]
            if "severity" in kwargs:
                tool_kwargs["severity"] = kwargs["severity"]
            if "timeout" in kwargs:
                tool_kwargs["timeout"] = kwargs["timeout"]
            
            # Execute scan
            result = await tool.run(target_path, **tool_kwargs)
            
            return {
                "status": "success" if result.success else "failed",
                "tool_name": result.tool_name,
                "findings": result.raw_data.get("findings", []),
                "errors": result.raw_data.get("errors", []),
                "output": result.output[:1000] if result.output else "",
                "error": result.error if not result.success else None,
                "exit_code": result.raw_data.get("exit_code"),
            }
            
        except ImportError as e:
            logger.error(f"Failed to import SemgrepTool: {e}")
            return {
                "status": "error",
                "message": f"Semgrep tool not available: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Semgrep scan failed: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Scan failed: {str(e)}"
            }
