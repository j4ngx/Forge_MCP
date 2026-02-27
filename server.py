"""forge_mcp — FastMCP server entrypoint.

This module creates the :class:`FastMCP` server instance, registers every
tool defined under the ``tools/`` package, and exposes the ``main()``
function used by the ``[project.scripts]`` console entrypoint.

Usage (stdio transport for VS Code Copilot Agent Mode)::

    uv run server.py
"""

import logging
import sys

from mcp.server.fastmcp import FastMCP

from tools.analyze_code import TOOL_DESCRIPTION as ANALYZE_CODE_DESCRIPTION
from tools.analyze_code import TOOL_NAME as ANALYZE_CODE_NAME
from tools.analyze_code import analyze_code
from tools.decompose_function import TOOL_DESCRIPTION as DECOMPOSE_FUNCTION_DESCRIPTION
from tools.decompose_function import TOOL_NAME as DECOMPOSE_FUNCTION_NAME
from tools.decompose_function import decompose_function
from tools.explain_code import TOOL_DESCRIPTION as EXPLAIN_CODE_DESCRIPTION
from tools.explain_code import TOOL_NAME as EXPLAIN_CODE_NAME
from tools.explain_code import explain_code
from tools.generate_changelog_entry import TOOL_DESCRIPTION as GENERATE_CHANGELOG_ENTRY_DESCRIPTION
from tools.generate_changelog_entry import TOOL_NAME as GENERATE_CHANGELOG_ENTRY_NAME
from tools.generate_changelog_entry import generate_changelog_entry
from tools.generate_docstrings import TOOL_DESCRIPTION as GENERATE_DOCSTRINGS_DESCRIPTION
from tools.generate_docstrings import TOOL_NAME as GENERATE_DOCSTRINGS_NAME
from tools.generate_docstrings import generate_docstrings
from tools.generate_module_doc import TOOL_DESCRIPTION as GENERATE_MODULE_DOC_DESCRIPTION
from tools.generate_module_doc import TOOL_NAME as GENERATE_MODULE_DOC_NAME
from tools.generate_module_doc import generate_module_doc
from tools.generate_test_fixtures import TOOL_DESCRIPTION as GENERATE_TEST_FIXTURES_DESCRIPTION
from tools.generate_test_fixtures import TOOL_NAME as GENERATE_TEST_FIXTURES_NAME
from tools.generate_test_fixtures import generate_test_fixtures
from tools.generate_unit_tests import TOOL_DESCRIPTION as GENERATE_UNIT_TESTS_DESCRIPTION
from tools.generate_unit_tests import TOOL_NAME as GENERATE_UNIT_TESTS_NAME
from tools.generate_unit_tests import generate_unit_tests
from tools.modernize_python import TOOL_DESCRIPTION as MODERNIZE_PYTHON_DESCRIPTION
from tools.modernize_python import TOOL_NAME as MODERNIZE_PYTHON_NAME
from tools.modernize_python import modernize_python
from tools.review_pr import TOOL_DESCRIPTION as REVIEW_PR_DESCRIPTION
from tools.review_pr import TOOL_NAME as REVIEW_PR_NAME
from tools.review_pr import review_pr
from tools.suggest_refactoring import TOOL_DESCRIPTION as SUGGEST_REFACTORING_DESCRIPTION
from tools.suggest_refactoring import TOOL_NAME as SUGGEST_REFACTORING_NAME
from tools.suggest_refactoring import suggest_refactoring
from tools.suggest_test_cases import TOOL_DESCRIPTION as SUGGEST_TEST_CASES_DESCRIPTION
from tools.suggest_test_cases import TOOL_NAME as SUGGEST_TEST_CASES_NAME
from tools.suggest_test_cases import suggest_test_cases
from tools.suggest_type_hints import TOOL_DESCRIPTION as SUGGEST_TYPE_HINTS_DESCRIPTION
from tools.suggest_type_hints import TOOL_NAME as SUGGEST_TYPE_HINTS_NAME
from tools.suggest_type_hints import suggest_type_hints

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

# ── Server instance ──────────────────────────────────────────────────────────
mcp = FastMCP(
    name="forge_mcp",
    instructions=(
        "forge_mcp is a collection of developer-productivity tools exposed "
        "via the Model Context Protocol. Use the available tools to review "
        "pull requests, generate documentation, write tests, and more."
    ),
)

# ── Tool registration ───────────────────────────────────────────────────────


@mcp.tool(name=REVIEW_PR_NAME, description=REVIEW_PR_DESCRIPTION)
def tool_review_pr(
    pr_diff: str,
    pr_title: str = "",
    pr_description: str = "",
    pr_author: str = "",
    pr_url: str = "",
    repo_context: str = "",
    severity_scope: str = "all",
    review_focus: str = "balanced",
    detail_level: str = "thorough",
) -> str:
    """Perform a senior-level Python PR code review.

    Args:
        pr_diff: The full Git diff content of the pull request.
        pr_title: Title of the pull request (optional).
        pr_description: Body / description of the pull request (optional).
        pr_author: Username of the PR author (optional).
        pr_url: GitHub PR URL — enables posting the review as a PR comment
            when GitHub MCP tools are available (optional).
        repo_context: Free-text description of frameworks, architecture,
            target Python version, and coding conventions (optional).
        severity_scope: ``"blockers_only"``, ``"blockers_and_major"``, or
            ``"all"`` (default).
        review_focus: ``"logic"``, ``"performance"``, ``"security"``,
            ``"style"``, or ``"balanced"`` (default).
        detail_level: ``"summary"`` or ``"thorough"`` (default).

    Returns:
        A structured Markdown review produced by the senior PR reviewer prompt.
    """
    try:
        return review_pr(
            pr_diff=pr_diff,
            pr_title=pr_title,
            pr_description=pr_description,
            pr_author=pr_author,
            pr_url=pr_url,
            repo_context=repo_context,
            severity_scope=severity_scope,
            review_focus=review_focus,
            detail_level=detail_level,
        )
    except ValueError as exc:
        logger.error("review_pr validation error: %s", exc)
        return f"Error: {exc}"
    except Exception as exc:
        logger.exception("Unexpected error in review_pr")
        return f"An unexpected error occurred while reviewing the PR: {exc}"


# ── Code Quality tools ───────────────────────────────────────────────────────


@mcp.tool(name=ANALYZE_CODE_NAME, description=ANALYZE_CODE_DESCRIPTION)
def tool_analyze_code(
    code: str,
    file_path: str = "",
    analysis_focus: str = "all",
    detail_level: str = "standard",
) -> str:
    """Analyze Python code for quality, complexity, and security issues.

    Args:
        code: The Python source code to analyze.
        file_path: Path of the file being analyzed (optional).
        analysis_focus: ``"all"`` (default), ``"complexity"``,
            ``"smells"``, ``"security"``, or ``"style"``.
        detail_level: ``"brief"``, ``"standard"`` (default), or
            ``"verbose"``.

    Returns:
        A structured Markdown analysis report.
    """
    try:
        return analyze_code(
            code=code,
            file_path=file_path,
            analysis_focus=analysis_focus,
            detail_level=detail_level,
        )
    except ValueError as exc:
        logger.error("analyze_code validation error: %s", exc)
        return f"Error: {exc}"
    except Exception as exc:
        logger.exception("Unexpected error in analyze_code")
        return f"An unexpected error occurred while analyzing code: {exc}"


@mcp.tool(name=SUGGEST_TYPE_HINTS_NAME, description=SUGGEST_TYPE_HINTS_DESCRIPTION)
def tool_suggest_type_hints(
    code: str,
    file_path: str = "",
    strictness: str = "strict",
    include_return_types: bool = True,
) -> str:
    """Suggest type annotations for Python code.

    Args:
        code: The Python source code to analyze.
        file_path: Path of the file being analyzed (optional).
        strictness: ``"basic"``, ``"strict"`` (default), or ``"complete"``.
        include_return_types: Include return type suggestions (default True).

    Returns:
        A structured Markdown report with type hint suggestions.
    """
    try:
        return suggest_type_hints(
            code=code,
            file_path=file_path,
            strictness=strictness,
            include_return_types=include_return_types,
        )
    except ValueError as exc:
        logger.error("suggest_type_hints validation error: %s", exc)
        return f"Error: {exc}"
    except Exception as exc:
        logger.exception("Unexpected error in suggest_type_hints")
        return f"An unexpected error occurred while suggesting type hints: {exc}"


@mcp.tool(name=EXPLAIN_CODE_NAME, description=EXPLAIN_CODE_DESCRIPTION)
def tool_explain_code(
    code: str,
    file_path: str = "",
    audience: str = "mid",
    explain_focus: str = "overview",
) -> str:
    """Explain what Python code does.

    Args:
        code: The Python source code to explain.
        file_path: Path of the file being explained (optional).
        audience: ``"junior"``, ``"mid"`` (default), or ``"senior"``.
        explain_focus: ``"overview"`` (default), ``"flow"``,
            ``"complexity"``, or ``"dependencies"``.

    Returns:
        A structured Markdown explanation adapted to the audience level.
    """
    try:
        return explain_code(
            code=code,
            file_path=file_path,
            audience=audience,
            explain_focus=explain_focus,
        )
    except ValueError as exc:
        logger.error("explain_code validation error: %s", exc)
        return f"Error: {exc}"
    except Exception as exc:
        logger.exception("Unexpected error in explain_code")
        return f"An unexpected error occurred while explaining code: {exc}"


# ── Documentation tools ──────────────────────────────────────────────────────


@mcp.tool(name=GENERATE_DOCSTRINGS_NAME, description=GENERATE_DOCSTRINGS_DESCRIPTION)
def tool_generate_docstrings(
    code: str,
    file_path: str = "",
    docstring_style: str = "google",
    include_examples: bool = True,
    include_raises: bool = True,
) -> str:
    """Generate or improve docstrings for Python code.

    Args:
        code: The Python source code to document.
        file_path: Path of the file being documented (optional).
        docstring_style: ``"google"`` (default), ``"numpy"``, or ``"sphinx"``.
        include_examples: Include usage examples (default True).
        include_raises: Include Raises sections (default True).

    Returns:
        The documented code with complete docstrings.
    """
    try:
        return generate_docstrings(
            code=code,
            file_path=file_path,
            docstring_style=docstring_style,
            include_examples=include_examples,
            include_raises=include_raises,
        )
    except ValueError as exc:
        logger.error("generate_docstrings validation error: %s", exc)
        return f"Error: {exc}"
    except Exception as exc:
        logger.exception("Unexpected error in generate_docstrings")
        return f"An unexpected error occurred while generating docstrings: {exc}"


@mcp.tool(name=GENERATE_MODULE_DOC_NAME, description=GENERATE_MODULE_DOC_DESCRIPTION)
def tool_generate_module_doc(
    code: str,
    module_name: str = "",
    doc_sections: str = "overview,usage,api",
    target_audience: str = "both",
) -> str:
    """Generate module-level documentation for Python code.

    Args:
        code: The Python module source code.
        module_name: Module name for the header (optional).
        doc_sections: Comma-separated sections: ``"overview"``,
            ``"usage"``, ``"api"``, ``"examples"``.
        target_audience: ``"user"``, ``"developer"``, or ``"both"``
            (default).

    Returns:
        Comprehensive module documentation in Markdown.
    """
    try:
        return generate_module_doc(
            code=code,
            module_name=module_name,
            doc_sections=doc_sections,
            target_audience=target_audience,
        )
    except ValueError as exc:
        logger.error("generate_module_doc validation error: %s", exc)
        return f"Error: {exc}"
    except Exception as exc:
        logger.exception("Unexpected error in generate_module_doc")
        return f"An unexpected error occurred while generating module documentation: {exc}"


@mcp.tool(name=GENERATE_CHANGELOG_ENTRY_NAME, description=GENERATE_CHANGELOG_ENTRY_DESCRIPTION)
def tool_generate_changelog_entry(
    changes: str,
    version: str = "",
    change_type: str = "auto",
    project_context: str = "",
) -> str:
    """Generate a CHANGELOG entry from changes.

    Args:
        changes: Diff, commit list, or description of changes.
        version: Semantic version (e.g., ``"1.2.0"``). Defaults to
            ``"[Unreleased]"``.
        change_type: ``"auto"`` (default), ``"added"``, ``"changed"``,
            ``"deprecated"``, ``"removed"``, ``"fixed"``, or ``"security"``.
        project_context: Additional project context (optional).

    Returns:
        A Markdown changelog entry ready for CHANGELOG.md.
    """
    try:
        return generate_changelog_entry(
            changes=changes,
            version=version,
            change_type=change_type,
            project_context=project_context,
        )
    except ValueError as exc:
        logger.error("generate_changelog_entry validation error: %s", exc)
        return f"Error: {exc}"
    except Exception as exc:
        logger.exception("Unexpected error in generate_changelog_entry")
        return f"An unexpected error occurred while generating changelog entry: {exc}"


# ── Testing tools ────────────────────────────────────────────────────────────


@mcp.tool(name=GENERATE_UNIT_TESTS_NAME, description=GENERATE_UNIT_TESTS_DESCRIPTION)
def tool_generate_unit_tests(
    code: str,
    file_path: str = "",
    test_framework: str = "pytest",
    use_polyfactory: bool = True,
    coverage_focus: str = "comprehensive",
) -> str:
    """Generate pytest unit tests for Python code.

    Args:
        code: The Python source code to test.
        file_path: Path of the source file (optional).
        test_framework: ``"pytest"`` (only supported framework).
        use_polyfactory: Generate Polyfactory factories (default True).
        coverage_focus: ``"happy_path"``, ``"edge_cases"``, ``"errors"``,
            or ``"comprehensive"`` (default).

    Returns:
        A complete, runnable pytest test file.
    """
    try:
        return generate_unit_tests(
            code=code,
            file_path=file_path,
            test_framework=test_framework,
            use_polyfactory=use_polyfactory,
            coverage_focus=coverage_focus,
        )
    except ValueError as exc:
        logger.error("generate_unit_tests validation error: %s", exc)
        return f"Error: {exc}"
    except Exception as exc:
        logger.exception("Unexpected error in generate_unit_tests")
        return f"An unexpected error occurred while generating unit tests: {exc}"


@mcp.tool(name=GENERATE_TEST_FIXTURES_NAME, description=GENERATE_TEST_FIXTURES_DESCRIPTION)
def tool_generate_test_fixtures(
    code: str,
    models_code: str = "",
    file_path: str = "",
    fixture_scope: str = "function",
    include_factories: bool = True,
) -> str:
    """Generate pytest fixtures and Polyfactory factories.

    Args:
        code: The Python source code to generate fixtures for.
        models_code: Model definitions (Pydantic, dataclasses, etc.)
            used by the source code (optional).
        file_path: Path of the source file (optional).
        fixture_scope: ``"function"`` (default), ``"class"``,
            ``"module"``, or ``"session"``.
        include_factories: Generate Polyfactory factories (default True).

    Returns:
        conftest.py and factories.py content in Markdown.
    """
    try:
        return generate_test_fixtures(
            code=code,
            models_code=models_code,
            file_path=file_path,
            fixture_scope=fixture_scope,
            include_factories=include_factories,
        )
    except ValueError as exc:
        logger.error("generate_test_fixtures validation error: %s", exc)
        return f"Error: {exc}"
    except Exception as exc:
        logger.exception("Unexpected error in generate_test_fixtures")
        return f"An unexpected error occurred while generating test fixtures: {exc}"


@mcp.tool(name=SUGGEST_TEST_CASES_NAME, description=SUGGEST_TEST_CASES_DESCRIPTION)
def tool_suggest_test_cases(
    code: str,
    file_path: str = "",
    test_depth: str = "thorough",
    include_integration: bool = False,
) -> str:
    """Enumerate test cases for Python code without writing test code.

    Args:
        code: The Python source code to analyze.
        file_path: Path of the source file (optional).
        test_depth: ``"basic"``, ``"thorough"`` (default), or
            ``"exhaustive"``.
        include_integration: Include integration test suggestions
            (default False).

    Returns:
        A structured test plan with prioritized test cases.
    """
    try:
        return suggest_test_cases(
            code=code,
            file_path=file_path,
            test_depth=test_depth,
            include_integration=include_integration,
        )
    except ValueError as exc:
        logger.error("suggest_test_cases validation error: %s", exc)
        return f"Error: {exc}"
    except Exception as exc:
        logger.exception("Unexpected error in suggest_test_cases")
        return f"An unexpected error occurred while suggesting test cases: {exc}"


# ── Refactoring tools ────────────────────────────────────────────────────────


@mcp.tool(name=SUGGEST_REFACTORING_NAME, description=SUGGEST_REFACTORING_DESCRIPTION)
def tool_suggest_refactoring(
    code: str,
    file_path: str = "",
    refactor_goals: str = "all",
    max_suggestions: int = 10,
) -> str:
    """Propose refactoring opportunities for Python code.

    Args:
        code: The Python source code to analyze.
        file_path: Path of the file being analyzed (optional).
        refactor_goals: ``"readability"``, ``"performance"``,
            ``"maintainability"``, ``"testability"``, or ``"all"``
            (default).
        max_suggestions: Max suggestions (1-50, default 10).

    Returns:
        Prioritized refactoring suggestions with before/after code.
    """
    try:
        return suggest_refactoring(
            code=code,
            file_path=file_path,
            refactor_goals=refactor_goals,
            max_suggestions=max_suggestions,
        )
    except ValueError as exc:
        logger.error("suggest_refactoring validation error: %s", exc)
        return f"Error: {exc}"
    except Exception as exc:
        logger.exception("Unexpected error in suggest_refactoring")
        return f"An unexpected error occurred while suggesting refactorings: {exc}"


@mcp.tool(name=MODERNIZE_PYTHON_NAME, description=MODERNIZE_PYTHON_DESCRIPTION)
def tool_modernize_python(
    code: str,
    file_path: str = "",
    min_python_version: str = "3.11",
    aggressive: bool = False,
) -> str:
    """Suggest modern Python 3.11+ idioms for code.

    Args:
        code: The Python source code to modernize.
        file_path: Path of the file being analyzed (optional).
        min_python_version: ``"3.11"`` (default), ``"3.12"``, or ``"3.13"``.
        aggressive: Suggest all modernizations including structural
            rewrites (default False).

    Returns:
        A modernization report with before/after suggestions.
    """
    try:
        return modernize_python(
            code=code,
            file_path=file_path,
            min_python_version=min_python_version,
            aggressive=aggressive,
        )
    except ValueError as exc:
        logger.error("modernize_python validation error: %s", exc)
        return f"Error: {exc}"
    except Exception as exc:
        logger.exception("Unexpected error in modernize_python")
        return f"An unexpected error occurred while modernizing Python code: {exc}"


@mcp.tool(name=DECOMPOSE_FUNCTION_NAME, description=DECOMPOSE_FUNCTION_DESCRIPTION)
def tool_decompose_function(
    code: str,
    function_name: str = "",
    file_path: str = "",
    max_lines_per_function: int = 30,
    decomposition_strategy: str = "extract_method",
) -> str:
    """Decompose a complex function into smaller ones.

    Args:
        code: Python source code containing the function to decompose.
        function_name: Name of the target function (optional — the
            largest function is used if not specified).
        file_path: Path of the source file (optional).
        max_lines_per_function: Target max lines per function (10-100,
            default 30).
        decomposition_strategy: ``"extract_method"`` (default),
            ``"strategy_pattern"``, or ``"pipeline"``.

    Returns:
        A decomposition map and complete refactored code.
    """
    try:
        return decompose_function(
            code=code,
            function_name=function_name,
            file_path=file_path,
            max_lines_per_function=max_lines_per_function,
            decomposition_strategy=decomposition_strategy,
        )
    except ValueError as exc:
        logger.error("decompose_function validation error: %s", exc)
        return f"Error: {exc}"
    except Exception as exc:
        logger.exception("Unexpected error in decompose_function")
        return f"An unexpected error occurred while decomposing function: {exc}"


# ── Entrypoint ───────────────────────────────────────────────────────────────


def main() -> None:
    """Run the MCP server using stdio transport."""
    logger.info("Starting forge_mcp server (stdio transport)…")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
