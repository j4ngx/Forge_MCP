# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-02-27

### Added

- **MCP Server** — FastMCP-based server (`server.py`) with stdio transport for VS Code integration
- **`review_pr` tool** — Senior PR reviewer with 9 configurable parameters:
  - `pr_diff` (required), `pr_title`, `pr_description`, `pr_author`, `pr_url`
  - `repo_context`, `severity_scope`, `review_focus`, `detail_level`
- **Prompt-driven architecture** — System prompts loaded from `prompts/*.md` with caching
- **Comprehensive review prompt** — 374-line production prompt covering:
  - GitHub MCP integration (fetch PR data, post review as PR comment)
  - 8-category review checklist (logic, architecture, security, performance, error handling, style, testing, documentation)
  - 7-section structured output format
  - Configurable severity scopes, review focuses, and detail levels
- **TUI Installer** (`installer/install.sh`) — GLaDOS-style interactive installer:
  - ASCII art banner with orange gradient
  - 5-step pipeline: Preflight → Python/uv → MCP Setup → VS Code Config → Verification
  - Unicode box drawing, animated spinners, progress bars, step tracker
  - Plan card with interactive review before proceeding
  - Health-check rows and completion/failure screens
  - Supports `--dry-run`, `--non-interactive`, `--verbose`, `--local`, `--skip-*` flags
- **VS Code configuration** via `.vscode/mcp.json` (stdio transport)
- **Project tooling** — Ruff linting, mypy strict type checking, hatchling build

[0.1.0]: https://github.com/j4ngx/forge_mcp/releases/tag/v0.1.0
