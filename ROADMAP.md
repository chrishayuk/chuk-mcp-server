# ChukMCPServer Development Roadmap

This document outlines the development roadmap for `chuk-mcp-server`, the Python MCP framework. It reflects current capabilities, recent completions, review findings, MCP specification gap analysis, and planned work across upcoming releases.

---

## Current State: v0.18.0

**1592 tests | 88% coverage | 36K+ RPS**

ChukMCPServer provides a decorator-based framework for building production-ready Model Context Protocol servers in Python. The current release includes:

| Area | Capabilities |
|------|-------------|
| **Core API** | `@tool`, `@resource`, `@prompt` decorators with automatic JSON schema generation |
| **Transports** | HTTP (Starlette/Uvicorn), STDIO (sync + async), bidirectional on both transports |
| **Protocol** | JSON-RPC 2.0, MCP specification 2025-06-18, full protocol surface |
| **Context** | Session management, user context, progress reporting, metadata, sampling, elicitation, roots |
| **Types** | `ToolHandler`, `ResourceHandler`, `PromptHandler` with orjson caching |
| **OAuth** | Base provider, Google Drive provider, middleware integration |
| **Cloud** | Auto-detection and deployment for GCP, AWS, Azure, Vercel, Netlify, Cloudflare |
| **Composition** | `import_server` (static), `mount` (dynamic), module loader, proxy |
| **Sampling** | Server-to-client LLM requests via `context.create_message()` (STDIO + HTTP) |
| **Elicitation** | Server-to-client structured user input via `context.create_elicitation()` (form mode) |
| **Progress** | Server-to-client progress notifications via `context.send_progress()` |
| **Roots** | Client filesystem root discovery via `context.list_roots()` |
| **Subscriptions** | Client subscribes to resource URIs and receives update notifications |
| **Completions** | Argument auto-completion for resources and prompts |
| **Logging** | `logging/setLevel` handler with MCP-to-Python level mapping |
| **Audio** | `AudioContent` type support via chuk_mcp |
| **Artifacts** | Optional `chuk-artifacts` integration for persistent storage |
| **Performance** | 36K+ requests per second with schema and orjson caching |
| **CLI** | Project scaffolding (`init`), Claude Desktop integration (`--claude`), `--reload`, `--inspect` |
| **Testing** | `ToolRunner` test harness for invoking tools without transport |
| **OpenAPI** | Auto-generated OpenAPI 3.1.0 spec from tool schemas at `/openapi.json` |
| **Errors** | Structured error messages with fix suggestions and fuzzy tool name matching |

### Recently Completed (v0.18.0)

- **HTTP bidirectional transport** -- SSE-based server-to-client requests (sampling, elicitation, roots, progress) over HTTP via `/mcp/respond` endpoint
- **ToolRunner test harness** -- `ToolRunner` class for invoking tools without transport overhead, exported from `chuk_mcp_server`
- **Improved error messages** -- Structured errors with fix suggestions; fuzzy tool name matching ("Did you mean X?")
- **OpenAPI generation** -- Auto-generated OpenAPI 3.1.0 spec from registered tool schemas at `/openapi.json`
- **Hot reload** -- `--reload` CLI flag enables uvicorn hot reload during development
- **MCP Inspector integration** -- `--inspect` CLI flag opens MCP Inspector in browser on server start

### Previously Completed (v0.17.0)

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

## Code Review Findings

A comprehensive code review identified the following issues organized by severity. These findings inform the roadmap priorities below.

### Critical

| Finding | Location | Description |
|---------|----------|-------------|
| Resource subscription memory leak | `protocol.py:137` | `_resource_subscriptions` dict grows unbounded. Subscriptions are tracked per session but never cleaned up when sessions expire or are evicted. |
| Session eviction drops active sessions | `protocol.py:74-76` | When at capacity, the oldest session by `last_activity` is evicted with no grace period or check for in-flight requests. Under uniform load, an actively-used session can be evicted. |
| Version drift | `pyproject.toml` vs docs | `pyproject.toml` says `0.16.5` while `ARCHITECTURE.md` and `ROADMAP.md` reference `0.18.0`. |

### High

| Finding | Location | Description |
|---------|----------|-------------|
| Broad exception handling | `protocol.py:396` | OAuth validation catches bare `Exception`, masking real bugs (`TypeError`, `ImportError`). Should catch specific OAuth errors. |
| No rate limiting or request size limits | Protocol layer | Any client can send unlimited tool calls or arbitrarily large payloads. Denial-of-service vector in HTTP mode. |
| Thread safety of global state | `decorators.py`, `__init__.py` | Global mutable lists/singletons with no locking. Safe in single-threaded asyncio but unsafe if imported from threads. |
| Large files need splitting | `core.py` (1031 lines), `protocol.py` (953 lines) | Both files handle too many concerns. `core.py` manages registration, composition, proxy, config, and lifecycle all in one class. |

### Medium

| Finding | Location | Description |
|---------|----------|-------------|
| Pending request cleanup | `stdio_transport.py` | `_pending_requests` dict entries may linger if timeout fires but dict entry is not removed. |
| Test suite duplication | `tests/` | Multiple `*_coverage.py` and `*_final_coverage.py` files alongside main counterparts. Iterative coverage improvements never consolidated. |
| Weak assertions in core tests | `test_core.py` | Many tests use `try/except` with `pytest.skip()` and only assert method existence rather than testing behavior. |
| No concurrency tests | `tests/` | Zero tests for concurrent tool execution, parallel sampling, or race conditions in the context system. |
| Uncommitted work on main | Working tree | 13 modified files and 10 new untracked files sitting on `main`. |
| No input validation at protocol boundary | `protocol.py` | JSON-RPC handler trusts incoming `params` dicts. No schema validation before calling tool functions. |

### Low

| Finding | Location | Description |
|---------|----------|-------------|
| Import-time side effects | `__init__.py` | `_auto_export_cloud_handlers()` runs at import time, triggering cloud detection logic. |
| Magic numbers | `errors.py`, `protocol.py` | Fuzzy match cutoff `0.6`, `max_sessions=100`, `cleanup_interval=10` undocumented. |
| `dist/` in working tree | Repository root | Built distribution files should be gitignored. |

---

## MCP Specification Gap Analysis

The server currently targets **MCP specification 2025-06-18**. The latest specification is **2025-11-25**. This section identifies all gaps against the latest spec, organized by specification version.

### Missing from 2025-03-26

| Feature | Spec Section | Gap | Priority |
|---------|-------------|-----|----------|
| **Tool annotations** | `server/tools` | No support for `readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint` metadata on tools. Clients use these to decide execution policy. | High |
| **Streamable HTTP transport** | `basic/transports` | Server uses legacy HTTP+SSE (separate GET/POST endpoints). Spec replaced this with Streamable HTTP: single endpoint, POST returns JSON or SSE, GET opens SSE stream, `MCP-Session-Id` header, session termination via DELETE. | High |

### Missing from 2025-06-18

| Feature | Spec Section | Gap | Priority |
|---------|-------------|-----|----------|
| **Structured tool output** | `server/tools` | No `outputSchema` on tool definitions. No `structuredContent` in tool results. Tools can only return `content` (text/image/audio), not typed JSON objects. | High |
| **Resource links in tool results** | `server/tools` | No support for returning `ResourceLink` objects alongside tool content to reference server resources. | Medium |
| **Resource templates** | `server/resources` | No `resources/templates/list` method. URI template-based resources (RFC 6570) not discoverable. | Medium |
| **Content annotations** | Multiple | No `annotations` field on content types (`audience`, `priority`, `lastModified`). Used for filtering content by recipient (user vs assistant). | Medium |
| **Request cancellation** | `basic/utilities` | No `notifications/cancelled` support. Clients cannot cancel in-flight requests; servers cannot cancel sampling/elicitation. | Medium |
| **Pagination** | `server/utilities` | No cursor-based pagination for `tools/list`, `resources/list`, `prompts/list`, `resources/templates/list`. All responses return full lists. | Medium |
| **`notifications/message` for logging** | `server/utilities` | `logging/setLevel` is implemented but server does not emit `notifications/message` log entries to clients via the protocol. | Low |
| **`MCP-Protocol-Version` header** | `basic/transports` | Not sent on HTTP responses. Required by spec for Streamable HTTP transport. | Low (blocked by Streamable HTTP) |

### Missing from 2025-11-25 (Latest)

| Feature | Spec Section | Gap | Priority |
|---------|-------------|-----|----------|
| **Tasks system** (experimental) | `basic/utilities/tasks` | No support for `tasks/get`, `tasks/result`, `tasks/list`, `tasks/cancel`, `notifications/tasks/status`. Tasks are durable state machines for long-running requests with status lifecycle (`working` → `completed`/`failed`/`cancelled`). | High |
| **URL mode elicitation** | `client/elicitation` | Only form mode implemented. No URL mode for directing users to external URLs for sensitive interactions (OAuth flows, payment, credential entry). No `URLElicitationRequiredError` (-32042). | High |
| **Tool calling in sampling** | `client/sampling` | `sampling/createMessage` does not support `tools` array or `toolChoice` parameter. Clients cannot provide tools for the sampled LLM to call. | Medium |
| **Icons** | Multiple | No `icons` field on `Implementation`, `Tool`, `Prompt`, `Resource`, `ResourceTemplate`. Icons enable richer UI rendering. | Medium |
| **Enhanced Implementation info** | `basic/lifecycle` | Server `initialize` response does not include `title`, `description`, `icons`, or `websiteUrl` in `serverInfo`. | Low |
| **SSE resumability** | `basic/transports` | No SSE event IDs for reconnection. Clients cannot resume interrupted SSE streams with `Last-Event-ID`. | Low |
| **Enhanced OAuth** | `basic/authorization` | No Protected Resource Metadata (RFC 9728), no Client ID Metadata Documents, no Resource Indicators (RFC 8707). | Low |
| **Default values in elicitation schema** | `client/elicitation` | Elicitation `requestedSchema` does not support `default` on primitives. | Low |
| **Tool name validation** | `server/tools` | No enforcement of 1-128 character limit, case-sensitive, alphanumeric + underscore/hyphen/dot naming rules. | Low |

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
| **Logging** (setLevel, notifications/message) | Implemented |
| **Cancellation** | Implemented |
| **Tasks** | Implemented |
| **Pagination** | Implemented |
| **Streamable HTTP** | Implemented |
| **Content annotations** | Implemented |
| **Tool annotations** | Implemented |
| **Structured output** | Implemented |
| **Icons** | Implemented |

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

## Phase 5: Production Hardening -- v0.21

Address critical findings from the code review. Harden the server for sustained production workloads with reliability, observability, and security improvements.

| Feature | Status | Description |
|---------|--------|-------------|
| Resource subscription cleanup | Planned | Tie `_resource_subscriptions` cleanup to session eviction and expiry to prevent memory leaks |
| Session eviction improvements | Planned | Grace period for active sessions, check for in-flight requests before eviction, TTL-based expiration |
| Request size limits | Planned | Maximum payload size enforcement on HTTP transport to prevent denial-of-service |
| Rate limiting | Planned | Per-tool and per-session rate limiting with configurable policies |
| Protocol boundary validation | Planned | JSON schema validation of incoming tool arguments before invoking handler functions |
| Narrow exception handling | Planned | Replace broad `except Exception` blocks in OAuth and protocol handling with specific exception types |
| Pending request cleanup | Planned | Explicit cleanup of `_pending_requests` entries in STDIO transport on timeout |
| Thread safety | Planned | Add locking to global mutable state in `decorators.py` and `__init__.py` for thread-safe imports |
| OpenTelemetry integration | Planned | Metrics, traces, and spans for tool invocations, transport I/O, and protocol events |
| Health check enhancements | Planned | Separate readiness and liveness probes; dependency health reporting |
| Graceful shutdown | Planned | Drain in-flight requests before stopping; configurable timeout |
| Connection pooling for proxy | Planned | Reuse connections when proxying to upstream MCP servers |

---

## Phase 6: Codebase Quality -- v0.22

Refactoring and test improvements to keep the codebase maintainable as it grows.

| Feature | Status | Description |
|---------|--------|-------------|
| Split `core.py` | Planned | Extract composition, proxy, and server lifecycle into separate modules (currently 1031 lines) |
| Split `protocol.py` | Planned | Extract session management and subscription tracking into separate modules (currently 953 lines) |
| Consolidate test files | Planned | Merge `*_coverage.py` and `*_final_coverage.py` test variants into their main test files |
| Strengthen core tests | Planned | Replace `try/except`+`pytest.skip()` patterns in `test_core.py` with proper behavioral assertions |
| Add concurrency tests | Planned | Test concurrent tool execution, parallel sampling, race conditions in context system |
| Add integration tests | Planned | End-to-end HTTP and STDIO transport tests with real client connections |
| Remove import-time side effects | Planned | Defer `_auto_export_cloud_handlers()` from import time to first server creation |
| Document magic numbers | Planned | Replace hardcoded values (fuzzy cutoff `0.6`, `max_sessions=100`, `cleanup_interval=10`) with named constants |

---

## Phase 7: Advanced Composition -- v0.23

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

## Phase 8: Security and Enterprise -- v0.24+

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

*This roadmap is a living document. Priorities may shift based on community feedback, MCP specification changes, and production experience. Last updated: 2025-02.*
