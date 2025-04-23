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
from a2a.core.mcp.mcp_client import MCPClient


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
        self.mcp_client = None
    
    def configure_mcp_client(self, mcp_client: MCPClient) -> None:
        """
        Configure MCP client for tool access.
        
        Args:
            mcp_client: The MCP client
        """
        self.mcp_client = mcp_client
    
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
        
        # Check if this is an MCP task
        if self.task_manager.mcp_bridge and self.task_manager._can_use_mcp_for_task(task):
            try:
                import asyncio
                return asyncio.run(self.task_manager.process_task(task_id))
            except Exception as e:
                print(f"Error processing MCP task: {e}")
                # Fall back to normal processing
        
        ollama_messages = self._get_ollama_messages(task_id)
        
        # Set up retry parameters
        max_retries = 3
        retry_count = 0
        last_error = None
        
        while retry_count < max_retries:
            try:
                # Add available MCP tools to the system message if MCP is configured
                if self.mcp_client and self.mcp_client.available_tools:
                    # Check if we have a system message, if not add one
                    has_system_message = False
                    for msg in ollama_messages:
                        if msg.get("role") == "system":
                            has_system_message = True
                            # Add MCP tools to existing system message
                            msg["content"] += self._get_mcp_tools_description()
                            break
                            
                    if not has_system_message:
                        # Create a new system message with MCP tools
                        ollama_messages.insert(0, {
                            "role": "system",
                            "content": f"You are {self.agent_card.name}, {self.agent_card.description}. {self._get_mcp_tools_description()}"
                        })
                
                # Generate a response using Ollama
                response = self.client.chat(
                    model=self.model,
                    messages=ollama_messages
                )
                
                # Check for MCP tool calls in the response
                response_content = response.get("message", {}).get("content", "")
                tool_calls = self._extract_tool_calls(response_content)
                
                if tool_calls and self.mcp_client:
                    # Execute the tool calls and append results
                    tool_results = []
                    for tool_call in tool_calls:
                        tool_name = tool_call.get("name")
                        parameters = tool_call.get("parameters", {})
                        
                        try:
                            import asyncio
                            result = asyncio.run(self.mcp_client.execute_tool(tool_name, parameters))
                            tool_results.append({
                                "name": tool_name,
                                "result": result.result,
                                "error": result.error
                            })
                        except Exception as e:
                            tool_results.append({
                                "name": tool_name,
                                "result": None,
                                "error": str(e)
                            })
                    
                    # Add the tool results to the messages
                    ollama_messages.append({
                        "role": "assistant",
                        "content": response_content
                    })
                    
                    # Add tool results message
                    ollama_messages.append({
                        "role": "system",
                        "content": f"Tool results: {json.dumps(tool_results)}"
                    })
                    
                    # Generate a final response that incorporates the tool results
                    final_response = self.client.chat(
                        model=self.model,
                        messages=ollama_messages
                    )
                    
                    response = final_response
                
                # Update task status
                self.task_manager.update_task_status(task_id, "completed")
                
                # Create A2A message from the response
                message_id = str(uuid.uuid4())
                a2a_message = {
                    "id": message_id,
                    "role": "agent",
                    "parts": [
                        {
                            "type": "text",
                            "content": response.get("message", {}).get("content", "")
                        }
                    ]
                }
                
                # Add the message to the task
                self.message_handler.add_message(task_id, a2a_message)
                
                return {
                    "task_id": task_id,
                    "message_id": message_id,
                    "status": "completed",
                    "message": a2a_message
                }
                
            except Exception as e:
                last_error = str(e)
                retry_count += 1
                print(f"Error processing task (attempt {retry_count}): {e}")
                time.sleep(1)  # Wait before retrying
        
        # If we get here, all retries failed
        self.task_manager.update_task_status(task_id, "failed")
        
        return {
            "task_id": task_id,
            "status": "failed",
            "error": last_error
        }
    
    def _extract_tool_calls(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract MCP tool calls from an Ollama response.
        
        Args:
            content: The response content
            
        Returns:
            List of extracted tool calls
        """
        tool_calls = []
        
        # Simple parsing for tool calls - in reality this would need to be more robust
        # Example format to detect: {"name": "tool_name", "parameters": {"param1": "value1"}}
        import re
        
        # Look for JSON objects that might be tool calls
        json_pattern = r'\{\s*"name"\s*:\s*"([^"]*)"\s*,\s*"parameters"\s*:\s*(\{[^}]*\})\s*\}'
        matches = re.finditer(json_pattern, content)
        
        for match in matches:
            try:
                tool_name = match.group(1)
                parameters_str = match.group(2)
                parameters = json.loads(parameters_str)
                
                tool_calls.append({
                    "name": tool_name,
                    "parameters": parameters
                })
            except Exception as e:
                print(f"Error parsing tool call: {e}")
        
        return tool_calls
        
    def _get_mcp_tools_description(self) -> str:
        """
        Get a description of available MCP tools.
        
        Returns:
            Description of MCP tools
        """
        if not self.mcp_client or not self.mcp_client.available_tools:
            return ""
            
        tools_description = "You have access to the following tools:\n\n"
        
        for name, tool in self.mcp_client.available_tools.items():
            tools_description += f"- {name}: {tool.description}\n"
            
            if tool.parameters:
                tools_description += "  Parameters:\n"
                for param in tool.parameters:
                    required = " (required)" if param.required else ""
                    tools_description += f"  - {param.name}{required}: {param.description}\n"
                    
            tools_description += "\n"
            
        tools_description += "\nTo use a tool, respond with JSON in this format: {\"name\": \"tool_name\", \"parameters\": {\"param1\": \"value1\"}}\n"
        
        return tools_description
        
    def _process_task_stream(self, task_id: str) -> Iterator[Dict[str, Any]]:
        """
        Process a task using Ollama with streaming.
        
        Args:
            task_id: The ID of the task to process
            
        Returns:
            Iterator of streaming chunks
        """
        task = self.task_manager.get_task(task_id)
        
        if not task:
            yield {
                "task_id": task_id,
                "error": f"Task not found: {task_id}",
                "done": True
            }
            return
            
        # If this is an MCP task, we don't support streaming yet
        if self.task_manager.mcp_bridge and self.task_manager._can_use_mcp_for_task(task):
            yield {
                "task_id": task_id,
                "error": "Streaming not supported for MCP tasks",
                "done": True
            }
            return
        
        ollama_messages = self._get_ollama_messages(task_id)
        
        # Update task status
        self.task_manager.update_task_status(task_id, "working")
        
        # Generate a message ID
        message_id = str(uuid.uuid4())
        
        # Initialize content buffer
        full_content = ""
        
        # Add available MCP tools to the system message if MCP is configured
        if self.mcp_client and self.mcp_client.available_tools:
            # Check if we have a system message, if not add one
            has_system_message = False
            for msg in ollama_messages:
                if msg.get("role") == "system":
                    has_system_message = True
                    # Add MCP tools to existing system message
                    msg["content"] += self._get_mcp_tools_description()
                    break
                    
            if not has_system_message:
                # Create a new system message with MCP tools
                ollama_messages.insert(0, {
                    "role": "system",
                    "content": f"You are {self.agent_card.name}, {self.agent_card.description}. {self._get_mcp_tools_description()}"
                })
        
        try:
            # Stream response from Ollama
            for chunk in self.client.chat(
                model=self.model,
                messages=ollama_messages,
                stream=True
            ):
                content = chunk.get("message", {}).get("content", "")
                
                if content:
                    full_content += content
                    
                    # Send chunk
                    yield {
                        "task_id": task_id,
                        "message_id": message_id,
                        "chunk": {
                            "type": "text",
                            "content": content
                        },
                        "done": False
                    }
        except Exception as e:
            # Handle error
            error_message = str(e)
            self.task_manager.update_task_status(task_id, "failed")
            
            yield {
                "task_id": task_id,
                "message_id": message_id,
                "error": error_message,
                "status": "failed",
                "done": True
            }
            return
        
        # Check for MCP tool calls in the response
        tool_calls = self._extract_tool_calls(full_content)
        
        if tool_calls and self.mcp_client:
            # Execute the tool calls and append results
            yield {
                "task_id": task_id,
                "message_id": message_id,
                "chunk": {
                    "type": "text",
                    "content": "\n\nExecuting tool calls..."
                },
                "done": False
            }
            
            tool_results = []
            for tool_call in tool_calls:
                tool_name = tool_call.get("name")
                parameters = tool_call.get("parameters", {})
                
                try:
                    import asyncio
                    result = asyncio.run(self.mcp_client.execute_tool(tool_name, parameters))
                    tool_results.append({
                        "name": tool_name,
                        "result": result.result,
                        "error": result.error
                    })
                    
                    # Send a chunk with the tool result
                    yield {
                        "task_id": task_id,
                        "message_id": message_id,
                        "chunk": {
                            "type": "text",
                            "content": f"\nTool '{tool_name}' result: {json.dumps(result.result)}"
                        },
                        "done": False
                    }
                except Exception as e:
                    error_msg = str(e)
                    tool_results.append({
                        "name": tool_name,
                        "result": None,
                        "error": error_msg
                    })
                    
                    # Send a chunk with the tool error
                    yield {
                        "task_id": task_id,
                        "message_id": message_id,
                        "chunk": {
                            "type": "text",
                            "content": f"\nTool '{tool_name}' error: {error_msg}"
                        },
                        "done": False
                    }
            
            # Add the tool results to the messages
            ollama_messages.append({
                "role": "assistant",
                "content": full_content
            })
            
            # Add tool results message
            ollama_messages.append({
                "role": "system",
                "content": f"Tool results: {json.dumps(tool_results)}"
            })
            
            # Generate a final response that incorporates the tool results
            yield {
                "task_id": task_id,
                "message_id": message_id,
                "chunk": {
                    "type": "text",
                    "content": "\n\nGenerating final response with tool results..."
                },
                "done": False
            }
            
            final_content = ""
            try:
                # Stream final response
                for chunk in self.client.chat(
                    model=self.model,
                    messages=ollama_messages,
                    stream=True
                ):
                    content = chunk.get("message", {}).get("content", "")
                    
                    if content:
                        final_content += content
                        
                        # Send chunk
                        yield {
                            "task_id": task_id,
                            "message_id": message_id,
                            "chunk": {
                                "type": "text",
                                "content": content
                            },
                            "done": False
                        }
            except Exception as e:
                # Handle error in final response
                error_message = str(e)
                yield {
                    "task_id": task_id,
                    "message_id": message_id,
                    "chunk": {
                        "type": "text",
                        "content": f"\n\nError generating final response: {error_message}"
                    },
                    "done": False
                }
                
            # Update the full content to include the final response
            full_content += "\n\n" + final_content
        
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