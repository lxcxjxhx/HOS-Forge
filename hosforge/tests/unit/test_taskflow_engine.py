"""Unit tests for Taskflow Engine components."""

import pytest
from pathlib import Path
from hosforge.taskflow import (
    Workflow,
    Task,
    TaskflowSchema,
    WorkflowParser,
    WorkflowExecutor,
    TaskScheduler,
)
from hosforge.taskflow.schema import TaskStatus


class TestWorkflowSchema:
    """Test workflow schema definitions."""

    def test_task_creation(self):
        """Test Task dataclass creation."""
        task = Task(
            name="test_task",
            agent=["audit_agent"],
            tools=["semgrep"],
            depends_on=[],
            timeout=300,
            description="Test task"
        )
        assert task.name == "test_task"
        assert task.agent == ["audit_agent"]
        assert task.tools == ["semgrep"]
        assert task.depends_on == []
        assert task.timeout == 300
        assert task.status == TaskStatus.PENDING

    def test_task_to_dict(self):
        """Test Task serialization to dict."""
        task = Task(
            name="test_task",
            agent=["audit_agent"],
            tools=["semgrep"],
            depends_on=["dep1"],
            timeout=120,
            description="Test"
        )
        task_dict = task.to_dict()
        assert task_dict["name"] == "test_task"
        assert task_dict["agent"] == ["audit_agent"]
        assert task_dict["tools"] == ["semgrep"]
        assert task_dict["depends_on"] == ["dep1"]
        assert task_dict["timeout"] == 120
        assert task_dict["status"] == "pending"

    def test_task_from_dict(self):
        """Test Task deserialization from dict."""
        data = {
            "name": "test_task",
            "agent": ["audit_agent"],
            "tools": ["semgrep"],
            "depends_on": [],
            "timeout": 180,
            "description": "Test",
            "status": "success"
        }
        task = Task.from_dict(data)
        assert task.name == "test_task"
        assert task.status == TaskStatus.SUCCESS

    def test_workflow_creation(self):
        """Test Workflow dataclass creation."""
        task1 = Task(name="task1", agent=["audit_agent"])
        task2 = Task(name="task2", agent=["audit_agent"], depends_on=["task1"])
        workflow = Workflow(
            name="Test Workflow",
            description="Test",
            tasks=[task1, task2]
        )
        assert workflow.name == "Test Workflow"
        assert len(workflow.tasks) == 2

    def test_workflow_get_task(self):
        """Test getting task by name."""
        task1 = Task(name="task1", agent=["audit_agent"])
        task2 = Task(name="task2", agent=["audit_agent"])
        workflow = Workflow(name="Test", tasks=[task1, task2])
        
        found = workflow.get_task("task1")
        assert found is not None
        assert found.name == "task1"
        
        not_found = workflow.get_task("nonexistent")
        assert not_found is None

    def test_workflow_get_execution_order(self):
        """Test topological sort for execution order."""
        task1 = Task(name="task1", agent=["audit_agent"])
        task2 = Task(name="task2", agent=["audit_agent"], depends_on=["task1"])
        task3 = Task(name="task3", agent=["audit_agent"], depends_on=["task1", "task2"])
        workflow = Workflow(name="Test", tasks=[task1, task2, task3])
        
        order = workflow.get_execution_order()
        assert order.index("task1") < order.index("task2")
        assert order.index("task2") < order.index("task3")

    def test_workflow_get_ready_tasks(self):
        """Test getting tasks ready for execution."""
        task1 = Task(name="task1", agent=["audit_agent"])
        task2 = Task(name="task2", agent=["audit_agent"], depends_on=["task1"])
        workflow = Workflow(name="Test", tasks=[task1, task2])
        
        # Initially only task1 is ready
        ready = workflow.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].name == "task1"
        
        # After task1 completes, task2 becomes ready
        task1.status = TaskStatus.SUCCESS
        ready = workflow.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].name == "task2"


class TestWorkflowParser:
    """Test workflow parser functionality."""

    def test_parse_dict_minimal(self):
        """Test parsing minimal workflow dict."""
        data = {
            "hos": {"version": "1.0"},
            "workflow": {
                "name": "Test",
                "tasks": [
                    {"name": "task1", "agent": ["audit_agent"]}
                ]
            }
        }
        schema = WorkflowParser.parse_dict(data)
        assert schema.workflow.name == "Test"
        assert len(schema.workflow.tasks) == 1

    def test_parse_dict_with_dependencies(self):
        """Test parsing workflow with dependencies."""
        data = {
            "hos": {"version": "1.0"},
            "workflow": {
                "name": "Test",
                "tasks": [
                    {"name": "task1", "agent": ["audit_agent"]},
                    {"name": "task2", "agent": ["audit_agent"], "depends_on": ["task1"]}
                ]
            }
        }
        schema = WorkflowParser.parse_dict(data)
        assert len(schema.workflow.tasks) == 2
        assert schema.workflow.tasks[1].depends_on == ["task1"]

    def test_parse_dict_missing_hos(self):
        """Test parsing fails when 'hos' field is missing."""
        data = {
            "workflow": {
                "name": "Test",
                "tasks": [{"name": "task1", "agent": ["audit_agent"]}]
            }
        }
        with pytest.raises(ValueError, match="Missing required field: 'hos'"):
            WorkflowParser.parse_dict(data)

    def test_parse_dict_missing_workflow(self):
        """Test parsing fails when 'workflow' field is missing."""
        data = {"hos": {"version": "1.0"}}
        with pytest.raises(ValueError, match="Missing required field: 'workflow'"):
            WorkflowParser.parse_dict(data)

    def test_parse_dict_no_tasks(self):
        """Test parsing fails when workflow has no tasks."""
        data = {
            "hos": {"version": "1.0"},
            "workflow": {"name": "Test", "tasks": []}
        }
        with pytest.raises(ValueError, match="must contain at least one task"):
            WorkflowParser.parse_dict(data)

    def test_parse_dict_duplicate_task_names(self):
        """Test parsing fails with duplicate task names."""
        data = {
            "hos": {"version": "1.0"},
            "workflow": {
                "name": "Test",
                "tasks": [
                    {"name": "task1", "agent": ["audit_agent"]},
                    {"name": "task1", "agent": ["audit_agent"]}
                ]
            }
        }
        with pytest.raises(ValueError, match="Duplicate task names"):
            WorkflowParser.parse_dict(data)

    def test_parse_dict_unknown_dependency(self):
        """Test parsing fails when dependency is unknown."""
        data = {
            "hos": {"version": "1.0"},
            "workflow": {
                "name": "Test",
                "tasks": [
                    {"name": "task1", "agent": ["audit_agent"], "depends_on": ["nonexistent"]}
                ]
            }
        }
        with pytest.raises(ValueError, match="depends on unknown task"):
            WorkflowParser.parse_dict(data)

    def test_parse_dict_circular_dependency(self):
        """Test parsing fails with circular dependencies."""
        data = {
            "hos": {"version": "1.0"},
            "workflow": {
                "name": "Test",
                "tasks": [
                    {"name": "task1", "agent": ["audit_agent"], "depends_on": ["task2"]},
                    {"name": "task2", "agent": ["audit_agent"], "depends_on": ["task1"]}
                ]
            }
        }
        with pytest.raises(ValueError, match="Circular dependency"):
            WorkflowParser.parse_dict(data)

    def test_parse_file(self, tmp_path):
        """Test parsing workflow from YAML file."""
        yaml_content = """
hos:
  version: "1.0"
workflow:
  name: "Test Workflow"
  tasks:
    - name: task1
      agent:
        - audit_agent
      tools:
        - semgrep
"""
        yaml_file = tmp_path / "test_workflow.yaml"
        yaml_file.write_text(yaml_content)
        
        schema = WorkflowParser.parse_file(yaml_file)
        assert schema.workflow.name == "Test Workflow"
        assert len(schema.workflow.tasks) == 1

    def test_parse_file_not_found(self):
        """Test parsing fails when file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            WorkflowParser.parse_file("/nonexistent/path.yaml")


class TestTaskScheduler:
    """Test task scheduler functionality."""

    def test_scheduler_initialization(self):
        """Test scheduler initialization."""
        task = Task(name="task1", agent=["audit_agent"])
        workflow = Workflow(name="Test", tasks=[task])
        scheduler = TaskScheduler(workflow)
        assert scheduler.workflow == workflow

    def test_register_handler(self):
        """Test registering task handler."""
        task = Task(name="task1", agent=["audit_agent"])
        workflow = Workflow(name="Test", tasks=[task])
        scheduler = TaskScheduler(workflow)
        
        async def handler(t):
            return {"result": "ok"}
        
        scheduler.register_handler("task1", handler)
        assert "task1" in scheduler.task_handlers

    @pytest.mark.asyncio
    async def test_execute_task(self):
        """Test executing a single task."""
        task = Task(name="task1", agent=["audit_agent"])
        workflow = Workflow(name="Test", tasks=[task])
        scheduler = TaskScheduler(workflow)
        
        async def handler(t):
            return {"result": "success"}
        
        scheduler.register_handler("task1", handler)
        result = await scheduler.execute_task(task)
        
        assert result == {"result": "success"}
        assert task.status == TaskStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_execute_task_no_handler(self):
        """Test executing task without handler raises error."""
        task = Task(name="task1", agent=["audit_agent"])
        workflow = Workflow(name="Test", tasks=[task])
        scheduler = TaskScheduler(workflow)
        
        with pytest.raises(ValueError, match="No handler registered"):
            await scheduler.execute_task(task)

    def test_get_execution_plan_simple(self):
        """Test getting execution plan for simple workflow."""
        task1 = Task(name="task1", agent=["audit_agent"])
        task2 = Task(name="task2", agent=["audit_agent"])
        workflow = Workflow(name="Test", tasks=[task1, task2])
        scheduler = TaskScheduler(workflow)
        
        stages = scheduler.get_execution_plan()
        assert len(stages) == 1
        assert set(stages[0]) == {"task1", "task2"}

    def test_get_execution_plan_with_dependencies(self):
        """Test getting execution plan with dependencies."""
        task1 = Task(name="task1", agent=["audit_agent"])
        task2 = Task(name="task2", agent=["audit_agent"], depends_on=["task1"])
        task3 = Task(name="task3", agent=["audit_agent"])
        workflow = Workflow(name="Test", tasks=[task1, task2, task3])
        scheduler = TaskScheduler(workflow)
        
        stages = scheduler.get_execution_plan()
        assert len(stages) == 2
        assert set(stages[0]) == {"task1", "task3"}
        assert stages[1] == ["task2"]


class TestWorkflowExecutor:
    """Test workflow executor functionality."""

    def test_executor_initialization(self):
        """Test executor initialization."""
        task = Task(name="task1", agent=["audit_agent"])
        workflow = Workflow(name="Test", tasks=[task])
        executor = WorkflowExecutor(workflow)
        
        assert executor.workflow == workflow
        assert executor.enable_parallel is True
        assert executor.enable_checkpoint is False

    def test_executor_with_checkpoint(self, tmp_path):
        """Test executor initialization with checkpoint enabled."""
        task = Task(name="task1", agent=["audit_agent"])
        workflow = Workflow(name="Test", tasks=[task])
        executor = WorkflowExecutor(
            workflow,
            enable_checkpoint=True,
            checkpoint_dir=str(tmp_path / "checkpoints")
        )
        
        assert executor.enable_checkpoint is True
        assert (tmp_path / "checkpoints").exists()

    def test_get_execution_plan(self):
        """Test getting execution plan from executor."""
        task1 = Task(name="task1", agent=["audit_agent"])
        task2 = Task(name="task2", agent=["audit_agent"], depends_on=["task1"])
        workflow = Workflow(name="Test", tasks=[task1, task2])
        executor = WorkflowExecutor(workflow)
        
        stages = executor.get_execution_plan()
        assert len(stages) == 2

    def test_generate_summary_empty(self):
        """Test generating summary with no results."""
        task = Task(name="task1", agent=["audit_agent"])
        workflow = Workflow(name="Test", tasks=[task])
        executor = WorkflowExecutor(workflow)
        
        summary = executor._generate_summary()
        assert summary["total_tasks"] == 1
        assert summary["completed"] == 0
        assert summary["failed"] == 0
        assert summary["success_rate"] == 0

    def test_generate_summary_with_results(self):
        """Test generating summary with execution results."""
        task1 = Task(name="task1", agent=["audit_agent"])
        task2 = Task(name="task2", agent=["audit_agent"])
        workflow = Workflow(name="Test", tasks=[task1, task2])
        executor = WorkflowExecutor(workflow)
        
        executor.execution_results = {
            "task1": {"status": "completed"},
            "task2": {"status": "failed"}
        }
        
        summary = executor._generate_summary()
        assert summary["total_tasks"] == 2
        assert summary["completed"] == 1
        assert summary["failed"] == 1
        assert summary["success_rate"] == 50.0
