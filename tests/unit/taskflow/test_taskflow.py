"""Unit tests for HOS Taskflow Engine."""

import pytest
from pathlib import Path
from hosforge.taskflow import (
    Workflow,
    Task,
    TaskflowSchema,
    WorkflowParser,
    TaskScheduler,
    CheckpointManager,
)
from hosforge.taskflow.schema import TaskStatus, AgentType


class TestTaskSchema:
    """Tests for Task dataclass."""
    
    def test_task_creation(self):
        """Test basic task creation."""
        task = Task(
            name="test_task",
            agent=["audit_agent"],
            tools=["hos_ls"],
            depends_on=["dep_task"],
            timeout=300,
        )
        
        assert task.name == "test_task"
        assert task.agent == ["audit_agent"]
        assert task.tools == ["hos_ls"]
        assert task.depends_on == ["dep_task"]
        assert task.timeout == 300
        assert task.status == TaskStatus.PENDING
    
    def test_task_to_dict(self):
        """Test task serialization."""
        task = Task(
            name="test_task",
            agent=["audit_agent"],
            status=TaskStatus.SUCCESS,
        )
        
        task_dict = task.to_dict()
        
        assert task_dict["name"] == "test_task"
        assert task_dict["agent"] == ["audit_agent"]
        assert task_dict["status"] == "success"
    
    def test_task_from_dict(self):
        """Test task deserialization."""
        task_dict = {
            "name": "test_task",
            "agent": ["audit_agent"],
            "tools": ["hos_ls"],
            "status": "running",
        }
        
        task = Task.from_dict(task_dict)
        
        assert task.name == "test_task"
        assert task.agent == ["audit_agent"]
        assert task.status == TaskStatus.RUNNING


class TestWorkflowSchema:
    """Tests for Workflow dataclass."""
    
    def test_workflow_creation(self):
        """Test basic workflow creation."""
        workflow = Workflow(
            version="1.0",
            name="test_workflow",
            description="Test workflow",
        )
        
        assert workflow.version == "1.0"
        assert workflow.name == "test_workflow"
        assert workflow.description == "Test workflow"
        assert workflow.tasks == []
    
    def test_get_task(self):
        """Test getting task by name."""
        task1 = Task(name="task1", agent=["audit_agent"])
        task2 = Task(name="task2", agent=["redteam_agent"])
        
        workflow = Workflow(
            version="1.0",
            name="test_workflow",
            tasks=[task1, task2],
        )
        
        found_task = workflow.get_task("task1")
        assert found_task is not None
        assert found_task.name == "task1"
        
        not_found = workflow.get_task("nonexistent")
        assert not_found is None
    
    def test_get_ready_tasks(self):
        """Test getting tasks that are ready to execute."""
        task1 = Task(name="task1", agent=["audit_agent"], depends_on=[])
        task2 = Task(name="task2", agent=["redteam_agent"], depends_on=["task1"])
        task3 = Task(name="task3", agent=["blueteam_agent"], depends_on=[])
        
        workflow = Workflow(
            version="1.0",
            name="test_workflow",
            tasks=[task1, task2, task3],
        )
        
        ready = workflow.get_ready_tasks()
        assert len(ready) == 2
        assert task1 in ready
        assert task3 in ready
        assert task2 not in ready
        
        # Mark task1 as success
        task1.status = TaskStatus.SUCCESS
        
        ready = workflow.get_ready_tasks()
        assert len(ready) == 2
        assert task2 in ready
        assert task3 in ready


class TestWorkflowParser:
    """Tests for WorkflowParser."""
    
    def test_parse_dict_basic(self):
        """Test basic dictionary parsing."""
        data = {
            "hos": {"version": "1.0"},
            "workflow": {
                "name": "test_workflow",
                "tasks": [
                    {
                        "name": "task1",
                        "agent": ["audit_agent"],
                        "tools": ["hos_ls"],
                    }
                ]
            }
        }
        
        schema = WorkflowParser.parse_dict(data)
        
        assert schema.workflow.name == "test_workflow"
        assert len(schema.workflow.tasks) == 1
        assert schema.workflow.tasks[0].name == "task1"
    
    def test_parse_dict_missing_hos(self):
        """Test parsing with missing 'hos' field."""
        data = {
            "workflow": {
                "name": "test_workflow",
                "tasks": []
            }
        }
        
        with pytest.raises(ValueError, match="Missing required field: 'hos'"):
            WorkflowParser.parse_dict(data)
    
    def test_parse_dict_missing_workflow(self):
        """Test parsing with missing 'workflow' field."""
        data = {
            "hos": {"version": "1.0"}
        }
        
        with pytest.raises(ValueError, match="Missing required field: 'workflow'"):
            WorkflowParser.parse_dict(data)
    
    def test_parse_dict_no_tasks(self):
        """Test parsing with no tasks."""
        data = {
            "hos": {"version": "1.0"},
            "workflow": {
                "name": "test_workflow",
                "tasks": []
            }
        }
        
        with pytest.raises(ValueError, match="must contain at least one task"):
            WorkflowParser.parse_dict(data)
    
    def test_parse_dict_duplicate_task_names(self):
        """Test parsing with duplicate task names."""
        data = {
            "hos": {"version": "1.0"},
            "workflow": {
                "name": "test_workflow",
                "tasks": [
                    {"name": "task1", "agent": ["audit_agent"]},
                    {"name": "task1", "agent": ["redteam_agent"]},
                ]
            }
        }
        
        with pytest.raises(ValueError, match="Duplicate task names"):
            WorkflowParser.parse_dict(data)
    
    def test_parse_dict_unknown_dependency(self):
        """Test parsing with unknown dependency."""
        data = {
            "hos": {"version": "1.0"},
            "workflow": {
                "name": "test_workflow",
                "tasks": [
                    {
                        "name": "task1",
                        "agent": ["audit_agent"],
                        "depends_on": ["nonexistent"],
                    }
                ]
            }
        }
        
        with pytest.raises(ValueError, match="unknown task"):
            WorkflowParser.parse_dict(data)
    
    def test_parse_dict_circular_dependency(self):
        """Test parsing with circular dependency."""
        data = {
            "hos": {"version": "1.0"},
            "workflow": {
                "name": "test_workflow",
                "tasks": [
                    {
                        "name": "task1",
                        "agent": ["audit_agent"],
                        "depends_on": ["task2"],
                    },
                    {
                        "name": "task2",
                        "agent": ["redteam_agent"],
                        "depends_on": ["task1"],
                    }
                ]
            }
        }
        
        with pytest.raises(ValueError, match="Circular dependency"):
            WorkflowParser.parse_dict(data)
    
    def test_parse_string(self):
        """Test parsing from YAML string."""
        yaml_content = """
hos:
  version: "1.0"

workflow:
  name: test_workflow
  tasks:
    - name: task1
      agent:
        - audit_agent
"""
        
        schema = WorkflowParser.parse_string(yaml_content)
        
        assert schema.workflow.name == "test_workflow"
        assert len(schema.workflow.tasks) == 1


class TestTaskScheduler:
    """Tests for TaskScheduler."""
    
    @pytest.mark.asyncio
    async def test_execute_task(self):
        """Test executing a single task."""
        task = Task(name="test_task", agent=["audit_agent"])
        workflow = Workflow(
            version="1.0",
            name="test_workflow",
            tasks=[task],
        )
        
        scheduler = TaskScheduler(workflow)
        
        async def handler(t):
            return {"result": "success"}
        
        scheduler.register_handler("test_task", handler)
        
        result = await scheduler.execute_task(task)
        
        assert result == {"result": "success"}
        assert task.status == TaskStatus.SUCCESS
        assert task.result == {"result": "success"}
    
    @pytest.mark.asyncio
    async def test_execute_task_failure(self):
        """Test task execution failure."""
        task = Task(name="test_task", agent=["audit_agent"])
        workflow = Workflow(
            version="1.0",
            name="test_workflow",
            tasks=[task],
        )
        
        scheduler = TaskScheduler(workflow)
        
        async def handler(t):
            raise Exception("Task failed")
        
        scheduler.register_handler("test_task", handler)
        
        with pytest.raises(Exception, match="Task failed"):
            await scheduler.execute_task(task)
        
        assert task.status == TaskStatus.FAILED
        assert task.error == "Task failed"
    
    def test_get_execution_plan(self):
        """Test execution plan generation."""
        task1 = Task(name="task1", agent=["audit_agent"], depends_on=[])
        task2 = Task(name="task2", agent=["redteam_agent"], depends_on=["task1"])
        task3 = Task(name="task3", agent=["blueteam_agent"], depends_on=[])
        
        workflow = Workflow(
            version="1.0",
            name="test_workflow",
            tasks=[task1, task2, task3],
        )
        
        scheduler = TaskScheduler(workflow)
        plan = scheduler.get_execution_plan()
        
        assert len(plan) == 2
        assert "task1" in plan[0]
        assert "task3" in plan[0]
        assert "task2" in plan[1]


class TestCheckpointManager:
    """Tests for CheckpointManager."""
    
    def test_save_and_load_checkpoint(self, tmp_path):
        """Test saving and loading checkpoint."""
        task = Task(name="test_task", agent=["audit_agent"], status=TaskStatus.SUCCESS)
        workflow = Workflow(
            version="1.0",
            name="test_workflow",
            tasks=[task],
        )
        
        manager = CheckpointManager(workflow, checkpoint_dir=tmp_path)
        
        # Save checkpoint
        checkpoint_path = manager.save_checkpoint("test")
        assert checkpoint_path.exists()
        
        # Load checkpoint
        restored = manager.load_checkpoint("test")
        assert restored.name == "test_workflow"
        assert len(restored.tasks) == 1
        assert restored.tasks[0].status == TaskStatus.SUCCESS
    
    def test_list_checkpoints(self, tmp_path):
        """Test listing checkpoints."""
        workflow = Workflow(
            version="1.0",
            name="test_workflow",
            tasks=[Task(name="task1", agent=["audit_agent"])],
        )
        
        manager = CheckpointManager(workflow, checkpoint_dir=tmp_path)
        
        manager.save_checkpoint("checkpoint1")
        manager.save_checkpoint("checkpoint2")
        
        checkpoints = manager.list_checkpoints()
        assert len(checkpoints) == 2
        assert "checkpoint1" in checkpoints
        assert "checkpoint2" in checkpoints
    
    def test_delete_checkpoint(self, tmp_path):
        """Test deleting checkpoint."""
        workflow = Workflow(
            version="1.0",
            name="test_workflow",
            tasks=[Task(name="task1", agent=["audit_agent"])],
        )
        
        manager = CheckpointManager(workflow, checkpoint_dir=tmp_path)
        
        manager.save_checkpoint("test")
        assert "test" in manager.list_checkpoints()
        
        result = manager.delete_checkpoint("test")
        assert result is True
        assert "test" not in manager.list_checkpoints()
