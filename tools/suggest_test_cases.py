"""MCP tool: suggest_test_cases — Enumerate test cases for Python code.

This module provides the ``suggest_test_cases`` tool which analyzes Python
code and produces a structured list of test cases covering happy paths,
edge cases, error conditions, and boundary values — without writing the
actual test code.  The system prompt is loaded from
``prompts/suggest_test_cases.md`` at import time.
"""

import logging

from utils.prompt_loader import load_prompt_cached

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────
PROMPT_FILENAME: str = "suggest_test_cases.md"
TOOL_NAME: str = "suggest_test_cases"
TOOL_DESCRIPTION: str = (
    "Analyze Python code and enumerate test cases without writing test "
    "code. Covers happy paths, edge cases, error conditions, and boundary "
    "values. Categorizes by priority and identifies mocking requirements. "
    "Useful for test planning before implementation."
)

_SYSTEM_PROMPT: str = load_prompt_cached(PROMPT_FILENAME)

# ── Valid parameter values ───────────────────────────────────────────────────
VALID_TEST_DEPTHS: frozenset[str] = frozenset({"basic", "thorough", "exhaustive"})


def suggest_test_cases(
    code: str,
    file_path: str = "",
    test_depth: str = "thorough",
    include_integration: bool = False,
) -> str:
    """Enumerate test cases for Python code.

    Args:
        code: The Python source code to analyze for test cases.
        file_path: Path of the source file (optional).
        test_depth: How thorough the test plan should be. One of
            ``"basic"``, ``"thorough"`` (default), or ``"exhaustive"``.
        include_integration: Whether to include integration test
            suggestions. Defaults to ``False``.

    Returns:
        The system prompt followed by code and configuration, formatted
        for the LLM to produce a test case enumeration.

    Raises:
        ValueError: If ``code`` is empty or ``test_depth`` is invalid.
    """
    if not code or not code.strip():
        msg = "code must not be empty. Provide the Python source code to analyze."
        raise ValueError(msg)

    if test_depth not in VALID_TEST_DEPTHS:
        msg = f"Invalid test_depth '{test_depth}'. Must be one of: {sorted(VALID_TEST_DEPTHS)}"
        raise ValueError(msg)

    logger.info("suggest_test_cases invoked — code length: %d characters", len(code))

    sections: list[str] = [_SYSTEM_PROMPT]

    config_block = (
        f"## Configuration\n\n- **Test depth**: {test_depth}\n- **Include integration tests**: {include_integration}"
    )
    if file_path:
        config_block += f"\n- **Source file**: `{file_path}`"
    sections.append(config_block)

    sections.append(f"## Code to Analyze\n\n```python\n{code}\n```")

    return "\n\n---\n\n".join(sections)
