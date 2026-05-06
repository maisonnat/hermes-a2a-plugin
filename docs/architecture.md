# Architecture

## System Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                    External A2A Client                           │
│              (OpenCode / Claude Code / Codex / etc.)             │
│                                                                  │
│   ┌────────────────────────────────────────────────────────┐     │
│   │                   A2A Protocol                          │     │
│   │  • JSON-RPC 2.0 over HTTP                              │     │
│   │  • Agent Card discovery (/.well-known/agent-card.json) │     │
│   │  • Task lifecycle (submitted → working → completed)    │     │
│   │  • SSE streaming for real-time progress                │     │
│   │  • Bearer token authentication                         │     │
│   └──────────────────────┬─────────────────────────────────┘     │
│                          │                                       │
└──────────────────────────┼───────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                     Hermes Agent                                 │
│                                                                  │
│   ┌──────────────────────────────────────────────────────────┐   │
│   │                 A2A Plugin (hermes_a2a_plugin/)           │   │
│   │                                                          │   │
│   │  ┌──────────────┐  ┌──────────────────┐                 │   │
│   │  │  server.py   │  │   bridge.py      │                 │   │
│   │  │  A2AServer   │  │ HermesTaskBridge  │                 │   │
│   │  │  HTTP Server │──│ → subprocess     │                 │   │
│   │  │  Endpoints:  │  │   hermes chat -q │                 │   │
│   │  │  • /health   │  └──────────────────┘                 │   │
│   │  │  • /agent-   │                                       │   │
│   │  │    card.json │  ┌──────────────────┐                 │   │
│   │  │  • /tasks/   │  │  bridge_mcp.py   │                 │   │
│   │  │    send      │  │  MCP Server      │                 │   │
│   │  └──────────────┘  │  → OpenCode      │                 │   │
│   │                    └──────────────────┘                 │   │
│   │                                                          │   │
│   │  Register(ctx) hooks: session_start, pre/post_tool       │   │
│   │  Tools: a2a_serve, a2a_status, a2a_stop                  │   │
│   │  CLI: hermes a2a serve                                   │   │
│   └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

## Plugin Lifecycle

1. **Session start** → `PluginManager` scans `~/.hermes/plugins/`
2. **Discovery** → Reads `plugin.yaml` from `hermes-a2a/`
3. **Registration** → Calls `register(ctx)` which hooks into lifecycle
4. **Runtime** → Hooks fire: `session_start`, `pre_tool`, `post_tool`, `session_end`
5. **LLM interaction** → Tools `a2a_serve` / `a2a_status` / `a2a_stop` become available
6. **CLI** → `hermes a2a serve` becomes available as subcommand

## A2A Task Flow

```
Client                    A2AServer                  HermesTaskBridge
  │                         │                            │
  │  POST /tasks/send       │                            │
  │  JSON-RPC 2.0           │                            │
  │────────────────────────►│                            │
  │                         │  bridge.process_task()     │
  │                         │───────────────────────────►│
  │                         │                            │  subprocess
  │                         │                            ├─── hermes chat -q
  │                         │                            │   "Implement auth"
  │                         │                            │◄── response text
  │                         │◄───────────────────────────│
  │                         │  result                    │
  │◄────────────────────────│                            │
  │  {result, status,       │                            │
  │   artifacts}            │                            │
```

## OpenCode MCP Integration

```
OpenCode                     bridge_mcp.py                    Hermes CLI
  │                             │                                │
  │  MCP: tools/list            │                                │
  │────────────────────────────►│                                │
  │◄────────────────────────────│                                │
  │  [delegate, research,       │                                │
  │   status]                   │                                │
  │                             │                                │
  │  MCP: tools/call            │                                │
  │  hermes_delegate            │                                │
  │────────────────────────────►│                                │
  │                             │  subprocess: hermes chat -q    │
  │                             │───────────────────────────────►│
  │                             │◄───────────────────────────────│
  │◄────────────────────────────│                                │
  │  result                     │                                │
```

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Built-in http.server** | Zero external deps for MVP. Swap to Starlette+Uvicorn later if needed |
| **`hermes chat -q` subprocess** | Simple, proven, handles all Hermes features without internal coupling |
| **MCP protocol for OpenCode** | OpenCode's native extension mechanism — no modifications to OpenCode needed |
| **Google-style docstrings** | Required by mkdocstrings for auto-generated API reference |
| **MIT License** | Consistent with Hermes Agent, permissive for community adoption |
| **llms.txt + AGENTS.md** | Emerging standard for LLM-friendly project context |
