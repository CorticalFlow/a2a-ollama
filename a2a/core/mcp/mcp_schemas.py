"""
MCP Schemas Module

This module defines data structures used by MCP.
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field


class MCPParameterDefinition(BaseModel):
    """Definition of a parameter for an MCP tool."""
    
    name: str = Field(..., description="Name of the parameter")
    description: str = Field(..., description="Description of the parameter")
    type: str = Field(..., description="Type of the parameter (string, number, boolean, object, array)")
    required: bool = Field(False, description="Whether the parameter is required")
    schema_def: Optional[Dict[str, Any]] = Field(None, description="JSON Schema for complex types")


class MCPToolDefinition(BaseModel):
    """Definition of an MCP tool."""
    
    name: str = Field(..., description="Name of the tool")
    description: str = Field(..., description="Description of the tool")
    parameters: List[MCPParameterDefinition] = Field(default_factory=list, description="Parameters for the tool")
    return_schema: Optional[Dict[str, Any]] = Field(None, description="JSON Schema for the return value")
    
    def to_jsonschema(self) -> Dict[str, Any]:
        """Convert to JSONSchema format used by MCP."""
        parameters = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        for param in self.parameters:
            parameters["properties"][param.name] = {
                "description": param.description,
                "type": param.type
            }
            
            if param.schema_def:
                parameters["properties"][param.name].update(param.schema_def)
                
            if param.required:
                parameters["required"].append(param.name)
        
        return {
            "name": self.name,
            "description": self.description,
            "parameters": parameters
        }


class MCPToolCall(BaseModel):
    """Representation of an MCP tool call."""
    
    name: str = Field(..., description="Name of the tool being called")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the tool call")
    

class MCPToolResult(BaseModel):
    """Result of an MCP tool execution."""
    
    name: str = Field(..., description="Name of the tool that was called")
    result: Any = Field(..., description="Result of the tool execution")
    error: Optional[str] = Field(None, description="Error message if the tool execution failed") 