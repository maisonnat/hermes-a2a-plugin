# Hermes A2A Plugin — Agent Context

This file helps AI coding agents understand this project when working on it.

## Project Identity
- Name: hermes-a2a-plugin
- License: MIT
- Python: 3.10+
- Type: Hermes Agent Plugin (Python)
- Repo: github.com/maisonnat/hermes-a2a-plugin

## Key Architecture Rules
1. **Plugin = Python package** in `hermes_a2a_plugin/` with `plugin.yaml`
2. **Entry point**: `register(ctx)` in `__init__.py`
3. **Server**: Built-in `http.server` (zero deps), can upgrade to Starlette+Uvicorn
4. **A2A protocol**: JSON-RPC 2.0 over HTTP, Agent Card at /.well-known/
5. **Not ACP**: This is A2A (Agent2Agent), NOT ACP (Agent Client Protocol for IDEs)

## File Ownership
- `__init__.py` — Plugin registration, hooks, tools, CLI commands
- `plugin.yaml` — Manifest (modify when adding tools/hooks)
- `schemas.py` — LLM tool schemas (what the model sees to call tools)
- `server.py` — HTTP server, A2A endpoints, Agent Card
- `bridge.py` — Task processing, A2A → Hermes mapping
- `bridge_mcp.py` — MCP server for OpenCode integration
- `docs/*` — MkDocs documentation
- `tests/*` — pytest tests

## Conventions
- Docstrings: Google style (for mkdocstrings auto-generation)
- Tests: pytest + pytest-asyncio
- Commits: conventional commits (feat:, fix:, docs:, chore:)
- Type hints: always include
- License: MIT header in new files

## Dev Commands
```bash
cd ~/Projects/hermes-a2a-plugin
source .venv/bin/activate
make install      # pip install -e .
make test         # pytest -v
make docs         # mkdocs build
make serve-docs   # mkdocs serve (http://localhost:8000)
make lint         # ruff check
```
