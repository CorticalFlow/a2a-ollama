"""
A2A Client Module

This module provides a client for interacting with A2A agents.
"""

import json
import requests
from typing import Dict, List, Optional, Any


class A2AClient:
    """
    Client for interacting with A2A agents.
    """
    
    def __init__(self, endpoint: str):
        """
        Initialize the A2A client.
        
        Args:
            endpoint: The endpoint of the A2A agent
        """
        self.endpoint = endpoint.rstrip("/")
    
    def discover_agent(self) -> Dict[str, Any]:
        """
        Discover an agent's capabilities.
        
        Returns:
            The agent card
        """
        response = requests.get(f"{self.endpoint}/.well-known/agent.json")
        response.raise_for_status()
        return response.json()
    
    def create_task(self, params: Dict[str, Any]) -> str:
        """
        Create a new task.
        
        Args:
            params: Parameters for the task
            
        Returns:
            The ID of the created task
        """
        response = requests.post(f"{self.endpoint}/tasks", json=params)
        response.raise_for_status()
        return response.json()["task_id"]
    
    def get_task(self, task_id: str) -> Dict[str, Any]:
        """
        Get a task by ID.
        
        Args:
            task_id: The ID of the task
            
        Returns:
            The task
        """
        response = requests.get(f"{self.endpoint}/tasks/{task_id}")
        response.raise_for_status()
        return response.json()
    
    def add_message(self, task_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a message to a task.
        
        Args:
            task_id: The ID of the task
            message: The message to add
            
        Returns:
            The response
        """
        response = requests.post(f"{self.endpoint}/tasks/{task_id}/messages", json=message)
        response.raise_for_status()
        return response.json()
    
    def call_rpc(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Call an RPC method.
        
        Args:
            method: The name of the method
            params: Parameters for the method
            
        Returns:
            The response
        """
        if params is None:
            params = {}
        
        request = {
            "jsonrpc": "2.0",
            "id": "1",
            "method": method,
            "params": params
        }
        
        response = requests.post(f"{self.endpoint}/rpc", json=request)
        response.raise_for_status()
        return response.json()
    
    def chat(self, content: str, task_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Chat with the agent.
        
        Args:
            content: The message content
            task_id: An existing task ID (optional)
            
        Returns:
            The response
        """
        if not task_id:
            task_id = self.create_task({"type": "chat"})
        
        message = {
            "role": "user",
            "parts": [
                {
                    "type": "text",
                    "content": content
                }
            ]
        }
        
        return self.add_message(task_id, message)


if __name__ == "__main__":
    """Example usage of the A2A client."""
    import argparse
    
    parser = argparse.ArgumentParser(description="A2A Client")
    parser.add_argument("--endpoint", type=str, default="http://localhost:8000", help="The A2A agent endpoint")
    parser.add_argument("--message", type=str, required=True, help="The message to send")
    
    args = parser.parse_args()
    
    client = A2AClient(args.endpoint)
    
    try:
        agent_card = client.discover_agent()
        print(f"Connected to agent: {agent_card['name']}")
        print(f"Description: {agent_card['description']}")
        print(f"Skills: {', '.join(skill['name'] for skill in agent_card['skills'])}")
        
        response = client.chat(args.message)
        print("\nResponse:")
        
        if "message" in response:
            for part in response["message"]["parts"]:
                if part["type"] == "text":
                    print(part["content"])
        else:
            print(response)
    except Exception as e:
        print(f"Error: {e}") 