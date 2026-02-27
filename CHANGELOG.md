# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-02-28

### Added

- **`analyze_code`** — Static analysis tool reporting complexity, code smells, security issues, and style violations
- **`suggest_type_hints`** — Suggests type annotations for Python code with configurable strictness
- **`explain_code`** — Explains Python code adapted to audience level (junior/mid/senior)
- **`generate_docstrings`** — Generates Google/NumPy/Sphinx-style docstrings with examples and Raises sections
- **`generate_module_doc`** — Produces comprehensive module-level documentation in Markdown
- **`generate_changelog_entry`** — Creates Keep a Changelog-formatted entries from diffs or descriptions
- **`generate_unit_tests`** — Generates pytest test files with Polyfactory support and configurable coverage focus
- **`generate_test_fixtures`** — Scaffolds conftest.py fixtures and Polyfactory factories
- **`suggest_test_cases`** — Enumerates prioritised test cases without writing test code
- **`suggest_refactoring`** — Proposes refactoring opportunities with before/after code snippets
- **`modernize_python`** — Suggests Python 3.11+/3.12/3.13 modern idioms and patterns
- **`decompose_function`** — Decomposes complex functions via extract-method, strategy-pattern, or pipeline strategies
- **CI workflow** (`ci.yml`) — Ruff lint/format, mypy strict, smoke-test on Python 3.11–3.13
- **Installer test workflow** (`installer-test.yml`) — Dry-run on macOS & Ubuntu matrix, ShellCheck lint
- **Release workflow** (`release.yml`) — Quality gate → build → GitHub Release with wheel/sdist artifacts

### Changed

- Replaced Inditex-internal `ivm-uv` with standard community `uv` across `.tool-versions`, installer, and documentation

### Improved

- **Linux installer** — Added `sudo` password warning before `apt-get`/`dnf` calls, added `python3-dev`/`python3-devel` to install list
- **Flatpak VS Code** — Installer now detects Flatpak VS Code installations (`~/.var/app/com.visualstudio.code/`)
- **Disk check** — Simplified `preflight_check_disk()` by removing redundant OS branching

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

[0.2.0]: https://github.com/j4ngx/forge_mcp/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/j4ngx/forge_mcp/releases/tag/v0.1.0
