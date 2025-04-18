#!/usr/bin/env python3
"""
Webhook Notifications Client Example

This example demonstrates how to interact with an A2A agent that uses
webhook notifications for proactive status updates.
"""

import os
import sys
import time
import json
import requests
import argparse
from typing import Dict, Any, List

# Add parent directory to Python path to import a2a
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from a2a.client import A2AClient

class WebhookMonitor:
    """Monitor for webhook notifications."""
    
    def __init__(self, webhook_base_url: str):
        """
        Initialize the webhook monitor.
        
        Args:
            webhook_base_url: Base URL of the webhook receiver (without /webhook)
        """
        self.logs_url = f"{webhook_base_url}/logs"
        self.task_logs_url = f"{webhook_base_url}/logs"
        self.clear_url = f"{webhook_base_url}/clear"
        self.last_log_count = 0
    
    def clear_logs(self) -> None:
        """Clear all webhook logs."""
        try:
            response = requests.post(self.clear_url)
            response.raise_for_status()
            self.last_log_count = 0
            print("Webhook logs cleared.")
        except Exception as e:
            print(f"Error clearing logs: {e}")
    
    def get_all_logs(self) -> List[Dict[str, Any]]:
        """Get all webhook logs."""
        try:
            response = requests.get(self.logs_url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting logs: {e}")
            return []
    
    def get_task_logs(self, task_id: str) -> List[Dict[str, Any]]:
        """Get webhook logs for a specific task."""
        try:
            response = requests.get(f"{self.task_logs_url}/{task_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting task logs: {e}")
            return []
    
    def check_for_new_logs(self) -> List[Dict[str, Any]]:
        """
        Check for new webhook logs since the last check.
        
        Returns:
            A list of new logs
        """
        all_logs = self.get_all_logs()
        new_logs = all_logs[self.last_log_count:]
        self.last_log_count = len(all_logs)
        return new_logs

def webhook_demo(a2a_endpoint: str, webhook_base_url: str, query: str) -> None:
    """
    Demonstrate webhook notifications with the A2A protocol.
    
    Args:
        a2a_endpoint: URL of the A2A server
        webhook_base_url: Base URL of the webhook receiver
        query: Query to send to the agent
    """
    print(f"Connecting to A2A server at {a2a_endpoint}...")
    client = A2AClient(a2a_endpoint)
    
    # Set up webhook monitoring
    monitor = WebhookMonitor(webhook_base_url)
    monitor.clear_logs()
    
    try:
        # Connect to the agent and get its capabilities
        agent_card = client.discover_agent()
        print(f"Connected to agent: {agent_card['name']}")
        print(f"Description: {agent_card['description']}")
        print(f"Skills: {', '.join(skill['name'] for skill in agent_card.get('skills', []))}\n")
        
        # Create a task and check for initial webhook
        print("Creating a new task...")
        task_id = client.create_task({"type": "webhook_demo"})
        print(f"Task created with ID: {task_id}")
        
        # Wait briefly for webhook notification
        print("Waiting for task creation webhook...")
        time.sleep(1)
        
        # Check for new webhooks
        new_logs = monitor.check_for_new_logs()
        display_webhook_logs(new_logs)
        
        # Send a message to the agent
        print(f"\nSending query: {query}")
        message = {
            "role": "user",
            "parts": [
                {
                    "type": "text",
                    "content": query
                }
            ]
        }
        
        # This will trigger the "working" status webhook
        response = client.add_message(task_id, message)
        
        # Display the agent's response
        print("\nAgent response:")
        print("-" * 50)
        if "message" in response:
            for part in response["message"]["parts"]:
                if part["type"] == "text":
                    print(part["content"])
        else:
            print(response)
        print("-" * 50)
        
        # Wait for any additional webhooks
        print("\nWaiting for additional webhooks (status updates, completion)...")
        time.sleep(2)
        
        # Check for new webhooks again
        new_logs = monitor.check_for_new_logs()
        display_webhook_logs(new_logs)
        
        # Show final task status
        task = client.get_task(task_id)
        print(f"\nFinal task status: {task['status']}")
        
        # Get all webhooks for this task
        all_task_logs = monitor.get_task_logs(task_id)
        print(f"\nTotal webhooks received for task {task_id}: {len(all_task_logs)}")
        
        # Display webhook timeline
        print("\nWebhook timeline:")
        print("-" * 50)
        for i, log in enumerate(all_task_logs):
            print(f"[{i+1}] Status: {log.get('status')} at {format_timestamp(log.get('timestamp'))}")
        print("-" * 50)
    
    except Exception as e:
        print(f"Error during webhook demonstration: {e}")

def display_webhook_logs(logs: List[Dict[str, Any]]) -> None:
    """Display webhook logs in a readable format."""
    if not logs:
        print("No new webhooks received.")
        return
    
    print(f"Received {len(logs)} webhook notifications:")
    for i, log in enumerate(logs):
        print(f"\n--- Webhook {i+1} ---")
        print(f"Task ID: {log.get('task_id')}")
        print(f"Status: {log.get('status')}")
        print(f"Timestamp: {format_timestamp(log.get('timestamp'))}")
        print(f"Data: {json.dumps(log.get('data'), indent=2)}")

def format_timestamp(timestamp: float) -> str:
    """Format a Unix timestamp as a human-readable string."""
    if not timestamp:
        return "Unknown"
    
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))

def main():
    """Run the webhook notifications client example."""
    parser = argparse.ArgumentParser(description="Webhook Notifications Client Example")
    parser.add_argument("--a2a-endpoint", type=str, default="http://localhost:8000", 
                      help="Endpoint of the A2A server")
    parser.add_argument("--webhook-base", type=str, default="http://localhost:8001", 
                      help="Base URL of the webhook receiver")
    parser.add_argument("--query", type=str, 
                      default="Process this request and demonstrate webhook notifications at each stage.", 
                      help="Query to send to the agent")
    
    args = parser.parse_args()
    webhook_demo(args.a2a_endpoint, args.webhook_base, args.query)

if __name__ == "__main__":
    main() 