"""
MCP Integration Module

This module provides integration between A2A and Model Context Protocol (MCP).
"""

from a2a.core.mcp.mcp_client import MCPClient
from a2a.core.mcp.mcp_server import MCPServer
from a2a.core.mcp.mcp_schemas import MCPToolDefinition
from a2a.core.mcp.mcp_tool_manager import MCPToolManager

__all__ = ["MCPClient", "MCPServer", "MCPToolDefinition", "MCPToolManager"] 