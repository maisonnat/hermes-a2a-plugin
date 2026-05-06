# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] — 2026-05-06

### Added
- 🚀 A2A server using built-in `http.server` (zero external dependencies)
- 📋 Agent Card publication at `/.well-known/agent-card.json`
- 🔄 JSON-RPC 2.0 task handling via `POST /tasks/send`
- 🧩 Hermes plugin system integration (`plugin.yaml` + `register(ctx)`)
- 🔗 Real bridge: A2A tasks → `hermes chat -q` subprocess
- 🧠 MCP bridge for OpenCode (3 tools: `hermes_delegate`, `hermes_research`, `hermes_status`)
- 🔐 Bearer token authentication support
- 📡 CORS headers for cross-origin requests
- 📖 MkDocs documentation site with Material theme
- 🤖 LLM-friendly docs (`llms.txt`, `llms-full.txt`, `AGENTS.md`)
- 🔄 Auto-documentation pipeline (mkdocstrings + GitHub Actions)
- 🧪 15 pytest tests (plugin, server, bridge, MCP bridge)
- 🎨 Logo and branding assets
- 📄 MIT License
