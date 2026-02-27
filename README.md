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

- 🔨 **`review_pr`** — Feeds a Git diff through a production-quality senior-reviewer system prompt and returns a structured Markdown review covering code quality, architecture, security, performance, testing, and documentation.
- 📝 **Prompt-driven architecture** — Every tool loads its system prompt from a dedicated Markdown file under `prompts/`, making prompts easy to iterate on without touching code.
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
│   └── PULL_REQUEST_TEMPLATE.md
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
│   └── review_pr.md              # System prompt for the PR reviewer
├── tools/
│   ├── __init__.py
│   └── review_pr.py              # review_pr tool definition
├── utils/
│   ├── __init__.py
│   └── prompt_loader.py          # Reusable prompt-loading utility
├── server.py                     # FastMCP server entrypoint
├── pyproject.toml                # Project metadata & dependencies
├── uv.lock                       # Reproducible dependency lock
├── .gitignore
├── .gitattributes
├── .editorconfig
├── .tool-versions                # asdf version pinning (ivm-uv)
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
uv run ruff check .

# Auto-fix
uv run ruff check . --fix

# Format
uv run ruff format .

# Type-check
uv run mypy .

# Test installer (dry-run)
bash installer/install.sh --dry-run --verbose
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

[MIT](LICENSE) © 2026 j4ngx
