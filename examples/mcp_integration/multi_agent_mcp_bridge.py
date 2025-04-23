"""
MCP Integration Example - Multi-Agent System with MCP Bridge

This example demonstrates a multi-agent system where agents communicate using A2A
and share tools via MCP.
"""

import os
import sys
import asyncio
import argparse
import json
import time
import requests
import logging

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from a2a.server import A2AServer
from a2a.client import A2AClient
from a2a.core.a2a_ollama import A2AOllama
from a2a.core.mcp.mcp_client import MCPClient
from a2a.core.mcp.mcp_server import MCPServer
from a2a.core.a2a_mcp_bridge import A2AMCPBridge


def configure_logging(log_level="INFO"):
    """Configure logging with appropriate level and format."""
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    # Set specific loggers of interest to the requested level
    loggers = [
        "mcp_client", 
        "mcp_server", 
        "a2a_mcp_bridge",
        "a2a_server",
        "a2a_client"
    ]
    for logger_name in loggers:
        logging.getLogger(logger_name).setLevel(numeric_level)
    
    return logging.getLogger("multi_agent_example")


def get_weather(location: str) -> dict:
    """Simple mock weather tool."""
    return {
        "temperature": 72,
        "condition": "sunny",
        "location": location
    }


def calculate(expression: str) -> dict:
    """Simple calculator tool."""
    try:
        result = eval(expression)
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}


def check_server_availability(url, max_retries=10, retry_delay=3):
    """Check if a server is available by making a simple HTTP request."""
    logger = logging.getLogger("server_check")
    for i in range(max_retries):
        try:
            logger.info(f"Checking server availability: {url} (Attempt {i+1}/{max_retries})")
            response = requests.get(url, timeout=30)  # Increased timeout to 30 seconds
            if response.status_code < 500:  # Consider any non-5xx response as available
                logger.info(f"Server at {url} is available (status {response.status_code})")
                return True
        except requests.RequestException as e:
            logger.warning(f"Request failed: {e}")
        
        logger.info(f"Server at {url} not ready yet, retrying in {retry_delay}s")
        time.sleep(retry_delay)
    
    logger.error(f"Server at {url} could not be reached after {max_retries} attempts")
    return False


async def main():
    """Run a multi-agent system with MCP bridge."""
    parser = argparse.ArgumentParser(description="Multi-Agent System with MCP Bridge")
    parser.add_argument("--host", type=str, default="localhost", help="Host to run the servers on")
    parser.add_argument("--model", type=str, default="llama2", help="Ollama model to use")
    parser.add_argument("--log-level", type=str, choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                        default="INFO", help="Set logging level")
    
    args = parser.parse_args()
    
    # Set up logging
    logger = configure_logging(args.log_level)
    logger.info(f"Starting multi-agent MCP bridge example with model: {args.model}")
    
    # Configure ports
    tool_provider_port = 8000
    tool_consumer_port = 8001
    mcp_server_port = 3000
    
    # Initialize servers to None
    mcp_server = None
    tool_provider_server = None
    tool_consumer_server = None
    
    try:
        # Create MCP server for tool provider
        logger.info(f"Creating MCP server on port {mcp_server_port}")
        mcp_server = MCPServer(
            host=args.host,
            port=mcp_server_port,
            name="Tool Provider MCP Server",
            description="MCP server providing common tools",
            version="1.0.0"
        )
        
        # Register tools with the MCP server
        logger.info("Registering get_weather tool")
        mcp_server.register_tool(
            name="get_weather",
            description="Get weather for a location",
            function=get_weather,
            parameters=[
                {
                    "name": "location",
                    "description": "City name",
                    "type": "string",
                    "required": True
                }
            ]
        )
        
        logger.info("Registering calculate tool")
        mcp_server.register_tool(
            name="calculate",
            description="Calculate a mathematical expression",
            function=calculate,
            parameters=[
                {
                    "name": "expression",
                    "description": "Mathematical expression to evaluate",
                    "type": "string",
                    "required": True
                }
            ]
        )
        
        # Start MCP server
        logger.info(f"Starting MCP server at http://{args.host}:{mcp_server_port}...")
        await mcp_server.start()
        logger.info("MCP server started.")
        
        # Add a small delay to allow the server to fully initialize
        logger.info("Waiting for MCP server initialization...")
        await asyncio.sleep(5)  # Increased from 2 to 5 seconds
        
        # Wait for MCP server to be fully ready
        logger.info("Checking MCP server availability...")
        mcp_server_url = f"http://{args.host}:{mcp_server_port}"
        discovery_url = f"{mcp_server_url}/.well-known/mcp.json"
        if not check_server_availability(discovery_url):
            logger.error("MCP server doesn't seem to be responding properly.")
            raise RuntimeError("Failed to start MCP server. Exiting.")
        
        # Create tool provider agent (just a basic A2A agent)
        tool_provider_name = "Tool Provider Agent"
        tool_provider_skills = [
            {
                "name": "provide_tools",
                "description": "Provide tools via MCP",
                "parameters": []
            }
        ]
        
        logger.info(f"Creating Tool Provider agent ({tool_provider_name})")
        tool_provider_agent = A2AOllama(
            model=args.model,
            name=tool_provider_name,
            description="Agent that provides tools via MCP",
            skills=tool_provider_skills,
            endpoint=f"http://{args.host}:{tool_provider_port}"
        )
        
        tool_provider_server = A2AServer(
            model=args.model,
            name=tool_provider_name,
            description="Agent that provides tools via MCP",
            skills=tool_provider_skills,
            port=tool_provider_port,
            endpoint=f"http://{args.host}:{tool_provider_port}"
        )
        
        # Start tool provider server
        logger.info(f"Starting tool provider server at http://{args.host}:{tool_provider_port}...")
        await tool_provider_server.start()
        logger.info("Tool provider server started.")
        
        # Create tool consumer agent that uses MCP tools
        tool_consumer_name = "Tool Consumer Agent"
        tool_consumer_skills = [
            {
                "name": "answer_questions",
                "description": "Answer questions using MCP tools when needed",
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
        
        logger.info(f"Creating Tool Consumer agent ({tool_consumer_name})")
        tool_consumer_agent = A2AOllama(
            model=args.model,
            name=tool_consumer_name,
            description="Agent that consumes tools via MCP",
            skills=tool_consumer_skills,
            endpoint=f"http://{args.host}:{tool_consumer_port}"
        )
        
        # Create MCP client for tool consumer
        logger.info(f"Creating MCP client for server at {mcp_server_url}")
        mcp_client = MCPClient(server_url=mcp_server_url)
        
        # Connect to MCP server
        logger.info(f"Connecting to MCP server...")
        mcp_connected = False
        try:
            logger.debug("Initiating connection to MCP server")
            server_info = await mcp_client.connect()
            logger.info(f"Connected to MCP server: {server_info.get('name', 'Unknown')}")
            mcp_connected = True
            
            # Discover tools
            logger.info("Discovering available MCP tools")
            tools = await mcp_client.list_tools()
            logger.info(f"Discovered {len(tools)} MCP tools:")
            for tool in tools:
                logger.info(f"  - {tool.name}: {tool.description}")
            
            # Create A2A-MCP bridge for tool consumer
            logger.info("Creating A2A-MCP bridge for Tool Consumer")
            bridge = A2AMCPBridge(mcp_client=mcp_client)
            
            # Enable MCP in tool consumer
            logger.info("Enabling MCP in Tool Consumer agent")
            tool_consumer_agent.task_manager.enable_mcp(bridge)
            tool_consumer_agent.configure_mcp_client(mcp_client)
            
            # Register MCP tools as A2A skills
            logger.info("Registering MCP tools as A2A skills")
            for tool in tools:
                logger.info(f"Registering {tool.name} as A2A skill")
                skill = await bridge.register_a2a_skill_for_mcp_tool(tool.name, tool.description)
                logger.info(f"Registered MCP tool '{tool.name}' as A2A skill in consumer agent")
        except Exception as e:
            logger.error(f"Warning: Failed to connect to MCP server or register tools: {e}")
            import traceback
            logger.debug("Error details:")
            logger.debug(traceback.format_exc())
            logger.info("Continuing without MCP tools...")
        
        # Create and start the tool consumer server regardless of MCP connection status
        logger.info("Creating tool consumer server...")
        tool_consumer_server = A2AServer(
            model=args.model,
            name=tool_consumer_name,
            description="Agent that consumes tools via MCP",
            skills=tool_consumer_skills,
            port=tool_consumer_port,
            endpoint=f"http://{args.host}:{tool_consumer_port}"
        )
        
        logger.info(f"Starting tool consumer server at http://{args.host}:{tool_consumer_port}...")
        await tool_consumer_server.start()
        logger.info("Tool consumer server started.")
        
        # Create A2A client to interact with tool consumer
        logger.info(f"Creating A2A client to interact with Tool Consumer at http://{args.host}:{tool_consumer_port}")
        client = A2AClient(endpoint=f"http://{args.host}:{tool_consumer_port}")
        
        # Test interaction with the multi-agent system
        try:
            # Discover agent capabilities
            logger.info("\nDiscovering agent capabilities...")
            agent_card = client.discover_agent()
            logger.info(f"Connected to agent: {agent_card['name']}")
            logger.info(f"Description: {agent_card['description']}")
            logger.info(f"Skills: {', '.join(skill['name'] for skill in agent_card['skills'])}")
            
            # Send test questions that should use MCP tools
            test_questions = [
                "What's the weather like in San Francisco?",
                "Calculate 123 * 456 + 789",
                "Tell me a joke and then calculate 15% of 67"
            ]
            
            for question in test_questions:
                logger.info(f"\n----- Testing Question: {question} -----")
                
                # Send the question to the agent
                logger.info(f"Sending question to agent at http://{args.host}:{tool_consumer_port}...")
                response = client.chat(question)
                
                # Display the response
                logger.info("\nResponse:")
                if "message" in response:
                    for part in response["message"]["parts"]:
                        if part["type"] == "text":
                            logger.info(part["content"])
                else:
                    logger.info(response)
                    
                logger.info("-" * 50)
                
            logger.info("\nMulti-agent system with MCP bridge test completed.")
        except Exception as e:
            logger.error(f"Error during interaction: {e}")
            import traceback
            logger.debug("Error details:")
            logger.debug(traceback.format_exc())
        
        logger.info("\nPress Ctrl+C to exit...")
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        logger.debug("Error details:")
        logger.debug(traceback.format_exc())
    finally:
        # Stop all servers that have been started
        logger.info("Stopping servers...")
        if tool_consumer_server:
            await tool_consumer_server.stop()
        if tool_provider_server:
            await tool_provider_server.stop()
        if mcp_server:
            await mcp_server.stop()
        logger.info("All servers stopped.")


if __name__ == "__main__":
    asyncio.run(main()) 