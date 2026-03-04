"""MCP tool: apply_issue — Implement a GitHub issue end-to-end.

This module defines the ``apply_issue`` tool which accepts a GitHub issue URL
and the issue details (fetched by the calling agent via ``mcp_github_issue_read``),
creates a branch using ``gh buddy``, and returns a structured workflow prompt
that guides the LLM through planning, implementation, self-review, and PR creation.

Prerequisites:
    - ``gh`` CLI installed and authenticated.
    - ``gh buddy`` extension installed (``gh extension install jesusgpo/gh-buddy``).

Note:
    This tool does NOT fetch issue details itself.  The calling agent MUST
    use the GitHub MCP tool ``mcp_github_issue_read`` to retrieve the issue
    title, body, labels, etc. and pass them as parameters.
"""

import logging
import re
import subprocess

from utils.prompt_loader import load_prompt_cached

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────
PROMPT_FILENAME: str = "apply_issue.md"
TOOL_NAME: str = "apply_issue"
TOOL_DESCRIPTION: str = (
    "Implement a GitHub issue end-to-end. "
    "IMPORTANT: Before calling this tool, you MUST fetch the issue details "
    "using the `mcp_github_issue_read` GitHub MCP tool and pass them as "
    "parameters (issue_title, issue_body, issue_labels). "
    "Accepts a GitHub issue URL (e.g. https://github.com/owner/repo/issues/42), "
    "the pre-fetched issue metadata, and a branch type. "
    "Creates a branch via `gh buddy`, checks it out, and returns a structured "
    "workflow that guides through: action plan proposal, user approval, "
    "implementation following best practices, self-review using the "
    "`review_pr` tool, and PR creation."
)

_SYSTEM_PROMPT: str = load_prompt_cached(PROMPT_FILENAME)

# ── Valid parameter values ───────────────────────────────────────────────────
VALID_BRANCH_TYPES: frozenset[str] = frozenset(
    {"feature", "bugfix", "hotfix", "release", "chore", "docs", "refactor", "test"}
)

# ── URL parsing pattern ─────────────────────────────────────────────────────
_ISSUE_URL_PATTERN: re.Pattern[str] = re.compile(
    r"https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/issues/(?P<number>\d+)"
)


def _parse_issue_url(issue_url: str) -> tuple[str, str, int]:
    """Extract owner, repo, and issue number from a GitHub issue URL.

    Args:
        issue_url: Full GitHub issue URL.

    Returns:
        A tuple of (owner, repo, issue_number).

    Raises:
        ValueError: If the URL does not match the expected GitHub issue format.
    """
    match = _ISSUE_URL_PATTERN.match(issue_url.strip())
    if not match:
        msg = (
            f"Invalid GitHub issue URL: '{issue_url}'. "
            "Expected format: https://github.com/<owner>/<repo>/issues/<number>"
        )
        raise ValueError(msg)
    return match.group("owner"), match.group("repo"), int(match.group("number"))


def _run_gh_command(args: list[str], *, cwd: str | None = None) -> str:
    """Execute a ``gh`` CLI command and return its stdout.

    Args:
        args: Command arguments (without the leading ``gh``).
        cwd: Working directory for the command (optional).

    Returns:
        The stripped stdout output of the command.

    Raises:
        RuntimeError: If the command exits with a non-zero status.
    """
    cmd = ["gh", *args]
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
        msg = f"gh command failed (exit {exc.returncode}): {stderr}"
        raise RuntimeError(msg) from exc
    except subprocess.TimeoutExpired as exc:
        msg = f"gh command timed out after 60s: {' '.join(cmd)}"
        raise RuntimeError(msg) from exc
    return result.stdout.strip()


def _create_branch(
    issue_number: int,
    branch_type: str,
    base_branch: str,
) -> str:
    """Create and checkout a branch using ``gh buddy create-branch``.

    Args:
        issue_number: The GitHub issue number.
        branch_type: Branch type (feature, bugfix, etc.).
        base_branch: Base branch to branch from (empty for default).

    Returns:
        The name of the created branch.

    Raises:
        RuntimeError: If the branch creation or checkout fails.
    """
    cmd_args = [
        "buddy",
        "create-branch",
        "--issue",
        str(issue_number),
        "--type",
        branch_type,
        "-y",
    ]
    if base_branch:
        cmd_args.extend(["--base", base_branch])

    output = _run_gh_command(cmd_args)
    logger.info("gh buddy create-branch output: %s", output)

    # Extract branch name from output — gh buddy prints the branch name
    # Try to find a line containing the branch pattern
    branch_name = ""
    for line in output.splitlines():
        stripped = line.strip()
        # gh buddy typically outputs something like: "Switched to branch 'feature/GH-42-...'"
        # or just the branch name
        branch_pattern = (
            r"(?:branch\s+['\"]?)?("
            r"(?:feature|bugfix|hotfix|release|chore|docs|refactor|test)"
            r"/GH-\d+-[\w-]+)"
        )
        branch_match = re.search(branch_pattern, stripped)
        if branch_match:
            branch_name = branch_match.group(1)
            break

    if not branch_name:
        # Fallback: get current branch name from git
        try:
            branch_name = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            ).stdout.strip()
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            branch_name = f"{branch_type}/GH-{issue_number}-unknown"

    logger.info("Created and checked out branch: %s", branch_name)
    return branch_name


def apply_issue(
    issue_url: str,
    issue_title: str,
    issue_body: str = "",
    issue_labels: str = "",
    branch_type: str = "feature",
    base_branch: str = "",
    repo_context: str = "",
) -> str:
    """Implement a GitHub issue end-to-end: branch, plan, code, review.

    The calling agent MUST fetch the issue details using the GitHub MCP
    tool ``mcp_github_issue_read`` before invoking this tool, and pass
    the retrieved title, body, and labels as parameters.

    This tool then creates a dedicated branch using ``gh buddy``, checks
    it out, and returns a structured prompt that guides the LLM through
    the full implementation workflow: action plan, user approval, coding,
    self-review via ``review_pr``, and PR creation.

    Args:
        issue_url: Full GitHub issue URL
            (e.g. ``https://github.com/owner/repo/issues/42``).
        issue_title: Title of the issue (fetched via
            ``mcp_github_issue_read``).
        issue_body: Body / description of the issue (fetched via
            ``mcp_github_issue_read``). Defaults to empty string.
        issue_labels: Comma-separated list of issue labels (fetched via
            ``mcp_github_issue_read``). Defaults to empty string.
        branch_type: Type of branch to create. One of ``"feature"``
            (default), ``"bugfix"``, ``"hotfix"``, ``"release"``,
            ``"chore"``, ``"docs"``, ``"refactor"``, or ``"test"``.
        base_branch: Base branch to branch from. Leave empty to use the
            repository default branch (optional).
        repo_context: Free-text description of the repository context such
            as frameworks, architecture, Python version, and coding
            conventions (optional).

    Returns:
        A structured Markdown workflow prompt containing the issue details,
        branch information, and step-by-step instructions for the LLM to
        follow.

    Raises:
        ValueError: If ``issue_url`` is empty or malformed, if
            ``issue_title`` is empty, or if ``branch_type`` is invalid.
        RuntimeError: If ``gh buddy`` CLI commands fail (authentication,
            network, missing extension, etc.).
    """
    # ── Validate inputs ──────────────────────────────────────────────────
    if not issue_url or not issue_url.strip():
        msg = "issue_url must not be empty. Provide a GitHub issue URL (e.g. https://github.com/owner/repo/issues/42)."
        raise ValueError(msg)

    if not issue_title or not issue_title.strip():
        msg = (
            "issue_title must not be empty. Fetch the issue details using "
            "mcp_github_issue_read before calling this tool."
        )
        raise ValueError(msg)

    if branch_type not in VALID_BRANCH_TYPES:
        msg = f"Invalid branch_type '{branch_type}'. Must be one of: {sorted(VALID_BRANCH_TYPES)}"
        raise ValueError(msg)

    # ── Parse URL ────────────────────────────────────────────────────────
    owner, repo, issue_number = _parse_issue_url(issue_url)
    logger.info(
        "apply_issue invoked — %s/%s#%d (type: %s)",
        owner,
        repo,
        issue_number,
        branch_type,
    )

    # ── Create branch via gh buddy ───────────────────────────────────────
    branch_name = _create_branch(
        issue_number=issue_number,
        branch_type=branch_type,
        base_branch=base_branch,
    )

    # ── Assemble output ─────────────────────────────────────────────────
    sections: list[str] = [_SYSTEM_PROMPT]

    # Issue details (pre-fetched by agent via mcp_github_issue_read)
    issue_block_lines = [
        "## Issue Details\n",
        f"- **Issue**: #{issue_number}",
        f"- **Title**: {issue_title.strip()}",
        f"- **Labels**: {issue_labels.strip() or 'none'}",
        f"- **URL**: {issue_url.strip()}",
    ]
    sections.append("\n".join(issue_block_lines))

    # Issue body / description
    body_text = issue_body.strip() if issue_body else "_No description provided._"
    sections.append(f"## Issue Description\n\n{body_text}")

    # Branch info
    branch_block = (
        "## Branch Information\n\n"
        f"- **Branch**: `{branch_name}`\n"
        f"- **Type**: {branch_type}\n"
        f"- **Base**: {base_branch or '(default branch)'}\n"
        f"- **Repository**: {owner}/{repo}"
    )
    sections.append(branch_block)

    # Repository context
    if repo_context and repo_context.strip():
        sections.append(f"## Repository Context\n\n{repo_context.strip()}")

    # Workflow reminder
    workflow_reminder = (
        "## Next Steps\n\n"
        "1. **Read and understand** the issue description and acceptance criteria above.\n"
        "2. **Propose an action plan** using the format specified in the system prompt.\n"
        "3. \u26d4 **STOP AND WAIT FOR USER APPROVAL** — Do NOT write any code, "
        "create any file, or make any change until the user explicitly approves "
        'the plan (e.g. "ok", "go ahead", "approved"). If the user requests '
        "changes, revise the plan and wait again.\n"
        "4. **Implement** the approved plan following coding standards.\n"
        "5. **Self-review** by calling the `review_pr` MCP tool with your diff.\n"
        "6. **Fix** any blocker or major findings from the review.\n"
        "7. **Create a PR** using `gh buddy create-pr -y` linking back to issue "
        f"#{issue_number}."
    )
    sections.append(workflow_reminder)

    return "\n\n---\n\n".join(sections)
