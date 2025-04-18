#!/usr/bin/env python3
"""
Webhook Notifications Server Example

This example demonstrates how to use webhook notifications for task status
updates in the A2A protocol, allowing agents to proactively notify clients.
"""

import os
import sys
import time
import threading
from flask import Flask, request, jsonify

# Add parent directory to Python path to import a2a
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from a2a.server import run_server

# Create a simple webhook receiver server for demonstration
webhook_app = Flask(__name__)
webhook_logs = []

@webhook_app.route("/webhook/<task_id>", methods=["POST"])
def receive_webhook(task_id):
    """Receive webhook notifications from the A2A server"""
    data = request.json
    print(f"\n=== WEBHOOK RECEIVED for Task {task_id} ===")
    print(f"Status: {data.get('status')}")
    print(f"Timestamp: {data.get('timestamp')}")
    print(f"Data: {data.get('data')}")
    print("=" * 50)
    
    # Store the webhook for later retrieval
    webhook_logs.append({
        "task_id": task_id,
        "status": data.get("status"),
        "timestamp": data.get("timestamp"),
        "data": data.get("data"),
        "received_at": time.time()
    })
    
    return jsonify({"status": "received"})

@webhook_app.route("/logs", methods=["GET"])
def get_logs():
    """View all webhook notification logs"""
    return jsonify(webhook_logs)

@webhook_app.route("/logs/<task_id>", methods=["GET"])
def get_task_logs(task_id):
    """View webhook notification logs for a specific task"""
    task_logs = [log for log in webhook_logs if log.get("task_id") == task_id]
    return jsonify(task_logs)

@webhook_app.route("/clear", methods=["POST"])
def clear_logs():
    """Clear the webhook logs"""
    webhook_logs.clear()
    return jsonify({"status": "cleared"})

def run_webhook_receiver(port=8001):
    """Run the webhook receiver server"""
    print(f"Starting webhook receiver on port {port}...")
    print(f"Webhook URL: http://localhost:{port}/webhook/<task_id>")
    webhook_app.run(host="0.0.0.0", port=port, debug=False)

def start_a2a_server(webhook_url, port=8000):
    """
    Start an A2A server with webhook notification support.
    
    Args:
        webhook_url: The URL to send webhook notifications to
        port: The port to run the A2A server on
    """
    # Define the agent's skills
    skills = [
        {
            "id": "task_processor",
            "name": "Task Processor",
            "description": "Processes tasks and sends status updates via webhooks"
        },
        {
            "id": "notification_generator",
            "name": "Notification Generator",
            "description": "Generates push notifications about task progress"
        }
    ]
    
    print(f"Starting A2A server on port {port} with webhook notifications...")
    print(f"Webhook notifications will be sent to: {webhook_url}")
    print("This server demonstrates the A2A protocol's webhook notification capabilities.")
    
    # Run the server using the core A2A implementation
    run_server(
        model="gemma3:27b",  # Use a model that's likely available
        name="Webhook Notification Agent",
        description="An A2A-compatible agent that demonstrates webhook notifications",
        skills=skills,
        port=port,
        webhook_url=webhook_url  # This is the key configuration for webhooks
    )

def start_servers(a2a_port=8000, webhook_port=8001):
    """
    Start both the webhook receiver and A2A server.
    
    Args:
        a2a_port: Port for the A2A server
        webhook_port: Port for the webhook receiver
    """
    # Start the webhook receiver in a separate thread
    webhook_thread = threading.Thread(target=run_webhook_receiver, args=(webhook_port,))
    webhook_thread.daemon = True
    webhook_thread.start()
    
    # Wait for webhook receiver to start
    time.sleep(1)
    
    # Configure the webhook URL for the A2A server
    webhook_url = f"http://localhost:{webhook_port}/webhook"
    
    # Start the A2A server with webhook support
    start_a2a_server(webhook_url, a2a_port)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Webhook Notifications Server Example")
    parser.add_argument("--a2a-port", type=int, default=8000, help="Port for the A2A server")
    parser.add_argument("--webhook-port", type=int, default=8001, help="Port for the webhook receiver")
    
    args = parser.parse_args()
    start_servers(args.a2a_port, args.webhook_port) 