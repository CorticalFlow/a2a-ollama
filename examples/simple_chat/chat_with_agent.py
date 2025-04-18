"""
Simple Chat Example - Client

This example demonstrates how to interact with an A2A agent.
"""

import os
import sys
import argparse

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from a2a.client import A2AClient


def main():
    """Chat with an A2A agent."""
    parser = argparse.ArgumentParser(description="Chat with an A2A Agent")
    parser.add_argument("--endpoint", type=str, default="http://localhost:8000", help="The A2A agent endpoint")
    parser.add_argument("--message", type=str, help="The message to send")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    
    args = parser.parse_args()
    
    client = A2AClient(args.endpoint)
    
    try:
        # Discover agent capabilities
        agent_card = client.discover_agent()
        print(f"Connected to agent: {agent_card['name']}")
        print(f"Description: {agent_card['description']}")
        print(f"Skills: {', '.join(skill['name'] for skill in agent_card['skills'])}")
        print()
        
        if args.interactive:
            # Interactive mode
            task_id = client.create_task({"type": "chat"})
            
            print("Enter your messages (type 'exit' to quit):")
            
            while True:
                user_input = input("> ")
                
                if user_input.lower() == "exit":
                    break
                
                message = {
                    "role": "user",
                    "parts": [
                        {
                            "type": "text",
                            "content": user_input
                        }
                    ]
                }
                
                response = client.add_message(task_id, message)
                
                if "message" in response:
                    for part in response["message"]["parts"]:
                        if part["type"] == "text":
                            print("\nAgent:", part["content"])
                else:
                    print("\nAgent:", response)
                
                print()
        elif args.message:
            # Single message mode
            response = client.chat(args.message)
            
            print("Response:")
            
            if "message" in response:
                for part in response["message"]["parts"]:
                    if part["type"] == "text":
                        print(part["content"])
            else:
                print(response)
        else:
            parser.print_help()
    
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main() 