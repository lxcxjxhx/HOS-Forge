"""Taskflow schema definitions for YAML workflow parsing."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class AgentType(str, Enum):
    """Agent type enumeration."""
    AUDIT_AGENT = "audit_agent"
    REDTEAM_AGENT = "redteam_agent"
    BLUETEAM_AGENT = "blueteam_agent"
    DEVELOPER_AGENT = "developer_agent"
    SECURITY_REVIEWER = "security_reviewer"
    SAST_AGENT = "sast_agent"


@dataclass
class Task:
    """Task definition in workflow."""
    name: str
    agent: List[str]
    tools: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)
    timeout: int = 300
    description: str = ""
    config: Dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "name": self.name,
            "agent": self.agent,
            "tools": self.tools,
            "depends_on": self.depends_on,
            "timeout": self.timeout,
            "description": self.description,
            "config": self.config,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create task from dictionary.
        
        Args:
            data: Dictionary data
            
        Returns:
            Task object
        """
        status = data.get("status", "pending")
        if isinstance(status, str):
            status = TaskStatus(status)
        
        return cls(
            name=data["name"],
            agent=data.get("agent", []),
            tools=data.get("tools", []),
            depends_on=data.get("depends_on", []),
            timeout=data.get("timeout", 300),
            description=data.get("description", ""),
            config=data.get("config", {}),
            status=status,
            result=data.get("result"),
            error=data.get("error", ""),
        )


@dataclass
class Workflow:
    """Workflow definition."""
    name: str = ""
    description: str = ""
    tasks: List[Task] = field(default_factory=list)
    version: str = "1.0"
    
    def get_task(self, task_name: str) -> Optional[Task]:
        """Get task by name.
        
        Args:
            task_name: Name of the task
            
        Returns:
            Task object if found, None otherwise
        """
        for task in self.tasks:
            if task.name == task_name:
                return task
        return None
    
    def get_execution_order(self) -> List[str]:
        """Get task execution order based on dependencies.
        
        Returns:
            List of task names in execution order
        """
        # Topological sort
        visited = set()
        order = []
        
        def visit(task_name: str):
            if task_name in visited:
                return
            visited.add(task_name)
            task = self.get_task(task_name)
            if task:
                for dep in task.depends_on:
                    visit(dep)
            order.append(task_name)
        
        for task in self.tasks:
            visit(task.name)
        
        return order
    
    def get_ready_tasks(self) -> List[Task]:
        """Get tasks that are ready to execute (all dependencies satisfied).
        
        Returns:
            List of Task objects that can be executed now
        """
        ready = []
        for task in self.tasks:
            if task.status != TaskStatus.PENDING:
                continue
            
            # Check if all dependencies are satisfied
            all_deps_done = True
            for dep_name in task.depends_on:
                dep_task = self.get_task(dep_name)
                if dep_task is None or dep_task.status != TaskStatus.SUCCESS:
                    all_deps_done = False
                    break
            
            if all_deps_done:
                ready.append(task)
        
        return ready
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "name": self.name,
            "description": self.description,
            "tasks": [task.to_dict() for task in self.tasks],
            "version": self.version,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Workflow':
        """Create workflow from dictionary.
        
        Args:
            data: Dictionary data
            
        Returns:
            Workflow object
        """
        tasks = [Task.from_dict(t) for t in data.get("tasks", [])]
        
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            tasks=tasks,
            version=data.get("version", "1.0"),
        )


@dataclass
class TaskflowSchema:
    """Complete taskflow schema."""
    workflow: Workflow
    hos_version: str = "1.0"

    def __getattr__(self, name: str) -> Any:
        """Proxy attribute access to internal workflow."""
        return getattr(self.workflow, name)

    @classmethod
    def from_yaml_dict(cls, data: Dict[str, Any]) -> 'TaskflowSchema':
        """Create TaskflowSchema from YAML dictionary.
        
        Args:
            data: Dictionary from YAML file
            
        Returns:
            TaskflowSchema object
        """
        hos_data = data.get('hos', {})
        workflow_data = data.get('workflow', {})
        
        # Parse tasks
        tasks = []
        for task_data in workflow_data.get('tasks', []):
            task = Task(
                name=task_data['name'],
                agent=task_data.get('agent', []),
                tools=task_data.get('tools', []),
                depends_on=task_data.get('depends_on', []),
                timeout=task_data.get('timeout', 300),
                description=task_data.get('description', ''),
                config=task_data.get('config', {}),
            )
            tasks.append(task)
        
        # Parse workflow
        workflow = Workflow(
            name=workflow_data.get('name', 'Unnamed Workflow'),
            description=workflow_data.get('description', ''),
            tasks=tasks,
            version=workflow_data.get('version', '1.0'),
        )
        
        return cls(
            workflow=workflow,
            hos_version=hos_data.get('version', '1.0'),
        )