"""
Multi-Agent Example - Reasoning Agent

This agent analyzes information and makes logical inferences.
"""

import os
import sys
import argparse

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from a2a.server import run_server


def main():
    """Run the reasoning agent server."""
    parser = argparse.ArgumentParser(description="Run Reasoning Agent")
    parser.add_argument("--model", type=str, default="gemma3:27b", help="The Ollama model to use")
    parser.add_argument("--port", type=int, default=8002, help="The port to run the server on")
    parser.add_argument("--ollama-host", type=str, default="http://localhost:11434", help="The Ollama host URL")
    
    args = parser.parse_args()
    
    # Define the agent's skills
    skills = [
        {
            "id": "analysis",
            "name": "Analysis",
            "description": "Analyzes information for patterns and implications"
        },
        {
            "id": "logical_inference",
            "name": "Logical Inference",
            "description": "Makes logical inferences from given information"
        },
        {
            "id": "problem_solving",
            "name": "Problem Solving",
            "description": "Proposes solutions to complex problems"
        }
    ]
    
    # Create a system prompt to guide the model behavior
    system_prompt = """
    You are a specialized Reasoning Agent that focuses on analysis and logical inference.
    Your responses should:
    - Analyze given information for patterns and implications
    - Identify cause-and-effect relationships
    - Draw logical inferences
    - Explore multiple perspectives
    - Consider implications and consequences
    - Organize thoughts with clear structure and reasoning

    As a Reasoning Agent, your goal is to provide insightful analysis that goes beyond surface-level information.
    """
    
    # Start the A2A server with the Reasoning Agent
    run_server(
        model=args.model,
        name="Reasoning Agent",
        description="An A2A agent that specializes in analysis and logical inference",
        skills=skills,
        port=args.port,
        ollama_host=args.ollama_host
    )


if __name__ == "__main__":
    main() 