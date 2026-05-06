"""Bridge — connects A2A task delegation to real Hermes execution.

This module implements the bridge between A2A protocol tasks and
Hermes Agent execution. When an A2A client (like OpenCode) sends
a task, the bridge processes it through Hermes and returns the result.

Two modes:
    1. Direct: Uses ``hermes chat -q`` subprocess (simple, proven)
    2. API: Direct Hermes AIAgent import (future, for streaming)

For the MVP, mode 1 is used — it's reliable, requires no internal
coupling, and handles all Hermes features (memory, skills, tools).
"""

import logging
import subprocess
import time
from dataclasses import dataclass

logger = logging.getLogger("hermes-a2a.bridge")


@dataclass
class TaskRecord:
    """Records the state of a processed task.

    Attributes:
        task_id: Unique A2A task identifier.
        input: Truncated input text (first 200 chars).
        status: Current task state (processing, completed, failed).
        result: Full task result text.
        started_at: Unix timestamp when processing began.
        duration_ms: Processing time in milliseconds.
    """
    task_id: str
    input: str
    status: str = "pending"
    result: str = ""
    started_at: float = 0.0
    duration_ms: float = 0.0


class HermesTaskBridge:
    """Bridges A2A task delegations to Hermes Agent execution.

    Processes incoming tasks by spawning ``hermes chat -q`` in
    one-shot mode. This gives each task a fresh Hermes session
    with full access to memory, skills, and tools.

    The bridge maintains an in-memory task registry for status
    queries and future streaming support.

    Example::

        bridge = HermesTaskBridge()
        result = bridge.process_task("task-1", "Research AI agents")
        # → Returns: "Based on my research, AI agents are..."
    """

    def __init__(self, hermes_timeout: int = 120):
        """Initialize the bridge.

        Args:
            hermes_timeout: Max seconds to wait for each Hermes task.
        """
        self.hermes_timeout = hermes_timeout
        self._tasks: dict[str, TaskRecord] = {}

    def process_task(self, task_id: str, text: str) -> str:
        """Process an A2A task delegation through Hermes Agent.

        Spawns ``hermes chat -q`` as a subprocess, feeds the task
        text as input, and captures the response.

        Args:
            task_id: Unique identifier for this task.
            text: The natural language task to execute.

        Returns:
            The full response text from Hermes Agent.

        Raises:
            RuntimeError: If Hermes subprocess fails or times out.
        """
        record = TaskRecord(
            task_id=task_id,
            input=text[:200],
            status="processing",
            started_at=time.time(),
        )
        self._tasks[task_id] = record

        logger.info("Processing task %s: %s", task_id, text[:100])

        try:
            result = self._run_hermes(text)
            record.status = "completed"
            record.result = result
            record.duration_ms = (time.time() - record.started_at) * 1000
            logger.info(
                "Task %s completed in %.0fms",
                task_id, record.duration_ms,
            )
            return result

        except Exception as e:
            record.status = "failed"
            record.result = str(e)
            record.duration_ms = (time.time() - record.started_at) * 1000
            logger.error("Task %s failed: %s", task_id, e)
            raise

    def _run_hermes(self, text: str) -> str:
        """Execute a task via Hermes CLI one-shot mode.

        Uses ``hermes chat -q`` which returns the response directly.

        Args:
            text: The task prompt to send to Hermes.

        Returns:
            Hermes response text.

        Raises:
            RuntimeError: If the subprocess fails or times out.
        """
        try:
            result = subprocess.run(
                ["hermes", "chat", "-q", text, "--quiet"],
                capture_output=True,
                text=True,
                timeout=self.hermes_timeout,
                env=None,  # Inherit current environment
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError(
                f"Hermes task timed out after {self.hermes_timeout}s"
            )
        except FileNotFoundError:
            raise RuntimeError(
                "Hermes CLI not found. Is 'hermes' installed and in PATH?"
            )

        if result.returncode != 0:
            error_msg = result.stderr.strip() or "Unknown error"
            raise RuntimeError(f"Hermes execution failed: {error_msg}")

        # Strip the session_id line from output if present
        output = result.stdout.strip()
        lines = output.split("\n")
        if lines and lines[0].startswith("session_id:"):
            output = "\n".join(lines[1:]).strip()

        return output

    def get_task_status(self, task_id: str) -> dict:
        """Get the current status of a task.

        Args:
            task_id: The task identifier to query.

        Returns:
            Dict with status, input preview, result, and timing info.
            Returns {"status": "unknown"} if task_id was never seen.
        """
        record = self._tasks.get(task_id)
        if not record:
            return {"status": "unknown"}
        return {
            "status": record.status,
            "input": record.input,
            "result": record.result[:500] if record.result else "",
            "duration_ms": record.duration_ms,
        }

    def get_stats(self) -> dict:
        """Get aggregate bridge statistics.

        Returns:
            Dict with total tasks, completed, failed, and average duration.
        """
        total = len(self._tasks)
        completed = sum(1 for t in self._tasks.values() if t.status == "completed")
        failed = sum(1 for t in self._tasks.values() if t.status == "failed")
        durations = [t.duration_ms for t in self._tasks.values() if t.duration_ms > 0]
        avg_duration = sum(durations) / len(durations) if durations else 0
        return {
            "total_tasks": total,
            "completed": completed,
            "failed": failed,
            "avg_duration_ms": round(avg_duration, 1),
        }
