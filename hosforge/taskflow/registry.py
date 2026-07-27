"""Agent and tool registry for Taskflow Engine.

Maps string names from YAML workflow definitions to concrete
Agent / Tool instances so the executor can look them up at runtime.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from hosforge.security_agents.base import BaseSecurityAgent
from hosforge.security_tools.base import BaseSecurityTool

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Agent registry
# ---------------------------------------------------------------------------

# Map agent type strings (used in YAML) → concrete agent classes
_AGENT_TYPE_MAP: Dict[str, str] = {
    # YAML names → Python class names
    "audit_agent": "AuditAgent",
    "sast_agent": "AuditAgent",
    "redteam_agent": "AttackAgent",
    "blueteam_agent": "DefenseAgent",
    "developer_agent": "DefenseAgent",
    "security_reviewer": "SecuritySupervisorAgent",
}


def _lazy_import_agent(class_name: str) -> type:
    """Import and return an agent class by name (lazy to avoid circular imports)."""
    if class_name == "AuditAgent":
        from hosforge.security_agents.audit import AuditAgent
        return AuditAgent
    if class_name == "AttackAgent":
        from hosforge.security_agents.attack import AttackAgent
        return AttackAgent
    if class_name == "DefenseAgent":
        from hosforge.security_agents.defense import DefenseAgent
        return DefenseAgent
    if class_name == "SecuritySupervisorAgent":
        from hosforge.security_agents.supervisor import SecuritySupervisorAgent
        return SecuritySupervisorAgent
    raise ValueError(f"Unknown agent class: {class_name}")


def get_agent(agent_type: str) -> BaseSecurityAgent:
    """Instantiate and return a security agent by its YAML type name.

    Args:
        agent_type: Agent type string from the workflow YAML
                    (e.g. "audit_agent", "redteam_agent")

    Returns:
        A fresh BaseSecurityAgent instance
    """
    class_name = _AGENT_TYPE_MAP.get(agent_type)
    if class_name is None:
        raise ValueError(
            f"Unknown agent type '{agent_type}'. "
            f"Available: {sorted(_AGENT_TYPE_MAP.keys())}"
        )
    cls = _lazy_import_agent(class_name)
    return cls()


# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------

_TOOL_TYPE_MAP: Dict[str, str] = {
    "nmap": "NmapTool",
    "semgrep": "SemgrepTool",
    "nuclei": "NucleiTool",
    "burp": "BurpTool",
    # Aliases used in some workflow files
    "hos_ls": "SemgrepTool",   # fallback: treat as SAST
    "codeql": "SemgrepTool",   # fallback: treat as SAST
    "exploit_db": "NucleiTool",  # fallback
    "github": "SemgrepTool",   # placeholder
}


def _lazy_import_tool(class_name: str) -> type:
    """Import and return a tool class by name."""
    if class_name == "NmapTool":
        from hosforge.security_tools.nmap_tool import NmapTool
        return NmapTool
    if class_name == "SemgrepTool":
        from hosforge.security_tools.semgrep_tool import SemgrepTool
        return SemgrepTool
    if class_name == "NucleiTool":
        from hosforge.security_tools.nuclei_tool import NucleiTool
        return NucleiTool
    if class_name == "BurpTool":
        from hosforge.security_tools.burp_tool import BurpTool
        return BurpTool
    raise ValueError(f"Unknown tool class: {class_name}")


def get_tool(tool_name: str) -> BaseSecurityTool:
    """Instantiate and return a security tool by its YAML name.

    Args:
        tool_name: Tool name from the workflow YAML (e.g. "nmap", "semgrep")

    Returns:
        A fresh BaseSecurityTool instance
    """
    class_name = _TOOL_TYPE_MAP.get(tool_name)
    if class_name is None:
        raise ValueError(
            f"Unknown tool '{tool_name}'. "
            f"Available: {sorted(_TOOL_TYPE_MAP.keys())}"
        )
    cls = _lazy_import_tool(class_name)
    return cls()


def list_available_agents() -> list[str]:
    """Return sorted list of available agent type names."""
    return sorted(set(_AGENT_TYPE_MAP.keys()))


def list_available_tools() -> list[str]:
    """Return sorted list of available tool names."""
    return sorted(set(_TOOL_TYPE_MAP.keys()))
