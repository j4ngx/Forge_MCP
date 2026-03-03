# forge_mcp

A **Model Context Protocol (MCP)** server exposing developer-productivity tools designed for use inside **VS Code** via **GitHub Copilot Agent Mode**.

## Features

| Tool | Description |
|------|-------------|
| **`review_pr`** | Senior-level Python PR code review. Accepts a Git diff and optional metadata, returns a structured Markdown review covering logic, design, security, performance, testing, readability, and integration. |
| **`apply_issue`** | End-to-end GitHub issue implementation. Creates a branch via `gh buddy`, proposes an action plan with a **mandatory approval gate**, implements the solution, self-reviews using `review_pr`, and creates a PR. |
| **`scaffold_project`** | Generate a complete hexagonal-architecture Python project on disk. Accepts entity names and creates domain models, repository ports, services, use cases, mappers, ORM entities, controllers, DI modules, REST stubs, and tests — supporting both AMIGA and generic (vanilla FastAPI) stacks. |

**Architecture highlights:**

- Prompt-driven — each tool loads its system prompt from a dedicated Markdown file under `prompts/`.
- GitHub MCP integration — `apply_issue` relies on `mcp_github_issue_read` for issue fetching.
- Easily extensible — add new tools by dropping a prompt and a thin Python module.

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | ≥ 3.11 | |
| [uv](https://docs.astral.sh/uv/) | latest | Package manager & runner |
| VS Code | ≥ 1.96 | |
| GitHub Copilot Chat extension | latest | Agent Mode required |
| [`gh` CLI](https://cli.github.com/) | latest | Authenticated (`gh auth login`) |
| [`gh buddy`](https://github.com/jesusgpo/gh-buddy) | latest | `gh extension install jesusgpo/gh-buddy` |

## Installation

```bash
# Clone the repository
git clone https://github.com/j4ngx/forge_mcp.git
cd forge_mcp

# Install dependencies
uv sync
```

## VS Code Integration

The project ships with a `.vscode/mcp.json` that registers the server using **stdio** transport:

```jsonc
{
  "servers": {
    "forge_mcp": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "server.py"]
    }
  }
}
```

1. Open the `forge_mcp` folder in VS Code.
2. The MCP server will be detected automatically via `.vscode/mcp.json`.
3. Open **Copilot Chat** in **Agent Mode** — both `review_pr` and `apply_issue` tools will be available.

## Usage

### Review a PR

In Copilot Agent Mode, ask the agent to review a PR:

> *Review this PR diff for issues:*
> *(paste your diff or let the agent fetch it)*

The agent will invoke the `review_pr` tool and return a structured review with **Summary**, **Critical Issues**, **Suggestions**, and **Positive Highlights**.

### Implement a GitHub Issue

Ask the agent to implement an issue:

> *Implement this issue: https://github.com/owner/repo/issues/42*

The agent will:

1. Fetch the issue details via `mcp_github_issue_read`.
2. Call `apply_issue` which creates a branch via `gh buddy` and checks it out.
3. Propose a detailed **action plan** and **wait for your approval** (⛔ mandatory gate).
4. Implement the changes following the plan.
5. Self-review using the `review_pr` tool.
6. Fix any issues found and create the PR via `gh buddy create-pr`.

### Scaffold a Hexagonal Project

Ask the agent to scaffold a new project:

> *Scaffold a new hexagonal project called "inventory" with entities Product, Category, Warehouse*

The agent will invoke the `scaffold_project` tool and generate the full directory structure under `code/` with boilerplate for all layers (domain, application, infrastructure, REST, tests).

You can also specify the stack and database:

> *Scaffold project "billing" with entities Invoice, Payment using the amiga stack and mariadb*

## Adding a New Tool

1. **Create a prompt** — Add `prompts/<tool_name>.md` with the full system prompt.
2. **Create a tool module** — Add `tools/<tool_name>.py` following the pattern in `tools/review_pr.py` or `tools/apply_issue.py`.
3. **Register in server** — Import and register the tool in `server.py` with the `@mcp.tool()` decorator.
4. **Test** — Verify the tool loads correctly: `python -c "from server import mcp; print('OK')"`.

## Project Structure

```
forge_mcp/
├── docs/
│   └── hexagonal-architecture.md  # Canonical hexagonal architecture reference
├── prompts/
│   ├── apply_issue.md        # System prompt for the issue implementation tool
│   ├── review_pr.md          # System prompt for the PR reviewer tool
│   └── scaffold_project.md   # System prompt for the project scaffolder tool
├── tools/
│   ├── __init__.py
│   ├── apply_issue.py        # Tool: end-to-end issue implementation
│   ├── review_pr.py          # Tool: senior PR code reviewer
│   └── scaffold_project.py   # Tool: hexagonal project scaffolder
├── utils/
│   ├── __init__.py
│   └── prompt_loader.py      # Reusable prompt-loading utility with caching
├── installer/
│   ├── install.sh            # GLaDOS-style TUI installer
│   └── lib/                  # Modular shell library (common, tui, python, etc.)
├── server.py                 # FastMCP server entrypoint
├── pyproject.toml            # Project metadata and dependencies (uv)
├── .vscode/
│   └── mcp.json              # VS Code MCP server configuration (stdio)
├── CHANGELOG.md
├── CONTRIBUTING.md
└── README.md
```

## Development

```bash
# Run the server manually (stdio)
uv run server.py

# Lint
uv run ruff check .

# Auto-fix lint issues
uv run ruff check . --fix

# Format
uv run ruff format .

# Type-check
uv run mypy .
```

## License

MIT
