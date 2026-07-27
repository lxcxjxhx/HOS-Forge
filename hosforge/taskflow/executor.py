"""Workflow executor for running taskflows."""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .schema import Workflow, Task, TaskStatus
from .registry import get_agent, get_tool
from .scheduler import TaskScheduler


logger = logging.getLogger(__name__)


class WorkflowExecutor:
    """Executor for running workflows with parallel task execution support."""
    
    def __init__(
        self,
        workflow: Workflow,
        enable_checkpoint: bool = False,
        checkpoint_dir: str = ".hos_checkpoints",
        enable_parallel: bool = True
    ):
        """Initialize workflow executor.
        
        Args:
            workflow: Workflow to execute
            enable_checkpoint: Enable checkpoint/resume functionality
            checkpoint_dir: Directory to store checkpoints
            enable_parallel: Enable parallel task execution (default: True)
        """
        self.workflow = workflow
        self.enable_checkpoint = enable_checkpoint
        self.checkpoint_dir = Path(checkpoint_dir)
        self.enable_parallel = enable_parallel
        self.execution_results: Dict[str, Any] = {}
        self.current_checkpoint_id: Optional[str] = None
        self.scheduler = TaskScheduler(workflow)
        
        if enable_checkpoint:
            self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    async def execute(self) -> Dict[str, Any]:
        """Execute the workflow with parallel task support.
        
        Returns:
            Dictionary containing execution results
        """
        logger.info(f"Starting workflow execution: {self.workflow.name}")
        start_time = time.time()
        
        if self.enable_parallel:
            # Use scheduler for parallel execution
            await self._execute_with_scheduler()
        else:
            # Fallback to sequential execution
            await self._execute_sequential()
        
        total_duration = time.time() - start_time
        logger.info(f"Workflow execution completed: {self.workflow.name} in {total_duration:.2f}s")
        
        return {
            "workflow_name": self.workflow.name,
            "task_results": self.execution_results,
            "total_duration": total_duration,
            "checkpoint_id": self.current_checkpoint_id,
            "summary": self._generate_summary()
        }
    
    async def _execute_with_scheduler(self) -> None:
        """Execute workflow using scheduler for parallel task execution."""
        # Register task handlers
        for task in self.workflow.tasks:
            self.scheduler.register_handler(task.name, self._execute_task)
        
        # Execute workflow
        try:
            results = await self.scheduler.execute_workflow()
            
            # Update execution results
            for task_name, result in results.items():
                if isinstance(result, dict) and "error" in result:
                    self.execution_results[task_name] = {
                        "status": "failed",
                        "error": result["error"],
                        "duration": 0
                    }
                else:
                    self.execution_results[task_name] = {
                        "status": "completed",
                        "result": result,
                        "duration": result.get("duration", 0) if isinstance(result, dict) else 0
                    }
                    
                    # Save checkpoint if enabled
                    if self.enable_checkpoint:
                        self._save_checkpoint(task_name)
        
        except RuntimeError as e:
            logger.error(f"Workflow execution failed: {e}")
            raise
    
    async def _execute_sequential(self) -> None:
        """Execute workflow sequentially (fallback mode)."""
        execution_order = self.workflow.get_execution_order()
        
        for task_name in execution_order:
            task = self.workflow.get_task(task_name)
            if not task:
                logger.error(f"Task not found: {task_name}")
                continue
            
            # Check dependencies
            if not self._check_dependencies(task):
                logger.error(f"Dependencies not met for task: {task_name}")
                self.execution_results[task_name] = {
                    "status": "skipped",
                    "error": "Dependencies not met"
                }
                task.status = TaskStatus.SKIPPED
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
                task.status = TaskStatus.SUCCESS
                
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
                task.status = TaskStatus.FAILED
    
    async def _execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute a single task with real agent and tool calls.
        
        Args:
            task: Task to execute
            
        Returns:
            Task execution result dictionary
        """
        logger.info(f"Executing task '{task.name}' with agents: {task.agent}, tools: {task.tools}")
        task_start = time.time()
        
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
                
                # Prepare tool kwargs from task config
                tool_kwargs = self._prepare_tool_kwargs(tool_name, task.config)
                
                # Run tool with kwargs
                tool_result = await tool.run(target, **tool_kwargs)
                
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
            "target": target,
            "duration": time.time() - task_start
        }
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate execution summary.
        
        Returns:
            Summary dictionary with statistics
        """
        total_tasks = len(self.workflow.tasks)
        completed = sum(1 for r in self.execution_results.values() if r.get("status") == "completed")
        failed = sum(1 for r in self.execution_results.values() if r.get("status") == "failed")
        skipped = sum(1 for r in self.execution_results.values() if r.get("status") == "skipped")
        
        return {
            "total_tasks": total_tasks,
            "completed": completed,
            "failed": failed,
            "skipped": skipped,
            "success_rate": (completed / total_tasks * 100) if total_tasks > 0 else 0
        }
    
    def get_execution_plan(self) -> List[List[str]]:
        """Get execution plan as list of parallel stages.
        
        Returns:
            List of stages, where each stage is a list of task names
        """
        return self.scheduler.get_execution_plan()
    
    def print_execution_plan(self) -> None:
        """Print execution plan in a human-readable format."""
        stages = self.get_execution_plan()
        print(f"\n{'='*60}")
        print(f"Workflow: {self.workflow.name}")
        print(f"{'='*60}")
        print(f"Total tasks: {len(self.workflow.tasks)}")
        print(f"Parallel stages: {len(stages)}")
        print(f"{'='*60}\n")
        
        for i, stage in enumerate(stages, 1):
            print(f"Stage {i}: {', '.join(stage)}")
            if len(stage) > 1:
                print(f"  → {len(stage)} tasks will run in parallel")
        print()
    
    def _prepare_tool_kwargs(self, tool_name: str, task_config: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare tool-specific kwargs from task config.
        
        Args:
            tool_name: Name of the tool
            task_config: Task configuration dictionary
            
        Returns:
            Dictionary of kwargs to pass to tool.run()
        """
        kwargs: Dict[str, Any] = {}
        
        # Generic config keys that apply to all tools
        if "timeout" in task_config:
            kwargs["timeout"] = task_config["timeout"]
        
        # Tool-specific config mappings
        if tool_name == "trivy":
            if "scan_type" in task_config:
                kwargs["scan_type"] = task_config["scan_type"]
            if "severity" in task_config:
                kwargs["severity"] = task_config["severity"]
            if "ignore_unfixed" in task_config:
                kwargs["ignore_unfixed"] = task_config["ignore_unfixed"]
            if "exit_code" in task_config:
                kwargs["exit_code"] = task_config["exit_code"]
            if "output_format" in task_config:
                kwargs["output_format"] = task_config["output_format"]
        
        elif tool_name == "nmap":
            if "ports" in task_config:
                kwargs["ports"] = task_config["ports"]
            if "scan_type" in task_config:
                kwargs["scan_type"] = task_config["scan_type"]
            if "service_detection" in task_config:
                kwargs["service_detection"] = task_config["service_detection"]
            if "os_detection" in task_config:
                kwargs["os_detection"] = task_config["os_detection"]
        
        elif tool_name == "semgrep":
            if "config" in task_config:
                kwargs["config"] = task_config["config"]
            if "languages" in task_config:
                kwargs["languages"] = task_config["languages"]
            if "severity" in task_config:
                kwargs["severity"] = task_config["severity"]
        
        elif tool_name == "nuclei":
            if "templates" in task_config:
                kwargs["templates"] = task_config["templates"]
            if "severity" in task_config:
                kwargs["severity"] = task_config["severity"]
            if "rate_limit" in task_config:
                kwargs["rate_limit"] = task_config["rate_limit"]
        
        return kwargs
    
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
