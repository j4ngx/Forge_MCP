#!/usr/bin/env bash
# =============================================================================
# lib/preflight.sh — Pre-flight checks for Forge MCP Installer
# =============================================================================
# Validates system requirements: OS, Python, disk, VS Code, network, git.
# =============================================================================

[[ -n "${_FORGE_PREFLIGHT_LOADED:-}" ]] && return 0
readonly _FORGE_PREFLIGHT_LOADED=1

###############################################################################
# OS and architecture
###############################################################################

preflight_check_os() {
  detect_os
  detect_arch

  case "$OS_TYPE" in
    macos|linux) ;;
    *)
      fail "Unsupported operating system: ${OS_TYPE}. Only macOS and Linux are supported."
      return 1
      ;;
  esac

  tui_status_line "Operating System" "${OS_TYPE} (${ARCH_TYPE})" "ok"
  return 0
}

###############################################################################
# Python version check
###############################################################################

preflight_check_python() {
  local py_cmd=""

  # Try common Python commands
  for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
      local ver
      ver="$("$cmd" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')" || continue
      if version_ge "$ver" "$MIN_PYTHON_VERSION"; then
        py_cmd="$cmd"
        PYTHON_CMD="$cmd"
        PYTHON_VERSION="$ver"
        break
      fi
    fi
  done

  if [[ -z "$py_cmd" ]]; then
    tui_status_line "Python" "not found (need ≥ ${MIN_PYTHON_VERSION})" "warn"
    return 1
  fi

  tui_status_line "Python" "${PYTHON_VERSION} ($(command -v "$py_cmd"))" "ok"
  return 0
}

###############################################################################
# uv check
###############################################################################

preflight_check_uv() {
  if command -v uv &>/dev/null; then
    local uv_ver
    uv_ver="$(uv --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')" || uv_ver="unknown"
    UV_CMD="uv"
    UV_VERSION="$uv_ver"
    tui_status_line "uv" "${uv_ver} ($(command -v uv))" "ok"
    return 0
  fi

  tui_status_line "uv" "not installed" "warn"
  return 1
}

###############################################################################
# Git check
###############################################################################

preflight_check_git() {
  if command -v git &>/dev/null; then
    local git_ver
    git_ver="$(git --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')" || git_ver="unknown"
    tui_status_line "Git" "${git_ver}" "ok"
    return 0
  fi

  tui_status_line "Git" "not installed" "error"
  return 1
}

###############################################################################
# VS Code detection
###############################################################################

preflight_check_vscode() {
  local code_cmd=""
  for cmd in code code-insiders; do
    if command -v "$cmd" &>/dev/null; then
      code_cmd="$cmd"
      break
    fi
  done

  if [[ -z "$code_cmd" ]]; then
    # Check common install paths
    local -a paths=()
    if [[ "$OS_TYPE" == "macos" ]]; then
      paths+=(
        "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code"
        "/Applications/Visual Studio Code - Insiders.app/Contents/Resources/app/bin/code-insiders"
      )
    else
      paths+=(
        "/usr/bin/code"
        "/snap/bin/code"
        "/usr/share/code/bin/code"
        "${HOME}/.var/app/com.visualstudio.code/usr/share/code/bin/code"
      )
    fi

    for p in "${paths[@]}"; do
      if [[ -x "$p" ]]; then
        code_cmd="$p"
        break
      fi
    done
  fi

  if [[ -n "$code_cmd" ]]; then
    VSCODE_CMD="$code_cmd"
    local vs_ver
    vs_ver="$("$code_cmd" --version 2>&1 | head -1)" || vs_ver="detected"
    tui_status_line "VS Code" "${vs_ver}" "ok"
    return 0
  fi

  tui_status_line "VS Code" "not found" "warn"
  return 1
}

###############################################################################
# Disk space check
###############################################################################

preflight_check_disk() {
  local target_dir="${1:-$HOME}"
  local min_mb="${MIN_DISK_MB:-200}"
  local avail_mb

  avail_mb="$(df -m "$target_dir" 2>/dev/null | awk 'NR==2{print $4}')"
  avail_mb="${avail_mb:-0}"

  if (( avail_mb >= min_mb )); then
    tui_status_line "Disk Space" "${avail_mb} MB free" "ok"
    return 0
  fi

  tui_status_line "Disk Space" "${avail_mb} MB (need ${min_mb} MB)" "error"
  return 1
}

###############################################################################
# Network connectivity check
###############################################################################

preflight_check_network() {
  local test_url="https://pypi.org"
  if curl -sSf --max-time 5 "$test_url" &>/dev/null; then
    tui_status_line "Network" "connected" "ok"
    return 0
  fi

  tui_status_line "Network" "no connection to PyPI" "warn"
  return 1
}

###############################################################################
# Homebrew check (macOS only)
###############################################################################

preflight_check_brew() {
  if [[ "$OS_TYPE" != "macos" ]]; then
    return 0
  fi

  if command -v brew &>/dev/null; then
    tui_status_line "Homebrew" "$(brew --version 2>&1 | head -1)" "ok"
    return 0
  fi

  tui_status_line "Homebrew" "not installed" "warn"
  return 1
}

###############################################################################
# Run all preflight checks
###############################################################################

run_preflight() {
  local failures=0

  preflight_check_os      || (( failures++ ))
  preflight_check_git     || (( failures++ ))
  preflight_check_python  || true   # Not fatal, we can install it
  preflight_check_uv      || true   # Not fatal, we can install it
  preflight_check_vscode  || true   # Not fatal, warn only
  preflight_check_disk    || (( failures++ ))
  preflight_check_network || true   # Not fatal if installing locally

  if [[ "$OS_TYPE" == "macos" ]]; then
    preflight_check_brew  || true
  fi

  return "$failures"
}
