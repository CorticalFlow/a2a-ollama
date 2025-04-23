"""
A2A-MCP Bridge Module

This module provides a bridge between A2A tasks and MCP tool calls.
"""

import json
import uuid
import logging
from typing import Dict, List, Optional, Any, Callable

from a2a.core.mcp.mcp_client import MCPClient
from a2a.core.mcp.mcp_server import MCPServer
from a2a.core.mcp.mcp_schemas import MCPToolDefinition

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("a2a_mcp_bridge")


class A2AMCPBridge:
    """Bridge between A2A tasks and MCP tool calls."""
    
    def __init__(self, mcp_client: Optional[MCPClient] = None, mcp_server: Optional[MCPServer] = None):
        """
        Initialize bridge with optional MCP client and server.
        
        Args:
            mcp_client: MCP client for connecting to external MCP servers
            mcp_server: MCP server for exposing agent capabilities as MCP tools
        """
        self.mcp_client = mcp_client
        self.mcp_server = mcp_server
        
        # Map of MCP tool names to A2A skills
        self.mcp_to_a2a_map = {}
        
        # Map of A2A skill names to MCP tools
        self.a2a_to_mcp_map = {}
        
        logger.info("Initialized A2A-MCP Bridge")
        
        if mcp_client:
            logger.info(f"MCP client configured: {mcp_client.server_url}")
        if mcp_server:
            logger.info(f"MCP server configured: {mcp_server.host}:{mcp_server.port}")
        
    async def register_a2a_skill_for_mcp_tool(
        self, 
        tool_name: str, 
        description: str
    ) -> Dict[str, Any]:
        """
        Register an MCP tool as an A2A skill.
        
        Args:
            tool_name: Name of the MCP tool
            description: Description for the A2A skill
            
        Returns:
            The A2A skill representation
        """
        if not self.mcp_client:
            logger.error("MCP client is required for registering A2A skills for MCP tools")
            raise ValueError("MCP client is required")
            
        logger.info(f"Registering MCP tool '{tool_name}' as A2A skill")
            
        # Ensure tools are discovered
        if not self.mcp_client.available_tools:
            logger.debug("No tools discovered yet, fetching from MCP server")
            await self.mcp_client.list_tools()
            
        if tool_name not in self.mcp_client.available_tools:
            logger.error(f"MCP tool not found: {tool_name}")
            logger.debug(f"Available tools: {', '.join(self.mcp_client.available_tools.keys())}")
            raise ValueError(f"MCP tool not found: {tool_name}")
            
        tool = self.mcp_client.available_tools[tool_name]
        
        # Convert MCP tool parameters to A2A skill parameters
        parameters = []
        for param in tool.parameters:
            parameters.append({
                "name": param.name,
                "description": param.description,
                "type": param.type,
                "required": param.required
            })
            
        # Create A2A skill
        skill = {
            "name": tool_name,
            "description": description or tool.description,
            "parameters": parameters,
            "protocol": "mcp"
        }
        
        # Register mapping
        self.mcp_to_a2a_map[tool_name] = skill
        logger.info(f"Successfully registered MCP tool '{tool_name}' as A2A skill")
        logger.debug(f"Skill definition: {json.dumps(skill)}")
        
        return skill
        
    async def process_a2a_task_with_mcp(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an A2A task using MCP tools if appropriate.
        
        Args:
            task: The A2A task
            
        Returns:
            The result of processing the task
        """
        if not self.mcp_client:
            logger.error("MCP client is required for processing A2A tasks with MCP")
            raise ValueError("MCP client is required")
            
        # Check if this is an MCP-related task
        skill_name = task.get("params", {}).get("skill")
        
        logger.info(f"Processing A2A task with skill: {skill_name}")
        logger.debug(f"Task details: {json.dumps(task)[:200]}...")
        
        if not skill_name or skill_name not in self.mcp_to_a2a_map:
            # Not an MCP task
            logger.info(f"Skill '{skill_name}' is not registered as an MCP tool")
            return {"error": "Not an MCP task"}
            
        # This is an MCP task - extract parameters
        tool_name = skill_name  # In our implementation, we use the same name
        params = task.get("params", {}).get("parameters", {})
        
        logger.info(f"Executing MCP tool '{tool_name}' with parameters")
        logger.debug(f"Parameters: {json.dumps(params)}")
        
        # Execute the MCP tool
        try:
            result = await self.mcp_client.execute_tool(tool_name, params)
            
            if result.error:
                logger.error(f"MCP tool execution failed: {result.error}")
                return {
                    "error": result.error,
                    "status": "failed"
                }
                
            logger.info(f"MCP tool '{tool_name}' executed successfully")
            logger.debug(f"Result: {json.dumps(result.result)[:200] if result.result else None}...")
            
            # Create A2A response format
            return {
                "task_id": task.get("id"),
                "status": "completed",
                "artifacts": {
                    "result": result.result
                }
            }
        except Exception as e:
            logger.error(f"Error executing MCP tool '{tool_name}': {e}")
            import traceback
            logger.debug(f"Error details: {traceback.format_exc()}")
            
            return {
                "task_id": task.get("id"),
                "status": "failed",
                "error": str(e)
            }
        
    async def expose_agent_skills_as_mcp_tools(self, skills: List[Dict[str, Any]]) -> List[MCPToolDefinition]:
        """
        Expose agent's A2A skills as MCP tools.
        
        Args:
            skills: List of A2A skills
            
        Returns:
            List of created MCP tool definitions
        """
        if not self.mcp_server:
            logger.error("MCP server is required for exposing agent skills as MCP tools")
            raise ValueError("MCP server is required")
            
        logger.info(f"Exposing {len(skills)} A2A skills as MCP tools")
        tool_definitions = []
        
        for skill in skills:
            skill_name = skill.get("name")
            description = skill.get("description")
            
            logger.info(f"Exposing A2A skill '{skill_name}' as MCP tool")
            
            # Convert A2A parameters to MCP parameters
            parameters = []
            for param in skill.get("parameters", []):
                parameters.append({
                    "name": param.get("name"),
                    "description": param.get("description", ""),
                    "type": param.get("type", "string"),
                    "required": param.get("required", False)
                })
                
            # Create a function that will handle executing this skill via A2A
            async def skill_executor(**kwargs):
                # This function would need to be implemented to call back into A2A
                # We'll use a placeholder that just returns the parameters
                logger.info(f"Executing A2A skill '{skill_name}' via MCP")
                logger.debug(f"Parameters: {json.dumps(kwargs)}")
                
                return {
                    "skill": skill_name,
                    "parameters": kwargs,
                    "status": "executed"
                }
                
            # Register the MCP tool
            tool_def = self.mcp_server.register_tool(
                name=skill_name,
                function=skill_executor,
                description=description,
                parameters=parameters
            )
            
            # Record the mapping
            self.a2a_to_mcp_map[skill_name] = tool_def
            tool_definitions.append(tool_def)
            
            logger.info(f"Successfully exposed A2A skill '{skill_name}' as MCP tool")
            
        logger.info(f"Exposed {len(tool_definitions)} A2A skills as MCP tools")
        return tool_definitions 