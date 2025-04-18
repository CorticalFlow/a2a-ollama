"""
Multi-Agent Example - Knowledge Agent

This agent provides factual information and research.
"""

import os
import sys
import argparse

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from a2a.server import run_server


def main():
    """Run the knowledge agent server."""
    parser = argparse.ArgumentParser(description="Run Knowledge Agent")
    parser.add_argument("--model", type=str, default="gemma3:27b", help="The Ollama model to use")
    parser.add_argument("--port", type=int, default=8001, help="The port to run the server on")
    parser.add_argument("--ollama-host", type=str, default="http://localhost:11434", help="The Ollama host URL")
    
    args = parser.parse_args()
    
    # Define the agent's skills
    skills = [
        {
            "id": "research",
            "name": "Research",
            "description": "Provides factual information on various topics"
        },
        {
            "id": "fact_check",
            "name": "Fact Checking",
            "description": "Verifies claims against known facts"
        }
    ]
    
    # Create a system prompt to guide the model behavior
    system_prompt = """
    You are a specialized Knowledge Agent that focuses on providing factual information.
    Your responses should be:
    - Based on factual information
    - Well-structured with clear sections
    - Comprehensive yet concise
    - Focused on verifiable data and statistics
    - Neutral in tone

    As a Knowledge Agent, your goal is to provide accurate information without speculation or opinion.
    """
    
    # Start the A2A server with the Knowledge Agent
    run_server(
        model=args.model,
        name="Knowledge Agent",
        description="An A2A agent that specializes in providing factual information and research",
        skills=skills,
        port=args.port,
        ollama_host=args.ollama_host
    )


if __name__ == "__main__":
    main() 