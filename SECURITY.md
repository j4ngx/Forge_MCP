# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅ |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do not** open a public GitHub issue
2. Email: [j4ngx](https://github.com/j4ngx) via GitHub private message
3. Include a clear description and steps to reproduce

## Security Measures

### MCP Server

- The server runs locally via **stdio** transport — no network exposure
- No credentials or secrets are stored in the codebase
- All user inputs (PR diffs, metadata) are passed through to the LLM without server-side execution
- The server does not execute arbitrary code from PR diffs

### Installer

- Supports `--dry-run` mode to preview all changes before execution
- Lock file prevents concurrent installer executions
- Backs up existing VS Code `mcp.json` before modification
- All downloads use HTTPS
- No credentials are required or stored during installation
