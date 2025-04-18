"""
A2A Ollama Integration - Main Module

This module provides the main functionality for integrating Ollama with Google's A2A protocol.
"""

import json
import uuid
import time
from typing import Dict, List, Optional, Union, Any, Generator, Iterator

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
        elif method == "process_task_stream":
            task_id = request.get("params", {}).get("task_id")
            return {"error": "Streaming not available via RPC, use HTTP streaming endpoint"}
        else:
            return {"error": f"Unknown method: {method}"}
    
    def _get_ollama_messages(self, task_id: str) -> List[Dict[str, Any]]:
        """
        Convert A2A messages to Ollama message format.
        
        Args:
            task_id: The task ID
            
        Returns:
            List of messages in Ollama format
        """
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
            
        return ollama_messages
    
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
        
        ollama_messages = self._get_ollama_messages(task_id)
        
        # Set up retry parameters
        max_retries = 3
        
        for retry in range(max_retries + 1):
            try:
                # First, check if the model is actually loaded
                try:
                    models_response = self.client._request("GET", "api/tags")
                    available_models = [m["name"] for m in models_response.get("models", [])]
                    
                    if self.model not in available_models:
                        fallback_msg = f"Model {self.model} not available. Available models: {available_models}"
                        print(fallback_msg)
                        
                        # Try to use an alternative model if available
                        for fallback in ["llama2", "gemma:2b", "mistral"]:
                            if fallback in available_models:
                                print(f"Falling back to model: {fallback}")
                                self.model = fallback
                                break
                except Exception as e:
                    print(f"Warning: Could not check available models: {e}")
                
                print(f"Using model: {self.model} for task processing")
                
                # Make the actual API call
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
                            "content": response["message"]["content"] if "message" in response and "content" in response["message"] else "No content received from model"
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
                error_message = f"Error processing task (attempt {retry+1}/{max_retries+1}): {str(e)}"
                print(error_message)
                
                if retry < max_retries:
                    # Wait before retrying
                    time.sleep(1)
                    continue
                
                # Generate a fallback response after all retries fail
                fallback_message = {
                    "id": str(uuid.uuid4()),
                    "role": "agent",
                    "parts": [
                        {
                            "type": "text",
                            "content": (
                                "I apologize, but I encountered an error while processing your request. "
                                "This could be due to issues with the Ollama service or model configuration. "
                                f"Error details: {str(e)}"
                            )
                        }
                    ]
                }
                
                self.message_handler.add_message(task_id, fallback_message)
                self.task_manager.update_task_status(task_id, "failed")
                
                return {
                    "task_id": task_id,
                    "status": "failed",
                    "error": str(e),
                    "message": fallback_message
                }
    
    def _process_task_stream(self, task_id: str) -> Iterator[Dict[str, Any]]:
        """
        Process a task using Ollama with streaming response.
        
        Args:
            task_id: The ID of the task to process
            
        Yields:
            Chunks of the response as they become available
        """
        task = self.task_manager.get_task(task_id)
        
        if not task:
            yield {"error": f"Task not found: {task_id}"}
            return
        
        ollama_messages = self._get_ollama_messages(task_id)
        
        # Initialize variables to store the full response
        message_id = str(uuid.uuid4())
        full_content = ""
        
        # Set up retry parameters
        max_retries = 3
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                # First, check if the model is actually loaded
                try:
                    models_response = self.client._request("GET", "api/tags")
                    available_models = [m["name"] for m in models_response.get("models", [])]
                    
                    if self.model not in available_models:
                        fallback_msg = f"Model {self.model} not available. Available models: {available_models}"
                        print(fallback_msg)
                        
                        # Try to use an alternative model if available
                        for fallback in ["llama2", "gemma:2b", "mistral"]:
                            if fallback in available_models:
                                print(f"Falling back to model: {fallback}")
                                self.model = fallback
                                break
                except Exception as e:
                    print(f"Warning: Could not check available models: {e}")
                
                print(f"Using model: {self.model} for streaming")
                
                # Stream the response from Ollama
                stream_response = self.client.chat(
                    model=self.model,
                    messages=ollama_messages,
                    stream=True
                )
                
                # Make sure it's an iterable
                if not hasattr(stream_response, '__iter__'):
                    yield {
                        "task_id": task_id,
                        "status": "failed",
                        "error": "Ollama did not return a streamable response",
                        "done": True
                    }
                    return
                
                # Process the stream
                for chunk in stream_response:
                    # Extract the new content
                    if 'message' in chunk and 'content' in chunk['message']:
                        new_content = chunk['message']['content']
                        full_content += new_content
                        
                        # Create chunk data with partial content
                        chunk_data = {
                            "task_id": task_id,
                            "message_id": message_id,
                            "chunk": {
                                "type": "text",
                                "content": new_content
                            },
                            "done": False
                        }
                        
                        yield chunk_data
                
                # If we get here, streaming completed successfully
                break
                
            except Exception as e:
                retry_count += 1
                error_msg = f"Error during streaming (attempt {retry_count}/{max_retries}): {str(e)}"
                print(error_msg)
                
                if retry_count > max_retries:
                    # We've exhausted our retries
                    yield {
                        "task_id": task_id,
                        "status": "failed",
                        "error": error_msg,
                        "done": True
                    }
                    return
                
                # Add a small delay before retrying
                time.sleep(1)
                
                # Let the user know we're retrying
                yield {
                    "task_id": task_id,
                    "message_id": message_id,
                    "chunk": {
                        "type": "text",
                        "content": f"\n[Retrying due to error: {str(e)}]\n"
                    },
                    "done": False
                }
        
        # If we reached here with no content, add a fallback response
        if not full_content:
            fallback_response = (
                "I apologize, but I was unable to generate a proper response. "
                "This could be due to issues with the Ollama API or the model configuration. "
                "Please check that Ollama is running correctly and that the requested model is available."
            )
            full_content = fallback_response
            
            yield {
                "task_id": task_id,
                "message_id": message_id,
                "chunk": {
                    "type": "text",
                    "content": fallback_response
                },
                "done": False
            }
        
        # Create the full A2A message
        a2a_message = {
            "id": message_id,
            "role": "agent",
            "parts": [
                {
                    "type": "text",
                    "content": full_content
                }
            ]
        }
        
        # Store the complete message
        self.message_handler.add_message(task_id, a2a_message)
        
        # Update task status
        self.task_manager.update_task_status(task_id, "completed")
        
        # Send final message
        yield {
            "task_id": task_id,
            "message_id": message_id,
            "status": "completed",
            "done": True,
            "message": a2a_message
        } 