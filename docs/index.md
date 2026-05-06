# Welcome to Hermes A2A Plugin

This plugin adds **Agent2Agent (A2A) protocol** support to [Hermes Agent](https://hermes-agent.nousresearch.com), enabling any
A2A-compatible agent to discover and delegate tasks to Hermes.

## Why A2A?

The [Agent2Agent protocol](https://github.com/a2aproject/A2A) (donated by Google to the Linux Foundation)
standardizes how independent AI agents communicate, discover capabilities, and collaborate on tasks.

Unlike ad-hoc integrations or custom APIs, A2A provides:

- **Standardized discovery** via Agent Cards (`/.well-known/agent-card.json`)
- **Structured task lifecycle** (`submitted → working → completed/failed`)
- **Streaming progress** via Server-Sent Events (SSE)
- **Secure authentication** via bearer tokens / OAuth 2.0

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                     A2A Client Agent                      │
│              (OpenCode / Claude Code / Codex)              │
│                                                           │
│  1. GET  /.well-known/agent-card.json  → discovers Hermes │
│  2. POST /tasks/send                   → delegates a task │
│  3. SSE  /tasks/stream                 → live progress    │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│                   Hermes A2A Plugin                       │
│                                                           │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Agent Card  │  │ Task Router  │  │ Auth Guard   │     │
│  │ (published) │  │→ session_key │  │ (bearer)     │     │
│  │             │  │→ AIAgent     │  │              │     │
│  └─────────────┘  └──────┬───────┘  └──────────────┘     │
│                          │                                │
│               PluginManager hooks registered:             │
│               session_start, pre_tool, post_tool          │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│                 Hermes Agent Core                         │
│    AIAgent.run_conversation() → SessionDB → Skills       │
└──────────────────────────────────────────────────────────┘
```

## Quick Overview

```bash
# Install the plugin
hermes plugins install yourusername/hermes-a2a-plugin

# Enable it
hermes plugins enable hermes-a2a

# Start the A2A server
hermes a2a serve --port 4097
```

## Components

This plugin consists of three main components:

1. **A2A Server** — HTTP server that accepts A2A task delegations
2. **Agent Card** — JSON document advertising Hermes capabilities
3. **Bridge** — Translates A2A tasks into Hermes `AIAgent.run_conversation()` calls
