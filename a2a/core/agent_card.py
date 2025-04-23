"""
Agent Card Module

This module handles the creation and management of A2A Agent Cards.
"""

import json
from typing import Dict, List, Any


class AgentCard:
    """
    Class representing an A2A Agent Card.
    
    Agent Cards are used for capability discovery in the A2A protocol.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        endpoint: str,
        skills: List[Dict[str, Any]],
        version: str = "1.0.0",
    ):
        """
        Initialize an Agent Card.
        
        Args:
            name: The name of the agent
            description: A description of the agent
            endpoint: The URL where the agent is accessible
            skills: A list of skills the agent has
            version: The version of the agent
        """
        self.name = name
        self.description = description
        self.endpoint = endpoint
        self.skills = skills
        self.version = version
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the Agent Card to a dictionary.
        
        Returns:
            The Agent Card as a dictionary
        """
        return {
            "name": self.name,
            "description": self.description,
            "endpoint": self.endpoint,
            "skills": self.skills,
            "version": self.version,
            "protocol": "a2a-1.0"
        }
    
    def to_json(self) -> str:
        """
        Convert the Agent Card to a JSON string.
        
        Returns:
            The Agent Card as a JSON string
        """
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentCard':
        """
        Create an Agent Card from a dictionary.
        
        Args:
            data: The dictionary containing agent card data
            
        Returns:
            A new AgentCard instance
        """
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            endpoint=data.get("endpoint", ""),
            skills=data.get("skills", []),
            version=data.get("version", "1.0.0"),
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'AgentCard':
        """
        Create an Agent Card from a JSON string.
        
        Args:
            json_str: The JSON string containing agent card data
            
        Returns:
            A new AgentCard instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
        
    def add_mcp_capabilities(self, mcp_tools: List[Dict[str, Any]]) -> None:
        """
        Add MCP tools to agent capabilities.
        
        Args:
            mcp_tools: List of MCP tool definitions
        """
        for tool in mcp_tools:
            # Convert MCP tool parameters to A2A skill parameters
            parameters = []
            if "parameters" in tool:
                tool_params = tool["parameters"].get("properties", {})
                required_params = tool["parameters"].get("required", [])
                
                for param_name, param_details in tool_params.items():
                    parameters.append({
                        "name": param_name,
                        "description": param_details.get("description", ""),
                        "type": param_details.get("type", "string"),
                        "required": param_name in required_params
                    })
            
            # Add MCP tool as an A2A skill
            self.skills.append({
                "name": tool["name"],
                "description": tool["description"],
                "protocol": "mcp",
                "parameters": parameters
            })
    
    def get_mcp_skills(self) -> List[Dict[str, Any]]:
        """
        Get all skills that use the MCP protocol.
        
        Returns:
            List of MCP-based skills
        """
        return [skill for skill in self.skills if skill.get("protocol") == "mcp"] 