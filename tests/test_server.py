"""Unit tests for the FastMCP server entrypoint (server.py).

Validates that server.py correctly creates the FastMCP instance,
delegates to the DI container, and exposes the main() entrypoint.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestServerModule:
    """Tests for server.py module-level behaviour."""

    def test_mcp_instance_exists(self) -> None:
        """The module exposes a FastMCP 'mcp' instance."""
        import server

        assert hasattr(server, "mcp")
        assert server.mcp.name == "forge_mcp"

    def test_mcp_has_registered_tools(self) -> None:
        """The mcp instance has all 5 tools registered at import time."""
        import server

        tool_names = {t.name for t in server.mcp._tool_manager.list_tools()}
        expected = {"review_pr", "apply_issue", "scaffold_project", "progressive_commit", "create_pr"}
        assert tool_names == expected

    def test_main_function_exists_and_callable(self) -> None:
        """server.main() exists and is callable."""
        import server

        assert callable(server.main)

    @patch("server.mcp")
    def test_main_calls_run_with_stdio(self, mock_mcp: MagicMock) -> None:
        """main() calls mcp.run(transport='stdio')."""
        import server

        server.main()

        mock_mcp.run.assert_called_once_with(transport="stdio")
