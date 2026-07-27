"""Checkpoint manager for workflow state persistence."""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union
from .schema import TaskStatus, Workflow


class CheckpointManager:
    """Manager for saving and restoring workflow checkpoints."""
    
    def __init__(self, workflow: Workflow, checkpoint_dir: Union[str, Path] = ".checkpoints"):
        """Initialize checkpoint manager.
        
        Args:
            workflow: Workflow to manage checkpoints for
            checkpoint_dir: Directory to store checkpoint files
        """
        self.workflow = workflow
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    def save_checkpoint(self, checkpoint_name: str = "latest") -> Path:
        """Save current workflow state to checkpoint.
        
        Args:
            checkpoint_name: Name of the checkpoint
            
        Returns:
            Path to checkpoint file
        """
        checkpoint_data = {
            "workflow": self.workflow.to_dict(),
            "metadata": {
                "name": checkpoint_name,
                "version": "1.0"
            }
        }
        
        checkpoint_path = self.checkpoint_dir / f"{checkpoint_name}.json"
        
        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
        
        return checkpoint_path
    
    def load_checkpoint(self, checkpoint_name: str = "latest") -> Workflow:
        """Load workflow state from checkpoint.
        
        Args:
            checkpoint_name: Name of the checkpoint to load
            
        Returns:
            Workflow with restored state
            
        Raises:
            FileNotFoundError: If checkpoint doesn't exist
        """
        checkpoint_path = self.checkpoint_dir / f"{checkpoint_name}.json"
        
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")
        
        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            checkpoint_data = json.load(f)
        
        # Restore workflow state
        workflow_data = checkpoint_data.get("workflow", {})
        restored_workflow = Workflow.from_dict(workflow_data)
        
        return restored_workflow
    
    def list_checkpoints(self) -> list[str]:
        """List all available checkpoints.
        
        Returns:
            List of checkpoint names
        """
        checkpoints = []
        
        if self.checkpoint_dir.exists():
            for file_path in self.checkpoint_dir.glob("*.json"):
                checkpoints.append(file_path.stem)
        
        return sorted(checkpoints)
    
    def delete_checkpoint(self, checkpoint_name: str) -> bool:
        """Delete a checkpoint.
        
        Args:
            checkpoint_name: Name of checkpoint to delete
            
        Returns:
            True if deleted, False if not found
        """
        checkpoint_path = self.checkpoint_dir / f"{checkpoint_name}.json"
        
        if checkpoint_path.exists():
            checkpoint_path.unlink()
            return True
        
        return False
    
    def get_task_status(self, task_name: str, checkpoint_name: str = "latest") -> Optional[TaskStatus]:
        """Get task status from checkpoint.
        
        Args:
            task_name: Name of the task
            checkpoint_name: Name of the checkpoint
            
        Returns:
            Task status or None if task not found
        """
        try:
            workflow = self.load_checkpoint(checkpoint_name)
            task = workflow.get_task(task_name)
            return task.status if task else None
        except FileNotFoundError:
            return None
    
    def restore_task_status(self, checkpoint_name: str = "latest") -> None:
        """Restore task statuses from checkpoint to current workflow.
        
        Args:
            checkpoint_name: Name of the checkpoint to restore from
            
        Raises:
            FileNotFoundError: If checkpoint doesn't exist
        """
        restored_workflow = self.load_checkpoint(checkpoint_name)
        
        for restored_task in restored_workflow.tasks:
            current_task = self.workflow.get_task(restored_task.name)
            if current_task:
                current_task.status = restored_task.status
                current_task.result = restored_task.result
                current_task.error = restored_task.error
