"""MCP tool: generate_test_fixtures — Generate pytest fixtures and factories.

This module provides the ``generate_test_fixtures`` tool which creates
pytest fixtures, conftest.py entries, and Polyfactory model factories
for Python test infrastructure.  The system prompt is loaded from
``prompts/generate_test_fixtures.md`` at import time.
"""

import logging

from utils.prompt_loader import load_prompt_cached

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────
PROMPT_FILENAME: str = "generate_test_fixtures.md"
TOOL_NAME: str = "generate_test_fixtures"
TOOL_DESCRIPTION: str = (
    "Generate pytest fixtures, conftest.py entries, and Polyfactory model "
    "factories for Python test infrastructure. Analyzes production code "
    "to create reusable, well-scoped fixtures with proper cleanup."
)

_SYSTEM_PROMPT: str = load_prompt_cached(PROMPT_FILENAME)

# ── Valid parameter values ───────────────────────────────────────────────────
VALID_FIXTURE_SCOPES: frozenset[str] = frozenset({"function", "class", "module", "session"})


def generate_test_fixtures(
    code: str,
    models_code: str = "",
    file_path: str = "",
    fixture_scope: str = "function",
    include_factories: bool = True,
) -> str:
    """Generate pytest fixtures and model factories.

    Args:
        code: The Python source code to generate fixtures for.
        models_code: Additional code containing Pydantic models,
            dataclasses, or SQLAlchemy models used by the source
            code (optional).
        file_path: Path of the source file (optional).
        fixture_scope: Default scope for generated fixtures. One of
            ``"function"`` (default), ``"class"``, ``"module"``, or
            ``"session"``.
        include_factories: Whether to generate Polyfactory model
            factories. Defaults to ``True``.

    Returns:
        The system prompt followed by code and configuration, formatted
        for the LLM to produce test fixtures and factories.

    Raises:
        ValueError: If ``code`` is empty or ``fixture_scope`` is invalid.
    """
    if not code or not code.strip():
        msg = "code must not be empty. Provide the Python source code to generate fixtures for."
        raise ValueError(msg)

    if fixture_scope not in VALID_FIXTURE_SCOPES:
        msg = f"Invalid fixture_scope '{fixture_scope}'. Must be one of: {sorted(VALID_FIXTURE_SCOPES)}"
        raise ValueError(msg)

    logger.info("generate_test_fixtures invoked — code length: %d characters", len(code))

    sections: list[str] = [_SYSTEM_PROMPT]

    config_block = (
        "## Configuration\n\n"
        f"- **Default fixture scope**: {fixture_scope}\n"
        f"- **Include Polyfactory factories**: {include_factories}"
    )
    if file_path:
        config_block += f"\n- **Source file**: `{file_path}`"
    sections.append(config_block)

    sections.append(f"## Production Code\n\n```python\n{code}\n```")

    if models_code and models_code.strip():
        sections.append(f"## Model Definitions\n\n```python\n{models_code}\n```")

    return "\n\n---\n\n".join(sections)
