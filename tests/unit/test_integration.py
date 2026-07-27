"""Integration tests for HOS-Forge platform."""

import pytest
import asyncio
from pathlib import Path

from hosforge.integration import SecurityAuditWorkflow
from hosforge.taskflow import WorkflowParser
from hosforge.personalities import PersonalityLoader
from hosforge.mcp.servers import HOSLSServer, SemgrepServer
from hosforge.memory import SecurityMemoryStore
from hosforge.verification import VerificationPipeline, FindingState


class TestSecurityAuditWorkflow:
    """Tests for SecurityAuditWorkflow integration."""
    
    def test_workflow_initialization(self):
        """Test workflow can be initialized."""
        workflow = SecurityAuditWorkflow()
        assert workflow is not None
        assert len(workflow.list_mcp_servers()) > 0
        assert len(workflow.list_personalities()) > 0
    
    @pytest.mark.asyncio
    async def test_static_analysis(self):
        """Test static analysis stage."""
        workflow = SecurityAuditWorkflow()
        results = await workflow._run_static_analysis("/tmp/test")
        assert "findings" in results
        assert "tools_used" in results
        assert "hos_ls" in results["tools_used"]
    
    def test_memory_stats(self):
        """Test memory stats retrieval."""
        workflow = SecurityAuditWorkflow()
        stats = workflow.get_memory_stats()
        assert isinstance(stats, dict)


class TestVerificationPipelineIntegration:
    """Tests for verification pipeline integration."""
    
    @pytest.mark.asyncio
    async def test_full_pipeline_with_memory(self):
        """Test full pipeline with memory store."""
        memory = SecurityMemoryStore()
        pipeline = VerificationPipeline(memory_store=memory)
        
        finding = {
            "id": "TEST-001",
            "title": "SQL Injection",
            "severity": "high",
            "file_path": "test.py",
            "line_number": 42,
            "description": "Potential SQL injection",
        }
        
        result = await pipeline.run(finding)
        assert result is not None
        assert "status" in result


class TestEndToEndWorkflow:
    """End-to-end workflow tests."""
    
    def test_workflow_file_parsing(self):
        """Test that the example workflow file can be parsed."""
        workflows_dir = Path(__file__).parent.parent.parent / "hosforge" / "taskflow" / "workflows"
        workflow_file = workflows_dir / "security-audit.yaml"
        
        if workflow_file.exists():
            schema = WorkflowParser.parse_file(workflow_file)
            assert schema.workflow.name == "Security Audit Workflow"
            assert len(schema.workflow.tasks) >= 4
    
    def test_personality_loading(self):
        """Test that all personalities can be loaded."""
        loader = PersonalityLoader()
        names = loader.list_personalities()
        
        assert len(names) >= 4
        
        for name in names:
            p = loader.get_personality(name)
            assert p.name == name
            assert p.role
            assert len(p.skills) > 0
    
    def test_mcp_server_tools(self):
        """Test that MCP servers expose expected tools."""
        hos_ls = HOSLSServer()
        tools = hos_ls.get_tool_list()
        assert len(tools) > 0
        assert any(t["name"] == "scan_code" for t in tools)
        
        semgrep = SemgrepServer()
        tools = semgrep.get_tool_list()
        assert any(t["name"] == "run_semgrep" for t in tools)
