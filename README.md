# Hermes A2A Plugin 🔌

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Docs](https://img.shields.io/badge/docs-mkdocs-blue)](https://maisonnat.github.io/hermes-a2a-plugin/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](pyproject.toml)
[![Tests](https://img.shields.io/badge/tests-15/15-success)](tests/)
[![LLMs](https://img.shields.io/badge/llms.txt-✓-8A2BE2)](llms.txt)
[![Agent Context](https://img.shields.io/badge/AGENTS.md-✓-8A2BE2)](AGENTS.md)

> **A Hermes Agent plugin that adds A2A (Agent2Agent) protocol support.**  
> Enables any A2A-compatible agent — OpenCode, Claude Code, Codex, etc. — to discover and delegate tasks to Hermes.

<p align="center">
  <img src="docs/assets/logo.png" alt="Hermes A2A Plugin Logo" width="200"/>
</p>

## ✨ Features

- 🚀 **A2A Server Mode** — Run Hermes as an A2A-compatible server
- 📋 **Agent Card** — Auto-published capabilities at `/.well-known/agent-card.json`
- 🔄 **Task Lifecycle** — Full `submitted → working → completed/failed` state machine
- 🔗 **Real Hermes Bridge** — Tasks execute via `hermes chat -q` with full memory + tools
- 🧩 **OpenCode MCP Bridge** — OpenCode discovers Hermes as native MCP tools
- 🔌 **Zero Config** — Drop-in Hermes plugin (`plugin.yaml` + `register(ctx)`)
- 🔐 **Auth Ready** — Bearer token authentication
- 📡 **Streaming SSE** — Real-time progress updates

## 📚 Documentation for Humans *and* AI Agents

This project is designed to be understood by **both humans and AI coding agents**:

| File | For | Description |
|------|-----|-------------|
| [llms.txt](llms.txt) | 🤖 LLMs | Curated project overview — structure, concepts, API reference |
| [llms-full.txt](llms-full.txt) | 🤖 LLMs | Full documentation in one file for deep LLM comprehension |
| [AGENTS.md](AGENTS.md) | 🤖 Coding Agents | File ownership, architecture rules, dev commands |
| [MkDocs Site](https://maisonnat.github.io/hermes-a2a-plugin/) | 👤 Humans | Beautiful docs with search, auto-generated API reference |
| [API Reference](docs/api/reference.md) | 👤🤖 Auto-generated | Extracted from Python docstrings via `mkdocstrings` |

### 🔄 Auto-Documentation Pipeline

```yaml
# .github/workflows/docs.yml — on every push to main:
# 1. pip install mkdocs-material mkdocstrings mkdocs-gen-files
# 2. mkdocs gh-deploy --force         → https://maisonnat.github.io/hermes-a2a-plugin/
#
# mkdocstrings extracts Google-style docstrings from Python code
# mkdocs-gen-files scans for new .py files automatically
# → API docs update themselves on every push
```

## 🏗️ Architecture

```
┌────────────────────────────┐    A2A Protocol     ┌───────────────────────┐
│       Hermes Agent         │◄──────────────────────│   A2A Client Agent    │
│                            │  JSON-RPC 2.0 + SSE   │  (OpenCode / Claude   │
│  ┌──────────────────────┐  │                       │   Code / Codex)       │
│  │  A2A Plugin          │──┤                       │                       │
│  │  ┌────────────────┐  │  │                       │  GET /.well-known/    │
│  │  │ Agent Card     │  │  │                       │  POST /tasks/send     │
│  │  │ Task Router    │  │  │                       │  SSE /tasks/stream    │
│  │  │ Auth Guard     │  │  │                       │                       │
│  │  └────────────────┘  │  │                       └───────────┬───────────┘
│  │  ┌────────────────┐  │  │                                   │
│  │  │ Real Bridge    │──┼──┤  subprocess: hermes chat -q       │
│  │  │ (hermes chat)  │  │  │                                   │
│  │  └────────────────┘  │  │                       ┌───────────┴───────────┐
│  │  ┌────────────────┐  │  │                       │  MCP Bridge           │
│  │  │ MCP Bridge     │──┼──┤  stdio/JSON-RPC 2.0   │  (OpenCode via        │
│  │  │ (for OpenCode) │  │  │                       │   opencode.jsonc)     │
│  │  └────────────────┘  │  │                       └───────────────────────┘
│  └──────────────────────┘  │
└────────────────────────────┘
```

## 🚀 Quick Start

```bash
# 1. Install the plugin
hermes plugins install maisonnat/hermes-a2a-plugin

# 2. Enable it
hermes plugins enable hermes-a2a

# 3. Start the A2A server
hermes a2a serve

# 4. From another terminal, test it:
curl http://localhost:4097/.well-known/agent-card.json
```

See [Getting Started](docs/getting-started.md) for full instructions.

### Connect OpenCode

Add to your `~/.opencode/opencode.jsonc`:

```json
{
  "mcpServers": {
    "hermes-a2a": {
      "command": "python3",
      "args": ["-m", "hermes_a2a_plugin.bridge_mcp"]
    }
  }
}
```

Now OpenCode can use `hermes_delegate`, `hermes_research`, and `hermes_status` tools.

## 🧩 Hermes Plugin System

This project is a standard [Hermes Agent plugin](https://hermes-agent.nousresearch.com/docs/user-guide/features/plugins/). It uses:

- `plugin.yaml` — Manifest declaring tools, hooks, and CLI commands
- `register(ctx)` — Entry point that registers everything
- Lifecycle hooks: `session_start`, `session_end`, `pre_tool`, `post_tool`
- Custom CLI command: `hermes a2a serve`
- LLM-callable tools: `a2a_serve`, `a2a_status`, `a2a_stop`

## 📦 Project Structure

```
hermes-a2a-plugin/
├── hermes_a2a_plugin/       # Plugin source
│   ├── __init__.py          # register(ctx) — entry point + hooks + CLI
│   ├── plugin.yaml          # Plugin manifest
│   ├── schemas.py           # LLM tool schemas
│   ├── server.py            # A2A HTTP server (built-in http.server)
│   ├── bridge.py            # Real bridge — A2A → hermes chat -q
│   └── bridge_mcp.py        # MCP server — OpenCode discovers Hermes tools
├── docs/                    # MkDocs documentation site
│   ├── assets/logo.png      # Project logo
│   ├── research/            # SDK research docs
│   ├── scripts/             # Auto-generation scripts
│   └── guides/              # Usage, config, OpenCode integration
├── tests/                   # 15 pytest tests
│   ├── test_plugin.py       # Plugin + server tests
│   └── test_bridge.py       # Bridge + MCP tests
├── llms.txt                 # 🤖 LLM-optimized project overview
├── llms-full.txt            # 🤖 Full documentation for LLMs
├── AGENTS.md                # 🤖 Context for coding agents
├── mkdocs.yml               # Docs config (Material theme)
├── .github/workflows/       # CI/CD — auto-deploy docs on push
├── pyproject.toml           # Python project config
└── LICENSE                  # MIT
```

## 🔄 Auto-Documentation Pipeline

Every push to `main` triggers:

```yaml
# .github/workflows/docs.yml
on: push → branches: [main]
steps:
  - pip install mkdocs-material mkdocstrings mkdocs-gen-files
  - mkdocs gh-deploy --force  # → GitHub Pages
```

**`mkdocstrings`** extracts Google-style docstrings from the Python source
**`mkdocs-gen-files`** auto-discovers new Python files
→ **API docs regenerate themselves on every push**

## 📖 Documentation

| Resource | Link |
|----------|------|
| 📖 Full Docs Site | [maisonnat.github.io/hermes-a2a-plugin](https://maisonnat.github.io/hermes-a2a-plugin/) |
| 🤖 LLM Context | [llms.txt](llms.txt) · [llms-full.txt](llms-full.txt) |
| 🤖 Agent Context | [AGENTS.md](AGENTS.md) |
| 🧪 Tests | `make test` — 15/15 passing |

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch
3. Run `make test` and `make lint`
4. Submit a PR

See [AGENTS.md](AGENTS.md) for architecture rules and conventions.

## 📄 License

MIT — see [LICENSE](LICENSE)

## 🙏 Acknowledgments

- [Nous Research](https://nousresearch.com) for [Hermes Agent](https://hermes-agent.nousresearch.com)
- [Google / Linux Foundation](https://github.com/a2aproject/A2A) for the A2A Protocol
- [OpenCode](https://github.com/anomalyco/opencode) for the awesome coding agent
