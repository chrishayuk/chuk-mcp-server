# ChukMCPServer — Architecture Principles

> These principles govern all code in chuk-mcp-server.
> Every PR should be evaluated against them.

---

## 1. Performance First

ChukMCPServer is the fastest Python MCP server. Every design decision preserves that.

**Rules:**
- Serialization uses `orjson` — never `json`. orjson is 2-10x faster for both encoding and decoding
- Tool schemas are pre-computed at registration time and cached as both `dict` and `bytes` (`_cached_mcp_format`, `_cached_mcp_bytes`)
- Deep copies use orjson round-trips (`orjson.loads(cached_bytes)`) instead of `copy.deepcopy` — orjson is ~10x faster than deepcopy for nested dicts
- `to_mcp_format()` MUST return a deep copy — shallow `.copy()` leaks nested dict references and allows callers to mutate cached state
- HTTP transport uses `httptools` for parsing and `uvloop` for the event loop (where available)
- Single-worker model — requests handled in the event loop, no process spawning overhead
- No per-request allocations for schema data — registries are pre-computed, responses assembled from cached parts
- `serialize_tools_list_from_bytes()` concatenates pre-serialized byte fragments directly
- Rate limiter uses O(1) token bucket refill — no timer threads, no periodic cleanup
- Optional features (telemetry, rate limiting, OAuth) have zero overhead when disabled

**Performance decisions by layer:**

| Layer | Technique | Impact |
|-------|-----------|--------|
| Serialization | orjson (Rust-based JSON) | ~5x vs json |
| Schema caching | Computed once at registration | Zero per-request |
| Handler caching | Pre-serialized bytes on ToolHandler | Zero per-list |
| Deep copy | orjson round-trip vs copy.deepcopy | ~10x faster |
| Protocol dispatch | Direct dict lookup, no reflection | O(1) dispatch |
| HTTP parser | httptools (C-based HTTP parsing) | ~3x vs pure-py |
| Event loop | uvloop (libuv-based event loop) | ~2x vs asyncio |
| Context | contextvars (C implementation in CPython) | Zero-lock |

**Benchmark target:** 36,000+ requests per second, <3ms framework overhead.

**Why:** MCP servers sit in the critical path between LLMs and tools. Every millisecond of overhead multiplies across thousands of tool calls per conversation.

---

## 2. orjson Type Safety

orjson's `dumps()` and `loads()` return `Any` per mypy stubs. This requires a specific pattern to maintain type safety.

**Rules:**
- Never `return orjson.dumps(data)` directly — mypy reports `no-any-return`
- Always assign to a typed intermediate variable:
  ```python
  # Correct
  result: bytes = orjson.dumps(data)
  return result

  # Correct
  decoded: str = orjson_bytes.decode("utf-8")
  return decoded

  # Wrong — triggers no-any-return
  return orjson.dumps(data)
  ```
- Same pattern applies to `orjson.loads()` — assign to `dict[str, Any]` before returning
- Do NOT use `# type: ignore[no-any-return]` to suppress — use the typed variable pattern instead

**Why:** Type safety across the codebase depends on consistent patterns at serialization boundaries. The typed variable pattern is the cleanest solution that keeps mypy strict mode happy without suppressions.

---

## 3. No Magic Strings

Use enums, constants, or compiled patterns — never bare string comparisons.

**Rules:**
- JSON-RPC version → `JSONRPC_VERSION = "2.0"`
- MCP method names → `McpMethod` enum (`INITIALIZE`, `TOOLS_LIST`, `TOOLS_CALL`, etc.)
- MCP task methods → `McpTaskMethod` enum (`TASKS_GET`, `TASKS_RESULT`, etc.)
- HTTP headers → named constants (`HEADER_MCP_SESSION_ID`, `HEADER_MCP_PROTOCOL_VERSION`, `HEADER_LAST_EVENT_ID`)
- Protocol versions → `MCP_PROTOCOL_VERSION_2025_06`, `MCP_PROTOCOL_VERSION_2025_11`
- Error codes → named constants (`PARSE_ERROR`, `INVALID_REQUEST`, `METHOD_NOT_FOUND`, `INVALID_PARAMS`, `INTERNAL_ERROR`)
- Content types → `CONTENT_TYPE_JSON`, `CONTENT_TYPE_SSE`
- Request limits → `MAX_REQUEST_BODY_BYTES`, `MAX_ARGUMENT_KEYS`, `MAX_PENDING_REQUESTS`
- Rate limit defaults → `DEFAULT_RATE_LIMIT_RPS`, `DEFAULT_RATE_LIMIT_BURST`
- Tool name validation → `TOOL_NAME_PATTERN` (compiled regex)
- If you find yourself writing `if x == "some_string"`, define a constant or enum in `constants.py` first

**Why:** Magic strings are invisible to refactoring tools, produce silent bugs when misspelled, and can't be auto-completed by IDEs. A typo in `"tools/lisst"` is a runtime bug; a typo in `McpMethod.TOOLS_LISST` is a compile-time error.

---

## 4. Async Native

All protocol-facing code is `async def`. No blocking calls in the request path.

**Rules:**
- Tool handlers can be `async def` or plain `def` — the framework detects and handles both via `inspect.iscoroutinefunction()`
- Protocol handler methods (`_handle_tools_call`, `_handle_resources_read`, etc.) are always `async def`
- Transport layers (HTTP, STDIO) are async — `StdioTransport` uses `asyncio.StreamReader/StreamWriter`
- Server-to-client requests (sampling, elicitation, roots, progress) are async with `asyncio.Future` tracking
- Use `asyncio.Lock` for async-context shared state, `threading.Lock` for cross-thread registration
- Synchronous helpers (pure computation, schema generation, orjson serialization) are acceptable but must not block the event loop
- Initialization is lazy where possible — `SmartConfig` auto-detects at construction, not import

**Why:** MCP servers handle concurrent tool calls, sampling requests, and SSE streams simultaneously. A single blocking call stalls every client sharing that event loop.

---

## 5. Schema Caching and Pre-Computation

Compute once at registration time, serve from cache forever.

**Rules:**
- `ToolHandler` pre-computes `_cached_mcp_format` (dict) and `_cached_mcp_bytes` (orjson bytes) at creation
- `ResourceHandler` caches both schema format and content with TTL (`_cached_content`, `_cache_timestamp`)
- JSON schemas are generated from Python type annotations once via `ToolParameter.from_annotation()`
- `_ensure_cached_formats()` runs eagerly during `from_function()` — not lazily on first request
- `invalidate_cache()` is available for runtime schema changes but should be rare
- Tool name validation pattern is compiled at module level (`re.compile(...)`)
- Input schema is built once via `build_input_schema()` which merges `$defs` for complex types

**Registration-time flow:**
```
function + metadata -> ToolHandler
                        |-- _cached_mcp_format  -> dict   (for _ensure_cached_formats)
                        +-- _cached_mcp_bytes   -> bytes  (for wire format & deep copies)
```

**Mutation safety:**
- `to_mcp_format()` returns `orjson.loads(self._cached_mcp_bytes)` — a full deep copy
- `to_mcp_bytes()` returns the bytes directly — bytes are immutable, no copy needed
- Never use `self._cached_mcp_format.copy()` — shallow copy leaks nested dict references (annotations, meta, icons)
- This was verified by benchmarking: orjson round-trip deep copy is ~10x faster than `copy.deepcopy()` and ~7x slower than shallow `.copy()`, but correctness requires deep copy

**Why:** Tool schemas don't change between requests. Pre-computing eliminates per-request JSON schema generation, which is the dominant cost in naive MCP server implementations.

---

## 6. Decorator-Driven API

The public API is decorators. Everything else is implementation detail.

**Rules:**
- `@tool` registers a function as an MCP tool with automatic JSON schema generation from type hints
- `@resource` registers a function as an MCP resource with URI and MIME type
- `@prompt` registers a function as an MCP prompt template
- `@resource_template` registers a function as an RFC 6570 URI template resource
- `@requires_auth` marks a tool as requiring OAuth authorization
- Decorators support both `@tool` and `@tool()` syntax (with and without parentheses)
- Decorator kwargs map directly to MCP spec fields: `read_only_hint`, `destructive_hint`, `idempotent_hint`, `open_world_hint`, `output_schema`, `icons`, `meta`
- Both standalone decorators (module-level `@tool`) and instance decorators (`@mcp.tool`) are supported
- Standalone decorators register to a global registry; instance decorators register to the server's protocol handler
- The global registry is consumed and cleared on server creation to avoid duplicate registrations

**Why:** Developers should think about their tools, not about protocol plumbing. A decorator with type hints is all that's needed to produce a fully conformant MCP tool with validated parameters, cached schemas, and proper error handling.

---

## 7. Thread Safety

Global registries are protected. Server instances are isolated.

**Rules:**
- `_registry_lock` (`threading.Lock`) protects the four global decorator registries (`_global_tools`, `_global_resources`, `_global_prompts`, `_global_resource_templates`)
- `get_global_*()` returns copies (`.copy()`) to prevent external mutation
- `clear_global_registry()` uses `.clear()` on the existing lists — never reassigns — to preserve references held by other code
- Server creation is protected by double-checked locking in `__init__.py`
- Each `ChukMCPServer` instance has its own `MCPProtocolHandler` — no shared mutable state between servers
- Session management is per-protocol-handler — no global session state
- Rate limiter buckets are per-session within a single protocol handler

**Why:** MCP servers may be instantiated from multiple threads (e.g., test runners, ASGI workers). Without locking, concurrent decorator registration corrupts the global registry.

---

## 8. Layered Architecture

ChukMCPServer is a facade. Subsystems are independent and composable.

```
ChukMCPServer (facade / decorator API)
    |
    +-- MCPProtocolHandler     (JSON-RPC dispatch, registries, sessions)
    |   +-- SessionManager     (creation, eviction, protected sessions)
    |   +-- TokenBucketRateLimiter  (per-session rate limiting)
    |   +-- Task Store         (long-running request state machines)
    |
    +-- HTTPServer             (Streamable HTTP transport via Starlette/Uvicorn)
    +-- StdioTransport         (STDIO transport with bidirectional support)
    +-- ProxyManager           (external MCP server composition)
    +-- SmartConfig            (auto-detection of environment and settings)

Type System (no runtime overhead):
    +-- ToolHandler            (schema caching, parameter validation, execution)
    +-- ResourceHandler        (content caching, TTL, URI matching)
    +-- PromptHandler          (argument schema, template rendering)
    +-- ResourceTemplateHandler (RFC 6570 URI templates)
    +-- ToolParameter          (type introspection, JSON schema generation)
```

**Rules:**
- `ChukMCPServer` coordinates; subsystems do the work
- Subsystems don't import each other — `HTTPServer` doesn't know about `StdioTransport`
- Each subsystem is independently testable via `ToolRunner` or direct protocol handler invocation
- Transport is injected — the same protocol handler works over HTTP, STDIO, or direct calls
- Configuration flows down — `SmartConfig` settings are passed at construction, not read from globals
- Optional integrations (`chuk-artifacts`, OpenTelemetry) degrade gracefully when not installed

**Why:** A monolithic server would be untestable and unextendable. Layering lets users deploy over HTTP in production and test via `ToolRunner` with zero transport overhead.

---

## 9. Full MCP Protocol Conformance

Every feature in the MCP specification is implemented or explicitly deferred.

**Rules:**
- Target the latest MCP specification version (currently 2025-11-25)
- Protocol version is negotiated during `initialize` handshake
- All standard methods are dispatched: tools, resources, prompts, sampling, elicitation, roots, progress, completions, logging, cancellation, tasks
- Server-to-client requests (sampling, elicitation, roots) work over both HTTP (SSE) and STDIO transports
- Pagination is cursor-based on all list endpoints
- SSE streams support resumability via event IDs and `Last-Event-ID` header
- New spec features are tracked in `ROADMAP.md` with gap analysis tables
- MCP Apps support: `_meta.ui.resourceUri` on tool definitions, `structuredContent` passthrough for pre-formatted results

**Conformance summary:**

| Spec Area | Status |
|-----------|--------|
| Lifecycle (initialize, ping) | Complete |
| Tools (list, call, annotations, structured output, pagination, icons) | Complete |
| Resources (list, read, subscribe, templates, links, annotations, icons) | Complete |
| Prompts (list, get, pagination, icons) | Complete |
| Sampling (createMessage, tool calling) | Complete |
| Elicitation (form mode, URL mode, defaults) | Complete |
| Roots (list, notifications) | Complete |
| Progress (notifications) | Complete |
| Completions (complete) | Complete |
| Logging (setLevel, notifications/message) | Complete (all 8 MCP levels) |
| Cancellation (notifications/cancelled) | Complete |
| Tasks (get, result, list, cancel, status notifications) | Complete |
| Streamable HTTP (single /mcp endpoint, SSE resumability) | Complete (Last-Event-ID replay) |
| List changed notifications (tools, resources, prompts) | Complete |
| MCP Apps (_meta, structuredContent passthrough) | Complete |

**Why:** Partial protocol implementations create subtle interop failures. Full conformance means ChukMCPServer works with every MCP client without negotiation surprises.

---

## 10. Structured Error Handling

Errors are typed, contextual, and never swallowed silently.

**Rules:**
- `MCPError` is the base error class with `code`, `suggestion`, and `docs_url` fields
- `ParameterValidationError` carries `param_name`, `expected_type`, and `actual_value`
- `ToolExecutionError` wraps handler exceptions with the tool name for context
- `URLElicitationRequiredError` (-32042) signals URL-mode elicitation to the client
- Unknown tool names trigger fuzzy matching via `difflib.get_close_matches(cutoff=0.6)` with suggestions in the error message
- Missing required arguments include the parameter schema in the error for client-side correction
- Exception handling is narrow: `asyncio.CancelledError` is re-raised, `ValueError`/`TypeError`/`KeyError` map to `INVALID_PARAMS`, generic exceptions return sanitized `"Internal server error"`
- Never `except Exception: pass` — log and handle or re-raise
- Import errors for optional dependencies use `try/except` at module level with graceful fallback

**Why:** `ParameterValidationError("user_id", "string", 42)` tells you exactly what went wrong. `TypeError: expected str` tells you nothing about which parameter or which tool.

---

## 11. Zero-Overhead Optionals

Optional features cost nothing when not used.

**Rules:**
- **OpenTelemetry**: Module-level `_OTEL_AVAILABLE` flag. `trace_tool_call()` is a no-op context manager when otel is not installed — zero import cost, zero runtime cost
- **Rate limiting**: Disabled by default (`rate_limit_rps=None`). When disabled, the rate limiter object is never created
- **OAuth**: Only checked if a tool has `@requires_auth`. No middleware overhead for unauthenticated tools
- **uvloop**: Falls back to standard `asyncio` if not available. Detected at import time
- **Artifacts**: Optional `chuk-artifacts` import. Server runs without persistent storage
- **Proxy**: `ProxyManager` only instantiated if `proxy_config` is provided
- Never add a mandatory dependency for an optional feature
- Feature detection happens once at import or construction time, not per-request

**Why:** Most MCP servers don't need rate limiting, OAuth, or telemetry. Those that do shouldn't pay for features they didn't enable. Those that don't shouldn't pay anything at all.

---

## 12. chuk-mcp Is the Protocol Layer

`chuk-mcp` is the single source of truth for MCP protocol types. `chuk-mcp-server` never redefines protocol-level models.

**Rules:**
- All protocol-level Pydantic models come from `chuk-mcp`: `ServerInfo`, `Implementation`, `ServerCapabilities`, `TextContent`, `ImageContent`, `AudioContent`, `ResourceLink`, `MCPTool`, `MCPToolInputSchema`, `MCPError`, `ValidationError`
- `chuk-mcp-server` adds *framework* types (`ToolHandler`, `ResourceHandler`, `PromptHandler`, `ToolParameter`) that wrap or extend protocol types — it does not duplicate them
- Protocol version constants, capability negotiation, and content type models live in `chuk-mcp`
- `chuk-mcp-server` depends on `chuk-mcp` for wire-format correctness — if the MCP spec changes, `chuk-mcp` updates first, then `chuk-mcp-server` adapts
- Never vendor or copy protocol model definitions into `chuk-mcp-server` — import them
- The `types/base.py` module re-exports the subset of `chuk-mcp` types used across the framework to centralize the dependency surface

**Why:** Separating protocol types from framework logic means MCP spec updates flow through a single package (`chuk-mcp`) without touching framework internals. It also lets other projects (e.g., `chuk-mcp-client`) share the same protocol models, ensuring wire-format compatibility.

---

## 13. No Unnecessary Dependencies

The dependency tree is minimal and intentional.

**Core dependencies** (each justified by measurable benefit):

| Package | Purpose |
|---------|---------|
| chuk-mcp | MCP protocol types (ServerInfo, etc.) |
| chuk-sessions | Session lifecycle management |
| chuk-tool-processor | Proxy resilience (timeouts, retries, circuit breakers) |
| orjson | Rust-based JSON serialization (~5x faster than json) |
| starlette | ASGI framework for HTTP transport |
| uvicorn | ASGI server |
| uvloop | libuv-based event loop (~2x faster than asyncio) |
| httptools | C-based HTTP parsing (~3x faster than pure-py) |

**Rules:**
- Every dependency must justify its presence with a measurable benefit
- Optional dependencies are declared in `[project.optional-dependencies]`, not `[project.dependencies]`
- No dependency on view-specific libraries — `chuk-view-schemas` is a separate optional package that targets ChukMCPServer's `meta` kwarg
- Pin minimum versions, not exact versions — allow downstream flexibility

**Why:** Every dependency is an attack surface, a potential version conflict, and a build-time cost. MCP servers should be lightweight and fast to install.

---

## 14. Clean Code

Small functions. Clear names. Single responsibility. Minimal coupling.

**Rules:**
- Functions do one thing; if a function needs a comment explaining what it does, extract sub-functions
- Modules have a single area of responsibility — types are separate from protocol, transport from dispatch
- Prefer composition over inheritance — `ChukMCPServer` composes `MCPProtocolHandler`, not extends it
- No dead code, no commented-out blocks, no `# TODO: maybe later` without a tracking issue
- Modern Python typing: `str | None` not `Optional[str]`, `collections.abc.Callable` not `typing.Callable`
- Use `from __future__ import annotations` for forward references, not string literals
- `@wraps(func)` on all decorator wrappers to preserve function metadata
- Keep the public API surface small — internal helpers are private (`_ensure_cached_formats`, `_validate_and_convert_arguments`)

**Why:** MCP servers span many concerns (protocol, transport, types, auth, composition). Clarity in each piece makes the whole system debuggable and extensible.

---

## 15. Test Coverage >= 90% Per File

Every source file must have >= 90% line coverage individually.

**Rules:**
- Each `src/.../foo.py` has corresponding test coverage
- Coverage is measured per-file, not just as a project aggregate
- Test both happy paths and error/edge cases
- Async tests use `pytest-asyncio` with auto mode
- `ToolRunner` enables transport-free testing — test tool logic without HTTP or STDIO overhead
- Mock external dependencies (storage backends, LLM callbacks) — never hit real services in unit tests
- CI enforces: `ruff` (lint + format), `mypy` (type checking), `pytest` (2300+ tests), `bandit` (security)
- `make check` runs the full suite — all checks must pass before merge

**Current status:** 2334 tests passing, 96.23% aggregate coverage.

**Why:** High coverage catches regressions early. Per-file measurement prevents coverage debt from hiding in low-coverage modules while the aggregate looks healthy.

---

## 16. Observable by Default

Every subsystem exposes structured diagnostics without opt-in.

**Rules:**
- Module-level loggers: `logger = logging.getLogger(__name__)` in every module
- Health endpoints: `/health` (liveness), `/health/ready` (readiness), `/health/detailed` (full state)
- `/health/detailed` exposes: session count, tool/resource/prompt counts, in-flight requests
- Protocol logging: `logging/setLevel` + `notifications/message` for client-visible log streams
- OpenTelemetry: Optional but zero-config when installed — `trace_tool_call()` wraps tool execution
- Observability must not throw — if metrics fail, execution still succeeds
- Structured log messages include context where available (tool name, session ID, error details)

**Why:** When an MCP tool call fails in production, you need to know: which tool, which session, what arguments, and what error — without redeploying with debug logging.

---

## Checklist for PRs

- [ ] Performance: No per-request allocations for schema data; orjson for all serialization
- [ ] Type safety: orjson results assigned to typed variables; no `# type: ignore[no-any-return]`
- [ ] No new magic strings — use enums/constants from `constants.py`
- [ ] New file has corresponding test coverage with >= 90% line coverage
- [ ] No blocking I/O in async code paths
- [ ] Errors use structured exception hierarchy with contextual fields
- [ ] Thread safety: global mutable state protected by `_registry_lock`
- [ ] Optional features have zero overhead when disabled
- [ ] No unnecessary new dependencies — justify each addition
- [ ] Protocol types imported from `chuk-mcp`, not redefined
- [ ] `make check` passes (ruff, mypy, pytest, bandit)
- [ ] New MCP protocol features tracked in `ROADMAP.md`
