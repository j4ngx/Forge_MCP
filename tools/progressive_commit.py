"""MCP tool: progressive_commit — Create progressive, well-structured commits.

This module defines the ``progressive_commit`` tool which analyzes uncommitted
changes on the current branch, runs quality checks (formatting, linting,
secret detection), and guides the LLM through creating atomic, logical commits
following the Conventional Commits specification with gitmoji.

The tool inspects the project configuration (``pyproject.toml``, ``README.md``,
``Makefile``, etc.) to detect available quality tools and runs them before
any commit is created.
"""

import logging
import subprocess
from pathlib import Path

from utils.prompt_loader import load_prompt_cached

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────
PROMPT_FILENAME: str = "progressive_commit.md"
TOOL_NAME: str = "progressive_commit"
TOOL_DESCRIPTION: str = (
    "Create progressive, well-structured Git commits from uncommitted changes. "
    "Analyzes all modified/staged files on the current branch, detects and runs "
    "quality tools (formatter, linter, detect-secrets) from the project "
    "configuration (pyproject.toml, README.md, Makefile), groups changes into "
    "logical atomic commits, and creates them using the Conventional Commits "
    "format with gitmoji. Presents a commit plan for user approval before "
    "executing. Ensures code quality checks pass before any commit is made."
)

_PYPROJECT_TOML: str = "pyproject.toml"

# Eagerly load the prompt so a missing file is caught at startup.
_SYSTEM_PROMPT: str = load_prompt_cached(PROMPT_FILENAME)


def _run_git_command(args: list[str], *, cwd: str | None = None) -> str:
    """Execute a ``git`` CLI command and return its stdout.

    Args:
        args: Command arguments (without the leading ``git``).
        cwd: Working directory for the command (optional).

    Returns:
        The stripped stdout output of the command.

    Raises:
        RuntimeError: If the command exits with a non-zero status.
    """
    cmd = ["git", *args]
    logger.info("Running: %s", " ".join(cmd))
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd=cwd,
            timeout=30,
        )
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() if exc.stderr else "no stderr"
        msg = f"git command failed (exit {exc.returncode}): {stderr}"
        raise RuntimeError(msg) from exc
    except subprocess.TimeoutExpired as exc:
        msg = f"git command timed out after 30s: {' '.join(cmd)}"
        raise RuntimeError(msg) from exc
    return result.stdout.strip()


def _detect_package_manager(root: Path) -> str:
    """Detect the project's package manager from configuration files.

    Args:
        root: Repository root path.

    Returns:
        The detected package manager name.
    """
    pyproject = root / _PYPROJECT_TOML
    if (root / "uv.lock").exists() or pyproject.exists():
        if pyproject.exists():
            content = pyproject.read_text(encoding="utf-8")
            return "poetry" if "[tool.poetry]" in content else "uv"
        return "uv"
    if (root / "package.json").exists():
        return "npm"
    return "unknown"


def _detect_pyproject_tools(root: Path) -> tuple[bool, bool, list[str]]:
    """Detect formatter and linter tools from ``pyproject.toml``.

    Args:
        root: Repository root path.

    Returns:
        A tuple of (has_formatter, has_linter, detail_lines).
    """
    pyproject = root / _PYPROJECT_TOML
    has_formatter = False
    has_linter = False
    details: list[str] = []

    if not pyproject.exists():
        return has_formatter, has_linter, details

    content = pyproject.read_text(encoding="utf-8")
    tool_checks = [
        ("[tool.ruff", True, True, "Ruff: detected (formatter + linter)"),
        ("[tool.black", True, False, "Black: detected (formatter)"),
        ("[tool.isort", True, False, "isort: detected (import sorter)"),
    ]
    for marker, fmt, lint, label in tool_checks:
        if marker in content:
            has_formatter = has_formatter or fmt
            has_linter = has_linter or lint
            details.append(f"- {label}")

    if "format" in content:
        has_formatter = True
        details.append("- Format script: detected")
    if "lint" in content:
        has_linter = True
        details.append("- Lint script: detected")

    return has_formatter, has_linter, details


def _detect_quality_tools(repo_path: str | None = None) -> dict[str, str | bool]:
    """Detect available quality tools from project configuration files.

    Inspects ``pyproject.toml``, ``Makefile``, ``package.json``, and
    ``.secrets.baseline`` to determine which quality tools are available.

    Args:
        repo_path: Path to the repository root (optional, defaults to cwd).

    Returns:
        A dictionary with detected tools and their configuration:
        - ``package_manager``: Detected package manager (``uv``, ``poetry``, ``pip``).
        - ``has_formatter``: Whether a formatter was detected.
        - ``has_linter``: Whether a linter was detected.
        - ``has_secrets_detection``: Whether detect-secrets is configured.
        - ``details``: Human-readable summary of detected tools.
    """
    root = Path(repo_path) if repo_path else Path.cwd()

    pkg_manager = _detect_package_manager(root)
    has_formatter, has_linter, details_lines = _detect_pyproject_tools(root)

    details_lines.insert(0, f"- Package manager: {pkg_manager}")

    has_secrets = (root / ".secrets.baseline").exists()
    if has_secrets:
        details_lines.append("- detect-secrets: configured (.secrets.baseline found)")

    if (root / ".pre-commit-config.yaml").exists():
        details_lines.append("- pre-commit: configured (.pre-commit-config.yaml found)")

    return {
        "package_manager": pkg_manager,
        "has_formatter": has_formatter,
        "has_linter": has_linter,
        "has_secrets_detection": has_secrets,
        "details": "\n".join(details_lines),
    }


def _detect_base_branch() -> str:
    """Auto-detect the default base branch.

    Tries ``origin/HEAD``, then falls back to common branch names.

    Returns:
        The detected base branch name.
    """
    try:
        return _run_git_command(["rev-parse", "--abbrev-ref", "origin/HEAD"]).replace("origin/", "")
    except RuntimeError:
        pass

    for candidate in ("main", "master", "develop"):
        try:
            _run_git_command(["rev-parse", "--verify", candidate])
            return candidate
        except RuntimeError:
            continue

    return "main"


def _safe_git(args: list[str]) -> str:
    """Run a git command, returning empty string on failure.

    Args:
        args: Git command arguments.

    Returns:
        Command output or empty string on error.
    """
    try:
        return _run_git_command(args)
    except RuntimeError:
        return ""


def _get_branch_info(base_branch: str = "") -> dict[str, str]:
    """Get information about the current branch and its changes.

    Args:
        base_branch: Base branch to compare against (empty for auto-detect).

    Returns:
        A dictionary with branch information:
        - ``current_branch``: Name of the current branch.
        - ``base_branch``: Name of the base branch.
        - ``status``: Output of ``git status --short``.
        - ``diff_stat``: Output of ``git diff --stat``.
        - ``staged_stat``: Output of ``git diff --cached --stat``.
        - ``log_since_base``: Commits since base branch.

    Raises:
        RuntimeError: If the current branch cannot be determined.
    """
    current = _run_git_command(["branch", "--show-current"])

    if not base_branch:
        base_branch = _detect_base_branch()

    return {
        "current_branch": current,
        "base_branch": base_branch,
        "status": _safe_git(["status", "--short"]),
        "diff_stat": _safe_git(["diff", "--stat"]),
        "staged_stat": _safe_git(["diff", "--cached", "--stat"]),
        "log_since_base": _safe_git(["log", "--oneline", f"{base_branch}..HEAD"]),
    }


def _build_quality_section(quality_tools: dict[str, str | bool]) -> str:
    """Build the quality tools Markdown section.

    Args:
        quality_tools: Dictionary from ``_detect_quality_tools``.

    Returns:
        Formatted Markdown section.
    """
    block = (
        "## Detected Quality Tools\n\n"
        f"- **Package manager**: {quality_tools['package_manager']}\n"
        f"- **Formatter available**: {'Yes' if quality_tools['has_formatter'] else 'No'}\n"
        f"- **Linter available**: {'Yes' if quality_tools['has_linter'] else 'No'}\n"
        f"- **Secret detection**: {'Yes' if quality_tools['has_secrets_detection'] else 'No'}\n"
    )
    if quality_tools["details"]:
        block += f"\n**Details:**\n{quality_tools['details']}"
    return block


_NEXT_STEPS: str = (
    "## Next Steps\n\n"
    "Follow the workflow defined in the system prompt:\n\n"
    "1. **Run quality checks** — Execute formatting, linting, and secret "
    "detection using the detected tools BEFORE creating any commits.\n"
    "2. **Analyze all changes** — Review diffs above and group them into "
    "logical, atomic units.\n"
    "3. **Propose a commit plan** — Present numbered commits with messages, "
    "files, and rationale.\n"
    "4. \u26d4 **WAIT FOR USER APPROVAL** — Do NOT create any commits until "
    "the user explicitly approves the plan.\n"
    "5. **Create commits progressively** — Stage and commit each group one "
    "at a time.\n"
    "6. **Verify** — Show the final commit log and confirm success."
)


def progressive_commit(
    base_branch: str = "",
    repo_path: str = "",
    include_untracked: bool = True,
) -> str:
    """Analyze changes and prepare progressive commits with quality checks.

    Inspects the current branch for uncommitted changes, detects available
    quality tools from project configuration, and returns a structured
    prompt that guides the LLM through running quality checks, grouping
    changes into logical commits, and creating them progressively using
    the Conventional Commits format with gitmoji.

    Args:
        base_branch: Base branch to compare against. Leave empty to
            auto-detect the default branch (optional).
        repo_path: Path to the repository root. Leave empty to use the
            current working directory (optional).
        include_untracked: Whether to include untracked files in the
            commit analysis. Defaults to ``True``.

    Returns:
        A structured Markdown workflow prompt containing branch status,
        detected quality tools, uncommitted changes, and step-by-step
        instructions for creating progressive commits.

    Raises:
        RuntimeError: If ``git`` commands fail (not in a git repository,
            authentication issues, etc.).
    """
    logger.info(
        "progressive_commit invoked — base_branch: %s, repo_path: %s",
        base_branch or "(auto-detect)",
        repo_path or "(cwd)",
    )

    # ── Gather branch info ───────────────────────────────────────────────
    branch_info = _get_branch_info(base_branch)
    logger.info(
        "Branch: %s (base: %s)",
        branch_info["current_branch"],
        branch_info["base_branch"],
    )

    # ── Detect quality tools ─────────────────────────────────────────────
    quality_tools = _detect_quality_tools(repo_path or None)
    logger.info("Quality tools detected: %s", quality_tools["details"])

    # ── Get detailed diff ────────────────────────────────────────────────
    full_diff = _safe_git(["diff"])
    staged_diff = _safe_git(["diff", "--cached"])

    untracked_files = ""
    if include_untracked:
        untracked_files = _safe_git(["ls-files", "--others", "--exclude-standard"])

    # ── Assemble output ─────────────────────────────────────────────────
    sections: list[str] = [
        _SYSTEM_PROMPT,
        (
            "## Branch Information\n\n"
            f"- **Current branch**: `{branch_info['current_branch']}`\n"
            f"- **Base branch**: `{branch_info['base_branch']}`"
        ),
    ]

    # Existing commits on branch
    log = branch_info["log_since_base"]
    sections.append(
        f"## Existing Commits on Branch\n\n```\n{log}\n```"
        if log
        else "## Existing Commits on Branch\n\n_No commits yet on this branch._"
    )

    sections.append(_build_quality_section(quality_tools))

    # Current status
    status = branch_info["status"]
    sections.append(
        f"## Current Git Status\n\n```\n{status}\n```"
        if status
        else "## Current Git Status\n\n_Working tree is clean — no uncommitted changes._"
    )

    if staged_diff:
        sections.append(
            "## Staged Changes (git diff --cached)\n\n"
            f"**Stat:**\n```\n{branch_info['staged_stat']}\n```\n\n"
            f"**Diff:**\n```diff\n{staged_diff}\n```"
        )

    if full_diff:
        sections.append(
            "## Unstaged Changes (git diff)\n\n"
            f"**Stat:**\n```\n{branch_info['diff_stat']}\n```\n\n"
            f"**Diff:**\n```diff\n{full_diff}\n```"
        )

    if untracked_files:
        sections.append(f"## Untracked Files\n\n```\n{untracked_files}\n```")

    sections.append(_NEXT_STEPS)

    return "\n\n---\n\n".join(sections)
