"""Tool schemas for the A2A plugin — what the LLM sees."""

A2A_SERVE_SCHEMA = {
    "name": "a2a_serve",
    "description": (
        "Start the A2A (Agent2Agent) protocol server. "
        "This allows other AI agents (OpenCode, Claude Code, etc.) "
        "to discover and delegate tasks to Hermes via the A2A protocol. "
        "The server runs in background and publishes an Agent Card "
        "at /.well-known/agent-card.json."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "port": {
                "type": "integer",
                "description": "Server port (default: 4097)",
                "default": 4097,
            },
            "host": {
                "type": "string",
                "description": "Bind address (default: 127.0.0.1)",
                "default": "127.0.0.1",
            },
            "token": {
                "type": "string",
                "description": "Optional bearer token for authentication",
                "default": "",
            },
        },
    },
}

A2A_STATUS_SCHEMA = {
    "name": "a2a_status",
    "description": "Check if the A2A server is running and get its status.",
    "parameters": {
        "type": "object",
        "properties": {},
    },
}

A2A_STOP_SCHEMA = {
    "name": "a2a_stop",
    "description": "Stop the A2A protocol server.",
    "parameters": {
        "type": "object",
        "properties": {},
    },
}
