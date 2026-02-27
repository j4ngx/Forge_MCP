"""MCP tool: generate_module_doc — Generate module-level documentation.

This module provides the ``generate_module_doc`` tool which creates
comprehensive documentation for Python modules including overview, usage
examples, API reference, and architectural notes.  The system prompt is
loaded from ``prompts/generate_module_doc.md`` at import time.
"""

import logging

from utils.prompt_loader import load_prompt_cached

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────
PROMPT_FILENAME: str = "generate_module_doc.md"
TOOL_NAME: str = "generate_module_doc"
TOOL_DESCRIPTION: str = (
    "Generate comprehensive module-level documentation for Python code. "
    "Covers overview, usage examples, full API reference, and architectural "
    "notes. Supports targeting end-users, developers, or both audiences."
)

_SYSTEM_PROMPT: str = load_prompt_cached(PROMPT_FILENAME)

# ── Valid parameter values ───────────────────────────────────────────────────
VALID_DOC_SECTIONS: frozenset[str] = frozenset({"overview", "usage", "api", "examples"})
VALID_TARGET_AUDIENCES: frozenset[str] = frozenset({"user", "developer", "both"})


def generate_module_doc(
    code: str,
    module_name: str = "",
    doc_sections: str = "overview,usage,api",
    target_audience: str = "both",
) -> str:
    """Generate documentation for a Python module.

    Args:
        code: The Python source code of the module to document.
        module_name: Name of the module for the documentation header
            (optional — inferred from code if not provided).
        doc_sections: Comma-separated list of sections to include.
            Valid values: ``"overview"``, ``"usage"``, ``"api"``,
            ``"examples"``. Defaults to ``"overview,usage,api"``.
        target_audience: Who the documentation is for. One of
            ``"user"``, ``"developer"``, or ``"both"`` (default).

    Returns:
        The system prompt followed by code and configuration, formatted
        for the LLM to produce module documentation.

    Raises:
        ValueError: If ``code`` is empty or parameters have invalid values.
    """
    if not code or not code.strip():
        msg = "code must not be empty. Provide the Python module source code."
        raise ValueError(msg)

    # Validate doc_sections
    requested_sections = {s.strip() for s in doc_sections.split(",")}
    invalid_sections = requested_sections - VALID_DOC_SECTIONS
    if invalid_sections:
        msg = f"Invalid doc_sections: {sorted(invalid_sections)}. Must be from: {sorted(VALID_DOC_SECTIONS)}"
        raise ValueError(msg)

    if target_audience not in VALID_TARGET_AUDIENCES:
        msg = f"Invalid target_audience '{target_audience}'. Must be one of: {sorted(VALID_TARGET_AUDIENCES)}"
        raise ValueError(msg)

    logger.info("generate_module_doc invoked — code length: %d characters", len(code))

    sections: list[str] = [_SYSTEM_PROMPT]

    config_block = (
        "## Configuration\n\n"
        f"- **Sections**: {doc_sections}\n"
        f"- **Target audience**: {target_audience}"
    )
    if module_name:
        config_block += f"\n- **Module name**: `{module_name}`"
    sections.append(config_block)

    sections.append(f"## Module Code\n\n```python\n{code}\n```")

    return "\n\n---\n\n".join(sections)
