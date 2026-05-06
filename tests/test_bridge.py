"""Tests for the MCP bridge and real Hermes task bridge."""

import json
import pytest
from unittest import mock
from hermes_a2a_plugin.bridge import HermesTaskBridge


def test_bridge_initialization():
    """Bridge initializes with default timeout."""
    bridge = HermesTaskBridge()
    assert bridge.hermes_timeout == 120
    assert bridge.get_stats()["total_tasks"] == 0


def test_bridge_get_task_unknown():
    """Unknown tasks return unknown status."""
    bridge = HermesTaskBridge()
    status = bridge.get_task_status("nonexistent")
    assert status["status"] == "unknown"


def test_bridge_get_stats_empty():
    """Empty bridge returns zero stats."""
    bridge = HermesTaskBridge()
    stats = bridge.get_stats()
    assert stats["total_tasks"] == 0
    assert stats["completed"] == 0
    assert stats["failed"] == 0


def test_bridge_get_hermes_not_found():
    """Running Hermes when CLI not found returns error."""
    bridge = HermesTaskBridge()
    with mock.patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError()
        with pytest.raises(RuntimeError, match="Hermes CLI not found"):
            bridge.process_task("test-1", "Hello")


def test_bridge_get_hermes_timeout():
    """Running Hermes when CLI times out returns error."""
    bridge = HermesTaskBridge()
    with mock.patch("subprocess.run") as mock_run:
        import subprocess as sp
        mock_run.side_effect = sp.TimeoutExpired(cmd="hermes", timeout=120)

        with pytest.raises(RuntimeError, match="timed out"):
            bridge.process_task("test-2", "Do something")


def test_bridge_hermes_response_no_session_id():
    """Bridge strips session_id from Hermes output."""
    bridge = HermesTaskBridge()

    class FakeResult:
        returncode = 0
        stdout = "session_id: abc123\nHello, world!"
        stderr = ""

    with mock.patch("subprocess.run", return_value=FakeResult()):
        result = bridge.process_task("test-3", "Hi")
        assert result == "Hello, world!"


def test_mcp_initialize():
    """MCP bridge handles initialize."""
    from hermes_a2a_plugin.bridge_mcp import handle_initialize

    result = handle_initialize({})
    assert "capabilities" in result
    assert "serverInfo" in result
    assert result["serverInfo"]["name"] == "hermes-a2a-mcp-bridge"


def test_mcp_tools_list():
    """MCP bridge returns tool definitions."""
    from hermes_a2a_plugin.bridge_mcp import handle_tools_list, AVAILABLE_TOOLS

    result = handle_tools_list({})
    assert "tools" in result
    assert len(result["tools"]) == len(AVAILABLE_TOOLS)
    tool_names = [t["name"] for t in result["tools"]]
    assert "hermes_delegate" in tool_names
    assert "hermes_research" in tool_names
    assert "hermes_status" in tool_names


def test_mcp_tools_call_unknown():
    """MCP bridge returns error for unknown tools."""
    from hermes_a2a_plugin.bridge_mcp import handle_tools_call

    result = handle_tools_call({"name": "unknown_tool", "arguments": {}})
    assert result.get("isError") is True
    assert "unknown_tool" in result["content"][0]["text"]


def test_mcp_tools_call_status():
    """MCP bridge status tool calls Hermes."""
    from hermes_a2a_plugin.bridge_mcp import _call_hermes_status

    with mock.patch("subprocess.run") as mock_run:
        class FakeResult:
            returncode = 0
            stdout = "session_id: x\nOK"
            stderr = ""

        mock_run.return_value = FakeResult()
        result = _call_hermes_status({})
        assert "available" in result.lower()


def test_mcp_delegate_missing_task():
    """Delegate tool errors on missing task arg."""
    from hermes_a2a_plugin.bridge_mcp import _call_hermes_delegate

    result = _call_hermes_delegate({})
    assert "required" in result
