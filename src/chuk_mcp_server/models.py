#!/usr/bin/env python3
"""
models.py - Data models and server state management

Contains all the data structures, session management, and global state
for the Fast MCP Server.
"""

import time
import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict


# ============================================================================
# Core Data Models
# ============================================================================

@dataclass
class MCPSession:
    """MCP session state with lifecycle management"""
    session_id: str
    client_info: Dict[str, Any]
    protocol_version: str
    created_at: float
    last_activity: float
    
    def touch(self):
        """Update last activity timestamp"""
        self.last_activity = time.time()
    
    def age(self) -> float:
        """Get session age in seconds"""
        return time.time() - self.created_at
    
    def idle_time(self) -> float:
        """Get idle time in seconds"""
        return time.time() - self.last_activity
    
    def is_expired(self, timeout: float = 3600) -> bool:
        """Check if session is expired (default 1 hour)"""
        return self.idle_time() > timeout


@dataclass
class ServerMetrics:
    """Runtime server metrics with performance tracking"""
    start_time: float
    total_requests: int = 0
    active_sessions: int = 0
    tool_calls: int = 0
    resource_reads: int = 0
    errors: int = 0
    
    def uptime(self) -> float:
        """Get server uptime in seconds"""
        return time.time() - self.start_time
    
    def rps(self) -> float:
        """Calculate requests per second"""
        uptime = self.uptime()
        return self.total_requests / uptime if uptime > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            **asdict(self),
            "uptime_seconds": self.uptime(),
            "requests_per_second": self.rps()
        }


@dataclass
class ToolDefinition:
    """Tool definition with schema validation"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    
    def to_mcp_format(self) -> Dict[str, Any]:
        """Convert to MCP protocol format"""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema
        }


@dataclass  
class ResourceDefinition:
    """Resource definition with metadata"""
    uri: str
    name: str
    description: str
    mime_type: str = "application/json"
    
    def to_mcp_format(self) -> Dict[str, Any]:
        """Convert to MCP protocol format"""
        return {
            "uri": self.uri,
            "name": self.name,
            "description": self.description
        }


# ============================================================================
# Server State Management
# ============================================================================

class ServerState:
    """Centralized server state with thread-safe operations"""
    
    def __init__(self):
        self.sessions: Dict[str, MCPSession] = {}
        self.metrics = ServerMetrics(start_time=time.time())
        self._tools: List[ToolDefinition] = []
        self._resources: List[ResourceDefinition] = []
        
        # Initialize with demo tools and resources
        self._initialize_demo_data()
    
    def _initialize_demo_data(self):
        """Initialize with demo tools and resources"""
        
        # Demo tools
        self._tools = [
            ToolDefinition(
                name="add",
                description="Add two numbers",
                input_schema={
                    "type": "object",
                    "properties": {
                        "a": {"type": "number", "description": "First number"},
                        "b": {"type": "number", "description": "Second number"}
                    },
                    "required": ["a", "b"]
                }
            ),
            ToolDefinition(
                name="hello",
                description="Say hello to someone",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Name to greet"}
                    },
                    "required": ["name"]
                }
            ),
            ToolDefinition(
                name="time",
                description="Get current time",
                input_schema={
                    "type": "object",
                    "properties": {}
                }
            )
        ]
        
        # Demo resources
        self._resources = [
            ResourceDefinition(
                uri="demo://server-info",
                name="Server Information",
                description="Current server status and information"
            ),
            ResourceDefinition(
                uri="demo://metrics",
                name="Server Metrics",
                description="Performance metrics and statistics"
            ),
            ResourceDefinition(
                uri="demo://tools",
                name="Available Tools",
                description="List of all available tools"
            )
        ]
    
    # Session Management
    def create_session(self, client_info: Dict[str, Any], protocol_version: str) -> MCPSession:
        """Create new MCP session"""
        session_id = str(uuid.uuid4())
        session = MCPSession(
            session_id=session_id,
            client_info=client_info,
            protocol_version=protocol_version,
            created_at=time.time(),
            last_activity=time.time()
        )
        self.sessions[session_id] = session
        self.metrics.active_sessions = len(self.sessions)
        return session
    
    def get_session(self, session_id: Optional[str]) -> Optional[MCPSession]:
        """Get session by ID and update activity"""
        if not session_id:
            return None
        session = self.sessions.get(session_id)
        if session:
            session.touch()
        return session
    
    def cleanup_expired_sessions(self, timeout: float = 3600):
        """Remove expired sessions"""
        expired = [
            sid for sid, session in self.sessions.items()
            if session.is_expired(timeout)
        ]
        for sid in expired:
            del self.sessions[sid]
        self.metrics.active_sessions = len(self.sessions)
        return len(expired)
    
    # Tools Management
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get all tools in MCP format"""
        return [tool.to_mcp_format() for tool in self._tools]
    
    def get_tool_by_name(self, name: str) -> Optional[ToolDefinition]:
        """Get tool by name"""
        for tool in self._tools:
            if tool.name == name:
                return tool
        return None
    
    def add_tool(self, tool: ToolDefinition):
        """Add a new tool"""
        # Remove existing tool with same name
        self._tools = [t for t in self._tools if t.name != tool.name]
        self._tools.append(tool)
    
    # Resources Management
    def get_resources(self) -> List[Dict[str, Any]]:
        """Get all resources in MCP format"""
        return [resource.to_mcp_format() for resource in self._resources]
    
    def get_resource_by_uri(self, uri: str) -> Optional[ResourceDefinition]:
        """Get resource by URI"""
        for resource in self._resources:
            if resource.uri == uri:
                return resource
        return None
    
    def add_resource(self, resource: ResourceDefinition):
        """Add a new resource"""
        # Remove existing resource with same URI
        self._resources = [r for r in self._resources if r.uri != resource.uri]
        self._resources.append(resource)
    
    # Metrics Management
    def increment_requests(self):
        """Increment total request counter"""
        self.metrics.total_requests += 1
    
    def increment_tool_calls(self):
        """Increment tool calls counter"""
        self.metrics.tool_calls += 1
    
    def increment_resource_reads(self):
        """Increment resource reads counter"""
        self.metrics.resource_reads += 1
    
    def increment_errors(self):
        """Increment error counter"""
        self.metrics.errors += 1
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get comprehensive server information"""
        return {
            "server": "fast-mcp-server",
            "version": "1.0.0",
            "protocol": "MCP 2025-06-18",
            "uptime_seconds": self.metrics.uptime(),
            "active_sessions": len(self.sessions),
            "total_tools": len(self._tools),
            "total_resources": len(self._resources),
            "performance": {
                "total_requests": self.metrics.total_requests,
                "requests_per_second": self.metrics.rps(),
                "tool_calls": self.metrics.tool_calls,
                "resource_reads": self.metrics.resource_reads,
                "errors": self.metrics.errors
            }
        }


# ============================================================================
# Global State Instance
# ============================================================================

# Global state instance - thread-safe for single-threaded async
# For multi-worker deployments, each worker gets its own instance
server_state = ServerState()


# ============================================================================
# Utility Functions
# ============================================================================

def get_state() -> ServerState:
    """Get the global server state instance"""
    return server_state


def reset_state():
    """Reset global state (useful for testing)"""
    global server_state
    server_state = ServerState()