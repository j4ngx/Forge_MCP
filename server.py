"""forge_mcp — FastMCP server entrypoint.

This module creates the :class:`FastMCP` server instance, registers every
tool defined under the ``tools/`` package, and exposes the ``main()``
function used by the ``[project.scripts]`` console entrypoint.

Usage (stdio transport for VS Code Copilot Agent Mode)::

    uv run server.py
"""

import logging
import sys

from mcp.server.fastmcp import FastMCP

from tools.apply_issue import TOOL_DESCRIPTION as APPLY_ISSUE_DESCRIPTION
from tools.apply_issue import TOOL_NAME as APPLY_ISSUE_NAME
from tools.apply_issue import apply_issue
from tools.review_pr import TOOL_DESCRIPTION as REVIEW_PR_DESCRIPTION
from tools.review_pr import TOOL_NAME as REVIEW_PR_NAME
from tools.review_pr import review_pr

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

# ── Tool registration ───────────────────────────────────────────────────────


@mcp.tool(name=REVIEW_PR_NAME, description=REVIEW_PR_DESCRIPTION)
def tool_review_pr(
    pr_diff: str,
    pr_title: str = "",
    pr_description: str = "",
    pr_author: str = "",
    pr_url: str = "",
    repo_context: str = "",
    severity_scope: str = "all",
    review_focus: str = "balanced",
    detail_level: str = "thorough",
) -> str:
    """Perform a senior-level Python PR code review.

    Args:
        pr_diff: The full Git diff content of the pull request.
        pr_title: Title of the pull request (optional).
        pr_description: Body / description of the pull request (optional).
        pr_author: Username of the PR author (optional).
        pr_url: GitHub PR URL — enables posting the review as a PR comment
            when GitHub MCP tools are available (optional).
        repo_context: Free-text description of frameworks, architecture,
            target Python version, and coding conventions (optional).
        severity_scope: ``"blockers_only"``, ``"blockers_and_major"``, or
            ``"all"`` (default).
        review_focus: ``"logic"``, ``"performance"``, ``"security"``,
            ``"style"``, or ``"balanced"`` (default).
        detail_level: ``"summary"`` or ``"thorough"`` (default).

    Returns:
        A structured Markdown review produced by the senior PR reviewer prompt.
    """
    try:
        return review_pr(
            pr_diff=pr_diff,
            pr_title=pr_title,
            pr_description=pr_description,
            pr_author=pr_author,
            pr_url=pr_url,
            repo_context=repo_context,
            severity_scope=severity_scope,
            review_focus=review_focus,
            detail_level=detail_level,
        )
    except ValueError as exc:
        logger.error("review_pr validation error: %s", exc)
        return f"Error: {exc}"
    except Exception as exc:
        logger.exception("Unexpected error in review_pr")
        return f"An unexpected error occurred while reviewing the PR: {exc}"


@mcp.tool(name=APPLY_ISSUE_NAME, description=APPLY_ISSUE_DESCRIPTION)
def tool_apply_issue(
    issue_url: str,
    issue_title: str,
    issue_body: str = "",
    issue_labels: str = "",
    branch_type: str = "feature",
    base_branch: str = "",
    repo_context: str = "",
) -> str:
    """Implement a GitHub issue end-to-end: branch, plan, code, review.

    IMPORTANT: Before calling this tool, fetch the issue details using
    ``mcp_github_issue_read`` and pass them as parameters.

    Args:
        issue_url: Full GitHub issue URL
            (e.g. ``https://github.com/owner/repo/issues/42``).
        issue_title: Title of the issue (from ``mcp_github_issue_read``).
        issue_body: Body / description of the issue (from
            ``mcp_github_issue_read``). Optional.
        issue_labels: Comma-separated list of issue labels (from
            ``mcp_github_issue_read``). Optional.
        branch_type: Type of branch to create. One of ``"feature"``
            (default), ``"bugfix"``, ``"hotfix"``, ``"release"``,
            ``"chore"``, ``"docs"``, ``"refactor"``, or ``"test"``.
        base_branch: Base branch to branch from. Leave empty to use the
            repository default branch (optional).
        repo_context: Free-text description of the repository context such
            as frameworks, architecture, Python version, and coding
            conventions (optional).

    Returns:
        A structured Markdown workflow prompt containing issue details and
        step-by-step instructions for implementing the issue.
    """
    try:
        return apply_issue(
            issue_url=issue_url,
            issue_title=issue_title,
            issue_body=issue_body,
            issue_labels=issue_labels,
            branch_type=branch_type,
            base_branch=base_branch,
            repo_context=repo_context,
        )
    except ValueError as exc:
        logger.error("apply_issue validation error: %s", exc)
        return f"Error: {exc}"
    except RuntimeError as exc:
        logger.error("apply_issue runtime error: %s", exc)
        return f"Error: {exc}"
    except Exception as exc:
        logger.exception("Unexpected error in apply_issue")
        return f"An unexpected error occurred while applying the issue: {exc}"


# ── Entrypoint ───────────────────────────────────────────────────────────────


def main() -> None:
    """Run the MCP server using stdio transport."""
    logger.info("Starting forge_mcp server (stdio transport)…")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
