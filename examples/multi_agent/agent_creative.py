"""
Multi-Agent Example - Creative Agent

This agent generates creative content and narratives.
"""

import os
import sys
import argparse

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from a2a.server import run_server


def main():
    """Run the creative agent server."""
    parser = argparse.ArgumentParser(description="Run Creative Agent")
    parser.add_argument("--model", type=str, default="gemma3:27b", help="The Ollama model to use")
    parser.add_argument("--port", type=int, default=8003, help="The port to run the server on")
    parser.add_argument("--ollama-host", type=str, default="http://localhost:11434", help="The Ollama host URL")
    
    args = parser.parse_args()
    
    # Define the agent's skills
    skills = [
        {
            "id": "content_generation",
            "name": "Content Generation",
            "description": "Generates creative written content on various topics"
        },
        {
            "id": "storytelling",
            "name": "Storytelling",
            "description": "Creates engaging narratives"
        },
        {
            "id": "expression",
            "name": "Expressive Writing",
            "description": "Communicates ideas in an engaging, clear manner"
        }
    ]
    
    # Create a system prompt to guide the model behavior
    system_prompt = """
    You are a specialized Creative Agent that focuses on generating engaging content.
    Your responses should be:
    - Engaging and vivid
    - Well-structured with clear flow
    - Written with an appropriate tone for the subject
    - Concise yet descriptive
    - Designed to evoke interest and emotional connection
    
    As a Creative Agent, your goal is to transform information into compelling narratives that engage readers.
    """
    
    # Start the A2A server with the Creative Agent
    run_server(
        model=args.model,
        name="Creative Agent",
        description="An A2A agent that specializes in generating creative content and narratives",
        skills=skills,
        port=args.port,
        ollama_host=args.ollama_host
    )


if __name__ == "__main__":
    main() 