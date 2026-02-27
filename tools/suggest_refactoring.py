"""MCP tool: suggest_refactoring — Propose Python code refactorings.

This module provides the ``suggest_refactoring`` tool which analyzes Python
code and proposes concrete refactoring opportunities with rationale and
before/after code sketches.  The system prompt is loaded from
``prompts/suggest_refactoring.md`` at import time.
"""

import logging

from utils.prompt_loader import load_prompt_cached

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────
PROMPT_FILENAME: str = "suggest_refactoring.md"
TOOL_NAME: str = "suggest_refactoring"
TOOL_DESCRIPTION: str = (
    "Analyze Python code and propose refactoring opportunities with "
    "before/after code sketches. Targets readability, performance, "
    "maintainability, and/or testability. Prioritizes by impact and "
    "effort, and suggests an application order."
)

_SYSTEM_PROMPT: str = load_prompt_cached(PROMPT_FILENAME)

# ── Valid parameter values ───────────────────────────────────────────────────
VALID_REFACTOR_GOALS: frozenset[str] = frozenset({
    "readability", "performance", "maintainability", "testability", "all",
})
MAX_SUGGESTIONS_LIMIT: int = 50


def suggest_refactoring(
    code: str,
    file_path: str = "",
    refactor_goals: str = "all",
    max_suggestions: int = 10,
) -> str:
    """Propose refactoring opportunities for Python code.

    Args:
        code: The Python source code to analyze.
        file_path: Path of the file being analyzed (optional).
        refactor_goals: Which dimensions to optimize. One of
            ``"readability"``, ``"performance"``,
            ``"maintainability"``, ``"testability"``, or ``"all"``
            (default).
        max_suggestions: Maximum number of suggestions to return.
            Defaults to ``10``. Must be between 1 and 50.

    Returns:
        The system prompt followed by code and configuration, formatted
        for the LLM to produce refactoring suggestions.

    Raises:
        ValueError: If ``code`` is empty or parameters have invalid values.
    """
    if not code or not code.strip():
        msg = "code must not be empty. Provide the Python source code to analyze."
        raise ValueError(msg)

    if refactor_goals not in VALID_REFACTOR_GOALS:
        msg = f"Invalid refactor_goals '{refactor_goals}'. Must be one of: {sorted(VALID_REFACTOR_GOALS)}"
        raise ValueError(msg)

    if not 1 <= max_suggestions <= MAX_SUGGESTIONS_LIMIT:
        msg = f"max_suggestions must be between 1 and {MAX_SUGGESTIONS_LIMIT}, got {max_suggestions}"
        raise ValueError(msg)

    logger.info("suggest_refactoring invoked — code length: %d characters", len(code))

    sections: list[str] = [_SYSTEM_PROMPT]

    config_block = (
        "## Configuration\n\n"
        f"- **Goals**: {refactor_goals}\n"
        f"- **Max suggestions**: {max_suggestions}"
    )
    if file_path:
        config_block += f"\n- **File**: `{file_path}`"
    sections.append(config_block)

    sections.append(f"## Code to Refactor\n\n```python\n{code}\n```")

    return "\n\n---\n\n".join(sections)
