# API Reference

The API reference is **auto-generated** from Python docstrings using `mkdocstrings`.
Extracted from the `hermes_a2a_plugin` package.

## Plugin Entry Point

::: hermes_a2a_plugin
    handler: python
    options:
      show_root_heading: true
      show_source: true
      members:
        - register
        - handle_a2a_serve
        - handle_a2a_status
        - handle_a2a_stop

## Server

::: hermes_a2a_plugin.server
    handler: python
    options:
      show_root_heading: true
      show_source: true
      members:
        - A2AServer
        - A2ARequestHandler

## Bridge

::: hermes_a2a_plugin.bridge
    handler: python
    options:
      show_root_heading: true
      show_source: true
      members:
        - HermesTaskBridge
        - TaskRecord

## MCP Bridge

::: hermes_a2a_plugin.bridge_mcp
    handler: python
    options:
      show_root_heading: true
      show_source: true

## Tool Schemas

::: hermes_a2a_plugin.schemas
    handler: python
    options:
      show_root_heading: true
      show_source: true
