"""Shared fixtures for forge_mcp test suite."""

from __future__ import annotations

import pytest
from mcp.server.fastmcp import FastMCP


@pytest.fixture()
def fastmcp_server() -> FastMCP:
    """Return a fresh FastMCP instance for testing tool registration."""
    return FastMCP(name="test_forge_mcp")
