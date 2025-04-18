#!/usr/bin/env python3
"""
SSE Streaming Server Example

This example demonstrates how to use Server-Sent Events (SSE) for real-time
streaming of agent responses in the A2A protocol.
"""

import os
import sys
import time

# Add parent directory to Python path to import a2a
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from a2a.server import run_server

def start_sse_server(port=8000):
    """
    Start a server with SSE streaming capabilities.
    
    This server uses the core A2A implementation's built-in SSE support
    to stream responses in real-time.
    """
    # Define the agent's skills
    skills = [
        {
            "id": "streaming_storyteller",
            "name": "Streaming Storyteller",
            "description": "Creates stories with real-time streaming output"
        },
        {
            "id": "streaming_code_generator",
            "name": "Streaming Code Generator",
            "description": "Generates code with real-time streaming feedback"
        }
    ]
    
    print(f"Starting SSE streaming server on port {port}...")
    print("This server demonstrates the A2A protocol's SSE streaming capabilities.")
    print("Use the SSE client example to see real-time streaming responses.")
    
    # Run the server using the core A2A implementation
    # No special configuration is needed as SSE support is built into the core
    run_server(
        model="gemma3:27b",  # Use a model that's likely available
        name="SSE Streaming Agent",
        description="An A2A-compatible agent that demonstrates real-time streaming responses",
        skills=skills,
        port=port
    )

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="SSE Streaming Server Example")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    
    args = parser.parse_args()
    start_sse_server(args.port) 