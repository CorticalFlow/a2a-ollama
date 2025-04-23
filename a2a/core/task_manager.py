"""
Task Manager Module

This module handles task creation, tracking, and lifecycle management for A2A.
"""

import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime


class TaskManager:
    """
    Class for managing A2A tasks.
    
    This class handles the lifecycle of tasks in the A2A protocol.
    """
    
    def __init__(self):
        """Initialize the Task Manager."""
        self.tasks = {}
        self.mcp_bridge = None
    
    def enable_mcp(self, mcp_bridge: Any) -> None:
        """
        Enable MCP integration with provided bridge.
        
        Args:
            mcp_bridge: The A2A-MCP bridge
        """
        self.mcp_bridge = mcp_bridge
        
    def create_task(self, params: Dict[str, Any]) -> str:
        """
        Create a new task.
        
        Args:
            params: Parameters for the task
            
        Returns:
            The ID of the created task
        """
        task_id = str(uuid.uuid4())
        
        task = {
            "id": task_id,
            "status": "submitted",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "params": params
        }
        
        self.tasks[task_id] = task
        return task_id
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a task by ID.
        
        Args:
            task_id: The ID of the task
            
        Returns:
            The task or None if not found
        """
        return self.tasks.get(task_id)
    
    def update_task_status(self, task_id: str, status: str) -> bool:
        """
        Update the status of a task.
        
        Args:
            task_id: The ID of the task
            status: The new status (submitted, working, input-required, completed, failed, canceled)
            
        Returns:
            True if successful, False otherwise
        """
        if task_id not in self.tasks:
            return False
        
        valid_statuses = ["submitted", "working", "input-required", "completed", "failed", "canceled"]
        if status not in valid_statuses:
            return False
        
        self.tasks[task_id]["status"] = status
        self.tasks[task_id]["updated_at"] = datetime.utcnow().isoformat()
        
        return True
    
    def list_tasks(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List tasks, optionally filtered by status.
        
        Args:
            status: Filter by this status if provided
            
        Returns:
            A list of tasks
        """
        if status:
            return [task for task in self.tasks.values() if task["status"] == status]
        else:
            return list(self.tasks.values())
            
    async def process_task(self, task_id: str) -> Dict[str, Any]:
        """
        Process a task, using MCP if appropriate.
        
        Args:
            task_id: The ID of the task
            
        Returns:
            Result of processing the task
        """
        task = self.get_task(task_id)
        
        if not task:
            return {"error": f"Task not found: {task_id}"}
            
        # If MCP is enabled and this task might be an MCP task
        if self.mcp_bridge and self._can_use_mcp_for_task(task):
            try:
                return await self.mcp_bridge.process_a2a_task_with_mcp(task)
            except Exception as e:
                # If MCP processing fails, log the error
                print(f"Error processing task with MCP: {e}")
                # Don't return yet - fall back to normal processing
        
        # If we got here, either MCP is not enabled, task is not an MCP task,
        # or MCP processing failed
        return {"status": "submitted", "message": "Task ready for normal processing"}
    
    def _can_use_mcp_for_task(self, task: Dict[str, Any]) -> bool:
        """
        Check if a task can be handled by MCP.
        
        Args:
            task: The task to check
            
        Returns:
            True if the task can be handled by MCP
        """
        if not self.mcp_bridge:
            return False
            
        # Check if the task specifies an MCP skill
        skill_name = task.get("params", {}).get("skill")
        if not skill_name:
            return False
            
        # Check if this skill is in our MCP-to-A2A mapping
        return skill_name in self.mcp_bridge.mcp_to_a2a_map 