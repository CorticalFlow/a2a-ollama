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