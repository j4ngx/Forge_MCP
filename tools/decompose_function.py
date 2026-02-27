"""MCP tool: decompose_function — Break complex functions into smaller ones.

This module provides the ``decompose_function`` tool which analyzes complex
Python functions and proposes decompositions into smaller, single-
responsibility functions.  The system prompt is loaded from
``prompts/decompose_function.md`` at import time.
"""

import logging

from utils.prompt_loader import load_prompt_cached

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────
PROMPT_FILENAME: str = "decompose_function.md"
TOOL_NAME: str = "decompose_function"
TOOL_DESCRIPTION: str = (
    "Analyze a complex Python function and propose decomposition into "
    "smaller, single-responsibility functions. Supports extract-method, "
    "strategy-pattern, and pipeline strategies. Returns complete "
    "refactored code with a decomposition map."
)

_SYSTEM_PROMPT: str = load_prompt_cached(PROMPT_FILENAME)

# ── Valid parameter values ───────────────────────────────────────────────────
VALID_STRATEGIES: frozenset[str] = frozenset({"extract_method", "strategy_pattern", "pipeline"})
MAX_LINES_FLOOR: int = 10
MAX_LINES_CEILING: int = 100


def decompose_function(
    code: str,
    function_name: str = "",
    file_path: str = "",
    max_lines_per_function: int = 30,
    decomposition_strategy: str = "extract_method",
) -> str:
    """Decompose a complex function into smaller ones.

    Args:
        code: The Python source code containing the function to decompose.
        function_name: Name of the function to decompose (optional —
            the largest function is analyzed if not provided).
        file_path: Path of the source file (optional).
        max_lines_per_function: Target maximum lines per resulting
            function. Defaults to ``30``.  Must be between 10 and 100.
        decomposition_strategy: How to decompose the function. One of
            ``"extract_method"`` (default), ``"strategy_pattern"``, or
            ``"pipeline"``.

    Returns:
        The system prompt followed by code and configuration, formatted
        for the LLM to produce a decomposition plan and refactored code.

    Raises:
        ValueError: If ``code`` is empty or parameters have invalid values.
    """
    if not code or not code.strip():
        msg = "code must not be empty. Provide the Python source code containing the function."
        raise ValueError(msg)

    if decomposition_strategy not in VALID_STRATEGIES:
        msg = f"Invalid decomposition_strategy '{decomposition_strategy}'. Must be one of: {sorted(VALID_STRATEGIES)}"
        raise ValueError(msg)

    if not MAX_LINES_FLOOR <= max_lines_per_function <= MAX_LINES_CEILING:
        msg = (
            f"max_lines_per_function must be between {MAX_LINES_FLOOR} and "
            f"{MAX_LINES_CEILING}, got {max_lines_per_function}"
        )
        raise ValueError(msg)

    logger.info("decompose_function invoked — code length: %d characters", len(code))

    sections: list[str] = [_SYSTEM_PROMPT]

    config_block = (
        "## Configuration\n\n"
        f"- **Strategy**: {decomposition_strategy}\n"
        f"- **Max lines per function**: {max_lines_per_function}"
    )
    if function_name:
        config_block += f"\n- **Target function**: `{function_name}`"
    if file_path:
        config_block += f"\n- **File**: `{file_path}`"
    sections.append(config_block)

    sections.append(f"## Code to Decompose\n\n```python\n{code}\n```")

    return "\n\n---\n\n".join(sections)
