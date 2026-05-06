"""A2A Client — envía tareas A2A desde Hermes a cualquier target.

Traduce solicitudes de Hermes en mensajes A2A JSON-RPC 2.0 y las envía
a un servidor A2A remoto. Soporta targets:
  - opencode-bridge: Traduce la tarea a `opencode run "task"` y captura resultado
  - http://host:port: Envía directamente a cualquier servidor A2A
  - local: Ejecuta localmente y devuelve como A2A artifact (fallback)
"""

import json
import logging
import subprocess
import time
import urllib.request
import urllib.error

logger = logging.getLogger("hermes-a2a.client")

# ── Schema for Hermes tool registration ──────────────────

A2A_DELEGATE_SCHEMA = {
    "name": "a2a_delegate",
    "description": (
        "Delegate a task to another agent via the A2A (Agent2Agent) protocol. "
        "Sends a JSON-RPC 2.0 task to an A2A-compatible server or bridge. "
        "Supported targets:\n"
        "  - 'opencode': Delegates to OpenCode CLI via built-in bridge\n"
        "  - 'http://host:port': Any A2A-compatible server\n"
        "  - 'local': Processes locally and returns result\n\n"
        "Use this when you want to delegate coding tasks to OpenCode, "
        "or send tasks to other A2A-capable agents."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "task": {
                "type": "string",
                "description": "The task description to delegate",
            },
            "target": {
                "type": "string",
                "description": (
                    "Target agent or URL. "
                    "'opencode' (default) sends to OpenCode CLI. "
                    "A URL like 'http://host:port' sends to any A2A server."
                ),
                "default": "opencode",
            },
            "context": {
                "type": "string",
                "description": "Optional background context or file paths",
                "default": "",
            },
        },
        "required": ["task"],
    },
}

A2A_CLIENT_SCHEMA = {
    "name": "a2a_client",
    "description": "Check A2A client status and available targets.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["status", "targets", "test"],
                "description": "What to check",
            },
            "target": {
                "type": "string",
                "description": "Optional target URL to test",
                "default": "",
            },
        },
        "required": ["action"],
    },
}


# ── Targets ──────────────────────────────────────────────


class OpenCodeBridge:
    """Bridge that translates A2A tasks to OpenCode CLI commands.

    Takes an A2A task, spawns ``opencode run``, captures the
    result, and returns it as an A2A artifact.
    """

    def __init__(self, timeout: int = 300):
        self.timeout = timeout

    def execute(self, task: str, context: str = "") -> dict:
        """Execute a task through OpenCode CLI.

        Args:
            task: The coding task to execute.
            context: Optional context or files to include.

        Returns:
            A2A-formatted result dict with status, stdout, and artifacts.
        """
        # Build the prompt
        prompt = task
        if context:
            prompt = f"{task}\n\nContext/Archivos relevantes:\n{context}"

        # Build opencode command
        cmd = [
            "opencode", "run", prompt,
            "--dangerously-skip-permissions",
        ]

        logger.info("OpenCode bridge executing: %s...", prompt[:80])

        start = time.time()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "message": f"OpenCode task timed out after {self.timeout}s",
                "duration_s": self.timeout,
            }
        except FileNotFoundError:
            return {
                "status": "error",
                "message": (
                    "OpenCode CLI not found. "
                    "Install: npm i -g opencode-ai"
                ),
                "duration_s": 0,
            }

        elapsed = time.time() - start
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        if result.returncode != 0:
            return {
                "status": "error",
                "message": f"OpenCode exited with code {result.returncode}",
                "stderr": stderr[:2000],
                "duration_s": round(elapsed, 1),
            }

        return {
            "status": "completed",
            "message": "Task completed via OpenCode",
            "stdout": stdout[:5000],
            "stderr": stderr[:1000] if stderr else "",
            "duration_s": round(elapsed, 1),
        }


class A2ADirectClient:
    """Sends A2A tasks directly to any A2A-compatible HTTP server."""

    def __init__(self, timeout: int = 60):
        self.timeout = timeout

    def send_task(self, url: str, task: str, context: str = "") -> dict:
        """Send a task to an A2A server via HTTP POST.

        Args:
            url: Base URL of the A2A server (e.g. http://localhost:4097).
            task: The task text.
            context: Optional context.

        Returns:
            A2A response dict.
        """
        prompt = task
        if context:
            prompt = f"{task}\n\nContext:\n{context}"

        payload = {
            "jsonrpc": "2.0",
            "id": f"hermes-{int(time.time())}",
            "params": {
                "id": f"task-{int(time.time())}",
                "message": {
                    "role": "user",
                    "parts": [{"text": prompt}],
                },
            },
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{url.rstrip('/')}/tasks/send",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                response_data = json.loads(resp.read().decode())
        except urllib.error.URLError as e:
            return {
                "status": "error",
                "message": f"Connection failed: {e.reason}",
            }
        except json.JSONDecodeError:
            return {
                "status": "error",
                "message": "Invalid JSON response from server",
            }

        result = response_data.get("result", {})
        artifacts = result.get("artifacts", [])
        text = ""
        for art in artifacts:
            for part in art.get("parts", []):
                if part.get("type") == "text":
                    text += part.get("text", "")

        return {
            "status": result.get("status", {}).get("state", "unknown"),
            "message": result.get("status", {}).get("message", ""),
            "result": text[:5000],
            "task_id": result.get("id"),
        }


# ── Client Router ────────────────────────────────────────


class A2AClient:
    """A2A client router — delegates tasks to the appropriate target.

    Example::

        client = A2AClient()
        # Delegate to OpenCode:
        client.send("Implement REST API in users.py", target="opencode")
        # Delegate to A2A server:
        client.send("Research AI trends", target="http://localhost:4097")
    """

    def __init__(self):
        self.opencode = OpenCodeBridge()
        self.direct = A2ADirectClient()

    def send(self, task: str, target: str = "opencode", context: str = "") -> dict:
        """Send a task to the specified target.

        Args:
            task: Task description.
            target: 'opencode' for OpenCode CLI, or a URL like 'http://host:port'.
            context: Optional context.

        Returns:
            Dict with status, result, and metadata.
        """
        logger.info("A2A delegate: target=%s task=%s", target, task[:80])

        if target == "opencode":
            result = self.opencode.execute(task, context)
        elif target.startswith("http://") or target.startswith("https://"):
            result = self.direct.send_task(target, task, context)
        else:
            result = {
                "status": "error",
                "message": f"Unknown target: {target}. Use 'opencode' or a URL.",
            }

        return result

    def get_targets(self) -> list[dict]:
        """List available A2A targets.

        Returns:
            List of target descriptions.
        """
        return [
            {
                "name": "opencode",
                "type": "local",
                "description": "OpenCode CLI via bridge — coding tasks",
                "status": "available",
            },
            {
                "name": "http://host:port",
                "type": "remote",
                "description": "Any A2A-compatible server",
                "status": "depends",
            },
        ]

    def test_target(self, target: str) -> dict:
        """Test connectivity to a target.

        Args:
            target: 'opencode' or a URL.

        Returns:
            Dict with connectivity info.
        """
        if target == "opencode":
            try:
                result = subprocess.run(
                    ["opencode", "--version"],
                    capture_output=True, text=True, timeout=10,
                )
                if result.returncode == 0:
                    return {
                        "status": "ok",
                        "version": result.stdout.strip()[:100],
                    }
                return {"status": "error", "message": result.stderr.strip()}
            except FileNotFoundError:
                return {"status": "error", "message": "OpenCode CLI not found"}
            except subprocess.TimeoutExpired:
                return {"status": "error", "message": "Timeout checking OpenCode"}

        return {"status": "unknown", "message": f"Can't test target: {target}"}
