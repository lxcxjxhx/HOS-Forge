"""Workflow executor for running taskflows."""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .schema import Workflow, Task
from .registry import get_agent, get_tool


logger = logging.getLogger(__name__)


class WorkflowExecutor:
    """Executor for running workflows."""
    
    def __init__(
        self,
        workflow: Workflow,
        enable_checkpoint: bool = False,
        checkpoint_dir: str = ".hos_checkpoints"
    ):
        """Initialize workflow executor.
        
        Args:
            workflow: Workflow to execute
            enable_checkpoint: Enable checkpoint/resume functionality
            checkpoint_dir: Directory to store checkpoints
        """
        self.workflow = workflow
        self.enable_checkpoint = enable_checkpoint
        self.checkpoint_dir = Path(checkpoint_dir)
        self.execution_results: Dict[str, Any] = {}
        self.current_checkpoint_id: Optional[str] = None
        
        if enable_checkpoint:
            self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    async def execute(self) -> Dict[str, Any]:
        """Execute the workflow.
        
        Returns:
            Dictionary containing execution results
        """
        logger.info(f"Starting workflow execution: {self.workflow.name}")
        
        # Get execution order
        execution_order = self.workflow.get_execution_order()
        
        # Execute tasks in order
        for task_name in execution_order:
            task = self.workflow.get_task(task_name)
            if not task:
                logger.error(f"Task not found: {task_name}")
                continue
            
            # Check dependencies
            if not self._check_dependencies(task):
                logger.error(f"Dependencies not met for task: {task_name}")
                self.execution_results[task_name] = {
                    "status": "failed",
                    "error": "Dependencies not met"
                }
                continue
            
            # Execute task
            logger.info(f"Executing task: {task_name}")
            start_time = time.time()
            
            try:
                result = await self._execute_task(task)
                self.execution_results[task_name] = {
                    "status": "completed",
                    "result": result,
                    "duration": time.time() - start_time
                }
                
                # Save checkpoint if enabled
                if self.enable_checkpoint:
                    self._save_checkpoint(task_name)
                
            except Exception as e:
                logger.error(f"Task execution failed: {task_name}", exc_info=True)
                self.execution_results[task_name] = {
                    "status": "failed",
                    "error": str(e),
                    "duration": time.time() - start_time
                }
        
        logger.info(f"Workflow execution completed: {self.workflow.name}")
        
        return {
            "workflow_name": self.workflow.name,
            "task_results": self.execution_results,
            "checkpoint_id": self.current_checkpoint_id
        }
    
    async def _execute_task(self, task: Task) -> Any:
        """Execute a single task with real agent and tool calls.
        
        Args:
            task: Task to execute
            
        Returns:
            Task execution result
        """
        logger.info(f"Executing task '{task.name}' with agents: {task.agent}, tools: {task.tools}")
        
        # Get target from task config or use workflow name
        target = task.config.get("target", self.workflow.name)
        
        # Execute with each agent
        agent_results = []
        for agent_name in task.agent:
            try:
                # Get agent instance from registry
                agent = get_agent(agent_name)
                logger.info(f"Running agent: {agent_name}")
                
                # Run agent analysis
                finding = await agent.analyze(target)
                
                agent_result = {
                    "agent": agent_name,
                    "status": "success",
                    "finding": finding.to_dict() if hasattr(finding, "to_dict") else str(finding)
                }
                
                # If task requires fix and agent supports it
                if task.config.get("auto_fix", False) and hasattr(agent, "fix"):
                    for vuln in finding.vulnerabilities:
                        try:
                            fix_result = await agent.fix(vuln)
                            agent_result.setdefault("fixes", []).append({
                                "vulnerability": vuln.name,
                                "fix": fix_result
                            })
                        except Exception as e:
                            logger.warning(f"Fix failed for {vuln.name}: {e}")
                
                agent_results.append(agent_result)
                
            except Exception as e:
                logger.error(f"Agent {agent_name} failed: {e}")
                agent_results.append({
                    "agent": agent_name,
                    "status": "failed",
                    "error": str(e)
                })
        
        # Execute with each tool
        tool_results = []
        for tool_name in task.tools:
            try:
                # Get tool instance from registry
                tool = get_tool(tool_name)
                logger.info(f"Running tool: {tool_name}")
                
                # Run tool
                tool_result = await tool.run(target)
                
                tool_results.append({
                    "tool": tool_name,
                    "status": "success" if tool_result.success else "failed",
                    "output": tool_result.output[:500] if tool_result.output else "",  # Truncate long output
                    "error": tool_result.error if not tool_result.success else None
                })
                
            except Exception as e:
                logger.error(f"Tool {tool_name} failed: {e}")
                tool_results.append({
                    "tool": tool_name,
                    "status": "failed",
                    "error": str(e)
                })
        
        # Determine overall task status
        all_agents_success = all(r["status"] == "success" for r in agent_results)
        all_tools_success = all(r["status"] == "success" for r in tool_results)
        overall_status = "success" if (all_agents_success and all_tools_success) else "partial"
        
        return {
            "task": task.name,
            "status": overall_status,
            "agents": agent_results,
            "tools": tool_results,
            "target": target
        }
    
    def _check_dependencies(self, task: Task) -> bool:
        """Check if task dependencies are met.
        
        Args:
            task: Task to check
            
        Returns:
            True if all dependencies are completed successfully
        """
        for dep in task.depends_on:
            if dep not in self.execution_results:
                return False
            if self.execution_results[dep]["status"] != "completed":
                return False
        return True
    
    def _save_checkpoint(self, completed_task: str) -> None:
        """Save checkpoint after task completion.
        
        Args:
            completed_task: Name of completed task
        """
        checkpoint_id = f"{self.workflow.name}_{int(time.time())}"
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.json"
        
        checkpoint_data = {
            "workflow_name": self.workflow.name,
            "completed_tasks": [
                name for name, result in self.execution_results.items()
                if result["status"] == "completed"
            ],
            "current_task": completed_task,
            "timestamp": time.time()
        }
        
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)
        
        self.current_checkpoint_id = checkpoint_id
        logger.info(f"Checkpoint saved: {checkpoint_id}")
    
    def save_checkpoint(self, checkpoint_data: Dict[str, Any]) -> str:
        """Save checkpoint with provided data.
        
        Args:
            checkpoint_data: Checkpoint data to save
            
        Returns:
            Checkpoint ID
        """
        checkpoint_id = f"{self.workflow.name}_{int(time.time())}"
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.json"
        
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)
        
        self.current_checkpoint_id = checkpoint_id
        logger.info(f"Checkpoint saved: {checkpoint_id}")
        return checkpoint_id
    
    def load_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """Load checkpoint by ID.
        
        Args:
            checkpoint_id: Checkpoint ID to load
            
        Returns:
            Checkpoint data if found, None otherwise
        """
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.json"
        
        if not checkpoint_file.exists():
            logger.error(f"Checkpoint not found: {checkpoint_id}")
            return None
        
        with open(checkpoint_file, 'r') as f:
            checkpoint_data = json.load(f)
        
        # Restore execution results for completed tasks
        for task_name in checkpoint_data["completed_tasks"]:
            self.execution_results[task_name] = {
                "status": "completed",
                "result": None,
                "duration": 0
            }
        
        self.current_checkpoint_id = checkpoint_id
        logger.info(f"Checkpoint loaded: {checkpoint_id}")
        
        return checkpoint_data
