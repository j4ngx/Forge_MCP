"""MCP tool: generate_unit_tests — Generate pytest unit tests.

This module provides the ``generate_unit_tests`` tool which creates
comprehensive pytest test suites with Polyfactory factories, AAA pattern,
and descriptive naming.  The system prompt is loaded from
``prompts/generate_unit_tests.md`` at import time.
"""

import logging

from utils.prompt_loader import load_prompt_cached

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────
PROMPT_FILENAME: str = "generate_unit_tests.md"
TOOL_NAME: str = "generate_unit_tests"
TOOL_DESCRIPTION: str = (
    "Generate comprehensive pytest unit tests for Python code. Uses AAA "
    "pattern (Arrange-Act-Assert), descriptive naming, and optionally "
    "Polyfactory factories for model mocking. Supports happy-path, "
    "edge-case, error, or comprehensive coverage focus."
)

_SYSTEM_PROMPT: str = load_prompt_cached(PROMPT_FILENAME)

# ── Valid parameter values ───────────────────────────────────────────────────
VALID_TEST_FRAMEWORKS: frozenset[str] = frozenset({"pytest"})
VALID_COVERAGE_FOCUSES: frozenset[str] = frozenset({
    "happy_path", "edge_cases", "errors", "comprehensive",
})


def generate_unit_tests(
    code: str,
    file_path: str = "",
    test_framework: str = "pytest",
    use_polyfactory: bool = True,
    coverage_focus: str = "comprehensive",
) -> str:
    """Generate unit tests for Python code.

    Args:
        code: The Python source code to generate tests for.
        file_path: Path of the source file (optional — used for
            imports in generated tests).
        test_framework: Test framework to use. Currently only
            ``"pytest"`` is supported.
        use_polyfactory: Whether to generate Polyfactory model
            factories for test data. Defaults to ``True``.
        coverage_focus: What to focus test coverage on. One of
            ``"happy_path"``, ``"edge_cases"``, ``"errors"``, or
            ``"comprehensive"`` (default).

    Returns:
        The system prompt followed by code and configuration, formatted
        for the LLM to produce a test suite.

    Raises:
        ValueError: If ``code`` is empty or parameters have invalid values.
    """
    if not code or not code.strip():
        msg = "code must not be empty. Provide the Python source code to test."
        raise ValueError(msg)

    if test_framework not in VALID_TEST_FRAMEWORKS:
        msg = f"Invalid test_framework '{test_framework}'. Must be one of: {sorted(VALID_TEST_FRAMEWORKS)}"
        raise ValueError(msg)

    if coverage_focus not in VALID_COVERAGE_FOCUSES:
        msg = f"Invalid coverage_focus '{coverage_focus}'. Must be one of: {sorted(VALID_COVERAGE_FOCUSES)}"
        raise ValueError(msg)

    logger.info("generate_unit_tests invoked — code length: %d characters", len(code))

    sections: list[str] = [_SYSTEM_PROMPT]

    config_block = (
        "## Configuration\n\n"
        f"- **Framework**: {test_framework}\n"
        f"- **Use Polyfactory**: {use_polyfactory}\n"
        f"- **Coverage focus**: {coverage_focus}"
    )
    if file_path:
        config_block += f"\n- **Source file**: `{file_path}`"
    sections.append(config_block)

    sections.append(f"## Code Under Test\n\n```python\n{code}\n```")

    return "\n\n---\n\n".join(sections)
