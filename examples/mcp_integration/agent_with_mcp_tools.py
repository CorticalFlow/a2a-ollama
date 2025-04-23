"""
MCP Integration Example - Agent Using External MCP Tools

This example demonstrates how to create an A2A agent that can use external MCP tools.
"""

import os
import sys
import asyncio
import argparse

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from a2a.server import A2AServer
from a2a.core.a2a_ollama import A2AOllama
from a2a.core.mcp.mcp_client import MCPClient
from a2a.core.a2a_mcp_bridge import A2AMCPBridge


async def main():
    """Run the A2A agent with MCP tools."""
    parser = argparse.ArgumentParser(description="A2A Agent with MCP Tools")
    parser.add_argument("--host", type=str, default="localhost", help="Host to run the server on")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    parser.add_argument("--model", type=str, default="llama2", help="Ollama model to use")
    parser.add_argument("--mcp_server", type=str, default="http://localhost:3000", help="MCP server URL")
    
    args = parser.parse_args()
    
    # Define basic A2A agent details
    agent_name = "MCP-Enabled A2A Agent"
    agent_description = "An A2A agent that can use tools from an MCP server"
    
    # Define A2A skills (these are not related to MCP tools)
    basic_skills = [
        {
            "name": "answer_question",
            "description": "Answer general questions about any topic",
            "parameters": [
                {
                    "name": "question",
                    "description": "The question to answer",
                    "type": "string",
                    "required": True
                }
            ]
        }
    ]
    
    # Create the A2A-Ollama agent
    a2a_ollama = A2AOllama(
        model=args.model,
        name=agent_name,
        description=agent_description,
        skills=basic_skills,
        endpoint=f"http://{args.host}:{args.port}"
    )
    
    # Create the MCP client
    mcp_client = MCPClient(server_url=args.mcp_server)
    
    # Initialize server to None
    server = None
    
    try:
        # Connect to the MCP server
        print(f"Connecting to MCP server at {args.mcp_server}...")
        try:
            server_info = await mcp_client.connect()
            print(f"Connected to MCP server: {server_info.get('name', 'Unknown')}")
            
            # Discover tools
            tools = await mcp_client.list_tools()
            print(f"Discovered {len(tools)} MCP tools:")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")
            
            # Create the A2A-MCP bridge
            bridge = A2AMCPBridge(mcp_client=mcp_client)
            
            # Enable MCP in the task manager
            a2a_ollama.task_manager.enable_mcp(bridge)
            
            # Configure MCP client in A2AOllama
            a2a_ollama.configure_mcp_client(mcp_client)
            
            # Register MCP tools as A2A skills
            for tool in tools:
                skill = await bridge.register_a2a_skill_for_mcp_tool(tool.name, tool.description)
                print(f"Registered MCP tool '{tool.name}' as A2A skill")
        except Exception as e:
            print(f"Warning: Failed to connect to MCP server: {e}")
            print("Continuing without MCP tools...")
        
        # Create and start the A2A server
        server = A2AServer(
            model=args.model,
            name=agent_name,
            description=agent_description,
            skills=basic_skills,
            port=args.port,
            endpoint=f"http://{args.host}:{args.port}"
        )
        
        print(f"Starting A2A server at http://{args.host}:{args.port}...")
        await server.start()
        
        print("\nAgent is running. Press Ctrl+C to stop.")
        
        # Keep the server running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if server is not None:
            await server.stop()
            print("Server stopped.")


if __name__ == "__main__":
    asyncio.run(main()) 