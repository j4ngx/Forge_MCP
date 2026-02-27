# Contributing to forge_mcp

Thank you for your interest in contributing! This guide will help you get started.

## Development Setup

```bash
# Clone the repository
git clone https://github.com/j4ngx/forge_mcp.git
cd forge_mcp

# Install dependencies
uv sync

# Run the server
uv run server.py
```

### Prerequisites

- Python ≥ 3.11
- [uv](https://docs.astral.sh/uv/) (latest)
- VS Code ≥ 1.96 (for testing MCP integration)

## Code Quality

Before submitting changes, run the following checks:

```bash
# Lint
uv run ruff check .

# Auto-fix lint issues
uv run ruff check . --fix

# Format
uv run ruff format .

# Type-check
uv run mypy .
```

## Adding a New Tool

1. **Create a prompt** — Add `prompts/<tool_name>.md` with the full system prompt
2. **Create a tool module** — Add `tools/<tool_name>.py` following the pattern in `tools/review_pr.py`
3. **Register in server** — Import and register the tool in `server.py`
4. **Test** — Verify the tool loads correctly and returns expected output

## Installer Development

The installer lives in `installer/` and follows a modular shell architecture:

| Module | Purpose |
|--------|---------|
| `lib/common.sh` | Constants, logging, OS detection, utilities |
| `lib/tui.sh` | TUI rendering (boxes, spinners, banners, etc.) |
| `lib/preflight.sh` | System requirement checks |
| `lib/python.sh` | Python & uv installation |
| `lib/vscode.sh` | VS Code mcp.json configuration |
| `lib/mcp.sh` | Clone/sync MCP server, verify startup |
| `install.sh` | Main entrypoint orchestrating all steps |

### Shell Coding Standards

- Use `set -euo pipefail` strict mode
- Quote all variables: `"$var"` not `$var`
- Use `[[ ]]` for conditionals (not `[ ]`)
- Source guards: `[[ -n "${_MODULE_LOADED:-}" ]] && return 0`
- Functions: `snake_case`, constants: `UPPER_SNAKE_CASE`
- Test with: `bash installer/install.sh --dry-run --verbose`

## Commit Messages

Follow **Conventional Commits** format with gitmoji:

```
<type>[scope]: <gitmoji> <description>
```

Examples:

```
feat(tools): ✨ add generate_docs tool
fix(installer): 🐛 fix spinner cleanup on macOS
docs: 📝 update README with new flags
```

## Pull Requests

1. Create a feature branch from `main`
2. Make your changes and ensure all checks pass
3. Write a clear PR description with context
4. Request a review

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
