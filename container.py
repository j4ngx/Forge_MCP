"""Dependency-injection container for forge_mcp.

Provides a centralised :class:`ToolRegistry` that automates the
registration of MCP tools on a :class:`FastMCP` server instance,
eliminating boilerplate wrapper functions and standardising error-handling.

Usage::

    from container import build_tool_registry

    mcp = FastMCP(name="forge_mcp", ...)
    build_tool_registry().register_all(mcp)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from functools import wraps
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)


# ── Data model ───────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    """Immutable descriptor for a single MCP tool.

    Attributes:
        name: Unique tool identifier registered with FastMCP.
        description: Human-readable description shown to LLM consumers.
        handler: The callable that implements the tool logic.
        error_handlers: Ordered sequence of ``(exception_type, log_prefix)``
            tuples.  The first matching entry wins; unmatched exceptions
            fall through to a generic catch-all that logs the full traceback.
    """

    name: str
    description: str
    handler: Callable[..., str]
    error_handlers: tuple[tuple[type[Exception], str], ...] = field(default_factory=tuple)


# ── Registry ─────────────────────────────────────────────────────────────────


class ToolRegistry:
    """Centralised registry that wires MCP tools to a FastMCP server.

    Example::

        registry = ToolRegistry()
        registry.add(ToolDefinition(
            name="review_pr",
            description="...",
            handler=review_pr,
            error_handlers=((ValueError, "review_pr validation error"),),
        ))
        registry.register_all(mcp)
    """

    def __init__(self) -> None:
        """Initialise an empty registry."""
        self._tools: list[ToolDefinition] = []

    def add(self, definition: ToolDefinition) -> ToolRegistry:
        """Append a tool definition.  Returns *self* for fluent chaining."""
        self._tools.append(definition)
        return self

    def register_all(self, server: FastMCP) -> None:
        """Register every collected tool on *server*.

        For each :class:`ToolDefinition` a thin error-handling wrapper is
        built (preserving the original function signature via
        :func:`functools.wraps`) and registered using ``server.tool()``.

        Args:
            server: The running :class:`FastMCP` instance.
        """
        for tool_def in self._tools:
            wrapped = _build_error_wrapper(tool_def)
            server.tool(name=tool_def.name, description=tool_def.description)(wrapped)
            logger.info("Registered tool: %s", tool_def.name)

        logger.info("Total tools registered: %d", len(self._tools))

    @property
    def tool_count(self) -> int:
        """Number of queued tool definitions."""
        return len(self._tools)


# ── Private helpers ──────────────────────────────────────────────────────────


def _build_error_wrapper(tool_def: ToolDefinition) -> Callable[..., str]:
    """Create a wrapper that preserves the handler's signature and adds error handling."""

    @wraps(tool_def.handler)
    def _wrapper(*args: object, **kwargs: object) -> str:
        try:
            return tool_def.handler(*args, **kwargs)
        except Exception as exc:
            for exc_type, log_prefix in tool_def.error_handlers:
                if isinstance(exc, exc_type):
                    logger.error("%s: %s", log_prefix, exc)
                    return f"Error: {exc}"
            logger.exception("Unexpected error in %s", tool_def.name)
            return f"An unexpected error occurred in {tool_def.name}: {exc}"

    return _wrapper


# ── Composition root ─────────────────────────────────────────────────────────


def build_tool_registry() -> ToolRegistry:
    """Construct the complete :class:`ToolRegistry` with all available tools.

    This is the **composition root** of the application: every tool module
    is imported here and wired into a single registry instance.

    Returns:
        A fully-populated :class:`ToolRegistry` ready for
        :meth:`ToolRegistry.register_all`.
    """
    # Imports at function scope keep the module importable without
    # triggering side-effects until explicitly called.
    from tools.apply_issue import TOOL_DESCRIPTION as APPLY_ISSUE_DESC
    from tools.apply_issue import TOOL_NAME as APPLY_ISSUE_NAME
    from tools.apply_issue import apply_issue
    from tools.create_pr import TOOL_DESCRIPTION as CREATE_PR_DESC
    from tools.create_pr import TOOL_NAME as CREATE_PR_NAME
    from tools.create_pr import create_pr
    from tools.progressive_commit import TOOL_DESCRIPTION as COMMIT_DESC
    from tools.progressive_commit import TOOL_NAME as COMMIT_NAME
    from tools.progressive_commit import progressive_commit
    from tools.review_pr import TOOL_DESCRIPTION as REVIEW_PR_DESC
    from tools.review_pr import TOOL_NAME as REVIEW_PR_NAME
    from tools.review_pr import review_pr
    from tools.scaffold_project import TOOL_DESCRIPTION as SCAFFOLD_DESC
    from tools.scaffold_project import TOOL_NAME as SCAFFOLD_NAME
    from tools.scaffold_project import scaffold_project

    registry = ToolRegistry()

    registry.add(
        ToolDefinition(
            name=REVIEW_PR_NAME,
            description=REVIEW_PR_DESC,
            handler=review_pr,
            error_handlers=((ValueError, "review_pr validation error"),),
        )
    )

    registry.add(
        ToolDefinition(
            name=APPLY_ISSUE_NAME,
            description=APPLY_ISSUE_DESC,
            handler=apply_issue,
            error_handlers=(
                (ValueError, "apply_issue validation error"),
                (RuntimeError, "apply_issue runtime error"),
            ),
        )
    )

    registry.add(
        ToolDefinition(
            name=SCAFFOLD_NAME,
            description=SCAFFOLD_DESC,
            handler=scaffold_project,
            error_handlers=(
                (ValueError, "scaffold_project validation error"),
                (OSError, "scaffold_project OS error"),
            ),
        )
    )

    registry.add(
        ToolDefinition(
            name=COMMIT_NAME,
            description=COMMIT_DESC,
            handler=progressive_commit,
            error_handlers=((RuntimeError, "progressive_commit runtime error"),),
        )
    )

    registry.add(
        ToolDefinition(
            name=CREATE_PR_NAME,
            description=CREATE_PR_DESC,
            handler=create_pr,
            error_handlers=((RuntimeError, "create_pr runtime error"),),
        )
    )

    return registry
