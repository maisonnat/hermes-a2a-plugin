"""Tests for the A2A client (Hermes → OpenCode delegation)."""

import json
import pytest
from unittest import mock
from hermes_a2a_plugin.a2a_client import (
    A2AClient,
    OpenCodeBridge,
    A2ADirectClient,
    A2A_DELEGATE_SCHEMA,
)


def test_schema_structure():
    """a2a_delegate schema has required fields."""
    assert "name" in A2A_DELEGATE_SCHEMA
    assert "description" in A2A_DELEGATE_SCHEMA
    assert "parameters" in A2A_DELEGATE_SCHEMA
    assert "required" in A2A_DELEGATE_SCHEMA["parameters"]
    assert "task" in A2A_DELEGATE_SCHEMA["parameters"]["required"]


def test_client_defaults():
    """Client initializes with defaults."""
    client = A2AClient()
    assert hasattr(client, "opencode")
    assert hasattr(client, "direct")


def test_client_targets():
    """Client lists available targets."""
    client = A2AClient()
    targets = client.get_targets()
    assert len(targets) >= 2
    names = [t["name"] for t in targets]
    assert "opencode" in names


def test_opencode_bridge_not_found():
    """Bridge handles missing OpenCode CLI."""
    bridge = OpenCodeBridge()
    with mock.patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError()
        result = bridge.execute("test task")
        assert result["status"] == "error"
        assert "not found" in result["message"]


def test_opencode_bridge_timeout():
    """Bridge handles timeout."""
    bridge = OpenCodeBridge(timeout=1)
    import subprocess as sp
    with mock.patch("subprocess.run") as mock_run:
        mock_run.side_effect = sp.TimeoutExpired(cmd="opencode", timeout=1)
        result = bridge.execute("test task")
        assert result["status"] == "error"
        assert "timed out" in result["message"]


def test_opencode_bridge_success():
    """Bridge handles successful execution."""
    bridge = OpenCodeBridge()

    class FakeResult:
        returncode = 0
        stdout = "Task completed successfully"
        stderr = ""

    with mock.patch("subprocess.run", return_value=FakeResult()):
        result = bridge.execute("Implement X")
        assert result["status"] == "completed"
        assert "completed" in result["message"]


def test_opencode_bridge_failure():
    """Bridge handles failed execution."""
    bridge = OpenCodeBridge()

    class FakeResult:
        returncode = 1
        stdout = ""
        stderr = "Some error"

    with mock.patch("subprocess.run", return_value=FakeResult()):
        result = bridge.execute("Implement X")
        assert result["status"] == "error"
        assert "code 1" in result["message"]


def test_direct_client_connection_error():
    """Direct A2A client handles connection failure."""
    client = A2ADirectClient()
    with mock.patch("urllib.request.urlopen") as mock_req:
        import urllib.error
        mock_req.side_effect = urllib.error.URLError(reason="Connection refused")
        result = client.send_task("http://localhost:1", "test")
        assert result["status"] == "error"
        assert "Connection refused" in result["message"]


def test_client_send_unknown_target():
    """Client handles unknown target."""
    client = A2AClient()
    result = client.send("test", target="nonexistent")
    assert result["status"] == "error"
    assert "unknown" in result["message"].lower()


def test_client_test_opencode_not_found():
    """Client test handles missing OpenCode."""
    client = A2AClient()
    with mock.patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError()
        result = client.test_target("opencode")
        assert result["status"] == "error"


def test_client_test_opencode_ok():
    """Client test handles available OpenCode."""
    client = A2AClient()

    class FakeResult:
        returncode = 0
        stdout = "1.14.33\n"
        stderr = ""

    with mock.patch("subprocess.run", return_value=FakeResult()):
        result = client.test_target("opencode")
        assert result["status"] == "ok"
        assert "1.14.33" in result.get("version", "")
