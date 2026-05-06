"""Hermes A2A Plugin — Agent2Agent protocol support for Hermes Agent.

This plugin enables Hermes to act as an A2A-compatible server, allowing
any A2A-capable agent (OpenCode, Claude Code, Codex, etc.) to discover
and delegate tasks to Hermes via the standard A2A protocol.
"""

import os
import threading
from .server import A2AServer
from .schemas import A2A_SERVE_SCHEMA, A2A_STATUS_SCHEMA, A2A_STOP_SCHEMA

_server_instance = None
_server_thread = None


def register(ctx):
    """Register plugin hooks, tools, and CLI commands."""

    # ── Lifecycle hooks ──────────────────────────────────────
    ctx.register_hook("session_start", on_session_start)
    ctx.register_hook("session_end", on_session_end)
    ctx.register_hook("pre_tool", on_pre_tool)
    ctx.register_hook("post_tool", on_post_tool)

    # ── Tools the LLM can call ────────────────────────────────
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

    # ── CLI subcommand ────────────────────────────────────────
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
                        "help": "Server port",
                    },
                    {
                        "name": "--host",
                        "type": str,
                        "default": "127.0.0.1",
                        "help": "Bind address",
                    },
                    {
                        "name": "--token",
                        "type": str,
                        "default": "",
                        "help": "Auth bearer token",
                    },
                ],
                "handler": cli_a2a_serve,
            },
        ],
    )


# ── Hook handlers ─────────────────────────────────────────


def on_session_start(session_data):
    """Called when a new Hermes session starts."""
    pass


def on_session_end(session_data):
    """Called when a Hermes session ends."""
    if _server_instance:
        _server_instance.stop()


def on_pre_tool(tool_data):
    """Called before a tool is executed."""
    return tool_data


def on_post_tool(tool_result):
    """Called after a tool is executed."""
    return tool_result


# ── Tool handlers ─────────────────────────────────────────


def handle_a2a_serve(port: int = 4097, host: str = "127.0.0.1", token: str = ""):
    """Start the A2A server in background."""
    global _server_instance, _server_thread

    if _server_instance and _server_instance.is_running:
        return f"A2A server already running on http://{host}:{port}"

    _server_instance = A2AServer(host=host, port=port, auth_token=token)

    _server_thread = threading.Thread(
        target=_server_instance.run,
        daemon=True,
    )
    _server_thread.start()

    return (
        f"A2A server starting on http://{host}:{port}\n"
        f"Agent Card: http://{host}:{port}/.well-known/agent-card.json"
    )


def handle_a2a_status():
    """Check server status."""
    if _server_instance and _server_instance.is_running:
        return (
            f"A2A server is running on "
            f"http://{_server_instance.host}:{_server_instance.port}"
        )
    return "A2A server is not running"


def handle_a2a_stop():
    """Stop the A2A server."""
    global _server_instance
    if _server_instance:
        _server_instance.stop()
        _server_instance = None
        return "A2A server stopped"
    return "A2A server is not running"


# ── CLI handlers ─────────────────────────────────────────


def cli_a2a_serve(port=4097, host="127.0.0.1", token=""):
    """Run the A2A server in foreground (CLI mode)."""
    server = A2AServer(host=host, port=port, auth_token=token)
    print(f"🚀 Hermes A2A Server starting on http://{host}:{port}")
    print(f"📋 Agent Card: http://{host}:{port}/.well-known/agent-card.json")
    server.run()
