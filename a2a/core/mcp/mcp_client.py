"""
MCP Client Module

This module provides a client for connecting to MCP servers.
"""

import json
import requests
import logging
from typing import Dict, List, Optional, Any, Callable

from a2a.core.mcp.mcp_schemas import MCPToolDefinition, MCPToolCall, MCPToolResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mcp_client")


class MCPClient:
    """Client for connecting to MCP servers and discovering/using tools."""
    
    def __init__(self, server_url: str, auth_config: Optional[Dict[str, Any]] = None):
        """
        Initialize MCP client with server URL and optional auth.
        
        Args:
            server_url: URL of the MCP server
            auth_config: Authentication configuration
        """
        self.server_url = server_url.rstrip("/")
        self.auth_config = auth_config
        self.available_tools: Dict[str, MCPToolDefinition] = {}
        logger.info(f"Initialized MCP client for server: {self.server_url}")
        
    async def connect(self) -> Dict[str, Any]:
        """
        Establish connection to MCP server and discover available tools.
        
        Returns:
            Server information
        """
        # Fetch server information
        discovery_url = f"{self.server_url}/.well-known/mcp.json"
        logger.info(f"Attempting to connect to MCP server at: {discovery_url}")
        
        try:
            headers = self._get_headers()
            logger.debug(f"Using headers: {headers}")
            
            response = requests.get(
                discovery_url,
                headers=headers,
                timeout=10  # Added timeout
            )
            
            logger.debug(f"Server response status: {response.status_code}")
            response.raise_for_status()
            
            server_info = response.json()
            logger.info(f"Successfully connected to MCP server: {server_info.get('name', 'Unknown')}")
            
            # Discover available tools
            await self.list_tools()
            
            return server_info
        except requests.exceptions.Timeout:
            logger.error(f"Connection to {discovery_url} timed out after 10 seconds")
            raise
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error to {discovery_url}: {e}")
            raise
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error connecting to {discovery_url}: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from {discovery_url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error connecting to {discovery_url}: {e}")
            raise
        
    async def list_tools(self) -> List[MCPToolDefinition]:
        """
        Return list of available tools from the MCP server.
        
        Returns:
            List of tool definitions
        """
        tools_url = f"{self.server_url}/tools"
        logger.info(f"Fetching available tools from: {tools_url}")
        
        try:
            response = requests.get(
                tools_url,
                headers=self._get_headers(),
                timeout=10  # Added timeout
            )
            
            logger.debug(f"Tools endpoint response status: {response.status_code}")
            response.raise_for_status()
            
            tools_data = response.json()
            logger.debug(f"Received tools data: {json.dumps(tools_data)[:200]}...")
            
            # Parse tools and store them
            tools = []
            for tool_data in tools_data.get("tools", []):
                tool = MCPToolDefinition(
                    name=tool_data.get("name", ""),
                    description=tool_data.get("description", ""),
                    # Convert from JSONSchema format to our internal format
                    parameters=[],  # This is simplified; would need to properly parse parameters
                    return_schema=tool_data.get("return", {})
                )
                tools.append(tool)
                self.available_tools[tool.name] = tool
                logger.info(f"Registered tool: {tool.name}")
                
            logger.info(f"Successfully discovered {len(tools)} tools")
            return tools
        except Exception as e:
            logger.error(f"Error fetching tools from {tools_url}: {e}")
            raise
        
    async def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> MCPToolResult:
        """
        Execute a tool on the MCP server with given parameters.
        
        Args:
            tool_name: Name of the tool to execute
            params: Parameters for the tool
            
        Returns:
            Result of the tool execution
        """
        if tool_name not in self.available_tools:
            logger.error(f"Tool not found: {tool_name}")
            raise ValueError(f"Tool not found: {tool_name}")
            
        call = MCPToolCall(name=tool_name, parameters=params)
        execute_url = f"{self.server_url}/execute"
        logger.info(f"Executing tool '{tool_name}' with parameters: {json.dumps(params)}")
        
        try:
            payload = {"name": call.name, "parameters": call.parameters}
            logger.debug(f"Sending execution request to {execute_url} with payload: {json.dumps(payload)}")
            
            response = requests.post(
                execute_url,
                headers=self._get_headers(),
                json=payload,
                timeout=30  # Longer timeout for execution
            )
            
            logger.debug(f"Tool execution response status: {response.status_code}")
            
            try:
                response.raise_for_status()
                result_data = response.json()
                logger.info(f"Tool '{tool_name}' executed successfully")
                logger.debug(f"Tool result: {json.dumps(result_data)[:200]}...")
                
                return MCPToolResult(
                    name=tool_name,
                    result=result_data.get("result"),
                    error=None
                )
            except requests.HTTPError as e:
                error_msg = str(e)
                try:
                    error_data = response.json()
                    if "error" in error_data:
                        error_msg = error_data["error"]
                        logger.error(f"Tool execution returned error: {error_msg}")
                except:
                    logger.error(f"Tool execution failed with status {response.status_code}, but no error details available")
                    pass
                    
                return MCPToolResult(
                    name=tool_name,
                    result=None,
                    error=error_msg
                )
        except Exception as e:
            logger.error(f"Unexpected error executing tool '{tool_name}': {e}")
            return MCPToolResult(
                name=tool_name,
                result=None,
                error=str(e)
            )
            
    def _get_headers(self) -> Dict[str, str]:
        """
        Get HTTP headers for MCP requests.
        
        Returns:
            Headers dictionary
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Add authentication headers if configured
        if self.auth_config:
            auth_type = self.auth_config.get("type")
            
            if auth_type == "bearer":
                token = self.auth_config.get("token", "")
                headers["Authorization"] = f"Bearer {token}"
                logger.debug("Added bearer token authentication to headers")
            elif auth_type == "api_key":
                key = self.auth_config.get("key", "")
                key_name = self.auth_config.get("key_name", "X-API-Key")
                headers[key_name] = key
                logger.debug(f"Added API key authentication with key name: {key_name}")
                
        return headers 