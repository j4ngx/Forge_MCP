"""MCP tool: review_pr — Senior PR reviewer powered by a Markdown prompt.

This module defines the ``review_pr`` tool which accepts a Git diff and
optional PR metadata, repository context, and review configuration. It
returns a structured review context for the LLM. The system prompt is
loaded from ``prompts/review_pr.md`` at import time so that missing files
are surfaced immediately rather than at first invocation.
"""

import logging

from utils.prompt_loader import load_prompt_cached

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────
PROMPT_FILENAME: str = "review_pr.md"
TOOL_NAME: str = "review_pr"
TOOL_DESCRIPTION: str = (
    "Perform a senior-level Python PR code review. Accepts the PR diff "
    "and optional metadata (title, description, author, PR URL), "
    "repository context (frameworks, architecture, Python version), "
    "and review configuration (severity scope, focus area, detail level). "
    "Returns a structured Markdown review covering logic, design, security, "
    "performance, testing, readability, and integration concerns. "
    "When a GitHub PR URL is provided and GitHub MCP tools are available, "
    "the review will also be posted as a PR comment."
)

# Eagerly load the prompt so a missing file is caught at startup.
_SYSTEM_PROMPT: str = load_prompt_cached(PROMPT_FILENAME)

# ── Severity / focus / detail valid values ───────────────────────────────────
VALID_SEVERITY_SCOPES: frozenset[str] = frozenset({"blockers_only", "blockers_and_major", "all"})
VALID_REVIEW_FOCUSES: frozenset[str] = frozenset({"logic", "performance", "security", "style", "balanced"})
VALID_DETAIL_LEVELS: frozenset[str] = frozenset({"summary", "thorough"})


def review_pr(  # noqa: PLR0913
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
    """Review a pull-request diff as a senior Python code reviewer.

    The tool loads a detailed system prompt from ``prompts/review_pr.md``
    and assembles it together with the user-supplied diff and optional
    context so that the backing LLM produces a structured review.

    Args:
        pr_diff: The full Git diff content of the pull request to review.
        pr_title: Title of the pull request (optional).
        pr_description: Body / description of the pull request (optional).
        pr_author: Username of the PR author (optional).
        pr_url: GitHub PR URL — when provided and GitHub MCP tools are
            available, the review will be posted as a PR comment (optional).
        repo_context: Free-text description of the repository context such
            as frameworks, architecture style, target Python version, and
            coding conventions (optional).
        severity_scope: Which severity levels to include in the review.
            One of ``"blockers_only"``, ``"blockers_and_major"``, or
            ``"all"`` (default).
        review_focus: Primary focus area for the review. One of
            ``"logic"``, ``"performance"``, ``"security"``, ``"style"``,
            or ``"balanced"`` (default).
        detail_level: Level of detail in the review output. One of
            ``"summary"`` or ``"thorough"`` (default).

    Returns:
        A string containing the system prompt followed by all provided
        context, formatted for the LLM to generate a structured review.

    Raises:
        ValueError: If ``pr_diff`` is empty, or if ``severity_scope``,
            ``review_focus``, or ``detail_level`` have invalid values.
    """
    # ── Validate required input ──────────────────────────────────────────
    if not pr_diff or not pr_diff.strip():
        msg = "pr_diff must not be empty. Provide the Git diff content of the pull request."
        raise ValueError(msg)

    if severity_scope not in VALID_SEVERITY_SCOPES:
        msg = f"Invalid severity_scope '{severity_scope}'. Must be one of: {sorted(VALID_SEVERITY_SCOPES)}"
        raise ValueError(msg)

    if review_focus not in VALID_REVIEW_FOCUSES:
        msg = f"Invalid review_focus '{review_focus}'. Must be one of: {sorted(VALID_REVIEW_FOCUSES)}"
        raise ValueError(msg)

    if detail_level not in VALID_DETAIL_LEVELS:
        msg = f"Invalid detail_level '{detail_level}'. Must be one of: {sorted(VALID_DETAIL_LEVELS)}"
        raise ValueError(msg)

    logger.info("review_pr invoked — diff length: %d characters", len(pr_diff))

    # ── Assemble context sections ────────────────────────────────────────
    sections: list[str] = [_SYSTEM_PROMPT]

    # PR metadata
    metadata_lines: list[str] = []
    if pr_title:
        metadata_lines.append(f"- **Title**: {pr_title}")
    if pr_description:
        metadata_lines.append(f"- **Description**: {pr_description}")
    if pr_author:
        metadata_lines.append(f"- **Author**: {pr_author}")
    if pr_url:
        metadata_lines.append(f"- **URL**: {pr_url}")

    if metadata_lines:
        sections.append("## PR Metadata\n\n" + "\n".join(metadata_lines))

    # Repository context
    if repo_context and repo_context.strip():
        sections.append(f"## Repository Context\n\n{repo_context.strip()}")

    # Review configuration
    config_block = (
        "## Review Configuration\n\n"
        f"- **Severity scope**: {severity_scope}\n"
        f"- **Focus**: {review_focus}\n"
        f"- **Detail level**: {detail_level}"
    )
    sections.append(config_block)

    # The diff itself
    sections.append(f"## Pull Request Diff\n\n```diff\n{pr_diff}\n```")

    return "\n\n---\n\n".join(sections)
