"""A2A HTTP Server — handles A2A protocol requests.

Uses Python's built-in ``http.server`` for zero external dependencies.
In production, can be swapped for Starlette + Uvicorn.

Architecture::

    Client                      A2AServer                     Bridge
      │                            │                            │
      │  GET /.well-known/         │                            │
      │  agent-card.json           │                            │
      │◄───────────────────────────│                            │
      │          Agent Card        │                            │
      │                            │                            │
      │  POST /tasks/send          │                            │
      │  {jsonrpc, method, params} │                            │
      │───────────────────────────►│                            │
      │                            │  bridge.process_task()     │
      │                            │───────────────────────────►│
      │                            │◄───────────────────────────│
      │◄───────────────────────────│          result             │
      │   {jsonrpc, result}        │                            │
"""

import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

logger = logging.getLogger("hermes-a2a")

# Default Agent Card — published at /.well-known/agent-card.json
AGENT_CARD = {
    "name": "Hermes Agent",
    "description": (
        "Self-improving AI agent with persistent memory, "
        "tool execution, web browsing, and multi-agent delegation"
    ),
    "version": "0.1.0",
    "capabilities": {
        "streaming": True,
        "extended_agent_card": True,
    },
    "default_input_modes": ["text/plain"],
    "default_output_modes": ["text/plain", "application/json"],
    "skills": [
        {
            "id": "hermes_general",
            "name": "General Purpose Agent",
            "description": (
                "Research topics, write and debug code, browse the web, "
                "execute terminal commands, and automate workflows"
            ),
            "tags": ["research", "coding", "automation", "web", "terminal"],
            "examples": [
                "Research the latest AI papers",
                "Implement a REST API endpoint",
                "Debug a Python traceback",
                "Automate a deployment pipeline",
                "Analyze server logs for anomalies",
            ],
            "input_modes": ["text/plain"],
            "output_modes": ["text/plain", "application/json"],
        },
    ],
}


class A2ARequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler implementing the A2A protocol.

    Handles GET for discovery (Agent Card, health) and POST for
    task delegation (tasks/send). Supports CORS and optional
    bearer token authentication.

    Attributes:
        server_instance: Reference to parent A2AServer (set at startup).
    """

    server_instance = None  # type: A2AServer | None

    def log_message(self, format: str, *args):
        """Override default logging to use Python logger."""
        logger.debug(format, *args)

    def _send_json(self, status_code: int, data: dict):
        """Send a JSON response with CORS headers.

        Args:
            status_code: HTTP status code.
            data: Serializable dict to send as JSON body.
        """
        body = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, status_code: int, message: str):
        """Send a JSON error response.

        Args:
            status_code: HTTP status code.
            message: Human-readable error description.
        """
        self._send_json(status_code, {"error": {"message": message}})

    def _check_auth(self) -> bool:
        """Validate bearer token if authentication is configured.

        Returns:
            True if auth passes or is disabled, False otherwise.
            Sends 401 response on failure.
        """
        if not self.server_instance or not self.server_instance.auth_token:
            return True
        auth = self.headers.get("Authorization", "")
        expected = f"Bearer {self.server_instance.auth_token}"
        if auth != expected:
            self._send_error(401, "Unauthorized: invalid or missing bearer token")
            return False
        return True

    def do_GET(self):
        """Handle GET requests: Agent Card discovery and health check."""
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        handlers = {
            "/.well-known/agent-card.json": self._handle_agent_card,
            "/health": self._handle_health,
        }
        handler = handlers.get(path)
        if handler:
            handler()
        else:
            self._send_error(404, f"Not found: {path}")

    def do_POST(self):
        """Handle POST requests: task delegation via tasks/send."""
        if not self._check_auth():
            return

        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length else b"{}"

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return self._send_error(400, "Invalid JSON in request body")

        if path == "/tasks/send":
            return self._handle_tasks_send(data)
        else:
            self._send_error(404, f"Not found: {path}")

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        self.end_headers()

    # ── Endpoint handlers ──────────────────────────────────

    def _handle_agent_card(self):
        """Serve the Agent Card — the agent's public capabilities manifest.

        Response is the AGENT_CARD dict with the URL field populated
        dynamically based on the actual server address.
        """
        card = dict(AGENT_CARD)
        card["url"] = (
            f"http://{self.server_instance.host}:{self.server_instance.port}"
        )
        self._send_json(200, card)

    def _handle_health(self):
        """Simple health check endpoint."""
        self._send_json(200, {
            "status": "ok",
            "agent": "hermes-a2a-plugin",
            "version": "0.1.0",
        })

    def _handle_tasks_send(self, data: dict):
        """Process an incoming A2A task delegation.

        Args:
            data: Parsed JSON body containing the A2A request.
                Expected format::
                    {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "params": {
                            "id": "task-id",
                            "message": {
                                "role": "user",
                                "parts": [{"text": "Do something"}]
                            }
                        }
                    }

        Returns:
            A2A JSON-RPC 2.0 response with task status and artifacts.
        """
        task_id = data.get("params", {}).get("id", "unknown")
        message = data.get("params", {}).get("message", {})

        logger.info("Received A2A task: %s", task_id)

        # Extract text from message parts
        parts = message.get("parts", [])
        user_text = ""
        for part in parts:
            if isinstance(part, dict) and "text" in part:
                user_text += part["text"]

        if not user_text:
            return self._send_error(400, "No text content in message parts")

        # Process via bridge (or fallback echo)
        if self.server_instance and self.server_instance.bridge:
            result = self.server_instance.bridge.process_task(task_id, user_text)
        else:
            result = (
                f"[A2A Bridge] Task '{task_id}' received.\n"
                f"Input: {user_text[:500]}\n\n"
                "⏳ This is the MVP stub. "
                "The full Hermes AIAgent integration is coming next."
            )

        # Return A2A-formatted response
        response = {
            "jsonrpc": "2.0",
            "id": data.get("id"),
            "result": {
                "id": task_id,
                "status": {
                    "state": "completed",
                    "message": "Task completed successfully",
                },
                "artifacts": [
                    {
                        "name": "response",
                        "parts": [{"type": "text", "text": result}],
                        "metadata": {
                            "agent": "Hermes",
                            "task_id": task_id,
                            "version": "0.1.0",
                        },
                    }
                ],
            },
        }
        self._send_json(200, response)


class A2AServer:
    """A2A protocol server wrapping an HTTP server.

    Runs a built-in ``http.server.HTTPServer`` with the A2A protocol
    request handler. Supports optional bearer token authentication
    and a pluggable task bridge.

    Example::

        server = A2AServer(host="127.0.0.1", port=4097)
        server.run()  # Blocks until Ctrl+C

    Attributes:
        host: Bind address (default: 127.0.0.1).
        port: HTTP port (default: 4097).
        auth_token: Optional bearer token for auth.
        bridge: Optional HermesTaskBridge for task processing.
        version: Server version string.
        is_running: Whether the server is currently accepting requests.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 4097,
        auth_token: str = "",
        bridge: object = None,
    ):
        """Initialize the A2A server.

        Args:
            host: Bind address.
            port: HTTP port.
            auth_token: Bearer token for authentication (empty = no auth).
            bridge: Task bridge instance (e.g. HermesTaskBridge) for processing.
        """
        self.host = host
        self.port = port
        self.auth_token = auth_token
        self.bridge = bridge
        self.version = "0.1.0"
        self.is_running = False
        self._httpd: HTTPServer | None = None

    def run(self):
        """Start the server (blocking). Press Ctrl+C to stop."""
        A2ARequestHandler.server_instance = self
        self._httpd = HTTPServer((self.host, self.port), A2ARequestHandler)
        self.is_running = True
        logger.info("A2A server listening on http://%s:%d", self.host, self.port)
        try:
            self._httpd.serve_forever()
        except KeyboardInterrupt:
            logger.info("A2A server shutting down")
        finally:
            self.is_running = False
            self._httpd.server_close()

    def stop(self):
        """Stop the server gracefully."""
        if self._httpd:
            self._httpd.shutdown()
        self.is_running = False
