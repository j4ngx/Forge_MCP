"""MCP tool: generate_docstrings — Generate Python docstrings.

This module provides the ``generate_docstrings`` tool which creates or
improves docstrings for Python functions, classes, and modules following
Google, NumPy, or Sphinx conventions.  The system prompt is loaded from
``prompts/generate_docstrings.md`` at import time.
"""

import logging

from utils.prompt_loader import load_prompt_cached

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────
PROMPT_FILENAME: str = "generate_docstrings.md"
TOOL_NAME: str = "generate_docstrings"
TOOL_DESCRIPTION: str = (
    "Generate or improve docstrings for Python functions, classes, and "
    "modules. Supports Google (default), NumPy, and Sphinx styles. "
    "Optionally includes usage examples and Raises sections. Returns "
    "the code with complete, accurate docstrings."
)

_SYSTEM_PROMPT: str = load_prompt_cached(PROMPT_FILENAME)

# ── Valid parameter values ───────────────────────────────────────────────────
VALID_DOCSTRING_STYLES: frozenset[str] = frozenset({"google", "numpy", "sphinx"})


def generate_docstrings(
    code: str,
    file_path: str = "",
    docstring_style: str = "google",
    include_examples: bool = True,
    include_raises: bool = True,
) -> str:
    """Generate docstrings for Python code.

    Args:
        code: The Python source code to document.
        file_path: Path of the file being documented (optional).
        docstring_style: Docstring convention to follow. One of
            ``"google"`` (default), ``"numpy"``, or ``"sphinx"``.
        include_examples: Whether to include usage examples in
            docstrings. Defaults to ``True``.
        include_raises: Whether to include Raises/Exceptions sections.
            Defaults to ``True``.

    Returns:
        The system prompt followed by code and configuration, formatted
        for the LLM to produce documented code.

    Raises:
        ValueError: If ``code`` is empty or ``docstring_style`` is invalid.
    """
    if not code or not code.strip():
        msg = "code must not be empty. Provide the Python source code to document."
        raise ValueError(msg)

    if docstring_style not in VALID_DOCSTRING_STYLES:
        msg = f"Invalid docstring_style '{docstring_style}'. Must be one of: {sorted(VALID_DOCSTRING_STYLES)}"
        raise ValueError(msg)

    logger.info("generate_docstrings invoked — code length: %d characters", len(code))

    sections: list[str] = [_SYSTEM_PROMPT]

    config_block = (
        "## Configuration\n\n"
        f"- **Style**: {docstring_style}\n"
        f"- **Include examples**: {include_examples}\n"
        f"- **Include raises**: {include_raises}"
    )
    if file_path:
        config_block += f"\n- **File**: `{file_path}`"
    sections.append(config_block)

    sections.append(f"## Code to Document\n\n```python\n{code}\n```")

    return "\n\n---\n\n".join(sections)
