"""Security Audit Workflow - End-to-end integration."""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from hosforge.taskflow import WorkflowParser, TaskScheduler, CheckpointManager
from hosforge.taskflow.schema import TaskStatus
from hosforge.personalities import PersonalityLoader
from hosforge.mcp import MCPServerRegistry, MCPConfig
from hosforge.mcp.servers import (
    HOSLSServer, SemgrepServer, NucleiServer,
    CodeQLServer, GitHubServer,
)
from hosforge.memory import SecurityMemoryStore
from hosforge.verification import VerificationPipeline

logger = logging.getLogger(__name__)


class SecurityAuditWorkflow:
    """End-to-end security audit workflow orchestrator.
    
    Integrates all HOS-Forge components:
    - Taskflow Engine for workflow execution
    - Personality System for expert roles
    - MCP Hub for tool invocation
    - Security Memory for knowledge
    - Verification Loop for finding validation
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize security audit workflow.
        
        Args:
            config_path: Optional path to MCP config file
        """
        # Initialize components
        self.personality_loader = PersonalityLoader()
        self.memory_store = SecurityMemoryStore()
        self.verification_pipeline = VerificationPipeline(memory_store=self.memory_store)
        
        # Initialize MCP servers
        self.mcp_servers = {
            "hos_ls": HOSLSServer(),
            "semgrep": SemgrepServer(),
            "nuclei": NucleiServer(),
            "codeql": CodeQLServer(),
            "github": GitHubServer(),
        }
        
        # Initialize MCP registry
        if config_path:
            self.mcp_registry = MCPServerRegistry(MCPConfig.from_yaml_file(config_path))
        else:
            self.mcp_registry = MCPServerRegistry()
        
        logger.info("SecurityAuditWorkflow initialized")
    
    async def run_audit(self, target_path: str, workflow_file: Optional[str] = None) -> Dict[str, Any]:
        """Run a complete security audit on target path.
        
        Args:
            target_path: Path to code to audit
            workflow_file: Optional custom workflow file
            
        Returns:
            Audit results dictionary
        """
        results = {
            "target": target_path,
            "stages": {},
            "findings": [],
            "status": "running",
        }
        
        # Stage 1: Static Analysis
        logger.info("Stage 1: Static Analysis")
        static_results = await self._run_static_analysis(target_path)
        results["stages"]["static_analysis"] = static_results
        
        # Stage 2: Vulnerability Verification
        logger.info("Stage 2: Vulnerability Verification")
        findings = static_results.get("findings", [])
        verified_findings = []
        
        for finding in findings:
            verification_result = await self.verification_pipeline.run(finding)
            verified_findings.append({
                "finding": finding,
                "verification": verification_result,
            })
        
        results["stages"]["verification"] = verified_findings
        results["findings"] = verified_findings
        
        # Stage 3: Summary
        results["status"] = "completed"
        results["summary"] = {
            "total_findings": len(findings),
            "verified_findings": len([f for f in verified_findings if f["verification"].get("status") == "CLOSED"]),
            "rejected_findings": len([f for f in verified_findings if f["verification"].get("status") == "REJECTED"]),
        }
        
        logger.info(f"Audit completed: {results['summary']}")
        return results
    
    async def _run_static_analysis(self, target_path: str) -> Dict[str, Any]:
        """Run static analysis using MCP servers.
        
        Args:
            target_path: Path to code to analyze
            
        Returns:
            Static analysis results
        """
        results = {"findings": [], "tools_used": []}
        
        # Run HOS-LS scan
        hos_ls = self.mcp_servers["hos_ls"]
        hos_ls_result = await hos_ls.tools["scan_code"]["handler"](target_path=target_path)
        results["tools_used"].append("hos_ls")
        if hos_ls_result.get("findings"):
            results["findings"].extend(hos_ls_result["findings"])
        
        # Run Semgrep
        semgrep = self.mcp_servers["semgrep"]
        semgrep_result = await semgrep.tools["run_semgrep"]["handler"](target_path=target_path)
        results["tools_used"].append("semgrep")
        if semgrep_result.get("findings"):
            results["findings"].extend(semgrep_result["findings"])
        
        # Run CodeQL
        codeql = self.mcp_servers["codeql"]
        codeql_result = await codeql.tools["analyze_code"]["handler"](target_path=target_path)
        results["tools_used"].append("codeql")
        if codeql_result.get("findings"):
            results["findings"].extend(codeql_result["findings"])
        
        return results
    
    def list_personalities(self) -> List[str]:
        """List available security personalities."""
        return self.personality_loader.list_personalities()
    
    def list_mcp_servers(self) -> List[str]:
        """List available MCP servers."""
        return list(self.mcp_servers.keys())
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get security memory statistics."""
        return self.memory_store.get_stats()
