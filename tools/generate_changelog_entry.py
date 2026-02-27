"""MCP tool: generate_changelog_entry — Generate Keep a Changelog entries.

This module provides the ``generate_changelog_entry`` tool which transforms
diffs or change descriptions into properly formatted changelog entries
following the Keep a Changelog format.  The system prompt is loaded from
``prompts/generate_changelog_entry.md`` at import time.
"""

import logging

from utils.prompt_loader import load_prompt_cached

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────
PROMPT_FILENAME: str = "generate_changelog_entry.md"
TOOL_NAME: str = "generate_changelog_entry"
TOOL_DESCRIPTION: str = (
    "Generate a CHANGELOG entry from a diff, commit list, or description "
    "of changes. Follows Keep a Changelog format with proper categorization "
    "(Added, Changed, Deprecated, Removed, Fixed, Security). Returns a "
    "Markdown block ready to paste into CHANGELOG.md."
)

_SYSTEM_PROMPT: str = load_prompt_cached(PROMPT_FILENAME)

# ── Valid parameter values ───────────────────────────────────────────────────
VALID_CHANGE_TYPES: frozenset[str] = frozenset(
    {
        "added",
        "changed",
        "deprecated",
        "removed",
        "fixed",
        "security",
        "auto",
    }
)


def generate_changelog_entry(
    changes: str,
    version: str = "",
    change_type: str = "auto",
    project_context: str = "",
) -> str:
    """Generate a changelog entry from changes.

    Args:
        changes: The diff, commit list, or free-text description of changes.
        version: Semantic version for the entry (e.g., ``"1.2.0"``).
            Defaults to ``"[Unreleased]"`` if empty.
        change_type: Force all changes under a specific type. One of
            ``"added"``, ``"changed"``, ``"deprecated"``, ``"removed"``,
            ``"fixed"``, ``"security"``, or ``"auto"`` (default — infer
            from content).
        project_context: Additional context about the project for more
            meaningful descriptions (optional).

    Returns:
        The system prompt followed by changes and configuration, formatted
        for the LLM to produce a changelog entry.

    Raises:
        ValueError: If ``changes`` is empty or ``change_type`` is invalid.
    """
    if not changes or not changes.strip():
        msg = "changes must not be empty. Provide a diff, commit list, or description of changes."
        raise ValueError(msg)

    if change_type not in VALID_CHANGE_TYPES:
        msg = f"Invalid change_type '{change_type}'. Must be one of: {sorted(VALID_CHANGE_TYPES)}"
        raise ValueError(msg)

    logger.info("generate_changelog_entry invoked — changes length: %d characters", len(changes))

    sections: list[str] = [_SYSTEM_PROMPT]

    config_block = f"## Configuration\n\n- **Version**: {version or '[Unreleased]'}\n- **Change type**: {change_type}"
    sections.append(config_block)

    if project_context and project_context.strip():
        sections.append(f"## Project Context\n\n{project_context.strip()}")

    sections.append(f"## Changes to Document\n\n{changes}")

    return "\n\n---\n\n".join(sections)
