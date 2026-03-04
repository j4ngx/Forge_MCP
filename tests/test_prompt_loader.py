"""Unit tests for utils/prompt_loader.py.

Covers load_prompt(), load_prompt_cached(), and edge cases like
missing files and caching behaviour.
"""

from __future__ import annotations

import pytest

from utils.prompt_loader import _PROMPTS_DIR, load_prompt, load_prompt_cached

# ═══════════════════════════════════════════════════════════════════════════════
# load_prompt
# ═══════════════════════════════════════════════════════════════════════════════


class TestLoadPrompt:
    """Tests for the non-cached prompt loader."""

    def test_loads_existing_prompt(self) -> None:
        """load_prompt() returns content for an existing .md file."""
        content = load_prompt("review_pr.md")

        assert isinstance(content, str)
        assert len(content) > 0

    def test_returns_non_empty_string(self) -> None:
        """Loaded prompts contain meaningful content (not just whitespace)."""
        content = load_prompt("review_pr.md")

        assert content.strip(), "Prompt content should not be blank"

    def test_missing_prompt_raises_file_not_found_error(self) -> None:
        """load_prompt() raises FileNotFoundError for a non-existent file."""
        with pytest.raises(FileNotFoundError, match="Prompt file not found"):
            load_prompt("does_not_exist.md")

    def test_all_expected_prompts_exist(self) -> None:
        """All 5 tool prompt files can be loaded without errors."""
        expected_prompts = [
            "review_pr.md",
            "apply_issue.md",
            "scaffold_project.md",
            "progressive_commit.md",
            "create_pr.md",
        ]

        for prompt_name in expected_prompts:
            content = load_prompt(prompt_name)
            assert len(content) > 50, f"Prompt '{prompt_name}' seems too short"

    def test_prompts_dir_points_to_correct_location(self) -> None:
        """_PROMPTS_DIR resolves to the prompts/ directory in the project root."""
        assert _PROMPTS_DIR.name == "prompts"
        assert _PROMPTS_DIR.is_dir()


# ═══════════════════════════════════════════════════════════════════════════════
# load_prompt_cached
# ═══════════════════════════════════════════════════════════════════════════════


class TestLoadPromptCached:
    """Tests for the cached prompt loader."""

    def test_returns_same_content_as_uncached(self) -> None:
        """Cached and uncached loaders return identical content."""
        # Clear cache first to avoid stale state from other tests
        load_prompt_cached.cache_clear()

        uncached = load_prompt("review_pr.md")
        cached = load_prompt_cached("review_pr.md")

        assert cached == uncached

    def test_caching_returns_same_object(self) -> None:
        """Calling load_prompt_cached twice returns the same string object (cached)."""
        load_prompt_cached.cache_clear()

        first = load_prompt_cached("review_pr.md")
        second = load_prompt_cached("review_pr.md")

        # Same object identity means the cache is working
        assert first is second

    def test_missing_prompt_raises_file_not_found_error(self) -> None:
        """Cached loader also raises FileNotFoundError for missing files."""
        load_prompt_cached.cache_clear()

        with pytest.raises(FileNotFoundError, match="Prompt file not found"):
            load_prompt_cached("nonexistent.md")

    def test_cache_info_shows_hits(self) -> None:
        """After two calls, cache_info shows at least one hit."""
        load_prompt_cached.cache_clear()

        load_prompt_cached("apply_issue.md")
        load_prompt_cached("apply_issue.md")

        info = load_prompt_cached.cache_info()
        assert info.hits >= 1
        assert info.misses >= 1
