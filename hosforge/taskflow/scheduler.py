"""Task scheduler for workflow execution."""

import asyncio
from typing import Any, Callable, Dict, List, Optional
from .schema import Task, TaskStatus, Workflow


class TaskScheduler:
    """Scheduler for executing workflow tasks."""

    def __init__(self, workflow: Workflow):
        """Initialize scheduler with workflow.

        Args:
            workflow: Workflow to execute
        """
        self.workflow = workflow
        self.execution_order: List[str] = []
        self.task_handlers: Dict[str, Callable] = {}

    def register_handler(self, task_name: str, handler: Callable) -> None:
        """Register a handler function for a task.

        Args:
            task_name: Name of the task
            handler: Async callable that executes the task
        """
        self.task_handlers[task_name] = handler

    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute a single task.

        Args:
            task: Task to execute

        Returns:
            Task result dictionary

        Raises:
            ValueError: If no handler registered for task
            Exception: If task execution fails
        """
        if task.name not in self.task_handlers:
            raise ValueError(f"No handler registered for task '{task.name}'")

        task.status = TaskStatus.RUNNING

        try:
            handler = self.task_handlers[task.name]
            result = await handler(task)

            task.status = TaskStatus.SUCCESS
            task.result = result
            self.execution_order.append(task.name)

            return result

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            raise

    async def execute_workflow(self) -> Dict[str, Any]:
        """Execute the entire workflow.

        Returns:
            Dictionary of task results

        Raises:
            Exception: If any task fails
        """
        results = {}

        while True:
            ready_tasks = self.workflow.get_ready_tasks()

            if not ready_tasks:
                # Check if all tasks are completed
                all_done = all(
                    task.status in [TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.SKIPPED]
                    for task in self.workflow.tasks
                )

                if all_done:
                    break
                else:
                    # Deadlock - no ready tasks but not all done
                    raise RuntimeError("Workflow deadlock: no tasks can proceed")

            # Execute ready tasks in parallel
            tasks_to_run = [
                self.execute_task(task) for task in ready_tasks
            ]

            task_results = await asyncio.gather(*tasks_to_run, return_exceptions=True)

            # Store results
            for task, result in zip(ready_tasks, task_results):
                if isinstance(result, Exception):
                    results[task.name] = {"error": str(result)}
                else:
                    results[task.name] = result

        return results

    def get_execution_plan(self) -> List[List[str]]:
        """Get execution plan as list of parallel stages.

        Returns:
            List of stages, where each stage is a list of task names
        """
        stages = []
        completed = set()
        remaining = set(task.name for task in self.workflow.tasks)

        while remaining:
            stage = []

            for task_name in list(remaining):
                task = self.workflow.get_task(task_name)
                if task:
                    # Check if all dependencies are completed
                    deps_met = all(
                        dep in completed for dep in task.depends_on
                    )

                    if deps_met:
                        stage.append(task_name)

            if not stage:
                raise RuntimeError("Cannot create execution plan: circular dependency or missing tasks")

            stages.append(stage)
            completed.update(stage)
            remaining -= set(stage)

        return stages
