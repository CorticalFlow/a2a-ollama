"""
A2A Server Module

This module provides a Flask-based HTTP server to expose A2A endpoints.
"""

import json
import os
from flask import Flask, request, jsonify
from typing import Dict, Any, List, Optional

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
        endpoint: str = None
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
        """
        self.port = port
        
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
                result = self.a2a_ollama._process_task(task_id)
                return jsonify(result)
            else:
                return jsonify({"message_id": added_message["id"]})
        
        @self.app.route("/rpc", methods=["POST"])
        def handle_rpc():
            request_data = request.json
            response = self.a2a_ollama.process_request(request_data)
            return jsonify(response)
    
    def run(self):
        """Run the A2A server."""
        print(f"Starting A2A server on port {self.port}...")
        self.app.run(host="0.0.0.0", port=self.port)


def run_server(
    model: str,
    name: str,
    description: str,
    skills: List[Dict[str, Any]],
    port: int = 8000,
    ollama_host: str = "http://localhost:11434",
    endpoint: str = None
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
    """
    server = A2AServer(
        model=model,
        name=name,
        description=description,
        skills=skills,
        port=port,
        ollama_host=ollama_host,
        endpoint=endpoint,
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