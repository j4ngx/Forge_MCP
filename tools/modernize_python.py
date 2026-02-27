"""MCP tool: modernize_python — Suggest modern Python 3.11+ idioms.

This module provides the ``modernize_python`` tool which analyzes Python code
and suggests upgrades to use modern syntax, standard library features, and
type system improvements available in Python 3.11+.  The system prompt is
loaded from ``prompts/modernize_python.md`` at import time.
"""

import logging

from utils.prompt_loader import load_prompt_cached

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────
PROMPT_FILENAME: str = "modernize_python.md"
TOOL_NAME: str = "modernize_python"
TOOL_DESCRIPTION: str = (
    "Suggest modern Python idioms and features for upgrading code. "
    "Covers match statements, walrus operator, dataclasses, StrEnum, "
    "pathlib, tomllib, modern type syntax, and performance patterns. "
    "Configurable minimum Python version and aggressiveness level."
)

_SYSTEM_PROMPT: str = load_prompt_cached(PROMPT_FILENAME)

# ── Valid parameter values ───────────────────────────────────────────────────
VALID_PYTHON_VERSIONS: frozenset[str] = frozenset({"3.11", "3.12", "3.13"})


def modernize_python(
    code: str,
    file_path: str = "",
    min_python_version: str = "3.11",
    aggressive: bool = False,
) -> str:
    """Suggest modern Python idioms for code.

    Args:
        code: The Python source code to modernize.
        file_path: Path of the file being analyzed (optional).
        min_python_version: Minimum Python version to target. One of
            ``"3.11"`` (default), ``"3.12"``, or ``"3.13"``. Only
            features available in this version or newer are suggested.
        aggressive: If ``True``, suggest all modernizations including
            structural rewrites. If ``False`` (default), only suggest
            clear, uncontroversial improvements.

    Returns:
        The system prompt followed by code and configuration, formatted
        for the LLM to produce modernization suggestions.

    Raises:
        ValueError: If ``code`` is empty or ``min_python_version`` is invalid.
    """
    if not code or not code.strip():
        msg = "code must not be empty. Provide the Python source code to modernize."
        raise ValueError(msg)

    if min_python_version not in VALID_PYTHON_VERSIONS:
        msg = (
            f"Invalid min_python_version '{min_python_version}'. "
            f"Must be one of: {sorted(VALID_PYTHON_VERSIONS)}"
        )
        raise ValueError(msg)

    logger.info("modernize_python invoked — code length: %d characters", len(code))

    sections: list[str] = [_SYSTEM_PROMPT]

    config_block = (
        "## Configuration\n\n"
        f"- **Min Python version**: {min_python_version}\n"
        f"- **Aggressive**: {aggressive}"
    )
    if file_path:
        config_block += f"\n- **File**: `{file_path}`"
    sections.append(config_block)

    sections.append(f"## Code to Modernize\n\n```python\n{code}\n```")

    return "\n\n---\n\n".join(sections)
