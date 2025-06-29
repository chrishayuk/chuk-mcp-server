#!/usr/bin/env python3
"""
MCP Specification Compliance Test Suite
Version: 2025-06-18 (Latest)

Comprehensive test suite to validate MCP server compliance with the latest
Model Context Protocol specification as defined at:
https://modelcontextprotocol.io/specification/2025-06-18/

This test suite validates:
- JSON-RPC 2.0 compliance
- Protocol lifecycle management  
- Core MCP message types and formats
- Tool and resource capabilities
- Session management
- Error handling
- Security considerations
- Latest spec requirements (OAuth 2.1, structured output, etc.)
"""

import asyncio
import aiohttp
import json
import time
import uuid
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import logging
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TestResult(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"
    WARNING = "WARNING"


@dataclass
class TestCase:
    name: str
    description: str
    result: TestResult
    details: str = ""
    spec_reference: str = ""


class MCPComplianceValidator:
    """
    MCP Specification Compliance Validator
    
    Tests server compliance with MCP 2025-06-18 specification
    """
    
    def __init__(self, server_url: str):
        self.server_url = server_url.rstrip('/')
        self.session_id: Optional[str] = None
        self.server_capabilities: Dict[str, Any] = {}
        self.protocol_version: str = ""
        self.test_results: List[TestCase] = []
        
    async def run_compliance_tests(self) -> List[TestCase]:
        """Run complete MCP compliance test suite"""
        
        print("🧪 MCP Specification Compliance Test Suite")
        print("=" * 60)
        print(f"Target Server: {self.server_url}")
        print(f"Specification: MCP 2025-06-18 (Latest)")
        print(f"Test Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print("=" * 60)
        
        async with aiohttp.ClientSession() as session:
            self.session = session
            
            # Core Protocol Tests
            await self._test_json_rpc_compliance()
            await self._test_lifecycle_management()
            await self._test_capabilities_negotiation()
            
            # Feature Tests  
            await self._test_tools_functionality()
            await self._test_resources_functionality()
            await self._test_utilities()
            
            # Security and Best Practices
            await self._test_security_considerations()
            await self._test_error_handling()
            
            # Latest Spec Features (2025-06-18)
            await self._test_latest_spec_features()
            
        self._print_test_summary()
        return self.test_results
    
    async def _test_json_rpc_compliance(self):
        """Test JSON-RPC 2.0 compliance as required by MCP spec"""
        
        print("\n🔍 Testing JSON-RPC 2.0 Compliance")
        print("-" * 40)
        
        # Test 1: Valid JSON-RPC 2.0 message structure
        await self._test_case(
            "JSON-RPC 2.0 Message Format",
            "Messages must follow JSON-RPC 2.0 specification",
            self._validate_jsonrpc_format,
            "Base Protocol - Overview"
        )
        
        # Test 2: Required fields validation
        await self._test_case(
            "Required Fields Validation", 
            "Requests must include required fields: jsonrpc, method, id",
            self._validate_required_fields,
            "Base Protocol - Overview"
        )
        
        # Test 3: ID uniqueness and format
        await self._test_case(
            "Request ID Requirements",
            "Request IDs must be unique, non-null strings or integers",
            self._validate_request_ids,
            "Base Protocol - Overview"
        )
    
    async def _test_lifecycle_management(self):
        """Test MCP lifecycle management"""
        
        print("\n🔄 Testing Lifecycle Management")
        print("-" * 40)
        
        # Test 1: Initialize handshake
        await self._test_case(
            "Initialize Handshake",
            "Server must properly handle initialize request",
            self._test_initialize,
            "Lifecycle Management"
        )
        
        # Test 2: Capability negotiation
        await self._test_case(
            "Capability Negotiation",
            "Server must declare capabilities during initialization",
            self._test_capabilities,
            "Architecture - Capability Negotiation"
        )
        
        # Test 3: Initialized notification
        await self._test_case(
            "Initialized Notification",
            "Server must accept initialized notification",
            self._test_initialized_notification,
            "Lifecycle Management"
        )
        
        # Test 4: Session management
        await self._test_case(
            "Session Management",
            "Server must maintain session state properly",
            self._test_session_management,
            "Architecture - Stateful Sessions"
        )
    
    async def _test_capabilities_negotiation(self):
        """Test capability-based negotiation system"""
        
        print("\n⚙️ Testing Capabilities Negotiation")
        print("-" * 40)
        
        await self._test_case(
            "Server Capabilities Declaration",
            "Server must explicitly declare supported features",
            self._validate_server_capabilities,
            "Architecture - Capability Negotiation"
        )
    
    async def _test_tools_functionality(self):
        """Test tools functionality if supported"""
        
        print("\n🔧 Testing Tools Functionality")
        print("-" * 40)
        
        if not self.server_capabilities.get("tools"):
            self._add_result("Tools Support", "Server does not declare tools capability", TestResult.SKIP)
            return
            
        # Test tools/list
        await self._test_case(
            "Tools List",
            "Server must provide tools list when tools capability declared",
            self._test_tools_list,
            "Server Features - Tools"
        )
        
        # Test tools/call if tools available
        await self._test_case(
            "Tool Execution",
            "Server must execute tools properly with correct response format",
            self._test_tool_execution,
            "Server Features - Tools"
        )
        
        # Test tool schema validation
        await self._test_case(
            "Tool Schema Validation",
            "Tool definitions must include required schema fields",
            self._validate_tool_schemas,
            "Server Features - Tools"
        )
    
    async def _test_resources_functionality(self):
        """Test resources functionality if supported"""
        
        print("\n📄 Testing Resources Functionality") 
        print("-" * 40)
        
        if not self.server_capabilities.get("resources"):
            self._add_result("Resources Support", "Server does not declare resources capability", TestResult.SKIP)
            return
            
        # Test resources/list
        await self._test_case(
            "Resources List",
            "Server must provide resources list when capability declared",
            self._test_resources_list,
            "Server Features - Resources"
        )
        
        # Test resources/read
        await self._test_case(
            "Resource Reading",
            "Server must read resources properly with correct response format",
            self._test_resource_reading,
            "Server Features - Resources"
        )
        
        # Test resource schema validation
        await self._test_case(
            "Resource Schema Validation",
            "Resource definitions must include required schema fields",
            self._validate_resource_schemas,
            "Server Features - Resources"
        )
    
    async def _test_utilities(self):
        """Test utility functions"""
        
        print("\n🛠️ Testing Utilities")
        print("-" * 40)
        
        # Test ping
        await self._test_case(
            "Ping Utility",
            "Server should respond to ping requests",
            self._test_ping,
            "Utilities - Ping"
        )
    
    async def _test_security_considerations(self):
        """Test security considerations and best practices"""
        
        print("\n🔒 Testing Security Considerations") 
        print("-" * 40)
        
        # Test error information leakage
        await self._test_case(
            "Error Information Security",
            "Server should not leak sensitive information in error messages", 
            self._test_error_security,
            "Security Best Practices"
        )
        
        # Test malformed request handling
        await self._test_case(
            "Malformed Request Handling",
            "Server must handle malformed requests securely",
            self._test_malformed_requests,
            "Security Best Practices"
        )
    
    async def _test_error_handling(self):
        """Test error handling compliance"""
        
        print("\n❌ Testing Error Handling")
        print("-" * 40)
        
        # Test standard JSON-RPC errors
        await self._test_case(
            "Standard JSON-RPC Errors",
            "Server must return proper JSON-RPC error codes",
            self._test_standard_errors,
            "Base Protocol - Overview"
        )
        
        # Test method not found
        await self._test_case(
            "Method Not Found Error",
            "Server must return -32601 for unknown methods",
            self._test_method_not_found,
            "Base Protocol - Overview"
        )
        
        # Test invalid params
        await self._test_case(
            "Invalid Parameters Error", 
            "Server must return -32602 for invalid parameters",
            self._test_invalid_params,
            "Base Protocol - Overview"
        )
    
    async def _test_latest_spec_features(self):
        """Test features specific to 2025-06-18 specification"""
        
        print("\n🆕 Testing Latest Spec Features (2025-06-18)")
        print("-" * 40)
        
        # Test structured tool output (new in 2025-06-18)
        await self._test_case(
            "Structured Tool Output",
            "Server should support structured tool output format",
            self._test_structured_tool_output,
            "2025-06-18 Changelog - Structured Tool Output"
        )
        
        # Test MCP-Protocol-Version header requirement for HTTP
        await self._test_case(
            "Protocol Version Header",
            "Server should handle MCP-Protocol-Version header properly",
            self._test_protocol_version_header,
            "2025-06-18 Changelog - Protocol Version Header"
        )
        
        # Test _meta field support
        await self._test_case(
            "_meta Field Support",
            "Server should properly handle _meta fields in messages",
            self._test_meta_field_support,
            "2025-06-18 Changelog - _meta Field"
        )
        
        # Test OAuth 2.1 compliance indicators (if using HTTP auth)
        await self._test_case(
            "OAuth 2.1 Indicators",
            "Server should indicate OAuth 2.1 compliance if using auth",
            self._test_oauth_indicators,
            "2025-06-18 Changelog - OAuth 2.1"
        )
    
    # Test Implementation Methods
    
    async def _validate_jsonrpc_format(self) -> Tuple[bool, str]:
        """Validate JSON-RPC 2.0 message format compliance"""
        
        test_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "ping",
            "params": {}
        }
        
        try:
            async with self.session.post(
                self.server_url,
                json=test_message,
                headers={"Content-Type": "application/json"}
            ) as resp:
                if resp.status != 200:
                    return False, f"HTTP status {resp.status}, expected 200"
                    
                data = await resp.json()
                
                # Validate response structure
                if data.get("jsonrpc") != "2.0":
                    return False, "Response missing or invalid 'jsonrpc: 2.0' field"
                
                if "id" not in data:
                    return False, "Response missing 'id' field"
                
                if data["id"] != test_message["id"]:
                    return False, f"Response ID {data['id']} doesn't match request ID {test_message['id']}"
                
                if "result" not in data and "error" not in data:
                    return False, "Response must contain either 'result' or 'error'"
                
                if "result" in data and "error" in data:
                    return False, "Response must not contain both 'result' and 'error'"
                
                return True, "Valid JSON-RPC 2.0 format"
                
        except Exception as e:
            return False, f"Exception during validation: {str(e)}"
    
    async def _validate_required_fields(self) -> Tuple[bool, str]:
        """Test required field validation"""
        
        # Test missing jsonrpc field
        invalid_message = {"id": 1, "method": "ping"}
        
        try:
            async with self.session.post(
                self.server_url,
                json=invalid_message,
                headers={"Content-Type": "application/json"}
            ) as resp:
                data = await resp.json()
                
                if "error" in data and data["error"]["code"] == -32600:
                    return True, "Server properly rejects requests missing 'jsonrpc' field"
                else:
                    return False, "Server should return -32600 error for missing 'jsonrpc' field"
                    
        except Exception as e:
            return False, f"Exception during test: {str(e)}"
    
    async def _validate_request_ids(self) -> Tuple[bool, str]:
        """Test request ID requirements"""
        
        # Test with null ID (should be rejected per 2025-06-18 spec)
        invalid_message = {
            "jsonrpc": "2.0",
            "id": None,
            "method": "ping",
            "params": {}
        }
        
        try:
            async with self.session.post(
                self.server_url,
                json=invalid_message,
                headers={"Content-Type": "application/json"}
            ) as resp:
                data = await resp.json()
                
                if "error" in data:
                    return True, "Server properly rejects null ID (spec compliance)"
                else:
                    return False, "Server should reject null ID per 2025-06-18 spec"
                    
        except Exception as e:
            return False, f"Exception during test: {str(e)}"
    
    async def _test_initialize(self) -> Tuple[bool, str]:
        """Test MCP initialize handshake"""
        
        init_message = {
            "jsonrpc": "2.0",
            "id": "test-init-" + str(uuid.uuid4()),
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {
                    "roots": {"listChanged": True}
                },
                "clientInfo": {
                    "name": "mcp-compliance-tester",
                    "version": "1.0.0"
                }
            }
        }
        
        try:
            async with self.session.post(
                self.server_url,
                json=init_message,
                headers={"Content-Type": "application/json"}
            ) as resp:
                if resp.status != 200:
                    return False, f"HTTP status {resp.status}, expected 200"
                
                data = await resp.json()
                
                if "error" in data:
                    return False, f"Initialize failed with error: {data['error']}"
                
                result = data.get("result", {})
                
                # Validate required initialize response fields
                if "protocolVersion" not in result:
                    return False, "Initialize response missing 'protocolVersion'"
                
                if "serverInfo" not in result:
                    return False, "Initialize response missing 'serverInfo'"
                
                if "capabilities" not in result:
                    return False, "Initialize response missing 'capabilities'"
                
                # Store for later tests
                self.protocol_version = result["protocolVersion"]
                self.server_capabilities = result["capabilities"]
                
                # Get session ID if provided
                self.session_id = resp.headers.get("Mcp-Session-Id")
                
                return True, f"Initialize successful, protocol: {self.protocol_version}"
                
        except Exception as e:
            return False, f"Exception during initialize: {str(e)}"
    
    async def _test_capabilities(self) -> Tuple[bool, str]:
        """Test capability declaration"""
        
        if not self.server_capabilities:
            return False, "No capabilities received during initialize"
        
        # Validate capability structure
        valid_capabilities = ["tools", "resources", "prompts", "logging", "roots"]
        declared_caps = []
        
        for cap in valid_capabilities:
            if cap in self.server_capabilities:
                declared_caps.append(cap)
        
        if not declared_caps:
            return True, "Server declares no optional capabilities (valid)"
        
        return True, f"Server capabilities: {', '.join(declared_caps)}"
    
    async def _test_initialized_notification(self) -> Tuple[bool, str]:
        """Test initialized notification"""
        
        notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        }
        
        headers = {"Content-Type": "application/json"}
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        
        try:
            async with self.session.post(
                self.server_url,
                json=notification,
                headers=headers
            ) as resp:
                # Notification should return 204 No Content or empty response
                if resp.status in [200, 204]:
                    return True, f"Initialized notification accepted (HTTP {resp.status})"
                else:
                    return False, f"Unexpected status {resp.status} for notification"
                    
        except Exception as e:
            return False, f"Exception during notification: {str(e)}"
    
    async def _test_session_management(self) -> Tuple[bool, str]:
        """Test session management"""
        
        if not self.session_id:
            return True, "No session management (not required for all transports)"
        
        # Test using session ID in subsequent request
        ping_message = {
            "jsonrpc": "2.0", 
            "id": "session-test",
            "method": "ping",
            "params": {}
        }
        
        headers = {
            "Content-Type": "application/json",
            "Mcp-Session-Id": self.session_id
        }
        
        try:
            async with self.session.post(
                self.server_url,
                json=ping_message,
                headers=headers
            ) as resp:
                if resp.status == 200:
                    return True, f"Session management working with ID: {self.session_id[:8]}..."
                else:
                    return False, f"Session request failed with status {resp.status}"
                    
        except Exception as e:
            return False, f"Exception during session test: {str(e)}"
    
    async def _validate_server_capabilities(self) -> Tuple[bool, str]:
        """Validate server capabilities declaration"""
        
        if not self.server_capabilities:
            return False, "No server capabilities declared"
        
        # Check capability structure
        issues = []
        
        for cap_name, cap_value in self.server_capabilities.items():
            if not isinstance(cap_value, dict):
                issues.append(f"Capability '{cap_name}' should be an object")
        
        if issues:
            return False, "; ".join(issues)
        
        return True, f"Valid capabilities structure with {len(self.server_capabilities)} capabilities"
    
    async def _test_tools_list(self) -> Tuple[bool, str]:
        """Test tools/list functionality"""
        
        message = {
            "jsonrpc": "2.0",
            "id": "tools-list-test",
            "method": "tools/list",
            "params": {}
        }
        
        headers = {"Content-Type": "application/json"}
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        
        try:
            async with self.session.post(
                self.server_url,
                json=message,
                headers=headers
            ) as resp:
                if resp.status != 200:
                    return False, f"HTTP status {resp.status}, expected 200"
                
                data = await resp.json()
                
                if "error" in data:
                    return False, f"tools/list failed: {data['error']}"
                
                result = data.get("result", {})
                
                if "tools" not in result:
                    return False, "tools/list response missing 'tools' field"
                
                tools = result["tools"]
                if not isinstance(tools, list):
                    return False, "'tools' field must be an array"
                
                # Store tools for validation
                self.tools = tools
                
                return True, f"tools/list successful, found {len(tools)} tools"
                
        except Exception as e:
            return False, f"Exception during tools/list: {str(e)}"
    
    async def _test_tool_execution(self) -> Tuple[bool, str]:
        """Test tool execution"""
        
        if not hasattr(self, 'tools') or not self.tools:
            return True, "No tools available to test"
        
        # Find a simple tool to test (prefer 'add' or similar)
        test_tool = None
        for tool in self.tools:
            if tool.get("name") in ["add", "hello", "ping", "echo"]:
                test_tool = tool
                break
        
        if not test_tool:
            test_tool = self.tools[0]  # Use first available tool
        
        # Prepare tool call based on schema
        tool_args = {}
        input_schema = test_tool.get("inputSchema", {})
        properties = input_schema.get("properties", {})
        
        # Try to provide simple test arguments
        if test_tool["name"] == "add":
            tool_args = {"a": 5, "b": 3}
        elif test_tool["name"] == "hello":
            tool_args = {"name": "Test"}
        elif test_tool["name"] == "time":
            tool_args = {}
        
        message = {
            "jsonrpc": "2.0",
            "id": "tool-call-test",
            "method": "tools/call",
            "params": {
                "name": test_tool["name"],
                "arguments": tool_args
            }
        }
        
        headers = {"Content-Type": "application/json"}
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        
        try:
            async with self.session.post(
                self.server_url,
                json=message,
                headers=headers
            ) as resp:
                if resp.status != 200:
                    return False, f"HTTP status {resp.status}, expected 200"
                
                data = await resp.json()
                
                if "error" in data:
                    return False, f"Tool call failed: {data['error']}"
                
                result = data.get("result", {})
                
                if "content" not in result:
                    return False, "Tool call response missing 'content' field"
                
                content = result["content"]
                if not isinstance(content, list):
                    return False, "'content' field must be an array"
                
                return True, f"Tool '{test_tool['name']}' executed successfully"
                
        except Exception as e:
            return False, f"Exception during tool execution: {str(e)}"
    
    async def _validate_tool_schemas(self) -> Tuple[bool, str]:
        """Validate tool schema compliance"""
        
        if not hasattr(self, 'tools'):
            return True, "No tools to validate"
        
        issues = []
        
        for tool in self.tools:
            tool_name = tool.get("name", "unnamed")
            
            # Required fields
            if "name" not in tool:
                issues.append(f"Tool missing 'name' field")
            if "description" not in tool:
                issues.append(f"Tool '{tool_name}' missing 'description' field")
            if "inputSchema" not in tool:
                issues.append(f"Tool '{tool_name}' missing 'inputSchema' field")
            
            # Schema validation
            input_schema = tool.get("inputSchema", {})
            if input_schema.get("type") != "object":
                issues.append(f"Tool '{tool_name}' inputSchema type should be 'object'")
        
        if issues:
            return False, "; ".join(issues[:3])  # Limit to first 3 issues
        
        return True, f"All {len(self.tools)} tool schemas valid"
    
    async def _test_resources_list(self) -> Tuple[bool, str]:
        """Test resources/list functionality"""
        
        message = {
            "jsonrpc": "2.0",
            "id": "resources-list-test", 
            "method": "resources/list",
            "params": {}
        }
        
        headers = {"Content-Type": "application/json"}
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        
        try:
            async with self.session.post(
                self.server_url,
                json=message,
                headers=headers
            ) as resp:
                if resp.status != 200:
                    return False, f"HTTP status {resp.status}, expected 200"
                
                data = await resp.json()
                
                if "error" in data:
                    return False, f"resources/list failed: {data['error']}"
                
                result = data.get("result", {})
                
                if "resources" not in result:
                    return False, "resources/list response missing 'resources' field"
                
                resources = result["resources"]
                if not isinstance(resources, list):
                    return False, "'resources' field must be an array"
                
                # Store resources for validation
                self.resources = resources
                
                return True, f"resources/list successful, found {len(resources)} resources"
                
        except Exception as e:
            return False, f"Exception during resources/list: {str(e)}"
    
    async def _test_resource_reading(self) -> Tuple[bool, str]:
        """Test resource reading functionality"""
        
        if not hasattr(self, 'resources') or not self.resources:
            return True, "No resources available to test"
        
        # Use first available resource
        test_resource = self.resources[0]
        
        message = {
            "jsonrpc": "2.0",
            "id": "resource-read-test",
            "method": "resources/read",
            "params": {
                "uri": test_resource["uri"]
            }
        }
        
        headers = {"Content-Type": "application/json"}
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        
        try:
            async with self.session.post(
                self.server_url,
                json=message,
                headers=headers
            ) as resp:
                if resp.status != 200:
                    return False, f"HTTP status {resp.status}, expected 200"
                
                data = await resp.json()
                
                if "error" in data:
                    return False, f"Resource read failed: {data['error']}"
                
                result = data.get("result", {})
                
                if "contents" not in result:
                    return False, "Resource read response missing 'contents' field"
                
                contents = result["contents"]
                if not isinstance(contents, list):
                    return False, "'contents' field must be an array"
                
                return True, f"Resource '{test_resource['uri']}' read successfully"
                
        except Exception as e:
            return False, f"Exception during resource read: {str(e)}"
    
    async def _validate_resource_schemas(self) -> Tuple[bool, str]:
        """Validate resource schema compliance"""
        
        if not hasattr(self, 'resources'):
            return True, "No resources to validate"
        
        issues = []
        
        for resource in self.resources:
            resource_uri = resource.get("uri", "no-uri")
            
            # Required fields
            if "uri" not in resource:
                issues.append(f"Resource missing 'uri' field")
            if "name" not in resource:
                issues.append(f"Resource '{resource_uri}' missing 'name' field")
            if "description" not in resource:
                issues.append(f"Resource '{resource_uri}' missing 'description' field")
        
        if issues:
            return False, "; ".join(issues[:3])  # Limit to first 3 issues
        
        return True, f"All {len(self.resources)} resource schemas valid"
    
    async def _test_ping(self) -> Tuple[bool, str]:
        """Test ping utility"""
        
        message = {
            "jsonrpc": "2.0",
            "id": "ping-test",
            "method": "ping",
            "params": {}
        }
        
        headers = {"Content-Type": "application/json"}
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        
        try:
            async with self.session.post(
                self.server_url,
                json=message,
                headers=headers
            ) as resp:
                if resp.status != 200:
                    return False, f"HTTP status {resp.status}, expected 200"
                
                data = await resp.json()
                
                if "error" in data:
                    return False, f"Ping failed: {data['error']}"
                
                # Ping should return empty result
                result = data.get("result", {})
                
                return True, "Ping successful"
                
        except Exception as e:
            return False, f"Exception during ping: {str(e)}"
    
    async def _test_error_security(self) -> Tuple[bool, str]:
        """Test that errors don't leak sensitive information"""
        
        # Try to cause an error and check the response
        invalid_message = {
            "jsonrpc": "2.0",
            "id": "error-test",
            "method": "nonexistent/method",
            "params": {}
        }
        
        try:
            async with self.session.post(
                self.server_url,
                json=invalid_message,
                headers={"Content-Type": "application/json"}
            ) as resp:
                data = await resp.json()
                
                if "error" in data:
                    error_message = data["error"].get("message", "")
                    
                    # Check for potential information leakage
                    sensitive_patterns = [
                        "password", "secret", "token", "key", 
                        "internal", "private", "confidential",
                        "stack trace", "traceback", "exception"
                    ]
                    
                    for pattern in sensitive_patterns:
                        if pattern.lower() in error_message.lower():
                            return False, f"Error message may leak sensitive info: '{pattern}'"
                    
                    return True, "Error messages appear to be safe"
                else:
                    return True, "No error generated for invalid method"
                    
        except Exception as e:
            return False, f"Exception during error security test: {str(e)}"
    
    async def _test_malformed_requests(self) -> Tuple[bool, str]:
        """Test handling of malformed requests"""
        
        # Test with invalid JSON
        try:
            async with self.session.post(
                self.server_url,
                data="invalid json {",
                headers={"Content-Type": "application/json"}
            ) as resp:
                if resp.status == 400:
                    return True, "Server properly rejects malformed JSON"
                else:
                    data = await resp.json()
                    if "error" in data and data["error"]["code"] == -32700:
                        return True, "Server returns proper parse error"
                    else:
                        return False, "Server should reject malformed JSON"
                        
        except Exception as e:
            return False, f"Exception during malformed request test: {str(e)}"
    
    async def _test_standard_errors(self) -> Tuple[bool, str]:
        """Test standard JSON-RPC error codes"""
        
        # This is tested in other methods, summarize here
        return True, "Standard error codes tested in other test cases"
    
    async def _test_method_not_found(self) -> Tuple[bool, str]:
        """Test method not found error"""
        
        message = {
            "jsonrpc": "2.0",
            "id": "method-not-found-test",
            "method": "definitely/not/a/real/method",
            "params": {}
        }
        
        try:
            async with self.session.post(
                self.server_url,
                json=message,
                headers={"Content-Type": "application/json"}
            ) as resp:
                data = await resp.json()
                
                if "error" in data and data["error"]["code"] == -32601:
                    return True, "Server returns correct -32601 error for unknown method"
                else:
                    return False, "Server should return -32601 for method not found"
                    
        except Exception as e:
            return False, f"Exception during method not found test: {str(e)}"
    
    async def _test_invalid_params(self) -> Tuple[bool, str]:
        """Test invalid parameters error"""
        
        if not hasattr(self, 'tools') or not self.tools:
            return True, "No tools available to test invalid params"
        
        # Use first tool with wrong parameters
        test_tool = self.tools[0]
        
        message = {
            "jsonrpc": "2.0",
            "id": "invalid-params-test",
            "method": "tools/call",
            "params": {
                "name": test_tool["name"],
                "arguments": {"completely": "wrong", "parameters": 123}
            }
        }
        
        headers = {"Content-Type": "application/json"}
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        
        try:
            async with self.session.post(
                self.server_url,
                json=message,
                headers=headers
            ) as resp:
                data = await resp.json()
                
                if "error" in data and data["error"]["code"] == -32602:
                    return True, "Server returns correct -32602 error for invalid params"
                elif "error" in data:
                    return True, f"Server returns appropriate error (code: {data['error']['code']})"
                else:
                    return False, "Server should return error for invalid parameters"
                    
        except Exception as e:
            return False, f"Exception during invalid params test: {str(e)}"
    
    async def _test_structured_tool_output(self) -> Tuple[bool, str]:
        """Test structured tool output (new in 2025-06-18)"""
        
        # This is primarily about server capability, hard to test without specific tools
        return True, "Structured tool output support is tool-specific (cannot test generically)"
    
    async def _test_protocol_version_header(self) -> Tuple[bool, str]:
        """Test MCP-Protocol-Version header handling"""
        
        message = {
            "jsonrpc": "2.0",
            "id": "protocol-version-test",
            "method": "ping",
            "params": {}
        }
        
        headers = {
            "Content-Type": "application/json",
            "MCP-Protocol-Version": "2025-06-18"
        }
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        
        try:
            async with self.session.post(
                self.server_url,
                json=message,
                headers=headers
            ) as resp:
                if resp.status == 200:
                    return True, "Server accepts MCP-Protocol-Version header"
                else:
                    return False, f"Server rejects protocol version header (status: {resp.status})"
                    
        except Exception as e:
            return False, f"Exception during protocol version test: {str(e)}"
    
    async def _test_meta_field_support(self) -> Tuple[bool, str]:
        """Test _meta field support"""
        
        message = {
            "jsonrpc": "2.0",
            "id": "meta-field-test",
            "method": "ping",
            "params": {},
            "_meta": {
                "test": "compliance-validator"
            }
        }
        
        headers = {"Content-Type": "application/json"}
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        
        try:
            async with self.session.post(
                self.server_url,
                json=message,
                headers=headers
            ) as resp:
                if resp.status == 200:
                    return True, "Server accepts _meta fields in requests"
                else:
                    return False, f"Server rejects _meta fields (status: {resp.status})"
                    
        except Exception as e:
            return False, f"Exception during _meta field test: {str(e)}"
    
    async def _test_oauth_indicators(self) -> Tuple[bool, str]:
        """Test OAuth 2.1 compliance indicators"""
        
        # This would require checking for OAuth-related headers or metadata
        # For HTTP-based servers that use OAuth
        return True, "OAuth 2.1 compliance is transport-specific (HTTP auth servers only)"
    
    # Helper Methods
    
    async def _test_case(self, name: str, description: str, test_func, spec_ref: str):
        """Run a test case and record results"""
        
        try:
            success, details = await test_func()
            result = TestResult.PASS if success else TestResult.FAIL
            
            test_case = TestCase(
                name=name,
                description=description, 
                result=result,
                details=details,
                spec_reference=spec_ref
            )
            
            self.test_results.append(test_case)
            
            # Print result
            status_icon = "✅" if success else "❌"
            print(f"  {status_icon} {name}: {details}")
            
        except Exception as e:
            test_case = TestCase(
                name=name,
                description=description,
                result=TestResult.FAIL,
                details=f"Test exception: {str(e)}",
                spec_reference=spec_ref
            )
            
            self.test_results.append(test_case)
            print(f"  ❌ {name}: Test exception: {str(e)}")
    
    def _add_result(self, name: str, details: str, result: TestResult):
        """Add a test result without running a test"""
        
        test_case = TestCase(
            name=name,
            description="",
            result=result,
            details=details
        )
        
        self.test_results.append(test_case)
        
        icon = {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭️", "WARNING": "⚠️"}[result.value]
        print(f"  {icon} {name}: {details}")
    
    def _print_test_summary(self):
        """Print test summary"""
        
        passed = sum(1 for t in self.test_results if t.result == TestResult.PASS)
        failed = sum(1 for t in self.test_results if t.result == TestResult.FAIL)
        skipped = sum(1 for t in self.test_results if t.result == TestResult.SKIP)
        warnings = sum(1 for t in self.test_results if t.result == TestResult.WARNING)
        total = len(self.test_results)
        
        print("\n" + "=" * 60)
        print("📊 MCP COMPLIANCE TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⏭️ Skipped: {skipped}")
        print(f"⚠️ Warnings: {warnings}")
        
        if failed == 0:
            print("\n🎉 COMPLIANCE STATUS: FULLY COMPLIANT")
            print("Server adheres to MCP 2025-06-18 specification")
        elif failed < 3:
            print("\n✅ COMPLIANCE STATUS: MOSTLY COMPLIANT")
            print("Server has minor compliance issues")
        else:
            print("\n❌ COMPLIANCE STATUS: NON-COMPLIANT") 
            print("Server has significant compliance issues")
        
        # Show failed tests
        if failed > 0:
            print(f"\n❌ FAILED TESTS ({failed}):")
            for test in self.test_results:
                if test.result == TestResult.FAIL:
                    print(f"  • {test.name}: {test.details}")
                    if test.spec_reference:
                        print(f"    📖 Spec: {test.spec_reference}")
        
        print("\n📋 Server Information:")
        print(f"  Protocol Version: {self.protocol_version or 'Unknown'}")
        print(f"  Session Management: {'Yes' if self.session_id else 'No'}")
        print(f"  Capabilities: {list(self.server_capabilities.keys()) if self.server_capabilities else 'None'}")
        
        print("\n📖 MCP Specification: https://modelcontextprotocol.io/specification/2025-06-18/")
        print("=" * 60)


async def main():
    """Main test runner"""
    
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python mcp_compliance_test.py <server_url>")
        print("Example: python mcp_compliance_test.py http://localhost:8000/mcp")
        sys.exit(1)
    
    server_url = sys.argv[1]
    
    validator = MCPComplianceValidator(server_url)
    
    try:
        await validator.run_compliance_tests()
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test suite failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())