# Getting Started

## Prerequisites

- **Hermes Agent** installed and configured
- **Python 3.10+**
- **pip** and **git**

## Installation

### 1. Install the Plugin

```bash
hermes plugins install yourusername/hermes-a2a-plugin
```

### 2. Enable the Plugin

```bash
hermes plugins enable hermes-a2a
```

Verify it's enabled:

```bash
hermes plugins list
# → hermes-a2a     [enabled]  A2A protocol support for Hermes
```

### 3. Configure

Create or edit `~/.hermes/config.yaml`:

```yaml
plugins:
  enabled:
    - hermes-a2a
```

### 4. Start the A2A Server

```bash
hermes a2a serve
# → A2A server running on http://127.0.0.1:4097
# → Agent Card at http://127.0.0.1:4097/.well-known/agent-card.json
```

### 5. Verify

Check the Agent Card:

```bash
curl http://127.0.0.1:4097/.well-known/agent-card.json | jq .
```

Send a test task:

```bash
curl -X POST http://127.0.0.1:4097/tasks/send \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tasks/send",
    "params": {
      "id": "test-1",
      "message": {
        "role": "user",
        "parts": [{"text": "Hello from A2A!"}]
      }
    }
  }'
```

## Connecting OpenCode

Configure the A2A MCP bridge in `~/.opencode/opencode.jsonc`:

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

Now OpenCode can discover Hermes capabilities and delegate tasks via MCP → A2A.
