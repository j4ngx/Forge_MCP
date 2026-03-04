"""MCP tool: create_pr — Create or update a pull request with full branch comparison.

This module defines the ``create_pr`` tool which compares the current branch
against its base, detects merge/rebase conflicts, generates a comprehensive
PR description following the Conventional Commits format with gitmoji, and
guides the LLM through creating the pull request.

If a pull request already exists for the current branch, the tool detects it
and provides context so the LLM can update the existing PR description with
the latest changes instead of creating a duplicate.

The PR description template includes: title, feature summary, per-commit
change details, diff stats, type-of-change checkboxes, a checklist, testing
instructions, and optional sections for screenshots and notes.
"""

import json
import logging
import subprocess

from utils.prompt_loader import load_prompt_cached

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────
PROMPT_FILENAME: str = "create_pr.md"
TOOL_NAME: str = "create_pr"
TOOL_DESCRIPTION: str = (
    "Create or update a pull request from the current branch. Compares the "
    "current branch against the base branch, detects merge/rebase conflicts "
    "(and asks the user how to resolve them), generates a comprehensive PR "
    "description following the Conventional Commits format with gitmoji, "
    "and creates the PR via GitHub MCP tools or `gh` CLI. If a PR already "
    "exists for the current branch, it detects the existing PR and guides "
    "through updating its description with the latest changes. The PR "
    "description includes: commit-by-commit changes, diff stats, "
    "type-of-change checkboxes, a quality checklist, and testing "
    "instructions. Presents the PR description for user approval before "
    "creating or updating."
)

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
            timeout=60,
        )
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() if exc.stderr else "no stderr"
        msg = f"git command failed (exit {exc.returncode}): {stderr}"
        raise RuntimeError(msg) from exc
    except subprocess.TimeoutExpired as exc:
        msg = f"git command timed out after 60s: {' '.join(cmd)}"
        raise RuntimeError(msg) from exc
    return result.stdout.strip()


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


def _check_conflicts(base_branch: str) -> dict[str, str | bool]:
    """Check if the current branch has conflicts with the base branch.

    Attempts a trial merge to detect conflicts without actually modifying
    the working tree.

    Args:
        base_branch: The base branch to check conflicts against.

    Returns:
        A dictionary with:
        - ``has_conflicts``: Whether conflicts were detected.
        - ``conflicting_files``: Newline-separated list of conflicting files.
        - ``details``: Human-readable conflict summary.
    """
    result: dict[str, str | bool] = {
        "has_conflicts": False,
        "conflicting_files": "",
        "details": "",
    }

    try:
        # Try merge-tree approach (Git 2.38+)
        merge_base = _run_git_command(["merge-base", base_branch, "HEAD"])
        cmd = ["git", "merge-tree", merge_base, base_branch, "HEAD"]
        merge_result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if merge_result.returncode != 0:
            result["has_conflicts"] = True
            # Extract conflicting file names from merge-tree output
            conflict_lines: list[str] = []
            for line in merge_result.stdout.splitlines():
                if "CONFLICT" in line or "conflict" in line:
                    conflict_lines.append(line.strip())
            result["conflicting_files"] = "\n".join(conflict_lines)
            result["details"] = f"Conflicts detected between current branch and `{base_branch}`:\n" + "\n".join(
                f"  - {line}" for line in conflict_lines
            )
        else:
            result["details"] = f"No conflicts with `{base_branch}`."

    except (RuntimeError, subprocess.TimeoutExpired):
        # Fallback: check if branches have diverged
        try:
            behind_ahead = _run_git_command(["rev-list", "--left-right", "--count", f"{base_branch}...HEAD"])
            parts = behind_ahead.split()
            if len(parts) == 2 and int(parts[0]) > 0:
                result["details"] = (
                    f"Branch is {parts[0]} commit(s) behind `{base_branch}` "
                    f"and {parts[1]} commit(s) ahead. "
                    "Potential conflicts may exist — a rebase or merge is recommended."
                )
            else:
                result["details"] = f"Branch is up to date with `{base_branch}`."
        except RuntimeError:
            result["details"] = "Could not determine conflict status."

    return result


def _safe_git(args: list[str], *, cwd: str | None = None) -> str:
    """Run a git command, returning empty string on failure.

    Args:
        args: Git command arguments.
        cwd: Working directory (optional).

    Returns:
        Command output or empty string on error.
    """
    try:
        return _run_git_command(args, cwd=cwd)
    except RuntimeError:
        return ""


def _gather_branch_data(current_branch: str, base_branch: str, cwd: str | None) -> dict[str, str]:
    """Gather all git data needed for PR comparison.

    Args:
        current_branch: Current branch name.
        base_branch: Base branch name.
        cwd: Working directory (optional).

    Returns:
        Dictionary with commit_log, commit_log_detailed, diff_stat,
        diff_stat_summary, full_diff, and uncommitted keys.
    """
    ref_range = f"{base_branch}..{current_branch}"
    return {
        "commit_log": _safe_git(["log", ref_range, "--oneline"], cwd=cwd),
        "commit_log_detailed": _safe_git(
            [
                "log",
                ref_range,
                "--pretty=format:%h %s%n  Author: %an <%ae>%n  Date: %ad%n",
                "--date=short",
            ],
            cwd=cwd,
        ),
        "diff_stat": _safe_git(["diff", ref_range, "--stat"], cwd=cwd),
        "diff_stat_summary": _safe_git(["diff", ref_range, "--shortstat"], cwd=cwd),
        "full_diff": _safe_git(["diff", ref_range], cwd=cwd),
        "uncommitted": _safe_git(["status", "--short"], cwd=cwd),
    }


def _build_diff_section(full_diff: str) -> str:
    """Build the full diff Markdown section, truncating if needed.

    Args:
        full_diff: The raw diff string.

    Returns:
        Formatted Markdown section.
    """
    max_diff_chars = 50000
    if len(full_diff) > max_diff_chars:
        return (
            "## Full Diff (truncated)\n\n"
            f"_Diff is {len(full_diff):,} characters — showing first "
            f"{max_diff_chars:,} characters._\n\n"
            f"```diff\n{full_diff[:max_diff_chars]}\n```"
        )
    return f"## Full Diff\n\n```diff\n{full_diff}\n```"


def _build_next_steps(*, has_conflicts: bool, is_update: bool) -> str:
    """Build the next steps Markdown section.

    Args:
        has_conflicts: Whether merge conflicts were detected.
        is_update: Whether an existing PR was detected (update mode).

    Returns:
        Formatted Markdown section.
    """
    steps = "## Next Steps\n\nFollow the workflow defined in the system prompt:\n\n"
    if has_conflicts:
        steps += "1. **Resolve conflicts** — Ask the user whether to rebase or merge.\n"
    if is_update:
        steps += (
            "2. **Update the PR description** — Incorporate the new commits and "
            "changes into the existing PR body. Keep existing context that is "
            "still relevant, add a new section for the latest changes.\n"
            "3. **Fill in the checklist** — Revise items based on current state.\n"
            "4. \u26d4 **PRESENT TO USER FOR APPROVAL** — Show the updated PR "
            "description and wait for approval before updating.\n"
            "5. **Push branch** — `git push` if there are unpushed commits.\n"
            "6. **Update the PR** — Use GitHub MCP tools (`mcp_github_update_pull_request`) "
            "or `gh pr edit`.\n"
            "7. **Report** — Confirm the PR has been updated."
        )
    else:
        steps += (
            "2. **Generate the PR description** — Use the commit log, diff stats, "
            "and template from the system prompt.\n"
            "3. **Fill in the checklist** — Mark items that can be verified.\n"
            "4. \u26d4 **PRESENT TO USER FOR APPROVAL** — Show the full PR description "
            "and wait for approval before creating.\n"
            "5. **Push branch** — `git push -u origin <branch>` if not already pushed.\n"
            "6. **Create the PR** — Use GitHub MCP tools or `gh pr create`.\n"
            "7. **Report** — Share the PR URL with the user."
        )
    return steps


def _build_branch_block(current_branch: str, base_branch: str, pr_title: str, issue_number: str) -> str:
    """Build the branch information Markdown block.

    Args:
        current_branch: Current branch name.
        base_branch: Base branch name.
        pr_title: Suggested PR title (may be empty).
        issue_number: Related issue number (may be empty).

    Returns:
        Formatted Markdown section.
    """
    block = (
        "## Branch Information\n\n"
        f"- **Current branch**: `{current_branch}`\n"
        f"- **Base branch**: `{base_branch}`\n"
        f"- **PR title suggestion**: {pr_title or '_(derive from commits)_'}"
    )
    if issue_number:
        block += f"\n- **Related issue**: #{issue_number.lstrip('#')}"
    return block


def _build_conflict_block(conflict_info: dict[str, str | bool], base_branch: str) -> str:
    """Build the conflict check Markdown section.

    Args:
        conflict_info: Dictionary from ``_check_conflicts``.
        base_branch: Base branch name (used in resolution commands).

    Returns:
        Formatted Markdown section.
    """
    if conflict_info["has_conflicts"]:
        return (
            "## \u26a0\ufe0f Merge Conflicts Detected\n\n"
            f"{conflict_info['details']}\n\n"
            "**Action required**: Ask the user how to resolve:\n"
            f"1. **Rebase** — `git rebase {base_branch}` (rewrite history, cleaner log)\n"
            f"2. **Merge** — `git merge {base_branch}` (preserve history)\n"
            "3. **Skip** — Create the PR with conflicts noted"
        )
    return f"## Conflict Check\n\n{conflict_info['details']}"


def _detect_existing_pr(current_branch: str, *, cwd: str | None = None) -> dict[str, str | int | None]:
    """Detect if a pull request already exists for the current branch.

    Uses ``gh pr list`` to check for open PRs whose head is the current
    branch.

    Args:
        current_branch: The branch name to look up.
        cwd: Working directory for the command (optional).

    Returns:
        A dictionary with ``number``, ``title``, ``url``, and ``body``
        if an existing PR is found, or an empty dict otherwise.
    """
    cmd = [
        "gh",
        "pr",
        "list",
        "--head",
        current_branch,
        "--state",
        "open",
        "--json",
        "number,title,url,body",
        "--limit",
        "1",
    ]
    logger.info("Checking for existing PR: %s", " ".join(cmd))
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd=cwd,
            timeout=30,
        )
        prs = json.loads(result.stdout.strip() or "[]")
        if prs:
            pr = prs[0]
            logger.info("Found existing PR #%s: %s", pr["number"], pr["title"])
            return {
                "number": pr["number"],
                "title": pr.get("title", ""),
                "url": pr.get("url", ""),
                "body": pr.get("body", ""),
            }
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        logger.warning("Could not check for existing PRs: %s", exc)

    return {}


def _build_existing_pr_section(pr_info: dict[str, str | int | None]) -> str:
    """Build a Markdown section describing the existing PR.

    Args:
        pr_info: Dictionary with ``number``, ``title``, ``url``, ``body``.

    Returns:
        Formatted Markdown section.
    """
    body_preview = str(pr_info.get("body") or "_(empty)_")
    max_body_preview = 3000
    if len(body_preview) > max_body_preview:
        body_preview = body_preview[:max_body_preview] + "\n\n_(truncated)_"

    return (
        "## \U0001f504 Existing Pull Request Detected\n\n"
        f"A PR already exists for this branch:\n\n"
        f"- **PR**: #{pr_info['number']}\n"
        f"- **Title**: {pr_info['title']}\n"
        f"- **URL**: {pr_info['url']}\n\n"
        "**Current PR description:**\n\n"
        f"<details>\n<summary>Click to expand current PR body</summary>\n\n"
        f"{body_preview}\n\n</details>\n\n"
        "**Action**: Update the existing PR description to incorporate the "
        "latest changes. Keep relevant existing content and add new commit "
        "details. Use `mcp_github_update_pull_request` or `gh pr edit` to "
        "apply the update."
    )


def _build_commit_sections(data: dict[str, str]) -> list[str]:
    """Build commit log Markdown sections.

    Args:
        data: Branch data dictionary from ``_gather_branch_data``.

    Returns:
        List of Markdown sections for commit log.
    """
    sections: list[str] = []
    if data["commit_log"]:
        sections.append(f"## Commit Log (oneline)\n\n```\n{data['commit_log']}\n```")
        if data["commit_log_detailed"]:
            sections.append(f"## Commit Log (detailed)\n\n```\n{data['commit_log_detailed']}\n```")
    else:
        sections.append(
            "## Commit Log\n\n"
            "_No commits found between the current branch and the base. "
            "There is nothing to create a PR for._"
        )

    if data["diff_stat"]:
        sections.append(f"## Diff Stats\n\n```\n{data['diff_stat']}\n```\n\n**Summary**: `{data['diff_stat_summary']}`")

    if data["full_diff"]:
        sections.append(_build_diff_section(data["full_diff"]))

    return sections


def create_pr(
    base_branch: str = "",
    pr_title: str = "",
    issue_number: str = "",
    repo_path: str = "",
) -> str:
    """Compare the current branch with the base and prepare a pull request.

    Gathers the full commit log, diff stats, and detailed changes between
    the current branch and the base branch. Checks for merge/rebase
    conflicts. If a PR already exists for the current branch, includes
    the existing PR context so the LLM can update it instead of creating
    a duplicate. Returns a structured prompt that guides the LLM through
    generating or updating the PR description, obtaining user approval,
    and creating/updating the pull request.

    Args:
        base_branch: Base branch to create the PR against. Leave empty to
            auto-detect the default branch (optional).
        pr_title: Suggested title for the PR. Leave empty to derive from
            commit history (optional).
        issue_number: Related issue number to reference in the PR
            (e.g. ``"42"`` or ``"#42"``). Optional.
        repo_path: Path to the repository root. Leave empty to use the
            current working directory (optional).

    Returns:
        A structured Markdown workflow prompt containing branch comparison
        data, conflict analysis, and step-by-step instructions for
        creating the pull request.

    Raises:
        RuntimeError: If ``git`` commands fail (not in a git repository,
            network issues, etc.).
    """
    cwd = repo_path if repo_path else None
    logger.info(
        "create_pr invoked — base_branch: %s, pr_title: %s, issue: %s",
        base_branch or "(auto-detect)",
        pr_title or "(derive from commits)",
        issue_number or "(none)",
    )

    # ── Determine branches ───────────────────────────────────────────────
    current_branch = _run_git_command(["branch", "--show-current"], cwd=cwd)

    if not base_branch:
        base_branch = _detect_base_branch()

    logger.info("Comparing %s → %s", current_branch, base_branch)

    # ── Fetch latest from remote ─────────────────────────────────────────
    try:
        _run_git_command(["fetch", "origin"], cwd=cwd)
    except RuntimeError as exc:
        logger.warning("Could not fetch from origin: %s", exc)

    # ── Gather all branch data ───────────────────────────────────────────
    data = _gather_branch_data(current_branch, base_branch, cwd)
    conflict_info = _check_conflicts(base_branch)
    existing_pr = _detect_existing_pr(current_branch, cwd=cwd)
    is_update = bool(existing_pr)

    # ── Assemble output ─────────────────────────────────────────────────
    sections: list[str] = [_SYSTEM_PROMPT]
    sections.append(_build_branch_block(current_branch, base_branch, pr_title, issue_number))

    if existing_pr:
        sections.append(_build_existing_pr_section(existing_pr))

    if data["uncommitted"]:
        sections.append(
            "## \u26a0\ufe0f Uncommitted Changes Detected\n\n"
            "The working tree has uncommitted changes. Consider committing them "
            "first (you can use the `progressive_commit` tool).\n\n"
            f"```\n{data['uncommitted']}\n```"
        )

    sections.append(_build_conflict_block(conflict_info, base_branch))
    sections.extend(_build_commit_sections(data))
    sections.append(_build_next_steps(has_conflicts=bool(conflict_info["has_conflicts"]), is_update=is_update))

    return "\n\n---\n\n".join(sections)
