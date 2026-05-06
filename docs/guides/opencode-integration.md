# OpenCode MCP Bridge Integration

Connect OpenCode to Hermes Agent via the MCP bridge, giving OpenCode
access to Hermes' research, memory, and general-purpose capabilities.

## How It Works

```
OpenCode ──MCP (stdio/JSON-RPC)──→ bridge_mcp.py ──subprocess──→ hermes chat -q
```

OpenCode discovers Hermes as MCP tools and delegates tasks seamlessly.

## Configuration

Add this to your OpenCode config file (``~/.opencode/opencode.jsonc``
or project-level ``opencode.jsonc``)::

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

## Available Tools

Once configured, OpenCode gains these tools:

### hermes_delegate
Delegate any complex task to Hermes. Use when you need web research,
persistent memory, browser automation, or multi-step reasoning.

Parameters:
- ``task`` (required): The task description
- ``context`` (optional): Background context or constraints

### hermes_research
Perform deep research on a topic. Wraps the query in a research-focused
prompt with extended timeout (5 min).

Parameters:
- ``query`` (required): Research question or topic

### hermes_status
Check if Hermes is available and responsive. Returns version and
connection status.

## Usage in OpenCode

Once configured, you can use the tools naturally in OpenCode:

```
# Delegate a complex task
> @hermes Delegate: "Research gRPC error handling patterns"

# Research
> @hermes Research: "Latest developments in WebAssembly GC"
```

Or via OpenCode's tool calling (the LLM decides when to use them):

```
# OpenCode will automatically delegate when it senses a task
# that needs Hermes' capabilities
```

## Troubleshooting

**OpenCode doesn't see the tools:**
- Verify the config path: ``~/.opencode/opencode.jsonc``
- Check the python3 path: ``which python3``
- Run the bridge directly: ``python3 -m hermes_a2a_plugin.bridge_mcp``
  (it will wait for MCP messages)

**Bridge fails to start:**
- Ensure hermes-a2a-plugin is installed: ``pip install -e ~/Projects/hermes-a2a-plugin``
- Check Hermes CLI: ``hermes chat -q "test" --quiet``
