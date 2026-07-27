"""Workflow parser for YAML taskflow files."""

import yaml
from pathlib import Path
from typing import Any, Dict, Union
from .schema import Workflow, Task, TaskflowSchema


class WorkflowParser:
    """Parser for YAML workflow files."""
    
    @staticmethod
    def parse_file(file_path: Union[str, Path]) -> TaskflowSchema:
        """Parse a YAML workflow file.
        
        Args:
            file_path: Path to the YAML file
            
        Returns:
            TaskflowSchema object
            
        Raises:
            FileNotFoundError: If file doesn't exist
            yaml.YAMLError: If YAML is invalid
            ValueError: If schema is invalid
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Workflow file not found: {file_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        return WorkflowParser.parse_dict(data)
    
    @staticmethod
    def parse_string(yaml_content: str) -> TaskflowSchema:
        """Parse YAML content from string.
        
        Args:
            yaml_content: YAML content as string
            
        Returns:
            TaskflowSchema object
            
        Raises:
            yaml.YAMLError: If YAML is invalid
            ValueError: If schema is invalid
        """
        data = yaml.safe_load(yaml_content)
        return WorkflowParser.parse_dict(data)
    
    @staticmethod
    def parse_dict(data: Dict[str, Any]) -> TaskflowSchema:
        """Parse workflow from dictionary.
        
        Args:
            data: Dictionary containing workflow definition
            
        Returns:
            TaskflowSchema object
            
        Raises:
            ValueError: If schema is invalid
        """
        if not isinstance(data, dict):
            raise ValueError("Workflow must be a dictionary")
        
        # Validate required fields
        if 'hos' not in data:
            raise ValueError("Missing required field: 'hos'")
        
        if 'workflow' not in data:
            raise ValueError("Missing required field: 'workflow'")
        
        # Parse using schema
        schema = TaskflowSchema.from_yaml_dict(data)
        
        # Validate workflow
        WorkflowParser._validate_workflow(schema.workflow)
        
        return schema
    
    @staticmethod
    def _validate_workflow(workflow: Workflow) -> None:
        """Validate workflow structure.
        
        Args:
            workflow: Workflow to validate
            
        Raises:
            ValueError: If workflow is invalid
        """
        if not workflow.tasks:
            raise ValueError("Workflow must contain at least one task")
        
        # Check for duplicate task names
        task_names = [task.name for task in workflow.tasks]
        if len(task_names) != len(set(task_names)):
            raise ValueError("Duplicate task names found")
        
        # Validate task dependencies
        for task in workflow.tasks:
            for dep in task.depends_on:
                if dep not in task_names:
                    raise ValueError(
                        f"Task '{task.name}' depends on unknown task '{dep}'"
                    )
        
        # Check for circular dependencies
        WorkflowParser._check_circular_dependencies(workflow)
    
    @staticmethod
    def _check_circular_dependencies(workflow: Workflow) -> None:
        """Check for circular dependencies in workflow.
        
        Args:
            workflow: Workflow to check
            
        Raises:
            ValueError: If circular dependency found
        """
        visited = set()
        rec_stack = set()
        
        def _dfs(task_name: str) -> bool:
            """DFS to detect cycle."""
            visited.add(task_name)
            rec_stack.add(task_name)
            
            task = workflow.get_task(task_name)
            if task:
                for dep in task.depends_on:
                    if dep not in visited:
                        if _dfs(dep):
                            return True
                    elif dep in rec_stack:
                        return True
            
            rec_stack.remove(task_name)
            return False
        
        for task in workflow.tasks:
            if task.name not in visited:
                if _dfs(task.name):
                    raise ValueError("Circular dependency detected in workflow")
