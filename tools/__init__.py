"""MCP tool definitions for forge_mcp.

Each sub-module in this package exposes a single MCP tool that is
registered with the FastMCP server instance in ``server.py``.

Available tools:
    - ``apply_issue``: Implement a GitHub issue end-to-end (branch, plan, code, review).
    - ``create_pr``: Create a pull request with full branch comparison and conflict detection.
    - ``progressive_commit``: Create progressive, well-structured Git commits with quality checks.
    - ``review_pr``: Senior-level Python PR code review.
    - ``scaffold_project``: Generate a hexagonal-architecture Python project on disk.
"""
