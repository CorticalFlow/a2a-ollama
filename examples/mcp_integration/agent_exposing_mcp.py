"""
MCP Integration Example - Agent Exposing MCP Tools

This example demonstrates how to create an A2A agent that exposes its capabilities as MCP tools.
"""

import os
import sys
import asyncio
import argparse

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from a2a.server import A2AServer
from a2a.core.a2a_ollama import A2AOllama
from a2a.core.mcp.mcp_server import MCPServer
from a2a.core.a2a_mcp_bridge import A2AMCPBridge


async def main():
    """Run the A2A agent that exposes MCP tools."""
    parser = argparse.ArgumentParser(description="A2A Agent Exposing MCP Tools")
    parser.add_argument("--host", type=str, default="localhost", help="Host to run the server on")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    parser.add_argument("--mcp_port", type=int, default=3000, help="Port to run the MCP server on")
    parser.add_argument("--model", type=str, default="llama2", help="Ollama model to use")
    
    args = parser.parse_args()
    
    # Define basic A2A agent details
    agent_name = "MCP Provider A2A Agent"
    agent_description = "An A2A agent that exposes its capabilities as MCP tools"
    
    # Define A2A skills
    skills = [
        {
            "name": "summarize_text",
            "description": "Summarize a given text",
            "parameters": [
                {
                    "name": "text",
                    "description": "The text to summarize",
                    "type": "string",
                    "required": True
                },
                {
                    "name": "max_length",
                    "description": "Maximum length of the summary",
                    "type": "integer",
                    "required": False
                }
            ]
        },
        {
            "name": "answer_question",
            "description": "Answer a question about a specific topic",
            "parameters": [
                {
                    "name": "question",
                    "description": "The question to answer",
                    "type": "string",
                    "required": True
                },
                {
                    "name": "context",
                    "description": "Additional context for the question",
                    "type": "string",
                    "required": False
                }
            ]
        }
    ]
    
    # Create the A2A-Ollama agent
    a2a_ollama = A2AOllama(
        model=args.model,
        name=agent_name,
        description=agent_description,
        skills=skills,
        endpoint=f"http://{args.host}:{args.port}"
    )
    
    # Initialize servers to None
    a2a_server = None
    mcp_server = None
    
    try:
        # Create and start the A2A server
        a2a_server = A2AServer(
            model=args.model,
            name=agent_name,
            description=agent_description,
            skills=skills,
            port=args.port,
            endpoint=f"http://{args.host}:{args.port}"
        )
        
        # Create the MCP server
        mcp_server = MCPServer(
            host=args.host,
            port=args.mcp_port,
            name=f"{agent_name} MCP Server",
            description=f"MCP server exposing {agent_name} capabilities",
            version="1.0.0"
        )
        
        # Create the A2A-MCP bridge
        bridge = A2AMCPBridge(mcp_server=mcp_server)
        
        # Start the A2A server
        print(f"Starting A2A server at http://{args.host}:{args.port}...")
        await a2a_server.start()
        
        # Expose A2A skills as MCP tools
        print(f"Exposing A2A skills as MCP tools...")
        try:
            tool_definitions = await bridge.expose_agent_skills_as_mcp_tools(skills)
            print(f"Exposed {len(tool_definitions)} A2A skills as MCP tools:")
            for tool in tool_definitions:
                print(f"  - {tool.name}: {tool.description}")
            
            # Start the MCP server
            print(f"Starting MCP server at http://{args.host}:{args.mcp_port}...")
            await mcp_server.start()
            
            print("\nAgent is running and exposing MCP tools. Press Ctrl+C to stop.")
        except Exception as e:
            print(f"Warning: Failed to expose skills as MCP tools: {e}")
            print("\nAgent is running without MCP tools. Press Ctrl+C to stop.")
        
        # Keep the servers running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Stop servers that have been started
        if a2a_server:
            await a2a_server.stop()
        if mcp_server:
            await mcp_server.stop()
        print("Servers stopped.")


if __name__ == "__main__":
    asyncio.run(main()) 