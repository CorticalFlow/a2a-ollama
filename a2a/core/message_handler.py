"""
Message Handler Module

This module handles message creation and exchange between agents in the A2A protocol.
"""

import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime


class MessageHandler:
    """
    Class for handling A2A messages.
    
    This class manages the exchange of messages between agents in the A2A protocol.
    """
    
    def __init__(self):
        """Initialize the Message Handler."""
        self.messages = {}
    
    def add_message(self, task_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a message to a task.
        
        Args:
            task_id: The ID of the task
            message: The message to add
            
        Returns:
            The added message
        """
        if task_id not in self.messages:
            self.messages[task_id] = []
        
        # Ensure message has an ID
        if "id" not in message:
            message["id"] = str(uuid.uuid4())
        
        # Add timestamp
        message["timestamp"] = datetime.utcnow().isoformat()
        
        self.messages[task_id].append(message)
        return message
    
    def get_messages(self, task_id: str) -> List[Dict[str, Any]]:
        """
        Get all messages for a task.
        
        Args:
            task_id: The ID of the task
            
        Returns:
            A list of messages for the task
        """
        return self.messages.get(task_id, [])
    
    def get_message(self, task_id: str, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific message by ID.
        
        Args:
            task_id: The ID of the task
            message_id: The ID of the message
            
        Returns:
            The message or None if not found
        """
        for message in self.messages.get(task_id, []):
            if message.get("id") == message_id:
                return message
        
        return None
    
    def format_message(self, role: str, content: str, content_type: str = "text") -> Dict[str, Any]:
        """
        Create a formatted A2A message.
        
        Args:
            role: The role of the message sender (user, agent)
            content: The content of the message
            content_type: The type of content (text, json, binary)
            
        Returns:
            A formatted A2A message
        """
        return {
            "id": str(uuid.uuid4()),
            "role": role,
            "parts": [
                {
                    "type": content_type,
                    "content": content
                }
            ]
        } 