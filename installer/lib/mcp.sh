#!/usr/bin/env bash
# =============================================================================
# lib/mcp.sh — MCP server setup for Forge MCP Installer
# =============================================================================
# Clones (or uses local) forge_mcp repo, runs uv sync, verifies server starts.
# =============================================================================

[[ -n "${_FORGE_MCP_LOADED:-}" ]] && return 0
readonly _FORGE_MCP_LOADED=1

###############################################################################
# Determine install directory
###############################################################################

_default_install_dir() {
  echo "${FORGE_MCP_DIR:-${HOME}/Projects/forge_mcp}"
}

###############################################################################
# Clone or symlink the project
###############################################################################

setup_mcp_source() {
  if [[ "$SKIP_MCP" == true ]]; then
    info "Skipping MCP setup (--skip-mcp)"
    return 0
  fi

  local install_dir
  install_dir="$(_default_install_dir)"
  FORGE_MCP_DIR="$install_dir"

  if [[ "$INSTALL_FROM_LOCAL" == true ]]; then
    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    local project_root
    project_root="$(cd "$script_dir/.." && pwd)"

    if [[ -f "${project_root}/server.py" ]]; then
      FORGE_MCP_DIR="$project_root"
      success "Using local forge_mcp at ${FORGE_MCP_DIR}"
      return 0
    else
      warn "Local project root does not contain server.py — falling back to clone"
    fi
  fi

  # Clone if directory doesn't exist
  if [[ -d "$install_dir" ]] && [[ -f "${install_dir}/server.py" ]]; then
    info "forge_mcp already exists at ${install_dir}"
    if tui_confirm "Update (git pull)?"; then
      run_cmd git -C "$install_dir" pull --rebase
    fi
  else
    info "Cloning forge_mcp to ${install_dir}…"
    run_cmd git clone "https://github.com/${FORGE_MCP_REPO}.git" "$install_dir"
  fi

  if [[ ! -f "${install_dir}/server.py" ]]; then
    fail "Clone succeeded but server.py not found in ${install_dir}"
    return 1
  fi

  FORGE_MCP_DIR="$install_dir"
  success "forge_mcp source ready at ${FORGE_MCP_DIR}"
  return 0
}

###############################################################################
# Install dependencies with uv
###############################################################################

install_mcp_deps() {
  if [[ "$SKIP_MCP" == true ]]; then return 0; fi

  local install_dir="${FORGE_MCP_DIR:-$(_default_install_dir)}"

  if [[ ! -f "${install_dir}/pyproject.toml" ]]; then
    fail "pyproject.toml not found in ${install_dir}"
    return 1
  fi

  info "Installing MCP dependencies with uv…"

  # Ensure .tool-versions exists (asdf compatibility)
  if [[ ! -f "${install_dir}/.tool-versions" ]]; then
    debug "Creating .tool-versions for asdf compatibility"
    if [[ "$DRY_RUN" != true ]]; then
      echo "ivm-uv 0.9.7" > "${install_dir}/.tool-versions"
    fi
  fi

  run_cmd uv --directory "$install_dir" sync

  if (( $? == 0 )); then
    success "MCP dependencies installed"
    return 0
  fi

  fail "uv sync failed"
  return 1
}

###############################################################################
# Verify server starts
###############################################################################

verify_mcp_server() {
  local install_dir="${FORGE_MCP_DIR:-$(_default_install_dir)}"

  if [[ "$SKIP_MCP" == true ]]; then
    tui_health_row "MCP Server" "skipped" true
    return 0
  fi

  if [[ "$DRY_RUN" == true ]]; then
    tui_health_row "MCP Server" "dry-run (not tested)" true
    return 0
  fi

  info "Verifying MCP server can start…"

  local py="${PYTHON_CMD:-python3}"
  local test_output
  test_output="$(cd "$install_dir" && uv run "$py" -c "
from server import mcp
print(f'forge_mcp server v{getattr(mcp, \"name\", \"unknown\")} OK')
" 2>&1)"

  if [[ $? -eq 0 ]] && [[ "$test_output" == *"OK"* ]]; then
    success "MCP server verified: ${test_output}"
    tui_health_row "MCP Server" "responsive" true
    return 0
  fi

  warn "Server verification returned: ${test_output}"
  tui_health_row "MCP Server" "verification failed" false
  return 1
}

###############################################################################
# Orchestration
###############################################################################

setup_mcp() {
  local rc=0
  setup_mcp_source   || rc=1
  install_mcp_deps   || rc=1
  return "$rc"
}
