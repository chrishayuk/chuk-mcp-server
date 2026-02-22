# ChukMCPServer Development Roadmap

This document outlines the development roadmap for `chuk-mcp-server`, the Python MCP framework. It reflects current capabilities, recent completions, review findings, MCP specification gap analysis, and planned work across upcoming releases.

---

## Current State: v0.23.0

**2388 tests | 95.96% coverage | 36K+ RPS | 0 mypy errors**

ChukMCPServer provides a decorator-based framework for building production-ready Model Context Protocol servers in Python. Full conformance with MCP specification **2025-11-25** (latest), including MCP Apps support. The current release includes:

| Area | Capabilities |
|------|-------------|
| **Core API** | `@tool`, `@resource`, `@resource_template`, `@prompt` decorators with automatic JSON schema generation |
| **Transports** | Streamable HTTP (Starlette/Uvicorn), STDIO (sync + async), bidirectional on both transports |
| **Protocol** | JSON-RPC 2.0, MCP specification 2025-11-25, full protocol surface |
| **MCP Apps** | `_meta.ui.resourceUri` on tools, `structuredContent` passthrough for interactive HTML UIs (SEP-1865) |
| **Context** | Session management, user context, progress reporting, log notifications, resource links, metadata, sampling, elicitation, roots |
| **Types** | `ToolHandler`, `ResourceHandler`, `ResourceTemplateHandler`, `PromptHandler` with orjson caching |
| **Tool Annotations** | `readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint` metadata on tools |
| **Structured Output** | `outputSchema` on tool definitions, `structuredContent` in tool results |
| **Icons** | Icons on tools, resources, resource templates, prompts, and server info |
| **Tasks** | Durable long-running request state machines with `tasks/get`, `tasks/result`, `tasks/list`, `tasks/cancel` |
| **Cancellation** | `notifications/cancelled` support for cancelling in-flight requests |
| **Pagination** | Cursor-based pagination for `tools/list`, `resources/list`, `prompts/list`, `resources/templates/list` |
| **OAuth** | Base provider, Google Drive provider, middleware integration |
| **Cloud** | Auto-detection and deployment for GCP, AWS, Azure, Vercel, Netlify, Cloudflare |
| **Composition** | `import_server` (static), `mount` (dynamic), module loader, proxy |
| **Sampling** | Server-to-client LLM requests via `context.create_message()` with tool calling support |
| **Elicitation** | Server-to-client structured user input via `context.create_elicitation()` (form mode + URL mode + defaults) |
| **Progress** | Server-to-client progress notifications via `context.send_progress()` |
| **Roots** | Client filesystem root discovery via `context.list_roots()` |
| **Subscriptions** | Client subscribes to resource URIs and receives update notifications |
| **Completions** | Argument auto-completion for resources and prompts |
| **Logging** | `logging/setLevel` handler + `notifications/message` log entries to clients |
| **Audio** | `AudioContent` type support via chuk_mcp |
| **Artifacts** | Optional `chuk-artifacts` integration for persistent storage |
| **Performance** | 36K+ requests per second with schema and orjson caching |
| **CLI** | Project scaffolding (`init`), Claude Desktop integration (`--claude`), `--reload`, `--inspect` |
| **Testing** | `ToolRunner` test harness for invoking tools without transport |
| **OpenAPI** | Auto-generated OpenAPI 3.1.0 spec from tool schemas at `/openapi.json` |
| **Errors** | Structured error messages with fix suggestions and fuzzy tool name matching |
| **Rate Limiting** | Per-session token bucket rate limiter, configurable via `rate_limit_rps`, disabled by default |
| **Validation** | Request body size limits (10 MB), argument key count limits (100), type checking |
| **Thread Safety** | Locked global registries, double-checked locking singleton, graceful shutdown with drain |
| **Health** | `/health` (liveness), `/health/ready` (readiness), `/health/detailed` (full state) |
| **Telemetry** | Thin OpenTelemetry wrapper, zero overhead without otel |

### Recently Completed (v0.22.0 -- MCP Apps Support)

- **Tool `_meta` field** -- `meta` parameter on `@tool` decorator, `ChukMCPServer.tool()`, and `ToolHandler.from_function()`. Emitted as `_meta` in `tools/list` responses. Enables `_meta.ui.resourceUri` for MCP Apps (SEP-1865, `io.modelcontextprotocol/ui`)
- **Pre-formatted result passthrough** -- When a tool returns `{"content": [...], "structuredContent": {...}}`, the protocol handler passes it through directly instead of re-wrapping via `format_content()`. This enables view-tool decorators (e.g., `chuk-view-schemas`) to return complete MCP Apps responses
- **Architecture principles** -- New `ARCHITECTURE.md` with 15 governing principles: performance first, orjson type safety, no magic strings, async native, schema caching, decorator-driven API, thread safety, layered architecture, full protocol conformance, structured errors, zero-overhead optionals, minimal dependencies, clean code, test coverage, observability

### Previously Completed (v0.21.0 -- Phase 5: Production Hardening)

- **Session lifecycle cleanup** -- `on_evict` callback cleans up `_resource_subscriptions`, `_sse_event_buffers`, `_sse_event_counters` on session eviction; protected sessions with active SSE streams skip eviction
- **Request validation** -- 10 MB body size limit on HTTP and STDIO transports, 100-key argument limit, type checking on tool arguments
- **Rate limiting** -- Per-session token bucket rate limiter (`TokenBucketRateLimiter`), configurable via `rate_limit_rps` parameter, disabled by default
- **Narrow exception handling** -- `asyncio.CancelledError` re-raised, `ValueError`/`TypeError`/`KeyError` return `INVALID_PARAMS`, generic exceptions return sanitized `"Internal server error"` message
- **Thread safety** -- `_registry_lock` on global decorator registries, double-checked locking on singleton in `__init__.py`, `clear_global_registry()` uses `.clear()` to preserve references
- **Graceful shutdown** -- `MCPProtocolHandler.shutdown(timeout=5.0)` drains in-flight requests with configurable timeout, then cancels remaining tasks and cleans all state
- **Health check enhancements** -- `/health/ready` readiness probe (checks tools registered), `/health/detailed` endpoint (sessions, tools, resources, prompts, in-flight requests)
- **Telemetry** -- Thin OpenTelemetry wrapper (`telemetry.py`), `trace_tool_call()` context manager, zero overhead when otel is not installed
- **Pending request limits** -- `MAX_PENDING_REQUESTS = 100` enforced in STDIO transport, `stop()` cancels all pending futures

### Previously Completed (v0.20.0 -- Phase 4: MCP 2025-11-25)

- **Streamable HTTP transport** -- Single MCP endpoint (POST+GET), `MCP-Session-Id` header, session DELETE, `MCP-Protocol-Version` header, SSE resumability with event IDs
- **Tasks system** -- `tasks/get`, `tasks/result`, `tasks/list`, `tasks/cancel`, `notifications/tasks/status` for durable long-running request state machines
- **URL mode elicitation** -- Direct users to external URLs for sensitive interactions, `URLElicitationRequiredError` (-32042)
- **Tool calling in sampling** -- `tools` array and `toolChoice` parameter in `sampling/createMessage`
- **Icons** -- `icons` field on tools, resources, resource templates, prompts, and server info
- **Enhanced ServerInfo** -- `title`, `description`, `icons`, `websiteUrl` in `serverInfo` during initialize
- **Elicitation defaults** -- `default` values on primitive types in elicitation schemas
- **Tool name validation** -- Enforce 1-128 character naming rules (alphanumeric + underscore/hyphen/dot)

### Previously Completed (v0.19.0 -- Phase 3: MCP 2025-06-18)

- **Structured tool output** -- `outputSchema` on tool definitions, `structuredContent` in tool results
- **Tool annotations** -- `readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint` via `@tool` decorator
- **Pagination** -- Cursor-based pagination for `tools/list`, `resources/list`, `prompts/list`, `resources/templates/list`
- **Resource templates** -- `resources/templates/list` method for URI template-based resource discovery (RFC 6570)
- **Resource links** -- Return `ResourceLink` objects alongside tool content to reference server resources
- **Content annotations** -- `audience`, `priority` annotations on content types
- **Request cancellation** -- `notifications/cancelled` support for cancelling in-flight requests
- **Log message notifications** -- Emit `notifications/message` to clients for server-side log events

### Previously Completed (v0.18.0)

- **Elicitation support** -- `elicitation/create` via `context.create_elicitation()` enables server-initiated structured user input requests
- **Progress notifications** -- `notifications/progress` via `context.send_progress()` for long-running tool operations
- **Roots support** -- `roots/list` via `context.list_roots()` for client filesystem root discovery
- **Resource subscriptions** -- `resources/subscribe` and `resources/unsubscribe` with `notify_resource_updated()` for live resource updates
- **Completions support** -- `completion/complete` with pluggable completion providers for resources and prompts

### Previously Completed (v0.16.5)

- **MCP Sampling support** -- `sampling/createMessage` via `context.create_message()` enables server-initiated LLM requests through the client
- **Bidirectional STDIO transport** -- Full duplex communication allowing server-to-client requests over STDIO
- **Client capability detection** -- Server reads and respects client capabilities declared during `initialize` handshake

---

## Architecture Audit Findings

A comprehensive audit against `ARCHITECTURE.md` principles identified the following issues. Items marked **Fixed** were addressed in previous phases.

### Principle 1: Performance First

| Finding | Location | Description | Status |
|---------|----------|-------------|--------|
| Blocking file I/O in async path | `composition/config_loader.py:49` | `open()` + `yaml.safe_load()` called synchronously from `async apply_to_manager()` | **Fixed** |
| Multiple `asyncio.run()` calls | `core.py:877,937,940,945` | Proxy start and shutdown create separate event loops instead of reusing | **Fixed** |
| `json.dumps()` in GCF adapter | `cloud/adapters/gcf.py:177,207,214` | Used stdlib `json` instead of `orjson` for response serialization | **Fixed** |
| Per-request event loop | `cloud/adapters/gcf.py:131-139` | Created and closed new `asyncio` event loop for every request | **Fixed** |

### Principle 2: orjson Type Safety

| Finding | Location | Description | Status |
|---------|----------|-------------|--------|
| `type: ignore[no-any-return]` | `__init__.py:183` | `Capabilities()` function — replace with typed variable | **Fixed** |
| `type: ignore[no-any-return]` | `types/tools.py:165,170` | `.name` and `.description` properties — replace with typed variable | **Fixed** |
| `type: ignore[no-any-return]` | `types/prompts.py:315` | `get_prompt()` return — replace with typed variable | **Fixed** |
| `orjson.dumps()` inline usage | `endpoints/*.py`, `http_server.py`, etc. | ~28 instances of `orjson.dumps()` passed directly without typed variable assignment | **Fixed** |
| `json` module usage | `config/base.py` | Used `json.loads()` instead of `orjson.loads()` | **Fixed** |
| `.decode()` without typed var | `types/resources.py`, `types/content.py` | ~7 instances of `orjson.dumps().decode()` without typed variable assignment | **Fixed** |

### Principle 3: No Magic Strings

| Finding | Location | Description | Status |
|---------|----------|-------------|--------|
| Content-type string literals | `http_server.py`, `core.py`, `decorators.py`, `types/resources.py`, `openapi.py`, `cloud/adapters/gcf.py` | ~17 instances of `"application/json"`, `"text/plain"`, `"text/markdown"` should use `CONTENT_TYPE_*` constants | **Fixed** |
| Error code magic numbers | `types/resources.py`, `errors.py`, `cloud/adapters/gcf.py` | Bare `-32603` should use `JsonRpcError.INTERNAL_ERROR` | **Fixed** |
| JSON-RPC key string literals | `testing.py`, `cloud/adapters/gcf.py` | ~12 instances of `"jsonrpc"`, `"method"`, `"params"`, `"result"` should use constants | **Fixed** |
| MCP method string comparisons | `endpoints/mcp.py` | `== "initialize"`, `== "tools/call"` should use `McpMethod.*` constants | **Fixed** |
| Duplicate constants file | `endpoints/constants.py` | Redefines `CONTENT_TYPE_*`, `HEADER_*`, `JSONRPC_VERSION`, `JsonRpcErrorCode` already in `constants.py` | **Fixed** |
| Attribute marker magic strings | `core.py`, `decorators.py` | Bare `func._mcp_tool`, `func._requires_auth` instead of `setattr(func, ATTR_MCP_TOOL, ...)` | **Fixed** |

### Principle 4: Async Native

| Finding | Location | Description | Status |
|---------|----------|-------------|--------|
| Blocking file I/O in async chain | `composition/config_loader.py:49-50,68` | Sync `open()` + `yaml.safe_load()` called from `async apply_to_manager()` | **Fixed** |
| `time.sleep()` in thread | `core.py:919` | Browser-opening thread uses blocking sleep instead of async task | Low |

### Principle 8: Layered Architecture

| Finding | Location | Description | Status |
|---------|----------|-------------|--------|
| `protocol.py` too large | `protocol/` package | 1,500 → 1,379 lines; extracted SessionManager, SSEEventBuffer, TaskManager | **Fixed** |
| `core.py` too large | `core.py` | 1,135 → 1,061 lines; extracted ComponentRegistry and startup functions | **Fixed** |
| `context.py` too large | `context.py` | 674 lines — highly cohesive, splitting deferred | Deferred |
| `cli.py` too large | `cli/` package | 797 → 251 lines; extracted templates to `cli/templates.py` | **Fixed** |
| `__init__.py` too large | `__init__.py` | 589 → 355 lines; extracted cloud functions to `cloud/exports.py` | **Fixed** |
| Import-time side effects | `__init__.py` | `_auto_export_cloud_handlers()` still runs at import; body moved to `cloud/exports.py` | Deferred |
| Endpoint→Protocol coupling | `endpoints/mcp.py`, `endpoints/health.py` | Clean DI already in place | Deferred |
| Cloud→Root coupling | `cloud/adapters/gcf.py` | Changed to lazy `import chuk_mcp_server` pattern | **Fixed** |

### Principle 7: Thread Safety by Default

| Finding | Location | Description | Status |
|---------|----------|-------------|--------|
| Unprotected global store | `artifacts_context.py:56` | `_global_artifact_store` read/write without lock | **Fixed** |

### Principle 10: Structured Error Handling

| Finding | Location | Description | Status |
|---------|----------|-------------|--------|
| OAuth error leakage | `oauth/middleware.py:349-392` | `str(e)` and `traceback.format_exc()` leaked to clients in error responses | **Fixed** |
| `str(e)` in client responses | `protocol/handler.py`, `endpoints/mcp.py`, `stdio_transport.py` | ~15 instances of `str(e)` exposed in JSON-RPC error messages | **Fixed** |
| `str(e)` in HTML response | `oauth/middleware.py:480` | Exception details exposed in authorization error HTML page | **Fixed** |
| Bare `except` without logging | `cloud/adapters/gcf.py:169` | JSON parse error silently swallowed | **Fixed** |

### Principle 12: No Unnecessary Dependencies

| Finding | Location | Description | Status |
|---------|----------|-------------|--------|
| `python-multipart` redundant | `pyproject.toml:20` | Transitive via Starlette — listed as required but never directly imported | Open (Phase 6) |
| `psutil` should be optional | `pyproject.toml:19`, `config/system_detector.py` | Imported inside try/except with fallback — already behaves as optional | **Fixed** |
| `pyyaml` imported unconditionally | `composition/config_loader.py:15` | Module-level `import yaml` but only used if composition config is loaded | **Fixed** |

### Principle 14: Test Coverage >= 90%

| Finding | Location | Description | Status |
|---------|----------|-------------|--------|
| `telemetry.py` at 63% | `telemetry.py` | OpenTelemetry-enabled paths (lines 40-51) completely untested | **Fixed** (100%) |
| 21 duplicate test files | `tests/` | `*_coverage.py` and `*_final_coverage.py` variants (e.g., 7 variants of `test_parameters*.py`) | Deferred |
| `pytest.skip()` masking | `test_core_final_coverage.py` | 7 skipped tests for STDIO detection and decorator fallback paths | **Fixed** |
| MCP Apps `meta` field untested | `types/tools.py` | No tests verify `meta` field on `ToolHandler` or `_meta` in `tools/list` response | **Fixed** |
| Pre-formatted passthrough untested | `protocol.py:585-595` | No test verifies the `structuredContent` passthrough conditional | **Fixed** |

### Previously Fixed

| Finding | Status | Phase |
|---------|--------|-------|
| Resource subscription memory leak | **Fixed** | Phase 5 |
| Session eviction drops active sessions | **Fixed** | Phase 5 |
| Broad exception handling in OAuth | **Fixed** | Phase 5 |
| No rate limiting or request size limits | **Fixed** | Phase 5 |
| Thread safety of global state | **Fixed** | Phase 5 |
| Pending request cleanup in STDIO | **Fixed** | Phase 5 |
| No input validation at protocol boundary | **Fixed** | Phase 5 |

---

## MCP Specification Conformance

The server targets **MCP specification 2025-11-25** (latest) and is fully conformant. The gap analysis below is historical — all items are now implemented.

### Conformance Summary

| Spec Area | Status |
|-----------|--------|
| **Lifecycle** (initialize, ping) | Implemented |
| **Tools** (list, call) | Implemented (annotations, structured output, pagination, icons, name validation) |
| **Resources** (list, read, subscribe) | Implemented (templates, links, pagination, content annotations, icons) |
| **Prompts** (list, get) | Implemented (pagination, icons) |
| **Sampling** (createMessage) | Implemented (including tool calling) |
| **Elicitation** (create) | Implemented (form mode + URL mode + defaults) |
| **Roots** (list) | Implemented |
| **Progress** (notifications) | Implemented |
| **Completions** (complete) | Implemented |
| **Logging** (setLevel, notifications/message) | Implemented (all 8 MCP levels) |
| **Cancellation** | Implemented |
| **Tasks** | Implemented (auto-wired to tool execution; `strict_init` mode available) |
| **Pagination** | Implemented |
| **Streamable HTTP** | Implemented (SSE resumability with Last-Event-ID) |
| **Content annotations** | Implemented |
| **Tool annotations** | Implemented |
| **Structured output** | Implemented |
| **Icons** | Implemented |
| **List changed notifications** | Implemented (tools, resources, prompts) |
| **MCP Apps** (`_meta`, structuredContent passthrough) | Implemented |

---

## Phase 1: Core Hardening -- v0.17 (Complete)

Complete the MCP specification surface area. Every protocol capability that a conformant server can expose is now supported or gracefully declined.

| Feature | Status | Description |
|---------|--------|-------------|
| Elicitation support | **Done** | `elicitation/create` -- server-to-client structured user input via `create_elicitation()` |
| Progress notifications | **Done** | `notifications/progress` -- server-to-client progress updates via `send_progress()` |
| Roots support | **Done** | `roots/list` -- client filesystem root discovery via `list_roots()` |
| Resource subscriptions | **Done** | `resources/subscribe` / `resources/unsubscribe` with update notifications |
| Completions support | **Done** | `completion/complete` with pluggable providers for resources and prompts |

---

## Phase 2: Developer Experience -- v0.18 (Complete)

Reduce friction for developers building and debugging MCP servers. Focus on the inner development loop: write, test, iterate.

| Feature | Status | Description |
|---------|--------|-------------|
| HTTP bidirectional transport | **Done** | SSE-based server-to-client requests (sampling, elicitation, roots, progress) over HTTP |
| Tool testing utilities | **Done** | `ToolRunner` test harness for invoking tools without transport overhead |
| Improved error messages | **Done** | Structured errors with fix suggestions; fuzzy tool name matching |
| OpenAPI generation | **Done** | Auto-generate OpenAPI 3.1.0 spec from tool schemas at `/openapi.json` |
| Hot reload | **Done** | `--reload` CLI flag enables uvicorn hot reload during development |
| MCP Inspector integration | **Done** | `--inspect` CLI flag opens MCP Inspector in browser on server start |
| Type stub generation | Deferred | Generate `.pyi` stubs for downstream consumers of published tool packages |

---

## Phase 3: Spec Conformance (2025-06-18) -- v0.19

Close all gaps against MCP specification 2025-06-18. Implement the protocol features needed for full conformance with the spec the server already targets.

| Feature | Status | Description |
|---------|--------|-------------|
| Structured tool output | **Done** | `outputSchema` on tool definitions, `structuredContent` in tool results for typed JSON responses |
| Tool annotations | **Done** | `readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint` metadata via `@tool` decorator |
| Pagination | **Done** | Cursor-based pagination for `tools/list`, `resources/list`, `prompts/list`, `resources/templates/list` |
| Resource templates | **Done** | `resources/templates/list` method for URI template-based resource discovery (RFC 6570) |
| Resource links | **Done** | Return `ResourceLink` objects alongside tool content to reference server resources |
| Content annotations | **Done** | `audience`, `priority`, `lastModified` annotations on content types |
| Request cancellation | **Done** | `notifications/cancelled` support for cancelling in-flight requests in both directions |
| Log message notifications | **Done** | Emit `notifications/message` to clients for server-side log events (completes logging support) |

---

## Phase 4: Spec Conformance (2025-11-25) -- v0.20

Upgrade to the latest MCP specification. Implement the new transport, tasks system, and enhanced features.

| Feature | Status | Description |
|---------|--------|-------------|
| Streamable HTTP transport | **Done** | Single MCP endpoint (POST+GET), `MCP-Session-Id` header, session DELETE, `MCP-Protocol-Version` header, SSE resumability with event IDs |
| Tasks system | **Done** | `tasks/get`, `tasks/result`, `tasks/list`, `tasks/cancel`, `notifications/tasks/status` for durable long-running request state machines |
| URL mode elicitation | **Done** | Direct users to external URLs for sensitive interactions (OAuth flows, payment, credentials), `URLElicitationRequiredError` (-32042) |
| Tool calling in sampling | **Done** | `tools` array and `toolChoice` parameter in `sampling/createMessage` for client-side tool loops |
| Icons | **Done** | `icons` field on `Implementation`, `Tool`, `Prompt`, `Resource`, `ResourceTemplate` for richer UI rendering |
| Enhanced Implementation info | **Done** | `title`, `description`, `icons`, `websiteUrl` in `serverInfo` during initialize |
| Elicitation defaults | **Done** | `default` values on primitive types in elicitation `requestedSchema` |
| Tool name validation | **Done** | Enforce 1-128 character naming rules (alphanumeric + underscore/hyphen/dot, case-sensitive) |

---

## Phase 5: Production Hardening -- v0.21 (Complete)

Address critical findings from the code review. Harden the server for sustained production workloads with reliability, observability, and security improvements.

| Feature | Status | Description |
|---------|--------|-------------|
| Resource subscription cleanup | **Done** | `on_evict` callback ties `_resource_subscriptions`, `_sse_event_buffers`, `_sse_event_counters` cleanup to session eviction and expiry |
| Session eviction improvements | **Done** | Protected sessions with active SSE streams skip eviction; `_cleanup_session_state()` centralized cleanup |
| Request size limits | **Done** | 10 MB body size limit on HTTP and STDIO transports; 100-key argument limit with type checking |
| Rate limiting | **Done** | Per-session token bucket rate limiter (`TokenBucketRateLimiter`), configurable via `rate_limit_rps`, disabled by default |
| Protocol boundary validation | **Done** | Argument type checking and key count validation before invoking tool handlers |
| Narrow exception handling | **Done** | `CancelledError` re-raised; `ValueError`/`TypeError`/`KeyError` → `INVALID_PARAMS`; generic exceptions sanitized |
| Pending request cleanup | **Done** | `MAX_PENDING_REQUESTS = 100` enforced in STDIO transport; `stop()` cancels all pending futures |
| Thread safety | **Done** | `_registry_lock` on global registries; double-checked locking on singleton; `.clear()` preserves references |
| OpenTelemetry integration | **Done** | Thin wrapper in `telemetry.py`; `trace_tool_call()` context manager; zero overhead without otel |
| Health check enhancements | **Done** | `/health/ready` readiness probe; `/health/detailed` with session/tool/resource/in-flight counts |
| Graceful shutdown | **Done** | `MCPProtocolHandler.shutdown(timeout=5.0)` drains in-flight requests then cancels remaining |
| Connection pooling for proxy | Deferred | Deferred to Phase 7 (Advanced Composition) |

---

## Phase 6: Codebase Quality -- v0.23 (Complete)

Refactoring, dependency cleanup, and test improvements driven by the architecture audit against `ARCHITECTURE.md` principles.

### 6A: Module Splitting (Principle 8: Layered Architecture)

| Feature | Status | Description |
|---------|--------|-------------|
| Split `protocol.py` (1,500 → 1,379 lines) | **Done** | Converted to `protocol/` package: extracted `SessionManager` to `session_manager.py` (84 lines), `SSEEventBuffer` to `events.py` (41 lines), `TaskManager` to `tasks.py` (164 lines). Backward-compat properties preserve test access. |
| Split `core.py` (1,135 → 1,061 lines) | **Done** | Extracted `ComponentRegistry` to `component_registry.py` (104 lines) and startup functions to `startup.py` (139 lines). Decorator methods delegate to `self._components`. |
| Split `cli.py` (797 → 251 lines) | **Done** | Converted to `cli/` package: extracted ~567 lines of scaffold templates to `cli/templates.py`. Added `encoding="utf-8"` to `write_text()` calls for Windows CI compat. |
| Slim `__init__.py` (589 → 355 lines) | **Done** | Moved cloud handler getters, detection helpers, auto-export, and examples to `cloud/exports.py` (266 lines). Functions use lazy `import chuk_mcp_server` for test patch compat. |
| Skip `context.py` (674 lines) | Deferred | Highly cohesive — 11 ContextVars with paired accessors sharing private state; splitting adds coupling with no benefit |
| Remove import-time side effects | Deferred | `_auto_export_cloud_handlers()` still runs at import; body moved to `cloud/exports.py` |
| Consolidate duplicate constants | **Done** | `endpoints/constants.py` now re-exports from main `constants.py` |
| Fix endpoint→protocol coupling | Deferred | Already clean DI in `mcp.py`; `health.py` module global is acceptable |
| Fix cloud→root coupling | **Done** | `cloud/adapters/gcf.py` now uses `import chuk_mcp_server` lazy pattern instead of relative `from ... import` |

### 6B: Magic String Elimination (Principle 3: No Magic Strings)

| Feature | Status | Description |
|---------|--------|-------------|
| Content-type constants | **Done** | Replaced ~17 instances with `CONTENT_TYPE_*` from `constants.py` |
| Error code constants | **Done** | Replaced bare `-32603` with `JsonRpcError.INTERNAL_ERROR` |
| JSON-RPC key constants | **Done** | Replaced `"jsonrpc"`, `"method"`, `"params"`, `"result"` in `testing.py`, `gcf.py`, `endpoints/mcp.py` |
| MCP method constants | **Done** | Replaced `== "initialize"`, `== "tools/call"` with `McpMethod.*` enum values |
| Attribute marker constants | **Done** | Replaced bare `func._mcp_tool` etc. with `setattr(func, ATTR_MCP_TOOL, ...)` in `core.py`, `decorators.py` |

### 6C: Type Safety Cleanup (Principle 2: orjson Type Safety)

| Feature | Status | Description |
|---------|--------|-------------|
| Remove `type: ignore[no-any-return]` | **Done** | Replaced with typed intermediate variables in `types/tools.py`, `types/prompts.py` |
| Fix `orjson.dumps()` inline usage | **Done** | 28+ instances in endpoints, http_server, registries now use `body: bytes = orjson.dumps(...)` pattern |
| Replace `json` with `orjson` | **Done** | `config/base.py` now uses `orjson.loads()` instead of `json.loads()` |
| Zero mypy errors | **Done** | Fixed all 34 mypy errors across 5 files: handler.py (typed returns), telemetry.py (typed assignment), oauth/middleware.py (correct ignore codes), artifacts_context.py (TYPE_CHECKING stubs + typed returns), cli/__init__.py (correct ignore codes), __init__.py (typed stubs) |

### 6D: Async Correctness (Principle 4: Async Native)

| Feature | Status | Description |
|---------|--------|-------------|
| Fix blocking I/O in config loader | **Done** | Changed to `await asyncio.to_thread(self.load)` in `apply_to_manager()` |
| Fix multiple `asyncio.run()` calls | **Done** | Consolidated shutdown into `_shutdown_all()` coroutine — single `asyncio.run()` call |

### 6E: Dependency Cleanup (Principle 12: No Unnecessary Dependencies)

| Feature | Status | Description |
|---------|--------|-------------|
| Remove `python-multipart` from required | Deferred | Needed by OAuth middleware's `request.form()` |
| Move `psutil` to optional extra | **Done** | Moved to `[project.optional-dependencies]` monitoring group |
| Guard `pyyaml` import | **Done** | Moved `import yaml` inside `load()` with helpful `ImportError` message |

### 6F: Test Infrastructure (Principle 14: Test Coverage >= 90%)

| Feature | Status | Description |
|---------|--------|-------------|
| Fix `telemetry.py` coverage (63%) | **Done** | Added mock-otel tests; now at 100% coverage |
| Add MCP Apps tests | **Done** | 12 tests for `meta` field, `_meta` in `tools/list`, pre-formatted `structuredContent` passthrough |
| Consolidate test files | Deferred | 21 `*_coverage.py` variants — low priority, tests pass and coverage is above 95% |
| Fix skipped tests | **Done** | Replaced 7 `pytest.skip()` in `test_core_final_coverage.py` with real STDIO detection and shutdown tests; removed dead decorator fallback tests |
| Add concurrency tests | **Done** | 7 tests: parallel tool execution, context isolation across coroutines, concurrent registration and session creation |
| Add integration tests | **Done** | 14 tests: full lifecycle flows (init → list → call → task → resource → prompt), strict init enforcement, error handling, multi-session |

### 6G: MCP Spec Compliance Fixes

| Feature | Status | Description |
|---------|--------|-------------|
| List changed notifications | **Done** | Added `notify_tools_list_changed()`, `notify_resources_list_changed()`, `notify_prompts_list_changed()` to protocol handler |
| Missing logging levels | **Done** | Added `notice`, `alert`, `emergency` mappings to `_handle_logging_set_level` |
| SSE resumability | **Done** | Connected `Last-Event-ID` header → `get_missed_events()` replay in GET handler |
| OAuth error sanitization | **Done** | Replaced `str(e)` with generic messages in OAuth error responses |
| Tasks auto-wire | **Done** | `_create_task` wired into `_handle_tools_call` — tasks created/updated automatically on tool execution |
| Pre-initialize enforcement | **Done** | `strict_init=True` on `MCPProtocolHandler` rejects requests with invalid/expired session IDs (off by default) |

---

## Phase 7: Advanced Composition -- v0.24

Enable large-scale MCP architectures where servers are composed from many sources and communicate across boundaries.

| Feature | Status | Description |
|---------|--------|-------------|
| Plugin system | Planned | Pip-installable tool packages discovered via entry points |
| Dynamic tool discovery | Planned | Discover and install tool packages from PyPI at runtime |
| Service mesh integration | Planned | First-class support for Istio, Linkerd, and similar service meshes |
| gRPC transport | Planned | Alternative transport for high-throughput, low-latency inter-service communication |
| WebSocket transport | Planned | Persistent bidirectional connections for sampling, elicitation, and streaming |
| Federation | Planned | Server-to-server tool delegation across trust boundaries |

---

## Phase 8: Security and Enterprise -- v0.25+

Capabilities required for enterprise deployments with strict compliance, governance, and multi-tenancy requirements.

| Feature | Status | Description |
|---------|--------|-------------|
| Enhanced OAuth (RFC 9728) | Planned | Protected Resource Metadata, Client ID Metadata Documents, Resource Indicators (RFC 8707) per latest MCP spec |
| Role-based access control | Planned | Per-tool RBAC with configurable roles and permissions |
| Audit logging | Planned | Immutable, structured audit trail for all tool invocations and administrative actions |
| Input sanitization framework | Planned | Pluggable validation and sanitization pipeline for tool inputs |
| Tool execution sandboxing | Planned | Isolate tool execution to limit blast radius of untrusted code |
| Certificate-based auth | Planned | Mutual TLS and certificate-based authentication for server-to-server communication |
| Multi-tenant support | Planned | Isolated tool registries, context, and storage per tenant |

---

## Version History

| Version | Milestone |
|---------|-----------|
| v0.23.0 | Codebase quality: module splitting, magic string elimination, type safety, async fixes, dependency cleanup, test infrastructure, MCP spec compliance |
| v0.22.0 | MCP Apps: `_meta` on tools, pre-formatted result passthrough, `structuredContent` for interactive HTML UIs |
| v0.21.0 | Production hardening: session lifecycle cleanup, request validation, rate limiting, exception handling, thread safety, graceful shutdown, health probes, telemetry |
| v0.20.0 | MCP 2025-11-25: Streamable HTTP, tasks, URL elicitation, tool calling in sampling, icons, enhanced ServerInfo |
| v0.19.0 | MCP 2025-06-18: Structured output, tool annotations, pagination, resource templates, resource links, content annotations, cancellation, log notifications |
| v0.18.0 | Developer experience: HTTP bidirectional, ToolRunner, improved errors, OpenAPI, hot reload, inspect |
| v0.17.0 | Full MCP protocol surface: elicitation, progress, roots, subscriptions, completions |
| v0.16.5 | MCP sampling, bidirectional STDIO, client capability detection |
| v0.16.0 | OAuth middleware, Google Drive provider |
| v0.15.0 | Composition: import_server, mount, proxy |
| v0.14.0 | Cloud auto-detection (GCP, AWS, Azure, Vercel, Netlify, Cloudflare) |
| v0.13.0 | orjson caching, 36K+ RPS performance milestone |
| v0.12.0 | CLI scaffolding, project init |

---

## Contributing

Contributions are welcome for any roadmap item. If you are interested in working on a planned feature, please open an issue to discuss the approach before submitting a pull request. See the [contributing guide](docs/contributing/setup.md) for development setup instructions.

---

*This roadmap is a living document. Priorities may shift based on community feedback, MCP specification changes, and production experience. Last updated: 2026-02.*
