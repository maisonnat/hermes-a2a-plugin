#!/usr/bin/env python3
"""MCP (Model Context Protocol) bridge — connects OpenCode to Hermes.

This module implements an MCP server that exposes Hermes Agent as
a set of tools that OpenCode can discover and invoke via the
Model Context Protocol.

OpenCode configuration (in ~/.opencode/opencode.jsonc or opencode.jsonc)::

    {
      "mcpServers": {
        "hermes-a2a": {
          "command": "python3",
          "args": ["-m", "hermes_a2a_plugin.bridge_mcp"]
        }
      }
    }

Then in OpenCode, tools like ``hermes_delegate``, ``hermes_research``,
``hermes_status`` become available.

Protocol: MCP uses JSON-RPC 2.0 over stdio.
  - Client → Server: {"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}
  - Server → Client: {"jsonrpc":"2.0","id":1,"result":{"tools":[...]}}
  - Client → Server: {"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"hermes_delegate","arguments":{...}}}
  - Server → Client: {"jsonrpc":"2.0","id":2,"result":{"content":[...]}}
"""

import json
import logging
import subprocess
import sys

logger = logging.getLogger("hermes-mcp-bridge")

# ── Tool Definitions (what OpenCode's LLM sees) ─────────────

HERMES_DELEGATE_TOOL = {
    "name": "hermes_delegate",
    "description": (
        "Delegate a complex or long-running task to Hermes Agent. "
        "Use this when a task requires web research, persistent memory, "
        "multi-step reasoning, or capabilities Hermes has that OpenCode "
        "doesn't (e.g., browser automation, memory, broader toolset). "
        "Hermes will process the task and return the result."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "task": {
                "type": "string",
                "description": "The task description for Hermes to execute",
            },
            "context": {
                "type": "string",
                "description": "Optional background context or constraints",
                "default": "",
            },
        },
        "required": ["task"],
    },
}

HERMES_RESEARCH_TOOL = {
    "name": "hermes_research",
    "description": (
        "Perform deep research on a topic using Hermes Agent. "
        "Hermes will search the web, analyze findings, and return "
        "a synthesized summary. Use this for research-heavy tasks."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Research question or topic to investigate",
            },
        },
        "required": ["query"],
    },
}

HERMES_STATUS_TOOL = {
    "name": "hermes_status",
    "description": (
        "Check if Hermes Agent is available and responsive. "
        "Returns connection status and version info."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {},
    },
}

AVAILABLE_TOOLS = [
    HERMES_DELEGATE_TOOL,
    HERMES_RESEARCH_TOOL,
    HERMES_STATUS_TOOL,
]


# ── MCP Protocol Implementation ────────────────────────────


def send_response(data: dict):
    """Send a JSON-RPC response to stdout (MCP protocol).

    Args:
        data: Dict to serialize as JSON response.
    """
    sys.stdout.write(json.dumps(data) + "\n")
    sys.stdout.flush()


def handle_initialize(_params: dict) -> dict:
    """Handle MCP initialize request.

    Returns server capabilities (tools supported).

    Args:
        _params: Initialize parameters (ignored).

    Returns:
        Server capabilities dict.
    """
    return {
        "capabilities": {
            "tools": {},  # Tools capability declared
        },
        "serverInfo": {
            "name": "hermes-a2a-mcp-bridge",
            "version": "0.1.0",
        },
    }


def handle_tools_list(_params: dict) -> dict:
    """Handle MCP tools/list request.

    Returns all available Hermes tools.

    Args:
        _params: List parameters (ignored).

    Returns:
        Dict with tools array.
    """
    return {"tools": AVAILABLE_TOOLS}


def handle_tools_call(params: dict) -> dict:
    """Handle MCP tools/call request.

    Routes to the appropriate handler based on tool name.

    Args:
        params: Dict with ``name`` (tool name) and ``arguments``.

    Returns:
        MCP content result with text output.
    """
    name = params.get("name", "")
    args = params.get("arguments", {})

    handlers = {
        "hermes_delegate": _call_hermes_delegate,
        "hermes_research": _call_hermes_research,
        "hermes_status": _call_hermes_status,
    }

    handler = handlers.get(name)
    if not handler:
        return {
            "isError": True,
            "content": [{"type": "text", "text": f"Unknown tool: {name}"}],
        }

    try:
        result = handler(args)
        return {
            "content": [{"type": "text", "text": result}],
        }
    except Exception as e:
        logger.error("Tool %s failed: %s", name, e)
        return {
            "isError": True,
            "content": [{"type": "text", "text": f"Error: {e}"}],
        }


# ── Tool Handlers ──────────────────────────────────────────


def _call_hermes(task_text: str, timeout: int = 180) -> str:
    """Execute a task through Hermes CLI one-shot mode.

    Spawns ``hermes chat -q`` and returns the response.

    Args:
        task_text: The full prompt to send to Hermes.
        timeout: Max seconds to wait for completion.

    Returns:
        Hermes response text.

    Raises:
        RuntimeError: If Hermes CLI fails or is not found.
    """
    try:
        result = subprocess.run(
            ["hermes", "chat", "-q", task_text, "--quiet"],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return f"[Hermes MCP Bridge] Task timed out after {timeout}s"
    except FileNotFoundError:
        return (
            "[Hermes MCP Bridge] Hermes CLI not found. "
            "Install with: curl -fsSL https://raw.githubusercontent.com/"
            "NousResearch/hermes-agent/main/scripts/install.sh | bash"
        )

    if result.returncode != 0:
        error = result.stderr.strip() or "Unknown error"
        return f"[Hermes MCP Bridge] Hermes error: {error}"

    output = result.stdout.strip()
    # Strip session_id header if present
    lines = output.split("\n")
    if lines and lines[0].startswith("session_id:"):
        output = "\n".join(lines[1:]).strip()
    return output


def _call_hermes_delegate(args: dict) -> str:
    """Handle hermes_delegate tool call.

    Args:
        args: Dict with ``task`` and optional ``context``.

    Returns:
        Hermes response.
    """
    task = args.get("task", "")
    context = args.get("context", "")

    if not task:
        return "[Hermes MCP Bridge] Error: 'task' argument is required"

    full_prompt = task
    if context:
        full_prompt = f"{task}\n\nContext: {context}"

    return _call_hermes(full_prompt)


def _call_hermes_research(args: dict) -> str:
    """Handle hermes_research tool call.

    Wraps the query in a research-focused prompt.

    Args:
        args: Dict with ``query``.

    Returns:
        Research results from Hermes.
    """
    query = args.get("query", "")
    if not query:
        return "[Hermes MCP Bridge] Error: 'query' argument is required"

    research_prompt = (
        f"Research the following topic thoroughly. "
        f"Search the web, analyze findings, and provide "
        f"a comprehensive summary with sources:\n\n{query}"
    )
    return _call_hermes(research_prompt, timeout=300)


def _call_hermes_status(_args: dict) -> str:
    """Check Hermes CLI availability.

    Returns:
        Status message.
    """
    try:
        result = subprocess.run(
            ["hermes", "chat", "-q", "Say OK if you're alive", "--quiet"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            output = result.stdout.strip()
            # Strip session_id if present
            lines = output.split("\n")
            if lines and lines[0].startswith("session_id:"):
                output = "\n".join(lines[1:]).strip()
            return (
                "✅ Hermes Agent is available and responsive.\n"
                f"Response: {output}"
            )
        return f"⚠️ Hermes responded with error code {result.returncode}"
    except FileNotFoundError:
        return "❌ Hermes CLI not found in PATH"
    except subprocess.TimeoutExpired:
        return "⚠️ Hermes did not respond within 15s"


# ── Main MCP Event Loop ───────────────────────────────────


def main():
    """Run the MCP bridge server.

    Reads JSON-RPC 2.0 messages from stdin and responds via stdout.
    Handles initialize, tools/list, and tools/call methods.
    """
    logger.info("Hermes MCP Bridge starting")

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            send_response({
                "jsonrpc": "2.0",
                "error": {"code": -32700, "message": "Parse error"},
            })
            continue

        req_id = request.get("id")
        method = request.get("method", "")
        params = request.get("params", {})

        logger.debug("Received: %s (id=%s)", method, req_id)

        try:
            if method == "initialize":
                result = handle_initialize(params)
            elif method == "tools/list":
                result = handle_tools_list(params)
            elif method == "tools/call":
                result = handle_tools_call(params)
            elif method == "notifications/initialized":
                # No response needed for notifications
                continue
            else:
                send_response({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}",
                    },
                })
                continue

            send_response({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": result,
            })

        except Exception as e:
            logger.exception("Error handling %s", method)
            send_response({
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {e}",
                },
            })


if __name__ == "__main__":
    main()
