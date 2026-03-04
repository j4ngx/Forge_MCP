"""forge_mcp — FastMCP server entrypoint.

This module creates the :class:`FastMCP` server instance, delegates tool
registration to the dependency-injection container, and exposes the
``main()`` function used by the ``[project.scripts]`` console entrypoint.

Usage (stdio transport for VS Code Copilot Agent Mode)::

    uv run server.py
"""

import logging
import sys

from mcp.server.fastmcp import FastMCP

from container import build_tool_registry

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

# ── Server instance ──────────────────────────────────────────────────────────
mcp = FastMCP(
    name="forge_mcp",
    instructions=(
        "forge_mcp is a collection of developer-productivity tools exposed "
        "via the Model Context Protocol. Use the available tools to review "
        "pull requests, generate documentation, write tests, and more."
    ),
)

# ── Tool registration (via dependency injection) ────────────────────────────
build_tool_registry().register_all(mcp)


# ── Entrypoint ───────────────────────────────────────────────────────────────


def main() -> None:
    """Run the MCP server using stdio transport."""
    logger.info("Starting forge_mcp server (stdio transport)…")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
