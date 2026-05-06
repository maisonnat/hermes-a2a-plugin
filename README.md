# Hermes A2A Plugin 🔌

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Documentation](https://img.shields.io/badge/docs-mkdocs-blue)](https://maisonnat.github.io/hermes-a2a-plugin/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](pyproject.toml)

> **A Hermes Agent plugin that adds A2A (Agent2Agent) protocol support.**  
> Enables any A2A-compatible agent — OpenCode, Claude Code, Codex, etc. — to discover and delegate tasks to Hermes.

<p align="center">
  <img src="docs/assets/logo.png" alt="Hermes A2A Plugin Logo" width="200"/>
</p>

## ✨ Features

- 🚀 **A2A Server Mode** — Run Hermes as an A2A-compatible server
- 📋 **Agent Card** — Auto-published capabilities for agent discovery
- 🔄 **Task Lifecycle** — Full `submitted → working → completed/failed` state machine
- 📡 **Streaming SSE** — Real-time progress updates via Server-Sent Events
- 🔌 **Zero Config** — Drop-in Hermes plugin, enable and go
- 🔐 **Auth Ready** — Bearer token authentication built-in
- 🧩 **OpenCode Bridge** — Connect OpenCode via MCP-to-A2A bridge

## 🏗️ Architecture

```
┌─────────────────────────┐     A2A Protocol     ┌──────────────────────┐
│    Hermes Agent         │◄──────────────────────│   A2A Client Agent   │
│                         │   JSON-RPC 2.0/SSE    │  (OpenCode / etc.)   │
│  ┌───────────────────┐  │                      │                      │
│  │ A2A Plugin        │──┤                      │  GET /.well-known/   │
│  │  • Agent Card     │  │                      │  POST /tasks/send    │
│  │  • Task Router    │  │                      │  SSE /tasks/stream   │
│  │  • Auth Guard     │  │                      │                      │
│  └───────────────────┘  │                      └──────────────────────┘
└─────────────────────────┘
```

## 🚀 Quick Start

```bash
# 1. Install the plugin
hermes plugins install yourusername/hermes-a2a-plugin

# 2. Enable it
hermes plugins enable hermes-a2a

# 3. Start the A2A server
hermes a2a serve

# 4. OpenCode connects automatically (via MCP bridge)
```

See [Getting Started](docs/getting-started.md) for full instructions.

## 🧩 Hermes Plugin System

This project is a standard [Hermes Agent plugin](https://hermes-agent.nousresearch.com/docs/user-guide/features/plugins/). It uses:

- `plugin.yaml` — Manifest
- `register(ctx)` — Entry point with hooks + tool registration
- Lifecycle hooks: `session_start`, `pre_tool`, `post_tool`
- Custom CLI command: `hermes a2a serve`

## 📦 Project Structure

```
hermes-a2a-plugin/
├── hermes_a2a_plugin/       # Plugin source
│   ├── __init__.py          # register(ctx) entry point
│   ├── plugin.yaml          # Plugin manifest
│   ├── schemas.py           # LLM tool schemas
│   ├── server.py            # A2A HTTP server (Starlette + Uvicorn)
│   └── bridge.py            # A2A → Hermes bridging logic
├── docs/                    # Documentation
├── tests/                   # Test suite
├── mkdocs.yml               # Docs config (Material theme)
└── pyproject.toml           # Python project config
```

## 📖 Documentation

Full documentation: [https://yourusername.github.io/hermes-a2a-plugin/](https://yourusername.github.io/hermes-a2a-plugin/)

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT — see [LICENSE](LICENSE)

## 🙏 Acknowledgments

- [Nous Research](https://nousresearch.com) for [Hermes Agent](https://hermes-agent.nousresearch.com)
- [Google / Linux Foundation](https://github.com/a2aproject/A2A) for the A2A Protocol
- [OpenCode](https://github.com/anomalyco/opencode) for the awesome coding agent
