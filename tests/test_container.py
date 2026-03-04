"""Unit tests for the dependency-injection container (container.py).

Covers ToolDefinition, ToolRegistry, error-wrapper behaviour, and the
build_tool_registry() composition root.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from container import ToolDefinition, ToolRegistry, _build_error_wrapper, build_tool_registry

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

# ═══════════════════════════════════════════════════════════════════════════════
# ToolDefinition
# ═══════════════════════════════════════════════════════════════════════════════


class TestToolDefinition:
    """Tests for the ToolDefinition dataclass."""

    def test_create_with_required_fields(self) -> None:
        """ToolDefinition can be created with only required fields."""
        handler = MagicMock(return_value="ok")
        td = ToolDefinition(name="my_tool", description="A tool", handler=handler)

        assert td.name == "my_tool"
        assert td.description == "A tool"
        assert td.handler is handler
        assert td.error_handlers == ()

    def test_create_with_error_handlers(self) -> None:
        """ToolDefinition stores error_handlers when provided."""
        handler = MagicMock(return_value="ok")
        error_handlers = ((ValueError, "val error"), (RuntimeError, "rt error"))
        td = ToolDefinition(
            name="my_tool",
            description="A tool",
            handler=handler,
            error_handlers=error_handlers,
        )

        assert len(td.error_handlers) == 2
        assert td.error_handlers[0] == (ValueError, "val error")

    def test_is_frozen(self) -> None:
        """ToolDefinition is immutable (frozen dataclass)."""
        handler = MagicMock(return_value="ok")
        td = ToolDefinition(name="my_tool", description="A tool", handler=handler)

        with pytest.raises(AttributeError):
            td.name = "changed"  # type: ignore[misc]


# ═══════════════════════════════════════════════════════════════════════════════
# ToolRegistry
# ═══════════════════════════════════════════════════════════════════════════════


class TestToolRegistry:
    """Tests for the ToolRegistry class."""

    def test_empty_registry(self) -> None:
        """A new registry starts with zero tools."""
        registry = ToolRegistry()

        assert registry.tool_count == 0

    def test_add_single_tool(self) -> None:
        """Adding one tool increments the count."""
        registry = ToolRegistry()
        td = ToolDefinition(name="t1", description="d1", handler=MagicMock(return_value="ok"))

        registry.add(td)

        assert registry.tool_count == 1

    def test_add_returns_self_for_chaining(self) -> None:
        """add() returns the registry instance for fluent API."""
        registry = ToolRegistry()
        td = ToolDefinition(name="t1", description="d1", handler=MagicMock(return_value="ok"))

        result = registry.add(td)

        assert result is registry

    def test_fluent_chaining(self) -> None:
        """Multiple tools can be added via fluent chaining."""
        registry = ToolRegistry()
        td1 = ToolDefinition(name="t1", description="d1", handler=MagicMock(return_value="ok"))
        td2 = ToolDefinition(name="t2", description="d2", handler=MagicMock(return_value="ok"))

        registry.add(td1).add(td2)

        assert registry.tool_count == 2

    def test_register_all_calls_server_tool(self, fastmcp_server: FastMCP) -> None:
        """register_all() registers each tool on the FastMCP server."""
        handler = MagicMock(return_value="result")
        registry = ToolRegistry()
        registry.add(ToolDefinition(name="test_tool", description="desc", handler=handler))

        registry.register_all(fastmcp_server)

        # Verify the tool is registered (FastMCP stores tools internally)
        tool_names = [t.name for t in fastmcp_server._tool_manager.list_tools()]
        assert "test_tool" in tool_names

    def test_register_all_multiple_tools(self, fastmcp_server: FastMCP) -> None:
        """register_all() registers all tools from the registry."""
        registry = ToolRegistry()
        for i in range(3):
            registry.add(
                ToolDefinition(
                    name=f"tool_{i}",
                    description=f"desc_{i}",
                    handler=MagicMock(return_value=f"r{i}"),
                )
            )

        registry.register_all(fastmcp_server)

        tool_names = [t.name for t in fastmcp_server._tool_manager.list_tools()]
        assert "tool_0" in tool_names
        assert "tool_1" in tool_names
        assert "tool_2" in tool_names

    def test_register_all_empty_registry(self, fastmcp_server: FastMCP) -> None:
        """register_all() on an empty registry does not fail."""
        registry = ToolRegistry()

        registry.register_all(fastmcp_server)

        assert registry.tool_count == 0


# ═══════════════════════════════════════════════════════════════════════════════
# _build_error_wrapper
# ═══════════════════════════════════════════════════════════════════════════════


class TestBuildErrorWrapper:
    """Tests for the error-wrapper factory function."""

    def test_success_passes_through(self) -> None:
        """When the handler succeeds, the wrapper returns its result."""
        handler = MagicMock(return_value="success")
        td = ToolDefinition(name="t", description="d", handler=handler)

        wrapped = _build_error_wrapper(td)
        result = wrapped("arg1", key="val")

        assert result == "success"
        handler.assert_called_once_with("arg1", key="val")

    def test_known_exception_returns_error_string(self) -> None:
        """Known exceptions produce 'Error: ...' messages."""
        handler = MagicMock(side_effect=ValueError("bad input"))
        td = ToolDefinition(
            name="t",
            description="d",
            handler=handler,
            error_handlers=((ValueError, "val error"),),
        )

        wrapped = _build_error_wrapper(td)
        result = wrapped()

        assert result.startswith("Error:")
        assert "bad input" in result

    def test_known_exception_first_match_wins(self) -> None:
        """When multiple error handlers match, the first one wins."""
        handler = MagicMock(side_effect=ValueError("oops"))
        td = ToolDefinition(
            name="t",
            description="d",
            handler=handler,
            error_handlers=(
                (ValueError, "first match"),
                (Exception, "second match"),
            ),
        )

        wrapped = _build_error_wrapper(td)
        result = wrapped()

        assert result == "Error: oops"

    def test_unknown_exception_returns_unexpected_error(self) -> None:
        """Unmatched exceptions produce 'An unexpected error...' messages."""
        handler = MagicMock(side_effect=TypeError("type fail"))
        td = ToolDefinition(
            name="my_tool",
            description="d",
            handler=handler,
            error_handlers=((ValueError, "val error"),),
        )

        wrapped = _build_error_wrapper(td)
        result = wrapped()

        assert "unexpected error" in result.lower()
        assert "my_tool" in result
        assert "type fail" in result

    def test_known_exception_logs_error(self, caplog: pytest.LogCaptureFixture) -> None:
        """Known exceptions are logged at ERROR level."""
        handler = MagicMock(side_effect=RuntimeError("rt issue"))
        td = ToolDefinition(
            name="t",
            description="d",
            handler=handler,
            error_handlers=((RuntimeError, "runtime problem"),),
        )

        wrapped = _build_error_wrapper(td)
        with caplog.at_level(logging.ERROR, logger="container"):
            wrapped()

        assert "runtime problem" in caplog.text
        assert "rt issue" in caplog.text

    def test_unknown_exception_logs_exception(self, caplog: pytest.LogCaptureFixture) -> None:
        """Unknown exceptions are logged via logger.exception (with traceback)."""
        handler = MagicMock(side_effect=KeyError("missing"))
        td = ToolDefinition(
            name="my_tool",
            description="d",
            handler=handler,
            error_handlers=(),
        )

        wrapped = _build_error_wrapper(td)
        with caplog.at_level(logging.ERROR, logger="container"):
            wrapped()

        assert "Unexpected error in my_tool" in caplog.text

    def test_wrapper_preserves_function_name(self) -> None:
        """The wrapper preserves the original handler's __name__."""

        def my_handler() -> str:
            return "ok"

        td = ToolDefinition(name="t", description="d", handler=my_handler)
        wrapped = _build_error_wrapper(td)

        assert wrapped.__name__ == "my_handler"

    def test_no_error_handlers_all_exceptions_generic(self) -> None:
        """With empty error_handlers, any exception hits the generic catch-all."""
        handler = MagicMock(side_effect=ValueError("v"))
        td = ToolDefinition(name="t", description="d", handler=handler, error_handlers=())

        wrapped = _build_error_wrapper(td)
        result = wrapped()

        assert "unexpected error" in result.lower()


# ═══════════════════════════════════════════════════════════════════════════════
# build_tool_registry (integration)
# ═══════════════════════════════════════════════════════════════════════════════


class TestBuildToolRegistry:
    """Integration tests for the composition root."""

    def test_returns_registry_with_five_tools(self) -> None:
        """build_tool_registry() produces a registry with exactly 5 tools."""
        registry = build_tool_registry()

        assert registry.tool_count == 5

    def test_register_all_on_fastmcp(self, fastmcp_server: FastMCP) -> None:
        """All 5 tools register successfully on a FastMCP server."""
        registry = build_tool_registry()

        registry.register_all(fastmcp_server)

        tool_names = {t.name for t in fastmcp_server._tool_manager.list_tools()}
        expected = {"review_pr", "apply_issue", "scaffold_project", "progressive_commit", "create_pr"}
        assert tool_names == expected

    def test_tool_names_match_module_constants(self) -> None:
        """Registered names match the TOOL_NAME constants in each module."""
        from tools.apply_issue import TOOL_NAME as APPLY
        from tools.create_pr import TOOL_NAME as CREATE
        from tools.progressive_commit import TOOL_NAME as COMMIT
        from tools.review_pr import TOOL_NAME as REVIEW
        from tools.scaffold_project import TOOL_NAME as SCAFFOLD

        registry = build_tool_registry()
        registered_names = {td.name for td in registry._tools}

        assert registered_names == {APPLY, CREATE, COMMIT, REVIEW, SCAFFOLD}

    def test_tool_descriptions_are_non_empty(self) -> None:
        """Every registered tool has a non-empty description."""
        registry = build_tool_registry()

        for td in registry._tools:
            assert td.description, f"Tool '{td.name}' has empty description"
            assert len(td.description) > 20, f"Tool '{td.name}' description is too short"

    def test_tool_handlers_are_callable(self) -> None:
        """Every registered tool handler is callable."""
        registry = build_tool_registry()

        for td in registry._tools:
            assert callable(td.handler), f"Tool '{td.name}' handler is not callable"

    def test_each_tool_has_error_handlers(self) -> None:
        """Every registered tool has at least one error handler defined."""
        registry = build_tool_registry()

        for td in registry._tools:
            assert len(td.error_handlers) >= 1, f"Tool '{td.name}' should have at least one error handler"
