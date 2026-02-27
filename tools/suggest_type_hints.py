"""MCP tool: suggest_type_hints — Analyze Python code and suggest type annotations.

This module provides the ``suggest_type_hints`` tool which examines Python code
and recommends missing or improved type hints, including generics, Protocol,
TypeVar, and modern syntax.  The system prompt is loaded from
``prompts/suggest_type_hints.md`` at import time.
"""

import logging

from utils.prompt_loader import load_prompt_cached

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────
PROMPT_FILENAME: str = "suggest_type_hints.md"
TOOL_NAME: str = "suggest_type_hints"
TOOL_DESCRIPTION: str = (
    "Analyze Python code and suggest missing or improved type annotations. "
    "Supports basic (signatures only), strict (all public surfaces), and "
    "complete (including TypeVar, Protocol, overloads) strictness levels. "
    "Returns a Markdown report with before/after diffs and rationale."
)

_SYSTEM_PROMPT: str = load_prompt_cached(PROMPT_FILENAME)

# ── Valid parameter values ───────────────────────────────────────────────────
VALID_STRICTNESS_LEVELS: frozenset[str] = frozenset({"basic", "strict", "complete"})


def suggest_type_hints(
    code: str,
    file_path: str = "",
    strictness: str = "strict",
    include_return_types: bool = True,
) -> str:
    """Suggest type annotations for Python code.

    Args:
        code: The Python source code to analyze.
        file_path: Path of the file being analyzed (optional).
        strictness: How thorough the suggestions should be. One of
            ``"basic"``, ``"strict"`` (default), or ``"complete"``.
        include_return_types: Whether to include return type suggestions.
            Defaults to ``True``.

    Returns:
        The system prompt followed by code and configuration, formatted
        for the LLM to produce type hint suggestions.

    Raises:
        ValueError: If ``code`` is empty or ``strictness`` is invalid.
    """
    if not code or not code.strip():
        msg = "code must not be empty. Provide the Python source code to analyze."
        raise ValueError(msg)

    if strictness not in VALID_STRICTNESS_LEVELS:
        msg = f"Invalid strictness '{strictness}'. Must be one of: {sorted(VALID_STRICTNESS_LEVELS)}"
        raise ValueError(msg)

    logger.info("suggest_type_hints invoked — code length: %d characters", len(code))

    sections: list[str] = [_SYSTEM_PROMPT]

    config_block = (
        f"## Configuration\n\n- **Strictness**: {strictness}\n- **Include return types**: {include_return_types}"
    )
    if file_path:
        config_block += f"\n- **File**: `{file_path}`"
    sections.append(config_block)

    sections.append(f"## Code to Analyze\n\n```python\n{code}\n```")

    return "\n\n---\n\n".join(sections)
