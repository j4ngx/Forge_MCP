# forge_mcp

A **Model Context Protocol (MCP)** server exposing developer-productivity tools — starting with a **senior PR reviewer** — designed for use inside **VS Code** via **GitHub Copilot Agent Mode**.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python ≥ 3.11](https://img.shields.io/badge/Python-≥3.11-blue.svg)](https://www.python.org/)

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
  - [Automated (Recommended)](#automated-recommended)
  - [Manual](#manual)
- [VS Code Integration](#vs-code-integration)
- [Usage](#usage)
- [Tools Reference](#tools-reference)
- [Adding a New Tool](#adding-a-new-tool)
- [Project Structure](#project-structure)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## Features

- 🔨 **`review_pr`** — Senior-level PR reviewer returning structured Markdown reviews covering code quality, architecture, security, performance, testing, and documentation.
- 🔍 **Code Quality** — `analyze_code`, `suggest_type_hints`, `explain_code` — static analysis, type-hint suggestions, and code explanations adapted to audience level.
- 📝 **Documentation** — `generate_docstrings`, `generate_module_doc`, `generate_changelog_entry` — automated docstrings (Google/NumPy/Sphinx), module documentation, and changelog entries.
- 🧪 **Testing** — `generate_unit_tests`, `generate_test_fixtures`, `suggest_test_cases` — pytest test generation with Polyfactory support, fixture scaffolding, and test-plan enumeration.
- ♻️ **Refactoring** — `suggest_refactoring`, `modernize_python`, `decompose_function` — refactoring suggestions, Python 3.11+ modernisation, and function decomposition.
- 📄 **Prompt-driven architecture** — Every tool loads its system prompt from a dedicated Markdown file under `prompts/`, making prompts easy to iterate on without touching code.
- 🚀 **TUI Installer** — GLaDOS-style interactive installer with ASCII art, progress tracking, and health checks.
- ⚡ **Easily extensible** — Add new tools by dropping a prompt and a thin Python module.
- 🛡 **GitHub MCP integration** — The review prompt instructs the agent to fetch PR data and post reviews as PR comments via GitHub MCP tools.

## Quick Start

```bash
# Clone & install in one command
git clone https://github.com/j4ngx/forge_mcp.git
cd forge_mcp && bash installer/install.sh --local
```

## Installation

### Platform Support

| Platform | Status | Package Manager |
|----------|--------|-----------------|
| **macOS** (Apple Silicon / Intel) | ✅ Fully supported | Homebrew |
| **Linux** (Debian / Ubuntu) | ✅ Fully supported | apt-get |
| **Linux** (Fedora / RHEL) | ✅ Supported | dnf |
| **Linux** (Arch) | ✅ Supported | pacman |

### Automated (Recommended)

The TUI installer handles everything: Python, uv, dependencies, and VS Code configuration.

```bash
bash installer/install.sh
```

#### Installer Options

| Flag | Description |
|------|-------------|
| `--local` | Use local source instead of cloning from GitHub |
| `--dry-run` | Preview all actions without executing |
| `--non-interactive` | Run with defaults, no prompts (CI-friendly) |
| `--verbose`, `-v` | Enable debug output |
| `--skip-python` | Skip Python installation check |
| `--skip-uv` | Skip uv installation check |
| `--skip-vscode` | Skip VS Code mcp.json configuration |
| `--skip-mcp` | Skip MCP server setup |
| `--dir PATH` | Override install directory |
| `--help`, `-h` | Show help |

#### What the Installer Does

1. **Pre-flight** — Checks OS, Python, uv, Git, VS Code, disk space, network
2. **Python & uv** — Installs Python ≥ 3.11 and uv if missing
3. **MCP Server** — Clones the repo (or uses local), runs `uv sync`
4. **VS Code** — Adds the `forge_mcp` server entry to your User `mcp.json`
5. **Verification** — Health-checks that the server imports and mcp.json is configured

### Manual

```bash
# Clone the repository
git clone https://github.com/j4ngx/forge_mcp.git
cd forge_mcp

# Install dependencies
uv sync

# (Optional) Configure VS Code — copy to your User settings
cp .vscode/mcp.json ~/Library/Application\ Support/Code/User/mcp.json
```

## VS Code Integration

The project ships with a `.vscode/mcp.json` that registers the server using **stdio** transport:

```jsonc
{
  "servers": {
    "forge_mcp": {
      "type": "stdio",
      "command": "uv",
      "args": ["--directory", "/path/to/forge_mcp", "run", "server.py"]
    }
  }
}
```

1. Open VS Code.
2. The MCP server is detected automatically from your User `mcp.json`.
3. Open **Copilot Chat** in **Agent Mode** — the `review_pr` tool appears in the tool list.

> **Note:** The installer writes the server entry to your **User-level** `mcp.json` so the tool is available in any workspace.

## Usage

In Copilot Agent Mode, ask the agent to review a PR:

> *Review this PR diff for issues:*
> *(paste your diff or let the agent fetch it via GitHub MCP)*

The agent will invoke the `review_pr` tool and return a structured review with:

- **Summary** — What the PR does, overall assessment
- **Critical Issues** — Blockers with exact code references
- **Suggestions** — Improvements grouped by category
- **Security Notes** — Vulnerabilities or concerns
- **Testing Recommendations** — Missing or inadequate tests
- **Positive Highlights** — Well-written code worth noting
- **Verdict** — APPROVE, REQUEST_CHANGES, or COMMENT

## Tools Reference

### `review_pr`

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `pr_diff` | `str` | ✅ | — | The Git diff to review |
| `pr_title` | `str` | ❌ | `""` | PR title for context |
| `pr_description` | `str` | ❌ | `""` | PR description / body |
| `pr_author` | `str` | ❌ | `""` | Author username |
| `pr_url` | `str` | ❌ | `""` | URL to the PR |
| `repo_context` | `str` | ❌ | `""` | Tech stack, conventions, etc. |
| `severity_scope` | `str` | ❌ | `"all"` | `blockers_only` \| `blockers_and_major` \| `all` |
| `review_focus` | `str` | ❌ | `"balanced"` | `logic` \| `performance` \| `security` \| `style` \| `balanced` |
| `detail_level` | `str` | ❌ | `"thorough"` | `summary` \| `thorough` |

### Code Quality

#### `analyze_code`

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `code` | `str` | ✅ | — | Python source code to analyze |
| `file_path` | `str` | ❌ | `""` | Path of the file (context) |
| `analysis_focus` | `str` | ❌ | `"all"` | `all` \| `complexity` \| `smells` \| `security` \| `style` |
| `detail_level` | `str` | ❌ | `"standard"` | `brief` \| `standard` \| `verbose` |

#### `suggest_type_hints`

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `code` | `str` | ✅ | — | Python source code |
| `file_path` | `str` | ❌ | `""` | Path of the file (context) |
| `strictness` | `str` | ❌ | `"strict"` | `basic` \| `strict` \| `complete` |
| `include_return_types` | `bool` | ❌ | `True` | Include return-type suggestions |

#### `explain_code`

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `code` | `str` | ✅ | — | Python source code to explain |
| `file_path` | `str` | ❌ | `""` | Path of the file (context) |
| `audience` | `str` | ❌ | `"mid"` | `junior` \| `mid` \| `senior` |
| `explain_focus` | `str` | ❌ | `"overview"` | `overview` \| `flow` \| `complexity` \| `dependencies` |

### Documentation

#### `generate_docstrings`

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `code` | `str` | ✅ | — | Python source code to document |
| `file_path` | `str` | ❌ | `""` | Path of the file (context) |
| `docstring_style` | `str` | ❌ | `"google"` | `google` \| `numpy` \| `sphinx` |
| `include_examples` | `bool` | ❌ | `True` | Include usage examples |
| `include_raises` | `bool` | ❌ | `True` | Include Raises sections |

#### `generate_module_doc`

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `code` | `str` | ✅ | — | Python module source code |
| `module_name` | `str` | ❌ | `""` | Module name for the header |
| `doc_sections` | `str` | ❌ | `"overview,usage,api"` | Comma-separated: `overview` \| `usage` \| `api` \| `examples` |
| `target_audience` | `str` | ❌ | `"both"` | `user` \| `developer` \| `both` |

#### `generate_changelog_entry`

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `changes` | `str` | ✅ | — | Diff, commits, or description |
| `version` | `str` | ❌ | `""` | Semantic version (e.g., `"1.2.0"`) |
| `change_type` | `str` | ❌ | `"auto"` | `auto` \| `added` \| `changed` \| `deprecated` \| `removed` \| `fixed` \| `security` |
| `project_context` | `str` | ❌ | `""` | Additional project context |

### Testing

#### `generate_unit_tests`

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `code` | `str` | ✅ | — | Python source code to test |
| `file_path` | `str` | ❌ | `""` | Path of the source file |
| `test_framework` | `str` | ❌ | `"pytest"` | `pytest` (only supported) |
| `use_polyfactory` | `bool` | ❌ | `True` | Generate Polyfactory factories |
| `coverage_focus` | `str` | ❌ | `"comprehensive"` | `happy_path` \| `edge_cases` \| `errors` \| `comprehensive` |

#### `generate_test_fixtures`

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `code` | `str` | ✅ | — | Python source code |
| `models_code` | `str` | ❌ | `""` | Model definitions (Pydantic, etc.) |
| `file_path` | `str` | ❌ | `""` | Path of the source file |
| `fixture_scope` | `str` | ❌ | `"function"` | `function` \| `class` \| `module` \| `session` |
| `include_factories` | `bool` | ❌ | `True` | Generate Polyfactory factories |

#### `suggest_test_cases`

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `code` | `str` | ✅ | — | Python source code to analyze |
| `file_path` | `str` | ❌ | `""` | Path of the source file |
| `test_depth` | `str` | ❌ | `"thorough"` | `basic` \| `thorough` \| `exhaustive` |
| `include_integration` | `bool` | ❌ | `False` | Include integration test suggestions |

### Refactoring

#### `suggest_refactoring`

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `code` | `str` | ✅ | — | Python source code |
| `file_path` | `str` | ❌ | `""` | Path of the file |
| `refactor_goals` | `str` | ❌ | `"all"` | `readability` \| `performance` \| `maintainability` \| `testability` \| `all` |
| `max_suggestions` | `int` | ❌ | `10` | Max suggestions (1–50) |

#### `modernize_python`

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `code` | `str` | ✅ | — | Python source code |
| `file_path` | `str` | ❌ | `""` | Path of the file |
| `min_python_version` | `str` | ❌ | `"3.11"` | `3.11` \| `3.12` \| `3.13` |
| `aggressive` | `bool` | ❌ | `False` | Include structural rewrites |

#### `decompose_function`

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `code` | `str` | ✅ | — | Source code containing the function |
| `function_name` | `str` | ❌ | `""` | Function to decompose (auto-detects largest) |
| `file_path` | `str` | ❌ | `""` | Path of the source file |
| `max_lines_per_function` | `int` | ❌ | `30` | Target max lines (10–100) |
| `decomposition_strategy` | `str` | ❌ | `"extract_method"` | `extract_method` \| `strategy_pattern` \| `pipeline` |

## Adding a New Tool

1. **Create the prompt** — Add `prompts/<tool_name>.md`
2. **Create the tool module** — Add `tools/<tool_name>.py`:

```python
"""MCP tool: <tool_name>."""

import logging
from utils.prompt_loader import load_prompt_cached

logger = logging.getLogger(__name__)

PROMPT_FILENAME: str = "<tool_name>.md"
TOOL_NAME: str = "<tool_name>"
TOOL_DESCRIPTION: str = "Short description of what the tool does."

_SYSTEM_PROMPT: str = load_prompt_cached(PROMPT_FILENAME)


def my_tool(input_param: str) -> str:
    """Process the input."""
    if not input_param or not input_param.strip():
        raise ValueError("input_param must not be empty.")
    return f"{_SYSTEM_PROMPT}\n\n---\n\n{input_param}"
```

3. **Register in `server.py`** — Import and add a `@mcp.tool()` handler
4. **Test** — `uv run python -c "from tools.<tool_name> import my_tool; print(my_tool('test'))"`

## Project Structure

```
forge_mcp/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── workflows/
│       ├── ci.yml                # Lint, type-check, smoke-test
│       ├── installer-test.yml    # Installer dry-run on macOS & Ubuntu
│       └── release.yml           # Build & publish GitHub Release
├── .vscode/
│   └── mcp.json                  # VS Code MCP server config (stdio)
├── installer/
│   ├── install.sh                # TUI installer entrypoint
│   └── lib/
│       ├── common.sh             # Constants, logging, OS detection
│       ├── tui.sh                # Box drawing, spinners, banners
│       ├── preflight.sh          # System requirement checks
│       ├── python.sh             # Python & uv installation
│       ├── vscode.sh             # VS Code mcp.json configuration
│       └── mcp.sh                # MCP server clone/sync/verify
├── prompts/
│   ├── review_pr.md              # System prompt: PR reviewer
│   ├── analyze_code.md           # System prompt: code analysis
│   ├── suggest_type_hints.md     # System prompt: type-hint suggestions
│   ├── explain_code.md           # System prompt: code explanations
│   ├── generate_docstrings.md    # System prompt: docstring generation
│   ├── generate_module_doc.md    # System prompt: module documentation
│   ├── generate_changelog_entry.md # System prompt: changelog entries
│   ├── generate_unit_tests.md    # System prompt: unit-test generation
│   ├── generate_test_fixtures.md # System prompt: fixture scaffolding
│   ├── suggest_test_cases.md     # System prompt: test-case planning
│   ├── suggest_refactoring.md    # System prompt: refactoring ideas
│   ├── modernize_python.md       # System prompt: Python modernisation
│   └── decompose_function.md     # System prompt: function decomposition
├── tools/
│   ├── __init__.py
│   ├── review_pr.py              # review_pr tool definition
│   ├── analyze_code.py           # analyze_code tool
│   ├── suggest_type_hints.py     # suggest_type_hints tool
│   ├── explain_code.py           # explain_code tool
│   ├── generate_docstrings.py    # generate_docstrings tool
│   ├── generate_module_doc.py    # generate_module_doc tool
│   ├── generate_changelog_entry.py # generate_changelog_entry tool
│   ├── generate_unit_tests.py    # generate_unit_tests tool
│   ├── generate_test_fixtures.py # generate_test_fixtures tool
│   ├── suggest_test_cases.py     # suggest_test_cases tool
│   ├── suggest_refactoring.py    # suggest_refactoring tool
│   ├── modernize_python.py       # modernize_python tool
│   └── decompose_function.py     # decompose_function tool
├── utils/
│   ├── __init__.py
│   └── prompt_loader.py          # Reusable prompt-loading utility
├── server.py                     # FastMCP server entrypoint
├── pyproject.toml                # Project metadata & dependencies
├── uv.lock                       # Reproducible dependency lock
├── .gitignore
├── .gitattributes
├── .editorconfig
├── .tool-versions                # Version pinning comment
├── CHANGELOG.md
├── CONTRIBUTING.md
├── SECURITY.md
├── LICENSE
└── README.md
```

## Development

```bash
# Run the server manually (stdio)
uv run server.py

# Lint
uvx ruff check .

# Auto-fix
uvx ruff check . --fix

# Format
uvx ruff format .

# Type-check
uvx mypy .

# Test installer (dry-run, macOS)
bash installer/install.sh --dry-run --verbose

# Test installer (dry-run, Linux)
bash installer/install.sh --dry-run --non-interactive --verbose
```

## CI/CD

Three GitHub Actions workflows run automatically:

| Workflow | Trigger | What it does |
|----------|---------|--------------|
| **CI** (`ci.yml`) | Push / PR to `main` | Ruff lint & format check, mypy strict, smoke-test on Python 3.11–3.13 |
| **Installer Test** (`installer-test.yml`) | Changes to `installer/**` | Dry-run installer on macOS & Ubuntu, ShellCheck lint |
| **Release** (`release.yml`) | Tag push `v*` | Quality gate → build wheel/sdist → create GitHub Release with artifacts |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

[MIT](LICENSE) © 2026 j4ngx
