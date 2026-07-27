"""Nuclei MCP Server - Vulnerability scanning integration."""

import logging
from typing import Any, Dict

from .base import BaseMCPServer

logger = logging.getLogger(__name__)


class NucleiServer(BaseMCPServer):
    """MCP server for Nuclei vulnerability scanner."""

    def __init__(self):
        """Initialize Nuclei server."""
        super().__init__("nuclei-server")
        self.register_tool(
            "scan_target",
            self.scan_target,
            "Scan target for vulnerabilities using Nuclei"
        )

    async def scan_target(self, target: str, templates: str = None, **kwargs) -> Dict[str, Any]:
        """Scan target for vulnerabilities.

        Args:
            target: Target URL or IP to scan
            templates: Nuclei templates to use
            **kwargs: Additional arguments (tags, severity, timeout, etc.)

        Returns:
            Scan results with findings
        """
        try:
            from hosforge.security_tools.nuclei_tool import NucleiTool
            
            tool = NucleiTool()
            
            # Build tool arguments
            tool_kwargs = {}
            if templates:
                tool_kwargs["templates"] = templates
            if "tags" in kwargs:
                tool_kwargs["tags"] = kwargs["tags"]
            if "severity" in kwargs:
                tool_kwargs["severity"] = kwargs["severity"]
            if "timeout" in kwargs:
                tool_kwargs["timeout"] = kwargs["timeout"]
            
            # Execute scan
            result = await tool.run(target, **tool_kwargs)
            
            return {
                "status": "success" if result.success else "failed",
                "tool_name": result.tool_name,
                "findings": result.raw_data.get("findings", []),
                "output": result.output[:1000] if result.output else "",
                "error": result.error if not result.success else None,
                "exit_code": result.raw_data.get("exit_code"),
            }
            
        except ImportError as e:
            logger.error(f"Failed to import NucleiTool: {e}")
            return {
                "status": "error",
                "message": f"Nuclei tool not available: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Nuclei scan failed: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Scan failed: {str(e)}"
            }
