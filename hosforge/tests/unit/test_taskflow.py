"""Unit tests for Taskflow Engine."""

import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

from hosforge.taskflow.schema import Task, TaskStatus, Workflow, TaskflowSchema
from hosforge.taskflow.parser import WorkflowParser
from hosforge.taskflow.executor import WorkflowExecutor
from hosforge.taskflow.scheduler import TaskScheduler
from hosforge.taskflow.registry import get_agent, get_tool, list_available_agents, list_available_tools


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------

class TestTaskSchema:
    def test_task_creation(self):
        task = Task(name="test_task", agent=["audit_agent"])
        assert task.name == "test_task"
        assert task.agent == ["audit_agent"]
        assert task.tools == []
        assert task.depends_on == []
        assert task.status == TaskStatus.PENDING

    def test_task_to_dict(self):
        task = Task(name="test_task", agent=["audit_agent"], tools=["semgrep"])
        d = task.to_dict()
        assert d["name"] == "test_task"
        assert d["agent"] == ["audit_agent"]
        assert d["tools"] == ["semgrep"]
        assert d["status"] == "pending"

    def test_task_from_dict(self):
        data = {
            "name": "test_task",
            "agent": ["audit_agent"],
            "tools": ["nmap"],
            "depends_on": ["prev_task"],
            "status": "success",
        }
        task = Task.from_dict(data)
        assert task.name == "test_task"
        assert task.status == TaskStatus.SUCCESS
        assert task.depends_on == ["prev_task"]


class TestWorkflowSchema:
    def test_workflow_creation(self):
        wf = Workflow(name="test_wf", description="Test workflow")
        assert wf.name == "test_wf"
        assert wf.tasks == []

    def test_get_task(self):
        task1 = Task(name="task1", agent=["audit_agent"])
        task2 = Task(name="task2", agent=["dast_agent"])
        wf = Workflow(name="test", tasks=[task1, task2])
        assert wf.get_task("task1") == task1
        assert wf.get_task("task2") == task2
        assert wf.get_task("nonexistent") is None

    def test_get_execution_order_no_deps(self):
        task1 = Task(name="task1", agent=["audit_agent"])
        task2 = Task(name="task2", agent=["dast_agent"])
        wf = Workflow(name="test", tasks=[task1, task2])
        order = wf.get_execution_order()
        assert set(order) == {"task1", "task2"}

    def test_get_execution_order_with_deps(self):
        task1 = Task(name="task1", agent=["audit_agent"])
        task2 = Task(name="task2", agent=["dast_agent"], depends_on=["task1"])
        task3 = Task(name="task3", agent=["security_reviewer"], depends_on=["task1", "task2"])
        wf = Workflow(name="test", tasks=[task1, task2, task3])
        order = wf.get_execution_order()
        assert order.index("task1") < order.index("task2")
        assert order.index("task2") < order.index("task3")

    def test_get_ready_tasks(self):
        task1 = Task(name="task1", agent=["audit_agent"])
        task2 = Task(name="task2", agent=["dast_agent"], depends_on=["task1"])
        wf = Workflow(name="test", tasks=[task1, task2])
        
        # Initially only task1 is ready
        ready = wf.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].name == "task1"
        
        # After task1 completes, task2 becomes ready
        task1.status = TaskStatus.SUCCESS
        ready = wf.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].name == "task2"


# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------

class TestWorkflowParser:
    def test_parse_valid_yaml(self, tmp_path):
        yaml_content = """
hos:
  version: "1.0"
workflow:
  name: "Test Workflow"
  description: "A test workflow"
  tasks:
    - name: task1
      agent:
        - audit_agent
      tools:
        - semgrep
    - name: task2
      agent:
        - dast_agent
      tools:
        - nuclei
      depends_on:
        - task1
"""
        wf_file = tmp_path / "test.yaml"
        wf_file.write_text(yaml_content)
        
        schema = WorkflowParser.parse_file(str(wf_file))
        assert schema.workflow.name == "Test Workflow"
        assert len(schema.workflow.tasks) == 2
        assert schema.workflow.tasks[1].depends_on == ["task1"]

    def test_parse_missing_hos_field(self, tmp_path):
        yaml_content = """
workflow:
  name: "Test"
  tasks:
    - name: task1
      agent:
        - audit_agent
"""
        wf_file = tmp_path / "test.yaml"
        wf_file.write_text(yaml_content)
        
        with pytest.raises(ValueError, match="Missing required field: 'hos'"):
            WorkflowParser.parse_file(str(wf_file))

    def test_parse_missing_workflow_field(self, tmp_path):
        yaml_content = """
hos:
  version: "1.0"
"""
        wf_file = tmp_path / "test.yaml"
        wf_file.write_text(yaml_content)
        
        with pytest.raises(ValueError, match="Missing required field: 'workflow'"):
            WorkflowParser.parse_file(str(wf_file))

    def test_parse_circular_dependency(self, tmp_path):
        yaml_content = """
hos:
  version: "1.0"
workflow:
  name: "Circular"
  tasks:
    - name: task1
      agent:
        - audit_agent
      depends_on:
        - task2
    - name: task2
      agent:
        - dast_agent
      depends_on:
        - task1
"""
        wf_file = tmp_path / "test.yaml"
        wf_file.write_text(yaml_content)
        
        with pytest.raises(ValueError, match="Circular dependency"):
            WorkflowParser.parse_file(str(wf_file))

    def test_parse_unknown_dependency(self, tmp_path):
        yaml_content = """
hos:
  version: "1.0"
workflow:
  name: "Bad dep"
  tasks:
    - name: task1
      agent:
        - audit_agent
      depends_on:
        - nonexistent
"""
        wf_file = tmp_path / "test.yaml"
        wf_file.write_text(yaml_content)
        
        with pytest.raises(ValueError, match="unknown task"):
            WorkflowParser.parse_file(str(wf_file))

    def test_parse_duplicate_task_names(self, tmp_path):
        yaml_content = """
hos:
  version: "1.0"
workflow:
  name: "Dup"
  tasks:
    - name: task1
      agent:
        - audit_agent
    - name: task1
      agent:
        - dast_agent
"""
        wf_file = tmp_path / "test.yaml"
        wf_file.write_text(yaml_content)
        
        with pytest.raises(ValueError, match="Duplicate task names"):
            WorkflowParser.parse_file(str(wf_file))

    def test_parse_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            WorkflowParser.parse_file("/nonexistent/path.yaml")


# ---------------------------------------------------------------------------
# Registry tests
# ---------------------------------------------------------------------------

class TestRegistry:
    def test_get_agent_known_types(self):
        for agent_type in ["audit_agent", "sast_agent", "redteam_agent", "dast_agent"]:
            agent = get_agent(agent_type)
            assert agent is not None

    def test_get_agent_unknown(self):
        with pytest.raises(ValueError, match="Unknown agent type"):
            get_agent("nonexistent_agent")

    def test_get_tool_known_types(self):
        for tool_name in ["nmap", "semgrep", "nuclei", "trivy", "burp"]:
            tool = get_tool(tool_name)
            assert tool is not None

    def test_get_tool_unknown(self):
        with pytest.raises(ValueError, match="Unknown tool"):
            get_tool("nonexistent_tool")

    def test_list_available_agents(self):
        agents = list_available_agents()
        assert "audit_agent" in agents
        assert "dast_agent" in agents

    def test_list_available_tools(self):
        tools = list_available_tools()
        assert "nmap" in tools
        assert "semgrep" in tools
        assert "nuclei" in tools
        assert "trivy" in tools


# ---------------------------------------------------------------------------
# Executor tests
# ---------------------------------------------------------------------------

class TestWorkflowExecutor:
    @pytest.mark.asyncio
    async def test_execute_simple_workflow(self):
        """Test executing a simple workflow with mocked tools."""
        task1 = Task(name="scan", agent=["audit_agent"], tools=["semgrep"])
        wf = Workflow(name="test_wf", tasks=[task1])
        
        executor = WorkflowExecutor(wf)
        
        # Mock the agent and tool
        mock_agent = AsyncMock()
        mock_finding = MagicMock()
        mock_finding.to_dict.return_value = {"vulns": []}
        mock_agent.analyze.return_value = mock_finding
        
        mock_tool = AsyncMock()
        mock_tool_result = MagicMock()
        mock_tool_result.success = True
        mock_tool_result.output = "scan output"
        mock_tool.run.return_value = mock_tool_result
        
        with (
            patch("hosforge.taskflow.executor.get_agent", return_value=mock_agent),
            patch("hosforge.taskflow.executor.get_tool", return_value=mock_tool),
        ):
            result = await executor.execute()
        
        assert result["workflow_name"] == "test_wf"
        assert "scan" in result["task_results"]
        assert result["task_results"]["scan"]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_execute_with_dependencies(self):
        """Test that tasks execute in dependency order."""
        task1 = Task(name="first", agent=["audit_agent"], tools=["semgrep"])
        task2 = Task(name="second", agent=["dast_agent"], tools=["nuclei"], depends_on=["first"])
        wf = Workflow(name="dep_wf", tasks=[task1, task2])
        
        executor = WorkflowExecutor(wf)
        
        mock_agent = AsyncMock()
        mock_finding = MagicMock()
        mock_finding.to_dict.return_value = {}
        mock_agent.analyze.return_value = mock_finding
        
        mock_tool = AsyncMock()
        mock_tool_result = MagicMock()
        mock_tool_result.success = True
        mock_tool_result.output = ""
        mock_tool.run.return_value = mock_tool_result
        
        with (
            patch("hosforge.taskflow.executor.get_agent", return_value=mock_agent),
            patch("hosforge.taskflow.executor.get_tool", return_value=mock_tool),
        ):
            result = await executor.execute()
        
        assert result["task_results"]["first"]["status"] == "completed"
        assert result["task_results"]["second"]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_execute_tool_failure(self):
        """Test that tool failures are captured."""
        task1 = Task(name="scan", agent=["audit_agent"], tools=["semgrep"])
        wf = Workflow(name="fail_wf", tasks=[task1])
        
        executor = WorkflowExecutor(wf)
        
        mock_agent = AsyncMock()
        mock_finding = MagicMock()
        mock_finding.to_dict.return_value = {}
        mock_agent.analyze.return_value = mock_finding
        
        mock_tool = AsyncMock()
        mock_tool.run.side_effect = Exception("Tool crashed")
        
        with (
            patch("hosforge.taskflow.executor.get_agent", return_value=mock_agent),
            patch("hosforge.taskflow.executor.get_tool", return_value=mock_tool),
        ):
            result = await executor.execute()
        
        # Task should still be recorded
        assert "scan" in result["task_results"]

    @pytest.mark.asyncio
    async def test_execute_with_config_kwargs(self):
        """Test that task config is passed to tools as kwargs."""
        task1 = Task(
            name="trivy_scan",
            agent=[],
            tools=["trivy"],
            config={"scan_type": "image", "severity": "HIGH,CRITICAL"},
        )
        wf = Workflow(name="config_wf", tasks=[task1])
        
        executor = WorkflowExecutor(wf)
        
        mock_tool = AsyncMock()
        mock_tool_result = MagicMock()
        mock_tool_result.success = True
        mock_tool_result.output = ""
        mock_tool.run.return_value = mock_tool_result
        
        with (
            patch("hosforge.taskflow.executor.get_tool", return_value=mock_tool),
        ):
            result = await executor.execute()
        
        # Verify tool.run was called with correct kwargs
        mock_tool.run.assert_called_once()
        call_kwargs = mock_tool.run.call_args[1]
        assert call_kwargs.get("scan_type") == "image"
        assert call_kwargs.get("severity") == "HIGH,CRITICAL"


# ---------------------------------------------------------------------------
# Scheduler tests
# ---------------------------------------------------------------------------

class TestTaskScheduler:
    @pytest.mark.asyncio
    async def test_parallel_execution(self):
        """Test that independent tasks run in parallel."""
        task1 = Task(name="task1", agent=["audit_agent"])
        task2 = Task(name="task2", agent=["dast_agent"])
        wf = Workflow(name="parallel_wf", tasks=[task1, task2])
        
        scheduler = TaskScheduler(wf)
        
        async def mock_handler(task):
            return {"task": task.name, "status": "done"}
        
        scheduler.register_handler("task1", mock_handler)
        scheduler.register_handler("task2", mock_handler)
        
        results = await scheduler.execute_workflow()
        assert "task1" in results
        assert "task2" in results

    def test_get_execution_plan(self):
        """Test execution plan generation."""
        task1 = Task(name="task1", agent=["audit_agent"])
        task2 = Task(name="task2", agent=["dast_agent"])
        task3 = Task(name="task3", agent=["security_reviewer"], depends_on=["task1", "task2"])
        wf = Workflow(name="plan_wf", tasks=[task1, task2, task3])
        
        scheduler = TaskScheduler(wf)
        plan = scheduler.get_execution_plan()
        
        # First stage should have task1 and task2 (parallel)
        assert set(plan[0]) == {"task1", "task2"}
        # Second stage should have task3
        assert plan[1] == ["task3"]

    @pytest.mark.asyncio
    async def test_deadlock_detection(self):
        """Test that circular dependencies are detected at runtime."""
        # This shouldn't happen because parser validates, but test scheduler robustness
        task1 = Task(name="task1", agent=["audit_agent"], depends_on=["task2"])
        task2 = Task(name="task2", agent=["dast_agent"], depends_on=["task1"])
        wf = Workflow(name="deadlock_wf", tasks=[task1, task2])
        
        scheduler = TaskScheduler(wf)
        
        async def mock_handler(task):
            return {"status": "done"}
        
        scheduler.register_handler("task1", mock_handler)
        scheduler.register_handler("task2", mock_handler)
        
        with pytest.raises(RuntimeError, match="deadlock|no tasks can proceed", ):
            await scheduler.execute_workflow()


# ---------------------------------------------------------------------------
# Checkpoint tests
# ---------------------------------------------------------------------------

class TestCheckpointManager:
    def test_save_and_load(self, tmp_path):
        from hosforge.taskflow.checkpoint import CheckpointManager
        
        task1 = Task(name="task1", agent=["audit_agent"], status=TaskStatus.SUCCESS)
        wf = Workflow(name="cp_wf", tasks=[task1])
        
        mgr = CheckpointManager(wf, checkpoint_dir=str(tmp_path))
        mgr.save_checkpoint("test_cp")
        
        # Verify file exists
        assert (tmp_path / "test_cp.json").exists()
        
        # Load and verify
        restored = mgr.load_checkpoint("test_cp")
        assert restored.name == "cp_wf"
        assert len(restored.tasks) == 1

    def test_list_checkpoints(self, tmp_path):
        from hosforge.taskflow.checkpoint import CheckpointManager
        
        wf = Workflow(name="test", tasks=[Task(name="t1", agent=["audit_agent"])])
        mgr = CheckpointManager(wf, checkpoint_dir=str(tmp_path))
        
        mgr.save_checkpoint("cp1")
        mgr.save_checkpoint("cp2")
        
        cps = mgr.list_checkpoints()
        assert "cp1" in cps
        assert "cp2" in cps

    def test_delete_checkpoint(self, tmp_path):
        from hosforge.taskflow.checkpoint import CheckpointManager
        
        wf = Workflow(name="test", tasks=[Task(name="t1", agent=["audit_agent"])])
        mgr = CheckpointManager(wf, checkpoint_dir=str(tmp_path))
        
        mgr.save_checkpoint("to_delete")
        assert mgr.delete_checkpoint("to_delete") is True
        assert mgr.delete_checkpoint("nonexistent") is False
