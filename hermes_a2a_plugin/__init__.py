"""Hermes A2A Plugin — Agent2Agent protocol support for Hermes Agent.

This plugin enables Hermes to act as an A2A-compatible server, allowing
any A2A-capable agent (OpenCode, Claude Code, Codex, etc.) to discover
and delegate tasks to Hermes via the standard A2A protocol.

Typical usage::

    # From within Hermes, start the server:
    hermes a2a serve --port 4097

    # From any A2A client:
    # 1. Fetch Agent Card: GET http://localhost:4097/.well-known/agent-card.json
    # 2. Send task:       POST http://localhost:4097/tasks/send
"""

import os
import threading
from .server import A2AServer
from .schemas import A2A_SERVE_SCHEMA, A2A_STATUS_SCHEMA, A2A_STOP_SCHEMA

# Module-level state for the background server
_server_instance: A2AServer | None = None
"""Singleton reference to the running A2A server instance."""
_server_thread: threading.Thread | None = None
"""Background thread running the A2A server."""


def register(ctx: object) -> None:
    """Register plugin hooks, tools, and CLI commands with Hermes.

    Called automatically by Hermes PluginManager on session start.
    Registers three lifecycle hooks, three LLM-callable tools,
    and the ``hermes a2a`` CLI subcommand.

    Args:
        ctx: PluginContext provided by Hermes. Exposes methods
            like register_hook(), register_tool(), register_cli_command().
    """
    # Lifecycle hooks
    ctx.register_hook("session_start", on_session_start)
    ctx.register_hook("session_end", on_session_end)
    ctx.register_hook("pre_tool", on_pre_tool)
    ctx.register_hook("post_tool", on_post_tool)

    # LLM-callable tools
    ctx.register_tool(
        name="a2a_serve",
        schema=A2A_SERVE_SCHEMA,
        handler=handle_a2a_serve,
    )
    ctx.register_tool(
        name="a2a_status",
        schema=A2A_STATUS_SCHEMA,
        handler=handle_a2a_status,
    )
    ctx.register_tool(
        name="a2a_stop",
        schema=A2A_STOP_SCHEMA,
        handler=handle_a2a_stop,
    )

    # CLI subcommand: hermes a2a serve
    ctx.register_cli_command(
        name="a2a",
        help_text="A2A protocol commands",
        subcommands=[
            {
                "name": "serve",
                "help": "Start the A2A protocol server",
                "args": [
                    {
                        "name": "--port",
                        "type": int,
                        "default": 4097,
                        "help": "Server port (default: 4097)",
                    },
                    {
                        "name": "--host",
                        "type": str,
                        "default": "127.0.0.1",
                        "help": "Bind address (default: 127.0.0.1)",
                    },
                    {
                        "name": "--token",
                        "type": str,
                        "default": "",
                        "help": "Optional bearer auth token",
                    },
                ],
                "handler": cli_a2a_serve,
            },
        ],
    )


# ── Hook handlers ─────────────────────────────────────────


def on_session_start(session_data):
    """Handle session start event.

    Args:
        session_data: Dict with session metadata (id, profile, etc.).
    """
    pass


def on_session_end(session_data):
    """Handle session end event. Stops the A2A server if running.

    Args:
        session_data: Dict with session metadata.
    """
    if _server_instance:
        _server_instance.stop()


def on_pre_tool(tool_data):
    """Filter/intercept tool calls before execution.

    Args:
        tool_data: Dict with tool name, args, and metadata.

    Returns:
        Modified tool_data dict, or None to cancel the tool call.
    """
    return tool_data


def on_post_tool(tool_result):
    """Process tool results after execution.

    Args:
        tool_result: Dict with tool output.

    Returns:
        Modified tool_result dict.
    """
    return tool_result


# ── Tool handlers ─────────────────────────────────────────


def handle_a2a_serve(port: int = 4097, host: str = "127.0.0.1", token: str = "") -> str:
    """Start the A2A server in a background thread.

    Args:
        port: HTTP server port (default: 4097).
        host: Bind address (default: 127.0.0.1).
        token: Optional bearer token for authentication.

    Returns:
        Status message indicating server URL and Agent Card endpoint.
    """
    global _server_instance, _server_thread

    if _server_instance and _server_instance.is_running:
        return f"✓ A2A server already running on http://{host}:{port}"

    _server_instance = A2AServer(host=host, port=port, auth_token=token)
    _server_thread = threading.Thread(
        target=_server_instance.run,
        daemon=True,
    )
    _server_thread.start()

    return (
        f"✓ A2A server starting on http://{host}:{port}\n"
        f"  Agent Card: http://{host}:{port}/.well-known/agent-card.json"
    )


def handle_a2a_status() -> str:
    """Check if the A2A server is running.

    Returns:
        Status string indicating running or stopped.
    """
    if _server_instance and _server_instance.is_running:
        return (
            f"✓ A2A server running on "
            f"http://{_server_instance.host}:{_server_instance.port}"
        )
    return "✗ A2A server is not running"


def handle_a2a_stop() -> str:
    """Stop the A2A server if running.

    Returns:
        Confirmation message.
    """
    global _server_instance
    if _server_instance:
        _server_instance.stop()
        _server_instance = None
        return "✓ A2A server stopped"
    return "✗ A2A server is not running"


# ── CLI handlers ─────────────────────────────────────────


def cli_a2a_serve(port=4097, host="127.0.0.1", token=""):
    """Run the A2A server in foreground (called from CLI).

    This is the handler for ``hermes a2a serve``. Blocks until
    Ctrl+C is pressed.

    Args:
        port: HTTP server port.
        host: Bind address.
        token: Optional auth bearer token.
    """
    server = A2AServer(host=host, port=port, auth_token=token)
    print(f"🚀 Hermes A2A Server ({server.version})")
    print(f"📍 http://{host}:{port}")
    print(f"📋 /.well-known/agent-card.json")
    print(f"🔌 /tasks/send")
    print("Press Ctrl+C to stop")
    server.run()
