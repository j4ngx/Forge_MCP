"""MCP tool: explain_code — Explain what Python code does.

This module provides the ``explain_code`` tool which produces clear,
audience-adapted explanations of Python code covering control flow,
algorithmic complexity, side effects, and dependencies.  The system
prompt is loaded from ``prompts/explain_code.md`` at import time.
"""

import logging

from utils.prompt_loader import load_prompt_cached

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────
PROMPT_FILENAME: str = "explain_code.md"
TOOL_NAME: str = "explain_code"
TOOL_DESCRIPTION: str = (
    "Explain what a Python code snippet does. Supports audience levels "
    "(junior, mid, senior) and focus modes (overview, flow, complexity, "
    "dependencies). Returns a structured Markdown explanation adapted to "
    "the reader's experience level."
)

_SYSTEM_PROMPT: str = load_prompt_cached(PROMPT_FILENAME)

# ── Valid parameter values ───────────────────────────────────────────────────
VALID_AUDIENCES: frozenset[str] = frozenset({"junior", "mid", "senior"})
VALID_EXPLAIN_FOCUSES: frozenset[str] = frozenset({"overview", "flow", "complexity", "dependencies"})


def explain_code(
    code: str,
    file_path: str = "",
    audience: str = "mid",
    explain_focus: str = "overview",
) -> str:
    """Explain what Python code does.

    Args:
        code: The Python source code to explain.
        file_path: Path of the file being explained (optional).
        audience: Target audience level. One of ``"junior"``,
            ``"mid"`` (default), or ``"senior"``.
        explain_focus: What aspect to focus on. One of ``"overview"``
            (default), ``"flow"``, ``"complexity"``, or
            ``"dependencies"``.

    Returns:
        The system prompt followed by code and configuration, formatted
        for the LLM to produce a structured explanation.

    Raises:
        ValueError: If ``code`` is empty or parameters have invalid values.
    """
    if not code or not code.strip():
        msg = "code must not be empty. Provide the Python source code to explain."
        raise ValueError(msg)

    if audience not in VALID_AUDIENCES:
        msg = f"Invalid audience '{audience}'. Must be one of: {sorted(VALID_AUDIENCES)}"
        raise ValueError(msg)

    if explain_focus not in VALID_EXPLAIN_FOCUSES:
        msg = f"Invalid explain_focus '{explain_focus}'. Must be one of: {sorted(VALID_EXPLAIN_FOCUSES)}"
        raise ValueError(msg)

    logger.info("explain_code invoked — code length: %d characters", len(code))

    sections: list[str] = [_SYSTEM_PROMPT]

    config_block = (
        "## Configuration\n\n"
        f"- **Audience**: {audience}\n"
        f"- **Focus**: {explain_focus}"
    )
    if file_path:
        config_block += f"\n- **File**: `{file_path}`"
    sections.append(config_block)

    sections.append(f"## Code to Explain\n\n```python\n{code}\n```")

    return "\n\n---\n\n".join(sections)
