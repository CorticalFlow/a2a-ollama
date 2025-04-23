"""
MCP Server Module

This module provides a server for exposing tools via the MCP protocol.
"""

import json
import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from aiohttp import web

from a2a.core.mcp.mcp_tool_manager import MCPToolManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mcp_server")


class MCPServer:
    """Server for exposing tools via the MCP protocol."""
    
    def __init__(
        self, 
        host: str = "localhost", 
        port: int = 3000,
        name: str = "MCP Server",
        description: str = "A server implementing the Model Context Protocol",
        version: str = "1.0.0"
    ):
        """
        Initialize MCP server.
        
        Args:
            host: Host to bind the server to
            port: Port to bind the server to
            name: Name of the server
            description: Description of the server
            version: Version of the server
        """
        self.host = host
        self.port = port
        self.name = name
        self.description = description
        self.version = version
        self.tool_manager = MCPToolManager()
        self.app = None
        self.runner = None
        self.site = None
        logger.info(f"Initialized MCP server {name} v{version} on {host}:{port}")
        
    def register_tool(
        self,
        name: str,
        description: str,
        function: Callable,
        parameters: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Register a tool with the MCP server.
        
        Args:
            name: Name of the tool
            description: Description of the tool
            function: Function to execute when the tool is called
            parameters: List of parameters for the tool
            
        Returns:
            The registered tool definition
        """
        logger.info(f"Registering tool: {name}")
        logger.debug(f"Tool details - Description: {description}, Parameters: {json.dumps(parameters)}")
        return self.tool_manager.register_tool(name, description, function, parameters)
    
    async def start(self):
        """Start the MCP server."""
        logger.info(f"Starting MCP server on {self.host}:{self.port}")
        if self.app:
            logger.warning("Server already started")
            return
            
        # Create aiohttp app
        self.app = web.Application()
        
        # Register routes
        self.app.router.add_get('/.well-known/mcp.json', self._handler_discovery)
        self.app.router.add_get('/tools', self._handler_list_tools)
        self.app.router.add_post('/execute', self._handler_execute_tool)
        
        # Add CORS middleware
        logger.debug("Adding CORS middleware")
        @web.middleware
        async def cors_middleware(request, handler):
            resp = await handler(request)
            resp.headers['Access-Control-Allow-Origin'] = '*'
            resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            resp.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return resp
            
        self.app.middlewares.append(cors_middleware)
        
        # Start server
        try:
            logger.debug("Creating server runner")
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            
            logger.debug(f"Creating TCP site on {self.host}:{self.port}")
            self.site = web.TCPSite(self.runner, self.host, self.port)
            
            logger.debug("Starting site")
            await self.site.start()
            logger.info(f"MCP server started on http://{self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Error starting MCP server: {e}")
            # Clean up resources in case of error
            if self.runner:
                await self.runner.cleanup()
                self.runner = None
            self.app = None
            self.site = None
            raise
    
    async def stop(self):
        """Stop the MCP server."""
        logger.info("Stopping MCP server")
        if self.runner:
            logger.debug("Cleaning up server resources")
            await self.runner.cleanup()
            self.runner = None
            self.app = None
            self.site = None
            logger.info("MCP server stopped")
    
    async def _handler_discovery(self, request):
        """Handler for MCP discovery endpoint."""
        logger.info("Received discovery request")
        try:
            discovery_data = {
                "name": self.name,
                "description": self.description,
                "version": self.version,
                "contact": {},
                "auth": {
                    "type": "none"
                },
                "endpoints": {
                    "tools": "/tools",
                    "execute": "/execute"
                }
            }
            
            logger.debug(f"Returning discovery data: {json.dumps(discovery_data)}")
            return web.json_response(discovery_data)
        except Exception as e:
            logger.error(f"Error handling discovery request: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def _handler_list_tools(self, request):
        """Handler for listing tools endpoint."""
        logger.info("Received request to list tools")
        try:
            tools = self.tool_manager.list_tools()
            tool_list = []
            
            for tool in tools:
                tool_data = {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    },
                    "return": tool.return_schema
                }
                
                # Convert parameters to JSON Schema format
                for param in tool.parameters:
                    param_name = param.get("name")
                    tool_data["parameters"]["properties"][param_name] = {
                        "type": param.get("type", "string"),
                        "description": param.get("description", "")
                    }
                    
                    if param.get("required", False):
                        tool_data["parameters"]["required"].append(param_name)
                        
                tool_list.append(tool_data)
                
            response_data = {"tools": tool_list}
            logger.debug(f"Returning {len(tool_list)} tools")
            return web.json_response(response_data)
        except Exception as e:
            logger.error(f"Error handling list tools request: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def _handler_execute_tool(self, request):
        """Handler for executing a tool endpoint."""
        try:
            request_data = await request.json()
            tool_name = request_data.get("name")
            parameters = request_data.get("parameters", {})
            
            logger.info(f"Received request to execute tool: {tool_name}")
            logger.debug(f"Tool parameters: {json.dumps(parameters)}")
            
            if not tool_name:
                logger.warning("Missing tool name in request")
                return web.json_response({"error": "Missing tool name"}, status=400)
                
            # Execute the tool
            result = await self.tool_manager.execute_tool(tool_name, parameters)
            
            if "error" in result:
                logger.error(f"Error executing tool '{tool_name}': {result['error']}")
                return web.json_response({"error": result["error"]}, status=400)
                
            logger.info(f"Tool '{tool_name}' executed successfully")
            logger.debug(f"Tool result: {json.dumps(result)[:200]}...")
            
            return web.json_response({"result": result})
        except json.JSONDecodeError:
            logger.error("Invalid JSON in request body")
            return web.json_response({"error": "Invalid JSON in request body"}, status=400)
        except Exception as e:
            logger.error(f"Unexpected error handling tool execution: {e}")
            return web.json_response({"error": str(e)}, status=500) 