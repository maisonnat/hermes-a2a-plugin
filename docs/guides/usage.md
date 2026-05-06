# Usage Guide

## Starting the Server

```bash
# Default port (4097)
hermes a2a serve

# Custom port
hermes a2a serve --port 8080

# With authentication
hermes a2a serve --token your-secret-token

# With debug logging
hermes a2a serve --verbose
```

## Agent Card

The Agent Card is published at `/.well-known/agent-card.json` and describes:

- Agent identity (name, version, description)
- Supported capabilities (streaming, task states)
- Available skills (what tasks this agent can handle)
- Authentication requirements
- Endpoint URLs

```json
{
  "name": "Hermes Agent",
  "description": "Self-improving AI agent with persistent memory",
  "url": "http://localhost:4097",
  "version": "1.0.0",
  "capabilities": {
    "streaming": true
  },
  "skills": [
    {
      "id": "hermes_general",
      "name": "General Purpose",
      "description": "Research, coding, automation, web browsing",
      "tags": ["research", "coding", "automation"],
      "input_modes": ["text/plain"],
      "output_modes": ["text/plain", "application/json"]
    }
  ]
}
```

## Task Lifecycle

A2A tasks follow a standard state machine:

```
submitted ──→ working ──→ completed
                 │             │
                 ├──→ input-required ──→ working ──→...
                 │             │
                 └──→ failed
                 
                 cancelled (any state)
```

### Sending a Task (non-streaming)

```json
{
  "jsonrpc": "2.0",
  "method": "tasks/send",
  "params": {
    "id": "unique-task-id",
    "sessionId": "optional-session-id",
    "message": {
      "role": "user",
      "parts": [
        {"type": "text", "text": "Research the latest trends in AI agents"}
      ]
    }
  }
}
```

### Streaming Response

```json
// Event 1: Working
{"jsonrpc":"2.0","method":"tasks/event","params":{"id":"task-1","event":{"type":"status","state":"working"}}}

// Event 2: Progress
{"jsonrpc":"2.0","method":"tasks/event","params":{"id":"task-1","event":{"type":"artifact","artifact":{"parts":[{"type":"text","text":"Researching..."}]}}}}

// Event 3: Complete
{"jsonrpc":"2.0","method":"tasks/event","params":{"id":"task-1","event":{"type":"status","state":"completed","artifact":{"parts":[{"type":"text","text":"Final result here"}]}}}}
```

## OpenCode Integration

OpenCode can connect to Hermes via the MCP bridge. Configure it in `opencode.jsonc`:

```json
{
  "mcpServers": {
    "hermes-a2a": {
      "command": "python3",
      "args": ["-m", "hermes_a2a_plugin.bridge_mcp"]
    }
  }
}
```

Then in OpenCode you can use tools like:

- `hermes_research` — Delegate research tasks to Hermes
- `hermes_automate` — Delegate automation tasks
- `hermes_browse` — Delegate web browsing
