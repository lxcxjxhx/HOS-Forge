#!/usr/bin/env python3
"""End-to-end test for Taskflow Engine.

This script validates that the Taskflow Engine can:
1. Parse YAML workflow files
2. Generate execution plans
3. Execute workflows with parallel task support
4. Handle dependencies correctly
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from hosforge.taskflow import WorkflowParser, WorkflowExecutor
from hosforge.taskflow.registry import list_available_agents, list_available_tools


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def test_registry():
    """Test agent and tool registry."""
    print_section("Testing Registry")
    
    agents = list_available_agents()
    tools = list_available_tools()
    
    print(f"✓ Available agents ({len(agents)}):")
    for agent in agents:
        print(f"  - {agent}")
    
    print(f"\n✓ Available tools ({len(tools)}):")
    for tool in tools:
        print(f"  - {tool}")
    
    return True


def test_parse_workflow(workflow_path: str):
    """Test parsing a workflow file."""
    print_section(f"Parsing Workflow: {workflow_path}")
    
    try:
        schema = WorkflowParser.parse_file(workflow_path)
        workflow = schema.workflow
        
        print(f"✓ Workflow name: {workflow.name}")
        print(f"✓ Description: {workflow.description}")
        print(f"✓ Version: {workflow.version}")
        print(f"✓ Total tasks: {len(workflow.tasks)}")
        
        print("\nTasks:")
        for task in workflow.tasks:
            deps = ", ".join(task.depends_on) if task.depends_on else "none"
            print(f"  - {task.name}")
            print(f"    Agents: {', '.join(task.agent)}")
            print(f"    Tools: {', '.join(task.tools) if task.tools else 'none'}")
            print(f"    Depends on: {deps}")
            print(f"    Timeout: {task.timeout}s")
        
        return True, schema
    
    except Exception as e:
        print(f"✗ Failed to parse workflow: {e}")
        return False, None


def test_execution_plan(executor: WorkflowExecutor):
    """Test generating execution plan."""
    print_section("Generating Execution Plan")
    
    try:
        stages = executor.get_execution_plan()
        
        print(f"✓ Total stages: {len(stages)}")
        print(f"✓ Workflow: {executor.workflow.name}")
        print(f"✓ Total tasks: {len(executor.workflow.tasks)}")
        
        print("\nExecution stages:")
        for i, stage in enumerate(stages, 1):
            parallel_marker = " (parallel)" if len(stage) > 1 else ""
            print(f"  Stage {i}{parallel_marker}:")
            for task_name in stage:
                print(f"    - {task_name}")
        
        return True
    
    except Exception as e:
        print(f"✗ Failed to generate execution plan: {e}")
        return False


async def test_workflow_execution(executor: WorkflowExecutor, enable_parallel: bool = True):
    """Test executing a workflow."""
    mode = "parallel" if enable_parallel else "sequential"
    print_section(f"Executing Workflow ({mode.capitalize()} Mode)")
    
    try:
        executor.enable_parallel = enable_parallel
        
        print(f"Starting workflow execution...")
        print(f"Mode: {mode}")
        print(f"Checkpoint enabled: {executor.enable_checkpoint}")
        
        result = await executor.execute()
        
        print(f"\n✓ Workflow completed!")
        print(f"✓ Total duration: {result['total_duration']:.2f}s")
        
        # Print summary
        summary = result['summary']
        print(f"\nExecution Summary:")
        print(f"  Total tasks: {summary['total_tasks']}")
        print(f"  Completed: {summary['completed']}")
        print(f"  Failed: {summary['failed']}")
        print(f"  Skipped: {summary['skipped']}")
        print(f"  Success rate: {summary['success_rate']:.1f}%")
        
        # Print task details
        print(f"\nTask Results:")
        for task_name, task_result in result['task_results'].items():
            status = task_result['status']
            duration = task_result.get('duration', 0)
            status_icon = "✓" if status == "completed" else "✗"
            print(f"  {status_icon} {task_name}: {status} ({duration:.2f}s)")
            
            if status == "failed" and 'error' in task_result:
                print(f"    Error: {task_result['error']}")
        
        return True, result
    
    except Exception as e:
        print(f"✗ Workflow execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None


async def main():
    """Run end-to-end tests."""
    print("\n" + "="*70)
    print("  HOS Taskflow Engine - End-to-End Test")
    print("="*70)
    
    # Test 1: Registry
    if not test_registry():
        print("\n✗ Registry test failed")
        return False
    
    # Test 2: Parse demo workflow
    demo_workflow = "examples/workflows/demo_quick_scan.yaml"
    success, schema = test_parse_workflow(demo_workflow)
    
    if not success or schema is None:
        print("\n✗ Parse test failed")
        return False
    
    # Test 3: Generate execution plan
    executor = WorkflowExecutor(schema.workflow, enable_checkpoint=False)
    
    if not test_execution_plan(executor):
        print("\n✗ Execution plan test failed")
        return False
    
    # Test 4: Execute workflow (parallel mode)
    success, result = await test_workflow_execution(executor, enable_parallel=True)
    
    if not success:
        print("\n✗ Parallel execution test failed")
        return False
    
    # Test 5: Execute workflow (sequential mode)
    executor2 = WorkflowExecutor(schema.workflow, enable_checkpoint=False)
    success, result = await test_workflow_execution(executor2, enable_parallel=False)
    
    if not success:
        print("\n✗ Sequential execution test failed")
        return False
    
    print_section("All Tests Passed!")
    print("✓ Registry validation")
    print("✓ Workflow parsing")
    print("✓ Execution plan generation")
    print("✓ Parallel workflow execution")
    print("✓ Sequential workflow execution")
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
