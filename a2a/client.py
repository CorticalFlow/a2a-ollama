"""
A2A Client Module

This module provides a client for interacting with A2A agents.
"""

import json
import requests
import sseclient
from typing import Dict, List, Optional, Any, Iterator, Callable


class A2AClient:
    """
    Client for interacting with A2A agents.
    """
    
    def __init__(self, endpoint: str, webhook_callback: Optional[Callable[[Dict[str, Any]], None]] = None):
        """
        Initialize the A2A client.
        
        Args:
            endpoint: The endpoint of the A2A agent
            webhook_callback: A function to call when a webhook notification is received
        """
        self.endpoint = endpoint.rstrip("/")
        self.webhook_callback = webhook_callback
    
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
    
    def add_message_stream(self, task_id: str, message: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        """
        Add a message to a task and stream the response.
        
        Args:
            task_id: The ID of the task
            message: The message to add
            
        Yields:
            Chunks of the response as they become available
        """
        response = requests.post(
            f"{self.endpoint}/tasks/{task_id}/messages/stream", 
            json=message,
            stream=True,
            headers={"Accept": "text/event-stream"}
        )
        response.raise_for_status()
        
        client = sseclient.SSEClient(response)
        for event in client.events():
            if event.event == "chunk":
                yield json.loads(event.data)
            elif event.event == "completed":
                yield json.loads(event.data)
            elif event.event == "status_changed":
                yield json.loads(event.data)
            elif event.event == "message_added":
                yield json.loads(event.data)
    
    def process_webhook(self, data: Dict[str, Any]) -> None:
        """
        Process a webhook notification.
        
        Args:
            data: The webhook data
        """
        if self.webhook_callback:
            self.webhook_callback(data)
    
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
    
    def chat_stream(self, content: str, task_id: Optional[str] = None) -> Iterator[Dict[str, Any]]:
        """
        Chat with the agent and stream the response.
        
        Args:
            content: The message content
            task_id: An existing task ID (optional)
            
        Yields:
            Chunks of the response as they become available
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
        
        yield from self.add_message_stream(task_id, message)


if __name__ == "__main__":
    """Example usage of the A2A client."""
    import argparse
    
    parser = argparse.ArgumentParser(description="A2A Client")
    parser.add_argument("--endpoint", type=str, default="http://localhost:8000", help="The A2A agent endpoint")
    parser.add_argument("--message", type=str, required=True, help="The message to send")
    parser.add_argument("--stream", action="store_true", help="Stream the response")
    
    args = parser.parse_args()
    
    client = A2AClient(args.endpoint)
    
    try:
        agent_card = client.discover_agent()
        print(f"Connected to agent: {agent_card['name']}")
        print(f"Description: {agent_card['description']}")
        print(f"Skills: {', '.join(skill['name'] for skill in agent_card['skills'])}")
        
        if args.stream:
            print("\nStreaming response:")
            full_response = ""
            for chunk in client.chat_stream(args.message):
                if "chunk" in chunk and "content" in chunk["chunk"]:
                    content = chunk["chunk"]["content"]
                    print(content, end="", flush=True)
                    full_response += content
            print("\n\nFull response:", full_response)
        else:
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