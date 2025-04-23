"""
MCP Tool Manager Module

This module handles registration and management of MCP tools.
"""

from typing import Dict, List, Optional, Any, Callable
from a2a.core.mcp.mcp_schemas import MCPToolDefinition


class MCPToolManager:
    """Manager for registering and executing MCP tools."""
    
    def __init__(self):
        """Initialize the Tool Manager."""
        self.tools: Dict[str, Dict[str, Any]] = {}
    
    def register_tool(
        self, 
        name: str, 
        description: str, 
        function: Callable, 
        parameters: List[Dict[str, Any]],
        return_schema: Optional[Dict[str, Any]] = None
    ) -> MCPToolDefinition:
        """
        Register a function as an MCP tool.
        
        Args:
            name: Name of the tool
            description: Description of the tool
            function: The function to execute when the tool is called
            parameters: Parameters for the tool
            return_schema: JSON Schema for the return value
            
        Returns:
            The tool definition
        """
        # Create parameter definitions from the parameter specs
        param_defs = []
        for param in parameters:
            param_defs.append({
                "name": param.get("name", ""),
                "description": param.get("description", ""),
                "type": param.get("type", "string"),
                "required": param.get("required", False),
                "schema_def": param.get("schema")
            })
        
        # Create the tool definition
        tool_def = MCPToolDefinition(
            name=name,
            description=description,
            parameters=param_defs,
            return_schema=return_schema
        )
        
        # Store the tool
        self.tools[name] = {
            "definition": tool_def,
            "function": function
        }
        
        return tool_def
        
    def execute_tool(self, name: str, parameters: Dict[str, Any]) -> Any:
        """
        Execute a registered tool.
        
        Args:
            name: Name of the tool to execute
            parameters: Parameters for the tool
            
        Returns:
            The result of the tool execution
        """
        if name not in self.tools:
            raise ValueError(f"Tool not found: {name}")
            
        tool = self.tools[name]
        
        # Execute the tool function with the provided parameters
        result = tool["function"](**parameters)
        
        return result
        
    def get_tool_definition(self, name: str) -> Optional[MCPToolDefinition]:
        """
        Get the definition of a registered tool.
        
        Args:
            name: Name of the tool
            
        Returns:
            The tool definition or None if not found
        """
        if name not in self.tools:
            return None
            
        return self.tools[name]["definition"]
        
    def list_tools(self) -> List[MCPToolDefinition]:
        """
        List all registered tools.
        
        Returns:
            List of tool definitions
        """
        return [tool["definition"] for tool in self.tools.values()] 