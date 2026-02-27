#!/usr/bin/env bash
# =============================================================================
# install.sh — Forge MCP Installer entry point
# =============================================================================
# Interactive TUI-driven installer that sets up forge_mcp for VS Code.
#
# Usage:
#   bash installer/install.sh [OPTIONS]
#
# Options:
#   --dry-run         Show what would be done without executing
#   --non-interactive Run with defaults, no prompts
#   --verbose         Enable debug output
#   --skip-python     Skip Python installation check
#   --skip-uv         Skip uv installation check
#   --skip-vscode     Skip VS Code configuration
#   --skip-mcp        Skip MCP source / deps setup
#   --local           Use local source (don't clone from GitHub)
#   --dir PATH        Override install directory
#   --help            Show help and exit
# =============================================================================

set -euo pipefail

###############################################################################
# Resolve paths
###############################################################################

INSTALLER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="${INSTALLER_DIR}/lib"

###############################################################################
# Source libraries
###############################################################################

# shellcheck source=lib/common.sh
source "${LIB_DIR}/common.sh"
# shellcheck source=lib/tui.sh
source "${LIB_DIR}/tui.sh"
# shellcheck source=lib/preflight.sh
source "${LIB_DIR}/preflight.sh"
# shellcheck source=lib/python.sh
source "${LIB_DIR}/python.sh"
# shellcheck source=lib/vscode.sh
source "${LIB_DIR}/vscode.sh"
# shellcheck source=lib/mcp.sh
source "${LIB_DIR}/mcp.sh"

###############################################################################
# Argument parsing
###############################################################################

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --dry-run)         DRY_RUN=true ;;
      --non-interactive) NON_INTERACTIVE=true ;;
      --verbose|-v)      VERBOSE=true ;;
      --skip-python)     SKIP_PYTHON=true ;;
      --skip-uv)         SKIP_UV=true ;;
      --skip-vscode)     SKIP_VSCODE=true ;;
      --skip-mcp)        SKIP_MCP=true ;;
      --local)           INSTALL_FROM_LOCAL=true ;;
      --dir)
        shift
        FORGE_MCP_DIR="${1:?'--dir requires a path'}"
        ;;
      --help|-h)
        show_help
        exit 0
        ;;
      *)
        warn "Unknown option: $1"
        show_help
        exit 1
        ;;
    esac
    shift
  done
}

show_help() {
  cat <<'HELP'
Forge MCP Installer — set up forge_mcp for VS Code

Usage:
  bash install.sh [OPTIONS]

Options:
  --dry-run           Show what would be done without executing
  --non-interactive   Run with defaults, no prompts
  --verbose, -v       Enable debug output
  --skip-python       Skip Python installation check
  --skip-uv           Skip uv installation check
  --skip-vscode       Skip VS Code configuration
  --skip-mcp          Skip MCP source / deps setup
  --local             Use local source (don't clone from GitHub)
  --dir PATH          Override install directory
  --help, -h          Show this help

Examples:
  bash install.sh                         # Full interactive install
  bash install.sh --local                 # Use local source
  bash install.sh --dry-run --verbose     # Preview with debug output
  bash install.sh --non-interactive       # CI-friendly unattended run
HELP
}

###############################################################################
# Step functions
###############################################################################

step_preflight() {
  section "Pre-flight Checks" "🔍"
  local failures
  run_preflight
  failures=$?

  if (( failures > 0 )); then
    warn "${failures} pre-flight check(s) reported issues"
    if ! confirm "Continue anyway?" "y"; then
      die "Aborted by user after failed pre-flight checks."
    fi
  fi

  success "Pre-flight checks complete"
}

step_python() {
  section "Python & uv Environment" "🐍"
  setup_python_env
}

step_mcp_source() {
  section "MCP Server Setup" "🔨"
  setup_mcp
}

step_vscode() {
  section "VS Code Configuration" "💻"
  configure_vscode
}

step_verify() {
  section "Verification & Health Check" "🩺"
  local failures=0

  verify_mcp_server  || (( failures++ ))
  verify_vscode_config || (( failures++ ))

  echo
  tui_divider "single"
  echo

  if (( failures == 0 )); then
    tui_notify "All health checks passed" "success"
  else
    tui_notify "${failures} health check(s) failed — review log at ${LOG_FILE}" "warn"
  fi

  return "$failures"
}

###############################################################################
# Interactive review
###############################################################################

interactive_review() {
  if [[ "$NON_INTERACTIVE" == true ]]; then return 0; fi

  tui_plan_card
  echo

  if ! confirm "Proceed with installation?" "y"; then
    info "Installation cancelled by user."
    release_lock
    exit 0
  fi
}

###############################################################################
# Summary
###############################################################################

print_summary() {
  local elapsed="$1"

  echo
  tui_divider "double" "$TUI_ACCENT"
  echo

  tui_status_line "Install dir"  "${FORGE_MCP_DIR:-N/A}" "info"
  tui_status_line "Python"       "${PYTHON_VERSION:-not checked}" "ok"
  tui_status_line "uv"           "${UV_VERSION:-not checked}" "ok"
  tui_status_line "VS Code"      "$(command -v "${VSCODE_CMD:-code}" 2>/dev/null || echo 'not found')" "info"
  tui_status_line "Duration"     "$elapsed" "info"
  tui_status_line "Log"          "$LOG_FILE" "info"

  echo
  tui_box "Next Steps" \
    "" \
    "1. Open VS Code in the forge_mcp project:" \
    "   ${TUI_BOLD}code ${FORGE_MCP_DIR:-~/Projects/forge_mcp}${TUI_RESET}" \
    "" \
    "2. The MCP server is configured in your User mcp.json." \
    "   Copilot Chat will auto-discover the forge_mcp tools." \
    "" \
    "3. In Copilot Agent Mode, use the review_pr tool:" \
    "   ${TUI_MUTED}\"Review the PR diff I just pasted\"${TUI_RESET}" \
    ""
}

###############################################################################
# Cleanup trap
###############################################################################

cleanup() {
  local exit_code=$?
  tui_spinner_stop 2>/dev/null || true
  release_lock

  if (( exit_code != 0 )); then
    tui_failure_screen "$exit_code"
  fi
}

###############################################################################
# Main
###############################################################################

main() {
  trap cleanup EXIT

  parse_args "$@"
  acquire_lock
  INSTALL_START_EPOCH="$(date +%s)"

  # --- Banner ---
  tui_forge_banner

  if [[ "$DRY_RUN" == true ]]; then
    tui_notify "DRY-RUN mode — no changes will be made" "warn"
  fi

  # --- Steps ---
  tui_steps_init \
    "Pre-flight Checks" \
    "Python & uv Environment" \
    "MCP Server Setup" \
    "VS Code Configuration" \
    "Verification"

  # Interactive plan card
  tui_step_active 0
  tui_steps_render
  interactive_review

  # Step 1: Preflight
  tui_step_active 0
  step_preflight && tui_step_done 0 || tui_step_failed 0

  # Step 2: Python & uv
  tui_step_active 1
  step_python && tui_step_done 1 || tui_step_failed 1

  # Step 3: MCP server
  tui_step_active 2
  step_mcp_source && tui_step_done 2 || tui_step_failed 2

  # Step 4: VS Code
  tui_step_active 3
  step_vscode && tui_step_done 3 || tui_step_failed 3

  # Step 5: Verify
  tui_step_active 4
  step_verify && tui_step_done 4 || tui_step_failed 4

  # --- Final render ---
  tui_steps_render

  local elapsed
  elapsed="$(elapsed_time "$INSTALL_START_EPOCH")"

  tui_completion_screen "$elapsed"
  print_summary "$elapsed"

  release_lock
  trap - EXIT
}

main "$@"
