"""
A2A Ollama Integration - Main Module

This module provides the main functionality for integrating Ollama with Google's A2A protocol.
"""

import json
import uuid
from typing import Dict, List, Optional, Union, Any

import ollama
from ollama import Client

from a2a.core.agent_card import AgentCard
from a2a.core.task_manager import TaskManager
from a2a.core.message_handler import MessageHandler


class A2AOllama:
    """
    Main class for A2A Ollama integration.
    
    This class integrates Ollama with the A2A protocol, allowing Ollama
    to communicate with other A2A-compatible agents.
    """
    
    def __init__(
        self,
        model: str,
        name: str,
        description: str,
        skills: List[Dict[str, Any]],
        host: str = "http://localhost:11434",
        endpoint: str = "http://localhost:8000",
    ):
        """
        Initialize A2AOllama.
        
        Args:
            model: The Ollama model to use
            name: The name of the agent
            description: A description of the agent
            skills: A list of skills the agent has
            host: The Ollama host URL
            endpoint: The endpoint where this agent is accessible
        """
        self.model = model
        self.client = Client(host=host)
        self.agent_card = AgentCard(
            name=name,
            description=description,
            endpoint=endpoint,
            skills=skills,
        )
        self.task_manager = TaskManager()
        self.message_handler = MessageHandler()
    
    def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an incoming A2A request.
        
        Args:
            request: The A2A request
            
        Returns:
            The response to the request
        """
        method = request.get("method")
        
        if method == "discovery":
            return self.agent_card.to_dict()
        elif method == "create_task":
            task_id = self.task_manager.create_task(request.get("params", {}))
            return {"task_id": task_id}
        elif method == "get_task":
            task_id = request.get("params", {}).get("task_id")
            return self.task_manager.get_task(task_id)
        elif method == "add_message":
            task_id = request.get("params", {}).get("task_id")
            message = request.get("params", {}).get("message")
            return self.message_handler.add_message(task_id, message)
        elif method == "process_task":
            task_id = request.get("params", {}).get("task_id")
            return self._process_task(task_id)
        else:
            return {"error": f"Unknown method: {method}"}
    
    def _process_task(self, task_id: str) -> Dict[str, Any]:
        """
        Process a task using Ollama.
        
        Args:
            task_id: The ID of the task to process
            
        Returns:
            The result of processing the task
        """
        task = self.task_manager.get_task(task_id)
        
        if not task:
            return {"error": f"Task not found: {task_id}"}
        
        messages = self.message_handler.get_messages(task_id)
        ollama_messages = []
        
        for message in messages:
            content = ""
            for part in message.get("parts", []):
                if part.get("type") == "text":
                    content += part.get("content", "")
            
            ollama_messages.append({
                "role": message.get("role", "user"),
                "content": content
            })
        
        try:
            response = self.client.chat(
                model=self.model,
                messages=ollama_messages
            )
            
            # Create A2A message from Ollama response
            a2a_message = {
                "id": str(uuid.uuid4()),
                "role": "agent",
                "parts": [
                    {
                        "type": "text",
                        "content": response["message"]["content"]
                    }
                ]
            }
            
            self.message_handler.add_message(task_id, a2a_message)
            self.task_manager.update_task_status(task_id, "completed")
            
            return {
                "task_id": task_id,
                "status": "completed",
                "message": a2a_message
            }
        except Exception as e:
            self.task_manager.update_task_status(task_id, "failed")
            return {
                "task_id": task_id,
                "status": "failed",
                "error": str(e)
            } 