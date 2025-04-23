"""
A2A Server Module

This module provides a Flask-based HTTP server to expose A2A endpoints.
"""

import json
import os
import time
import requests
import threading
from flask import Flask, request, jsonify, Response, stream_with_context
from typing import Dict, Any, List, Optional, Callable

from a2a.core.a2a_ollama import A2AOllama


class A2AServer:
    """
    A Flask-based HTTP server for A2A.
    """
    
    def __init__(
        self,
        model: str,
        name: str,
        description: str,
        skills: List[Dict[str, Any]],
        port: int = 8000,
        ollama_host: str = "http://localhost:11434",
        endpoint: str = None,
        webhook_url: str = None
    ):
        """
        Initialize the A2A server.
        
        Args:
            model: The Ollama model to use
            name: The name of the agent
            description: A description of the agent
            skills: A list of skills the agent has
            port: The port to run the server on
            ollama_host: The Ollama host URL
            endpoint: The endpoint where this agent is accessible
            webhook_url: URL to send task status updates to (optional)
        """
        self.port = port
        self.webhook_url = webhook_url
        self.server_thread = None
        self.should_stop = False
        
        if endpoint is None:
            endpoint = f"http://localhost:{port}"
        
        self.a2a_ollama = A2AOllama(
            model=model,
            name=name,
            description=description,
            skills=skills,
            host=ollama_host,
            endpoint=endpoint,
        )
        
        self.app = Flask(__name__)
        self._setup_routes()
    
    def _send_webhook_notification(self, task_id: str, status: str, data: Dict[str, Any]):
        """
        Send a webhook notification for task status updates.
        
        Args:
            task_id: The ID of the task
            status: The task status
            data: The notification data
        """
        if not self.webhook_url:
            return
            
        try:
            # Get the task to check for webhook_task_id
            task = self.a2a_ollama.task_manager.get_task(task_id)
            
            # Use webhook_task_id if available, otherwise use task_id
            webhook_task_id = task.get("params", {}).get("webhook_task_id", task_id)
            
            notification = {
                "task_id": task_id,
                "status": status,
                "timestamp": time.time(),
                "data": data
            }
            
            # Check if webhook_url already has a task_id in it
            webhook_url = self.webhook_url
            if not webhook_url.endswith(webhook_task_id):
                # If webhook URL doesn't end with a slash but also doesn't already have the task ID
                if not webhook_url.endswith('/'):
                    webhook_url = f"{webhook_url}/{webhook_task_id}"
                else:
                    webhook_url = f"{webhook_url}{webhook_task_id}"
            
            # Send the webhook notification
            response = requests.post(
                webhook_url, 
                json=notification,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            print(f"Webhook notification sent to {webhook_url}: {status}")
        except Exception as e:
            print(f"Error sending webhook notification: {e}")
    
    def _setup_routes(self):
        """Set up Flask routes."""
        @self.app.route("/.well-known/agent.json", methods=["GET"])
        def agent_card():
            return jsonify(self.a2a_ollama.agent_card.to_dict())
        
        @self.app.route("/tasks/<task_id>", methods=["GET"])
        def get_task(task_id):
            task = self.a2a_ollama.task_manager.get_task(task_id)
            if task:
                return jsonify(task)
            else:
                return jsonify({"error": f"Task not found: {task_id}"}), 404
        
        @self.app.route("/tasks", methods=["POST"])
        def create_task():
            request_data = request.json
            task_id = self.a2a_ollama.task_manager.create_task(request_data)
            
            # Send webhook notification if configured
            if self.webhook_url:
                # Extract webhook_task_id if specified
                webhook_task_id = request_data.get("webhook_task_id", task_id)
                print(f"Creating task with ID: {task_id}, webhook task ID: {webhook_task_id}")
                
                self._send_webhook_notification(
                    task_id, 
                    "submitted",
                    {"params": request_data}
                )
                
            return jsonify({"task_id": task_id}), 201
        
        @self.app.route("/tasks/<task_id>/messages", methods=["POST"])
        def add_message(task_id):
            task = self.a2a_ollama.task_manager.get_task(task_id)
            if not task:
                return jsonify({"error": f"Task not found: {task_id}"}), 404
            
            message = request.json
            added_message = self.a2a_ollama.message_handler.add_message(task_id, message)
            
            # Process the task if status is submitted
            if task["status"] == "submitted":
                self.a2a_ollama.task_manager.update_task_status(task_id, "working")
                
                # Send webhook notification for status change
                if self.webhook_url:
                    self._send_webhook_notification(
                        task_id, 
                        "working",
                        {"message_id": added_message["id"]}
                    )
                    
                result = self.a2a_ollama._process_task(task_id)
                
                # Send webhook notification for completion
                if self.webhook_url:
                    self._send_webhook_notification(
                        task_id, 
                        task["status"],
                        {"result": result}
                    )
                    
                return jsonify(result)
            else:
                return jsonify({"message_id": added_message["id"]})
        
        @self.app.route("/tasks/<task_id>/messages/stream", methods=["POST"])
        def add_message_stream(task_id):
            """Stream the response using Server-Sent Events (SSE)"""
            task = self.a2a_ollama.task_manager.get_task(task_id)
            if not task:
                return jsonify({"error": f"Task not found: {task_id}"}), 404
            
            message = request.json
            added_message = self.a2a_ollama.message_handler.add_message(task_id, message)
            
            def generate_streaming_response():
                """Generator function for SSE streaming"""
                # Send initial event with message ID
                yield f"event: message_added\ndata: {json.dumps({'message_id': added_message['id']})}\n\n"
                
                # Only process if status is submitted
                if task["status"] == "submitted":
                    # Update task status
                    self.a2a_ollama.task_manager.update_task_status(task_id, "working")
                    
                    # Send status change event
                    yield f"event: status_changed\ndata: {json.dumps({'status': 'working'})}\n\n"
                    
                    # Send webhook notification for status change
                    if self.webhook_url:
                        self._send_webhook_notification(
                            task_id, 
                            "working",
                            {"message_id": added_message["id"]}
                        )
                    
                    # Process the task with streaming
                    for chunk in self.a2a_ollama._process_task_stream(task_id):
                        # Send each chunk as SSE data
                        yield f"event: chunk\ndata: {json.dumps(chunk)}\n\n"
                    
                    # Get final task status
                    final_status = self.a2a_ollama.task_manager.get_task(task_id)["status"]
                    
                    # Send completion event
                    completion_data = {
                        "status": final_status,
                        "completed": True
                    }
                    yield f"event: completed\ndata: {json.dumps(completion_data)}\n\n"
                    
                    # Send webhook notification for completion
                    if self.webhook_url:
                        self._send_webhook_notification(
                            task_id, 
                            final_status,
                            {"completed": True}
                        )
            
            # Return streaming response
            return Response(
                stream_with_context(generate_streaming_response()),
                mimetype="text/event-stream"
            )
        
        @self.app.route("/rpc", methods=["POST"])
        def handle_rpc():
            request_data = request.json
            response = self.a2a_ollama.process_request(request_data)
            return jsonify(response)
    
    def _run_server(self):
        """Internal method to run the Flask server."""
        print(f"Starting A2A server on port {self.port}...")
        self.app.run(host="0.0.0.0", port=self.port, threaded=True)
    
    def run(self):
        """Run the A2A server synchronously."""
        self._run_server()
        
    async def start(self):
        """Start the A2A server asynchronously."""
        self.server_thread = threading.Thread(target=self._run_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        # Give the server a moment to start
        import asyncio
        await asyncio.sleep(0.5)
        
    async def stop(self):
        """Stop the A2A server asynchronously."""
        # Currently there's no clean way to stop Flask in a thread
        # This is a placeholder for proper shutdown logic
        self.should_stop = True
        # Just log for now
        print("A2A server stopping - note that the server thread may continue running until process exit")
        import asyncio
        await asyncio.sleep(0.1)


def run_server(
    model: str,
    name: str,
    description: str,
    skills: List[Dict[str, Any]],
    port: int = 8000,
    ollama_host: str = "http://localhost:11434",
    endpoint: str = None,
    webhook_url: str = None
):
    """
    Run the A2A server.
    
    Args:
        model: The Ollama model to use
        name: The name of the agent
        description: A description of the agent
        skills: A list of skills the agent has
        port: The port to run the server on
        ollama_host: The Ollama host URL
        endpoint: The endpoint where this agent is accessible
        webhook_url: URL to send task status updates to (optional)
    """
    server = A2AServer(
        model=model,
        name=name,
        description=description,
        skills=skills,
        port=port,
        ollama_host=ollama_host,
        endpoint=endpoint,
        webhook_url=webhook_url
    )
    
    server.run()


if __name__ == "__main__":
    # Example usage
    skills = [
        {
            "id": "answer_questions",
            "name": "Answer Questions",
            "description": "Can answer general knowledge questions"
        },
        {
            "id": "summarize_text",
            "name": "Summarize Text",
            "description": "Can summarize text content"
        }
    ]
    
    run_server(
        model="gemma3:27b",
        name="Ollama A2A Agent",
        description="An A2A-compatible agent powered by Ollama",
        skills=skills
    ) 