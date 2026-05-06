"""Basic tests for the A2A plugin."""

import json
import pytest
from unittest import mock
from hermes_a2a_plugin.server import A2AServer, AGENT_CARD


def test_agent_card_structure():
    """Agent Card has required fields."""
    assert "name" in AGENT_CARD
    assert "description" in AGENT_CARD
    assert "version" in AGENT_CARD
    assert "capabilities" in AGENT_CARD
    assert "skills" in AGENT_CARD
    assert len(AGENT_CARD["skills"]) > 0


def test_agent_card_skill():
    """Each skill has required fields."""
    for skill in AGENT_CARD["skills"]:
        assert "id" in skill
        assert "name" in skill
        assert "description" in skill
        assert "tags" in skill
        assert "input_modes" in skill
        assert "output_modes" in skill


def test_server_init():
    """Server initializes with defaults."""
    server = A2AServer()
    assert server.host == "127.0.0.1"
    assert server.port == 4097
    assert server.auth_token == ""
    assert server.is_running is False


def test_server_custom_port():
    """Server accepts custom port."""
    server = A2AServer(port=8080, auth_token="test-token")
    assert server.port == 8080
    assert server.auth_token == "test-token"
