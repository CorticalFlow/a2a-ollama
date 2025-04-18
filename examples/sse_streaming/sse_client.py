#!/usr/bin/env python3
"""
SSE Streaming Client Example

This example demonstrates how to consume real-time streaming responses 
using Server-Sent Events (SSE) in the A2A protocol.
"""

import os
import sys
import time
import argparse

# Add parent directory to Python path to import a2a
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from a2a.client import A2AClient

def visualize_stream(content, delay=0.01):
    """Add a visual effect to show streaming in action."""
    for char in content:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()

def streaming_demo(endpoint, query, visualization=False):
    """
    Demonstrate SSE streaming with the A2A client.
    
    Args:
        endpoint: The endpoint of the A2A server
        query: The query to send to the agent
        visualization: Whether to visualize the streaming effect
    """
    print(f"Connecting to SSE streaming server at {endpoint}...")
    client = A2AClient(endpoint)
    
    try:
        # Verify the server is up and get agent information
        agent_card = client.discover_agent()
        print(f"Connected to agent: {agent_card['name']}")
        print(f"Description: {agent_card['description']}")
        print(f"Skills: {', '.join(skill['name'] for skill in agent_card.get('skills', []))}\n")
        
        print(f"Sending query: {query}")
        print("Awaiting streaming response...\n")
        
        # Create a task specifically for demonstrating streaming
        task_id = client.create_task({"type": "streaming_demo"})
        
        # Prepare the message
        message = {
            "role": "user",
            "parts": [
                {
                    "type": "text",
                    "content": query
                }
            ]
        }
        
        # Display header for streaming content
        print("-" * 50)
        print("STREAMING CONTENT:")
        print("-" * 50)
        
        # Use the streaming method to get real-time chunks
        full_response = ""
        
        if visualization:
            # For visualization we collect chunks then display with effects
            chunks = []
            for chunk in client.add_message_stream(task_id, message):
                if "chunk" in chunk and "content" in chunk["chunk"]:
                    content = chunk["chunk"]["content"]
                    chunks.append(content)
                    full_response += content
            
            # Display with typing effect for visualization
            for chunk in chunks:
                visualize_stream(chunk, 0.005)
        else:
            # Normal streaming display - as chunks arrive
            for chunk in client.add_message_stream(task_id, message):
                if "chunk" in chunk and "content" in chunk["chunk"]:
                    content = chunk["chunk"]["content"]
                    print(content, end="", flush=True)
                    full_response += content
        
        print("\n" + "-" * 50)
        
        # Get the final task information
        task = client.get_task(task_id)
        print(f"\nTask completed with status: {task['status']}")
        print(f"Total response length: {len(full_response)} characters")
        
    except Exception as e:
        print(f"Error during streaming demonstration: {e}")

def main():
    """Run the SSE streaming client example."""
    parser = argparse.ArgumentParser(description="SSE Streaming Client Example")
    parser.add_argument("--endpoint", type=str, default="http://localhost:8000", 
                       help="Endpoint of the SSE streaming server")
    parser.add_argument("--query", type=str, 
                       default="Write a short story about an AI that learns to understand human emotions. Make it engaging with multiple paragraphs.", 
                       help="Query to send to the agent")
    parser.add_argument("--visualize", action="store_true", 
                       help="Add a visual typing effect to better demonstrate streaming")
    
    args = parser.parse_args()
    streaming_demo(args.endpoint, args.query, args.visualize)

if __name__ == "__main__":
    main() 