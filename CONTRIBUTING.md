# Contributing to Hermes A2A Plugin

Thanks for your interest in contributing! 🎉

## How to Contribute

1. **Fork** the repo
2. **Create a feature branch**: `git checkout -b feat/my-feature`
3. **Make your changes**
4. **Run tests**: `make test` (pytest)
5. **Check lint**: `make lint` (ruff)
6. **Build docs**: `make docs` (mkdocs build --strict)
7. **Commit** using [conventional commits](https://www.conventionalcommits.org/)
8. **Push** and open a **Pull Request**

## Development Setup

```bash
# Clone
git clone https://github.com/maisonnat/hermes-a2a-plugin.git
cd hermes-a2a-plugin

# Create venv + install
python3 -m venv .venv
source .venv/bin/activate
make install-dev

# Run tests
make test

# Build docs
make docs

# Serve docs locally
make serve-docs
# → http://localhost:8000
```

## Code Style

- **Python**: Follow PEP 8, use type hints
- **Docstrings**: Google style (required for auto-generated API docs)
- **Tests**: pytest + pytest-asyncio, mock external calls
- **Commits**: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`

## Project Structure

```
hermes_a2a_plugin/    # Plugin source
├── __init__.py       # Entry point — register() + hooks + tools + CLI
├── plugin.yaml       # Plugin manifest
├── server.py         # A2A HTTP server
├── bridge.py         # Real bridge (Hermes subprocess)
└── bridge_mcp.py     # MCP bridge (OpenCode)
docs/                 # MkDocs documentation
tests/                # pytest tests
```

## Pull Request Guidelines

- Keep PRs focused — one feature/fix per PR
- Add tests for new functionality
- Update docs if behavior changes
- Ensure `mkdocs build --strict` passes (0 warnings)
- Reference any related issues

## Code of Conduct

Be respectful and constructive. This is a small open-source project — help us make it great.

## Questions?

Open a [Discussion](https://github.com/maisonnat/hermes-a2a-plugin/discussions) or an [Issue](https://github.com/maisonnat/hermes-a2a-plugin/issues).
