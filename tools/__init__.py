"""MCP tool definitions for forge_mcp.

Each sub-module in this package exposes a single MCP tool that is
registered with the FastMCP server instance in ``server.py``.

Available tools:
    - ``apply_issue``: Implement a GitHub issue end-to-end (branch, plan, code, review).
    - ``review_pr``: Senior-level Python PR code review.
    - ``scaffold_project``: Generate a hexagonal-architecture Python project on disk.
"""
