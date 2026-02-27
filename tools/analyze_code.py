"""MCP tool: analyze_code — Comprehensive Python code analysis.

This module provides the ``analyze_code`` tool which examines Python source
code for complexity metrics, code smells, security red flags, PEP 8
violations, and best-practice adherence.  The system prompt is loaded from
``prompts/analyze_code.md`` at import time.
"""

import logging

from utils.prompt_loader import load_prompt_cached

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────
PROMPT_FILENAME: str = "analyze_code.md"
TOOL_NAME: str = "analyze_code"
TOOL_DESCRIPTION: str = (
    "Perform a comprehensive analysis of Python code covering complexity "
    "metrics, code smells, anti-patterns, security red flags, and PEP 8 "
    "style violations. Returns a structured Markdown report with severity "
    "ratings and actionable suggestions."
)

_SYSTEM_PROMPT: str = load_prompt_cached(PROMPT_FILENAME)

# ── Valid parameter values ───────────────────────────────────────────────────
VALID_ANALYSIS_FOCUSES: frozenset[str] = frozenset({"all", "complexity", "smells", "security", "style"})
VALID_DETAIL_LEVELS: frozenset[str] = frozenset({"brief", "standard", "verbose"})


def analyze_code(
    code: str,
    file_path: str = "",
    analysis_focus: str = "all",
    detail_level: str = "standard",
) -> str:
    """Analyze Python code for quality, complexity, and security issues.

    Args:
        code: The Python source code to analyze.
        file_path: Path of the file being analyzed, used for location
            references in the report (optional).
        analysis_focus: Which categories to analyze. One of ``"all"``
            (default), ``"complexity"``, ``"smells"``, ``"security"``,
            or ``"style"``.
        detail_level: Depth of the report. One of ``"brief"``,
            ``"standard"`` (default), or ``"verbose"``.

    Returns:
        The system prompt followed by the code and configuration, formatted
        for the LLM to produce a structured analysis report.

    Raises:
        ValueError: If ``code`` is empty or parameters have invalid values.
    """
    if not code or not code.strip():
        msg = "code must not be empty. Provide the Python source code to analyze."
        raise ValueError(msg)

    if analysis_focus not in VALID_ANALYSIS_FOCUSES:
        msg = f"Invalid analysis_focus '{analysis_focus}'. Must be one of: {sorted(VALID_ANALYSIS_FOCUSES)}"
        raise ValueError(msg)

    if detail_level not in VALID_DETAIL_LEVELS:
        msg = f"Invalid detail_level '{detail_level}'. Must be one of: {sorted(VALID_DETAIL_LEVELS)}"
        raise ValueError(msg)

    logger.info("analyze_code invoked — code length: %d characters", len(code))

    sections: list[str] = [_SYSTEM_PROMPT]

    # Configuration
    config_block = f"## Analysis Configuration\n\n- **Focus**: {analysis_focus}\n- **Detail level**: {detail_level}"
    if file_path:
        config_block += f"\n- **File**: `{file_path}`"
    sections.append(config_block)

    # The code to analyze
    sections.append(f"## Code to Analyze\n\n```python\n{code}\n```")

    return "\n\n---\n\n".join(sections)
