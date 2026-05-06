#!/usr/bin/env python3
"""Auto-generate AI-ready documentation files from project source.

Scans the project and regenerates:
  - llms.txt      — condensed overview for LLMs
  - llms-full.txt — comprehensive single-file context for LLMs
  - AGENTS.md     — structured context for AI coding agents

Run:  python3 scripts/generate_ai_docs.py
Envs: PROJECT_ROOT (default: repo root, auto-detected)
"""

import os
import re
import sys
import tomllib
import yaml
from pathlib import Path
from datetime import datetime

# ── Config ────────────────────────────────────────────────

REPO_ROOT = Path(os.environ.get(
    "PROJECT_ROOT",
    Path(__file__).resolve().parent.parent,
))
PLUGIN_DIR = REPO_ROOT / "hermes_a2a_plugin"
DOCS_DIR = REPO_ROOT / "docs"
TESTS_DIR = REPO_ROOT / "tests"

OUTPUT_FILES = {
    "llms.txt": REPO_ROOT / "llms.txt",
    "llms-full.txt": REPO_ROOT / "llms-full.txt",
    "AGENTS.md": REPO_ROOT / "AGENTS.md",
}


# ── Extractors ────────────────────────────────────────────


def load_pyproject() -> dict:
    """Read pyproject.toml metadata."""
    path = REPO_ROOT / "pyproject.toml"
    if not path.exists():
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)


def load_plugin_yaml() -> dict:
    """Read plugin.yaml manifest."""
    path = PLUGIN_DIR / "plugin.yaml"
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.load(f, Loader=yaml.FullLoader)


def list_modules() -> list[dict]:
    """Scan plugin directory for Python modules."""
    modules = []
    for f in sorted(PLUGIN_DIR.glob("*.py")):
        if f.name.startswith("__"):
            continue
        content = f.read_text()
        docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
        summary = ""
        if docstring_match:
            summary = docstring_match.group(1).strip().split("\n")[0][:120]
        modules.append({
            "name": f.stem,
            "path": str(f.relative_to(REPO_ROOT)),
            "summary": summary,
        })
    return modules


def extract_endpoints() -> list[dict]:
    """Extract HTTP endpoints from server.py."""
    server_py = PLUGIN_DIR / "server.py"
    if not server_py.exists():
        return []
    content = server_py.read_text()
    endpoints = []
    # Match do_GET / do_POST handler patterns + _handle_ methods
    for match in re.finditer(
        r'# ── Endpoint handlers .*?$'
        r'|path\s*==\s*"([^"]+)"'
        r'|def _handle_(\w+)',
        content,
        re.MULTILINE,
    ):
        pass  # We'll do simpler extraction below

    # Simpler: find route patterns in do_GET / do_POST
    for method in ("do_GET", "do_POST"):
        handler_match = re.search(
            rf'def {method}\(self\).*?(?=def do_|\Z)',
            content,
            re.DOTALL,
        )
        if handler_match:
            block = handler_match.group()
            for path_match in re.finditer(
                r'["\'](/[^"\']+)["\']',
                block,
            ):
                path = path_match.group(1)
                endpoint_method = method.replace("do_", "")
                endpoints.append({
                    "method": endpoint_method,
                    "path": path,
                })
    return endpoints


def extract_mcp_tools() -> list[dict]:
    """Extract MCP tool definitions from bridge_mcp.py."""
    mcp_py = PLUGIN_DIR / "bridge_mcp.py"
    if not mcp_py.exists():
        return []
    content = mcp_py.read_text()

    tools = []
    # Match AVAILABLE_TOOLS list entries
    for match in re.finditer(
        r'"name":\s*"([^"]+)".*?"description":\s*"([^"]+)"',
        content,
        re.DOTALL,
    ):
        tools.append({
            "name": match.group(1),
            "description": match.group(2).split(".")[0],
        })
    return tools


def count_tests() -> dict:
    """Count tests in tests/ directory."""
    count = 0
    files = 0
    for f in sorted(TESTS_DIR.glob("test_*.py")):
        content = f.read_text()
        count += len(re.findall(r"^def test_", content, re.MULTILINE))
        files += 1
    return {"files": files, "tests": count}


def extract_changelog() -> str:
    """Get latest changelog entry."""
    path = REPO_ROOT / "CHANGELOG.md"
    if not path.exists():
        return ""
    content = path.read_text()
    # Extract first version block
    match = re.search(
        r"## \[(.*?)\].*?\n(.*?)(?=\n## |\Z)",
        content,
        re.DOTALL,
    )
    if match:
        return f"## [{match.group(1)}]\n{match.group(2).strip()}"
    return ""


def get_nav_structure() -> str:
    """Get MkDocs nav as markdown bullet list."""
    mkdocs_path = REPO_ROOT / "mkdocs.yml"
    if not mkdocs_path.exists():
        return ""
    # Strip !!python/name tags before parsing (MkDocs-specific syntax)
    raw = mkdocs_path.read_text()
    cleaned = re.sub(r"\s+format:\s*!!python/name:\S+\s*\n", "\n", raw)
    config = yaml.safe_load(cleaned)
    nav = config.get("nav", [])

    lines = []
    for item in nav:
        for title, value in item.items():
            if isinstance(value, str):
                lines.append(f"- {title}")
            elif isinstance(value, list):
                lines.append(f"- {title}")
                for sub in value:
                    for stitle, svalue in sub.items():
                        lines.append(f"  - {stitle}")
    return "\n".join(lines)


# ── Generators ────────────────────────────────────────────


def generate_llms_txt(pyproject: dict, plugin: dict, modules: list,
                      endpoints: list, mcp_tools: list, tests: dict) -> str:
    """Generate llms.txt — condensed overview for LLMs."""
    meta = pyproject.get("project", {})
    version = plugin.get("version", meta.get("version", "dev"))
    description = meta.get("description", plugin.get("description", ""))

    tools_list = "\n".join(
        f"  - `{t['name']}` — {t['description']}"
        for t in mcp_tools
    ) if mcp_tools else "  - (none)"

    ep_list = "\n".join(
        f"  - `{e['method']} {e['path']}`"
        for e in endpoints
    ) if endpoints else "  - (none)"

    mod_list = "\n".join(
        f"  - `{m['name']}.py` — {m['summary']}"
        for m in modules
    )

    return f"""# {meta.get('name', 'hermes-a2a-plugin')}

> Auto-generated from source — last updated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}
> Version: {version}
> License: MIT

## Description
{description}

## Project Structure
{mod_list}

## API Endpoints
{ep_list}

## MCP Tools (for OpenCode)
{tools_list}

## Quick Start
```bash
# Enable in Hermes
hermes plugins enable hermes-a2a
# Start server
hermes a2a serve --port 4097
# Test
curl http://localhost:4097/.well-known/agent-card.json
```

## Tests
{tests['tests']} tests across {tests['files']} files

## Documentation
- Site: https://maisonnat.github.io/hermes-a2a-plugin/
- Repo: https://github.com/maisonnat/hermes-a2a-plugin

## Auto-Documentation Pipeline
- MkDocs + mkdocstrings: extracts Google-style docstrings from Python code
- mkdocs-gen-files: auto-discovers new Python files for API reference
- scripts/generate_ai_docs.py: auto-generates this file + AGENTS.md
- GitHub Actions: auto-deploys docs on every push to main
"""


def generate_llms_full(pyproject: dict, plugin: dict, modules: list,
                        endpoints: list, mcp_tools: list, tests: dict,
                        changelog: str, nav: str) -> str:
    """Generate llms-full.txt — comprehensive single-file context."""
    meta = pyproject.get("project", {})
    version = plugin.get("version", meta.get("version", "dev"))
    tools = plugin.get("provides_tools", [])
    hooks = plugin.get("provides_hooks", [])
    commands = plugin.get("provides_commands", [])

    ep_table = "\n".join(
        f"| {e['method']} | {e['path']} |"
        for e in endpoints
    ) if endpoints else "| - | - |"

    mcp_table = "\n".join(
        f"| `{t['name']}` | {t['description']} |"
        for t in mcp_tools
    ) if mcp_tools else "| - | - |"

    return f"""# Hermes A2A Plugin — Full Context for LLMs

> Auto-generated from source — last updated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}
> Version: {version}

## Project Identity
- **Name**: {meta.get('name', 'hermes-a2a-plugin')}
- **Description**: {meta.get('description', plugin.get('description', ''))}
- **Version**: {version}
- **License**: MIT
- **Python**: {meta.get('requires-python', '>=3.10')}
- **Repository**: https://github.com/maisonnat/hermes-a2a-plugin
- **Documentation**: https://maisonnat.github.io/hermes-a2a-plugin/

## Plugin Manifest (plugin.yaml)
- **Tools**: {', '.join(f'`{t}`' for t in tools)}
- **Hooks**: {', '.join(f'`{h}`' for h in hooks)}
- **CLI Commands**: `hermes {"` · `hermes ".join(c for c in commands)}`

## Python Modules
{chr(10).join(f'- **{m["name"]}.py** — {m["summary"]}' for m in modules)}

## HTTP API Endpoints
| Method | Path |
|--------|------|
{ep_table}

## MCP Tools for OpenCode
| Tool | Description |
|------|-------------|
{mcp_table}

## A2A vs ACP
- **A2A** (Agent2Agent): Google → Linux Foundation, universal agent communication.
  JSON-RPC 2.0 over HTTP, Agent Cards for discovery, task lifecycle.
- **ACP** (Agent Client Protocol): Zed/JetBrains, IDE ↔ Agent communication.
  JSON-RPC 2.0 over stdio. Used by `hermes acp`. DIFFERENT protocol.

## A2A Task Lifecycle
```
submitted → working → completed
                |          |
                ├──→ input-required → working → ...
                |          |
                └──→ failed
                cancelled (any state)
```

## Site Navigation
{nav}

## Tests
- **Total**: {tests['tests']} tests across {tests['files']} files
- **Run**: `make test` or `python -m pytest tests/ -v`

## Latest Changelog
{changelog}

## Quick Commands
```bash
# Local
pip install -e .
make test
mkdocs build --strict
mkdocs serve

# Hermes
hermes plugins enable hermes-a2a
hermes a2a serve --port 4097

# Test server
curl http://localhost:4097/health
curl http://localhost:4097/.well-known/agent-card.json
curl -X POST http://localhost:4097/tasks/send \\
  -H "Content-Type: application/json" \\
  -d '{{"jsonrpc":"2.0","id":1,"params":{{"id":"t","message":{{"role":"user","parts":[{{"text":"hi"}}]}}}}}}'
```

## Key Files
- `hermes_a2a_plugin/__init__.py` — Plugin entry point (register, hooks, tools, CLI)
- `hermes_a2a_plugin/plugin.yaml` — Plugin manifest
- `hermes_a2a_plugin/server.py` — A2A HTTP server
- `hermes_a2a_plugin/bridge.py` — Real Hermes bridge
- `hermes_a2a_plugin/bridge_mcp.py` — MCP bridge for OpenCode
- `hermes_a2a_plugin/schemas.py` — LLM tool schemas
- `docs/` — MkDocs documentation
- `tests/` — pytest tests

## Dependencies
{chr(10).join(f'- `{d}`' for d in meta.get('dependencies', ['(none)']))}

## Dev Dependencies
{chr(10).join(f'- `{d}`' for d in meta.get('optional-dependencies', {}).get('dev', ['(none)']))}
"""


def generate_agents_md(pyproject: dict, plugin: dict, modules: list,
                        tests: dict) -> str:
    """Generate AGENTS.md — context for AI coding agents."""
    meta = pyproject.get("project", {})
    version = plugin.get("version", meta.get("version", "dev"))
    tools = plugin.get("provides_tools", [])
    hooks = plugin.get("provides_hooks", [])
    commands = plugin.get("provides_commands", [])

    mod_table = "\n".join(
        f"| `{m['name']}.py` | {m['summary']} |"
        for m in modules
    )

    return f"""# Hermes A2A Plugin — Agent Context

> Auto-generated from source — last updated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}
> Project version: {version}

## Project Identity
- Name: {meta.get('name', 'hermes-a2a-plugin')}
- License: MIT
- Python: {meta.get('requires-python', '>=3.10')}
- Type: Hermes Agent Plugin (Python)
- Repo: github.com/maisonnat/hermes-a2a-plugin

## Key Architecture Rules
1. **Plugin = Python package** in `hermes_a2a_plugin/` with `plugin.yaml`
2. **Entry point**: `register(ctx)` in `__init__.py`
3. **Server**: Built-in `http.server` (zero deps), can upgrade to Starlette + Uvicorn
4. **A2A protocol**: JSON-RPC 2.0 over HTTP, Agent Card at /.well-known/
5. **Not ACP**: This is A2A (Agent2Agent), NOT ACP (Agent Client Protocol for IDEs)

## Plugin Tools
{chr(10).join(f'- `hermes {t}`' for t in tools) if tools else '- (none)'}

## Hooks
{chr(10).join(f'- `{h}`' for h in hooks) if hooks else '- (none)'}

## CLI Commands
- `hermes {"`\n- `hermes ".join(c for c in commands)}`

## File Ownership
| File | Purpose |
|------|---------|
{mod_table}
| `docs/*` | MkDocs documentation |
| `tests/*` | pytest tests |
| `scripts/generate_ai_docs.py` | Auto-generates AI docs |

## Conventions
- Docstrings: Google style (for mkdocstrings auto-generation)
- Tests: pytest + pytest-asyncio
- Commits: conventional commits (feat:, fix:, docs:, chore:)
- Type hints: always include
- Auto-generated files: DO NOT edit llms.txt, llms-full.txt, AGENTS.md manually
  They are regenerated by `scripts/generate_ai_docs.py`

## Dev Commands
```bash
cd ~/Projects/hermes-a2a-plugin
source .venv/bin/activate
make install           # pip install -e .
make test              # pytest -v ({tests['tests']} tests)
make docs              # mkdocs build --strict
make serve-docs        # mkdocs serve
make lint              # ruff check
python3 scripts/generate_ai_docs.py   # Regenerate AI docs
```

## Related Skills (Hermes Agent)
- `hermes-agent` — Core Hermes configuration and CLI
- `a2a-plugin-dev` — This project's development workflow
- `auto-docs-pipeline` — Auto-generate project documentation
- `opencode` — OpenCode-specific delegation patterns
"""


# ── Main ──────────────────────────────────────────────────


def main():
    """Run all extractors and generators, write output files."""

    # Extract
    pyproject = load_pyproject()
    plugin = load_plugin_yaml()
    modules = list_modules()
    endpoints = extract_endpoints()
    mcp_tools = extract_mcp_tools()
    tests = count_tests()
    changelog = extract_changelog()
    nav = get_nav_structure()

    # Generate
    outputs = {
        "llms.txt": generate_llms_txt(
            pyproject, plugin, modules, endpoints, mcp_tools, tests,
        ),
        "llms-full.txt": generate_llms_full(
            pyproject, plugin, modules, endpoints, mcp_tools, tests,
            changelog, nav,
        ),
        "AGENTS.md": generate_agents_md(
            pyproject, plugin, modules, tests,
        ),
    }

    # Write
    written = []
    for name, content in outputs.items():
        path = OUTPUT_FILES[name]
        path.write_text(content)
        size = len(content.encode("utf-8"))
        written.append(f"  ✅ {name} ({size:,} bytes)")

    print("📝 AI documentation files regenerated:")
    print("\n".join(written))
    print(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")


if __name__ == "__main__":
    main()
