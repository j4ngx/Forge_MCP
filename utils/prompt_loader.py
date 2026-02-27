"""Prompt loader utility for dynamically loading Markdown prompt files.

This module provides a reusable function to load prompt templates stored
as Markdown files in the ``prompts/`` directory. Every MCP tool should use
this loader instead of embedding prompt text directly in code.
"""

import logging
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

_PROMPTS_DIR: Path = Path(__file__).resolve().parent.parent / "prompts"


def load_prompt(prompt_name: str) -> str:
    """Load a Markdown prompt file from the ``prompts/`` directory.

    Args:
        prompt_name: The filename (without directory) of the prompt to load.
            Example: ``"review_pr.md"``.

    Returns:
        The full text content of the prompt file.

    Raises:
        FileNotFoundError: If the requested prompt file does not exist.
        OSError: If the file cannot be read due to permission or I/O errors.
    """
    prompt_path = _PROMPTS_DIR / prompt_name

    if not prompt_path.is_file():
        msg = (
            f"Prompt file not found: '{prompt_path}'. "
            f"Ensure the file '{prompt_name}' exists inside the prompts/ directory."
        )
        raise FileNotFoundError(msg)

    logger.info("Loading prompt file: %s", prompt_path)
    return prompt_path.read_text(encoding="utf-8")


@lru_cache(maxsize=32)
def load_prompt_cached(prompt_name: str) -> str:
    """Load and cache a Markdown prompt file.

    This is a thin caching wrapper around :func:`load_prompt` so that
    repeated invocations for the same prompt do not hit the filesystem.

    Args:
        prompt_name: The filename (without directory) of the prompt to load.

    Returns:
        The full text content of the prompt file.

    Raises:
        FileNotFoundError: If the requested prompt file does not exist.
        OSError: If the file cannot be read due to permission or I/O errors.
    """
    return load_prompt(prompt_name)
