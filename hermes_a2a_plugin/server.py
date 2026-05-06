"""A2A HTTP Server — handles A2A protocol requests.

Uses Python's built-in http.server for zero external dependencies.
In production, this can be swapped for Starlette + Uvicorn.
"""

import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

logger = logging.getLogger("hermes-a2a")

AGENT_CARD = {
    "name": "Hermes Agent",
    "description": "Self-improving AI agent with persistent memory, "
                   "tool execution, and multi-agent delegation",
    "url": "",
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
                "Debug a Python error",
                "Automate a deployment pipeline",
            ],
            "input_modes": ["text/plain"],
            "output_modes": ["text/plain", "application/json"],
        },
    ],
}


class A2ARequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for A2A protocol."""

    server_instance = None  # Set by A2AServer

    def log_message(self, format, *args):
        logger.debug(format, *args)

    def _send_json(self, status_code, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, status_code, message):
        self._send_json(status_code, {"error": {"message": message}})

    def _check_auth(self):
        """Check bearer token authentication."""
        if not self.server_instance or not self.server_instance.auth_token:
            return True
        auth = self.headers.get("Authorization", "")
        expected = f"Bearer {self.server_instance.auth_token}"
        if auth != expected:
            self._send_error(401, "Unauthorized")
            return False
        return True

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path == "/.well-known/agent-card.json":
            return self._handle_agent_card()
        elif path == "/health":
            return self._handle_health()
        else:
            self._send_error(404, "Not found")

    def do_POST(self):
        if not self._check_auth():
            return

        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length else b"{}"

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return self._send_error(400, "Invalid JSON")

        if path == "/tasks/send":
            return self._handle_tasks_send(data)
        else:
            self._send_error(404, "Not found")

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        self.end_headers()

    def _handle_agent_card(self):
        card = dict(AGENT_CARD)
        card["url"] = f"http://{self.server_instance.host}:{self.server_instance.port}"
        self._send_json(200, card)

    def _handle_health(self):
        self._send_json(200, {"status": "ok", "agent": "hermes-a2a-plugin"})

    def _handle_tasks_send(self, data):
        """Handle incoming A2A task delegation."""
        task_id = data.get("params", {}).get("id", "unknown")
        message = data.get("params", {}).get("message", {})

        logger.info(f"Received A2A task: {task_id}")

        # Extract user text from message
        parts = message.get("parts", [])
        user_text = ""
        for part in parts:
            if isinstance(part, dict) and "text" in part:
                user_text += part["text"]

        if not user_text:
            return self._send_error(400, "No text content in message")

        # Process via bridge
        if self.server_instance and self.server_instance.bridge:
            result = self.server_instance.bridge.process_task(task_id, user_text)
        else:
            result = f"Received: {user_text}"

        # Return A2A task response
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
                        },
                    }
                ],
            },
        }
        self._send_json(200, response)


class A2AServer:
    """A2A protocol server for Hermes."""

    def __init__(
        self,
        host="127.0.0.1",
        port=4097,
        auth_token="",
        bridge=None,
    ):
        self.host = host
        self.port = port
        self.auth_token = auth_token
        self.bridge = bridge
        self.is_running = False
        self._httpd = None

    def run(self):
        """Start the server (blocking)."""
        A2ARequestHandler.server_instance = self
        self._httpd = HTTPServer((self.host, self.port), A2ARequestHandler)
        self.is_running = True
        logger.info(
            "A2A server listening on http://%s:%d", self.host, self.port
        )
        try:
            self._httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.is_running = False
            self._httpd.server_close()

    def stop(self):
        """Stop the server."""
        if self._httpd:
            self._httpd.shutdown()
        self.is_running = False
