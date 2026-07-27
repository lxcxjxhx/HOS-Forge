"""端到端工作流集成测试。"""

import asyncio
import tempfile
from pathlib import Path

import pytest

from hosforge.taskflow import WorkflowParser, WorkflowExecutor
from hosforge.personality import PersonalityLoader
from hosforge.mcp import MCPServerRegistry
from hosforge.memory import SecurityMemoryStore
from hosforge.verification import VerificationPipeline


class TestE2EWorkflow:
    """端到端工作流测试。"""

    @pytest.fixture
    def sample_workflow_yaml(self):
        """示例工作流 YAML。"""
        return """
hos:
  version: "1.0"

workflow:
  name: "Test Security Audit"
  description: "Test workflow for E2E testing"
  
  tasks:
    - name: static_scan
      agent:
        - sast_agent
      tools:
        - hos_ls
      depends_on: []
      timeout: 60
    
    - name: exploit_verify
      agent:
        - redteam_agent
      tools:
        - nuclei
      depends_on:
        - static_scan
      timeout: 120
    
    - name: patch_generation
      agent:
        - developer_agent
      tools: []
      depends_on:
        - exploit_verify
      timeout: 60
"""

    @pytest.fixture
    def temp_workflow_file(self, sample_workflow_yaml):
        """创建临时工作流文件。"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(sample_workflow_yaml)
            f.flush()
            yield f.name
        Path(f.name).unlink(missing_ok=True)

    def test_workflow_parsing(self, temp_workflow_file):
        """测试工作流解析。"""
        parser = WorkflowParser()
        workflow = parser.parse_file(temp_workflow_file)

        assert workflow.name == "Test Security Audit"
        assert workflow.version == "1.0"
        assert len(workflow.tasks) == 3

        # 验证任务依赖关系
        static_scan = workflow.get_task("static_scan")
        assert static_scan is not None
        assert len(static_scan.depends_on) == 0

        exploit_verify = workflow.get_task("exploit_verify")
        assert exploit_verify is not None
        assert "static_scan" in exploit_verify.depends_on

        patch_gen = workflow.get_task("patch_generation")
        assert patch_gen is not None
        assert "exploit_verify" in patch_gen.depends_on

    def test_workflow_execution_order(self, temp_workflow_file):
        """测试工作流执行顺序。"""
        parser = WorkflowParser()
        workflow = parser.parse_file(temp_workflow_file)

        # 获取执行顺序
        execution_order = workflow.get_execution_order()

        # 验证执行顺序正确
        assert len(execution_order) == 3
        assert execution_order[0] == "static_scan"
        assert execution_order[1] == "exploit_verify"
        assert execution_order[2] == "patch_generation"

    @pytest.mark.asyncio
    async def test_workflow_executor_initialization(self, temp_workflow_file):
        """测试工作流执行器初始化。"""
        parser = WorkflowParser()
        workflow = parser.parse_file(temp_workflow_file)

        executor = WorkflowExecutor(workflow, enable_checkpoint=False)

        assert executor.workflow == workflow
        assert executor.enable_checkpoint is False

    def test_personality_loading(self):
        """测试 Personality 加载。"""
        # 创建临时 personality 文件
        personality_yaml = """
name: test_security_engineer
role: Security testing engineer
description: Test security engineer for E2E testing
skills:
  - vulnerability scanning
  - code review
  - penetration testing
rules:
  - verify all findings
  - provide evidence
tools:
  - nuclei
  - semgrep
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(personality_yaml)
            f.flush()
            personality_file = f.name

        try:
            loader = PersonalityLoader()
            personality = loader.load(personality_file)

            assert personality.name == "test_security_engineer"
            assert personality.role == "Security testing engineer"
            assert len(personality.skills) == 3
            assert len(personality.tools) == 2
            assert "nuclei" in personality.tools
        finally:
            Path(personality_file).unlink(missing_ok=True)

    def test_mcp_server_registry(self):
        """测试 MCP Server 注册。"""
        registry = MCPServerRegistry()

        # 注册一个模拟的 MCP Server
        registry.register_server(
            name="test_server",
            description="Test MCP Server",
            tools=["tool1", "tool2"],
        )

        servers = registry.list_servers()
        assert len(servers) == 1
        assert servers[0]["name"] == "test_server"
        assert servers[0]["tool_count"] == 2

    def test_security_memory_store(self):
        """测试 Security Memory 存储。"""
        from hosforge.memory.schema import VulnerabilityFinding
        
        store = SecurityMemoryStore()

        # 添加漏洞发现
        finding = VulnerabilityFinding(
            id="TEST-001",
            title="SQL Injection",
            severity="high",
            cwe_id="CWE-89",
            file_path="test.py",
            line_number=42,
            description="SQL Injection vulnerability",
        )

        store.add_finding(finding)

        # 查询发现
        findings = store.search_findings(cwe_id="CWE-89")
        assert len(findings) == 1
        assert findings[0].id == "TEST-001"

    @pytest.mark.asyncio
    async def test_verification_pipeline(self):
        """测试验证流水线。"""
        store = SecurityMemoryStore()
        pipeline = VerificationPipeline(memory_store=store)

        # 创建测试发现
        finding = {
            "id": "TEST-001",
            "cwe_id": "CWE-89",
            "severity": "high",
            "file_path": "test.py",
            "line_number": 42,
            "description": "SQL Injection vulnerability",
            "code_snippet": "cursor.execute(f'SELECT * FROM users WHERE id = {user_id}')",
        }

        # 运行流水线
        result = await pipeline.run(finding)

        # 验证结果结构
        assert "finding_id" in result
        assert "final_state" in result
        assert "stages" in result

        # 验证阶段结果
        assert "verification" in result["stages"]
        assert "exploit" in result["stages"]
        assert "patch" in result["stages"]
        assert "review" in result["stages"]

    def test_checkpoint_mechanism(self, temp_workflow_file):
        """测试 checkpoint 机制。"""
        parser = WorkflowParser()
        workflow = parser.parse_file(temp_workflow_file)

        executor = WorkflowExecutor(workflow, enable_checkpoint=True)

        # 模拟保存 checkpoint
        checkpoint_data = {
            "workflow_name": workflow.name,
            "completed_tasks": ["static_scan"],
            "current_task": "exploit_verify",
        }

        checkpoint_id = executor.save_checkpoint(checkpoint_data)
        assert checkpoint_id is not None

        # 模拟加载 checkpoint
        loaded_data = executor.load_checkpoint(checkpoint_id)
        assert loaded_data is not None
        assert loaded_data["current_task"] == "exploit_verify"


class TestMultiAgentCollaboration:
    """多 Agent 协作测试。"""

    @pytest.fixture
    def multi_agent_workflow(self):
        """多 Agent 协作工作流。"""
        return """
hos:
  version: "1.0"

workflow:
  name: "Multi-Agent Collaboration Test"
  description: "Test multi-agent collaboration"
  
  tasks:
    - name: parallel_scan
      agent:
        - sast_agent
        - dast_agent
      tools:
        - semgrep
        - nuclei
      depends_on: []
      timeout: 120
    
    - name: verification
      agent:
        - redteam_agent
      tools:
        - exploit_db
      depends_on:
        - parallel_scan
      timeout: 180
    
    - name: remediation
      agent:
        - developer_agent
        - security_reviewer
      tools: []
      depends_on:
        - verification
      timeout: 120
"""

    def test_parallel_task_parsing(self, multi_agent_workflow):
        """测试并行任务解析。"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(multi_agent_workflow)
            f.flush()
            workflow_file = f.name

        try:
            parser = WorkflowParser()
            workflow = parser.parse_file(workflow_file)

            parallel_scan = workflow.get_task("parallel_scan")
            assert parallel_scan is not None
            assert len(parallel_scan.agent) == 2
            assert "sast_agent" in parallel_scan.agent
            assert "dast_agent" in parallel_scan.agent

            remediation = workflow.get_task("remediation")
            assert remediation is not None
            assert len(remediation.agent) == 2
        finally:
            Path(workflow_file).unlink(missing_ok=True)


class TestToolIntegration:
    """工具集成测试。"""

    def test_mcp_tool_invocation(self):
        """测试 MCP 工具调用。"""
        registry = MCPServerRegistry()

        # 注册模拟工具
        registry.register_server(
            name="test_scanner",
            description="Test Scanner",
            tools=["scan_file", "scan_directory"],
        )

        # 获取工具列表
        tools = registry.get_tools_for_server("test_scanner")
        assert len(tools) == 2
        assert "scan_file" in tools
        assert "scan_directory" in tools

    def test_tool_availability_check(self):
        """测试工具可用性检查。"""
        registry = MCPServerRegistry()

        registry.register_server(
            name="tool_server",
            description="Tool Server",
            tools=["available_tool"],
        )

        # 检查工具是否可用
        assert registry.is_tool_available("available_tool") is True
        assert registry.is_tool_available("unavailable_tool") is False
