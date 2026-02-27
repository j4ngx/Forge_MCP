#!/usr/bin/env bash
# =============================================================================
# lib/common.sh — Shared constants, colours, logging and utility functions
# =============================================================================

[[ -n "${_FORGE_COMMON_LOADED:-}" ]] && return 0
readonly _FORGE_COMMON_LOADED=1

###############################################################################
# Global constants & defaults
# shellcheck disable=SC2034
###############################################################################

readonly INSTALLER_NAME="Forge MCP Installer"
readonly INSTALLER_VERSION="1.0.0"
readonly MIN_PYTHON_VERSION="3.11"
readonly MIN_DISK_MB=512               # 512 MB — Python venv + deps
readonly MIN_RAM_MB=512                # 512 MB minimum
readonly LOCK_FILE="${HOME}/.forge_mcp_installer.lock"

# Project defaults
readonly FORGE_MCP_REPO="j4ngx/forge_mcp"
FORGE_MCP_DIR="${FORGE_MCP_DIR:-}"     # Resolved in preflight or interactively
FORGE_MCP_BRANCH="${FORGE_MCP_BRANCH:-main}"

# Configurable via flags
NON_INTERACTIVE="${NON_INTERACTIVE:-false}"
DRY_RUN="${DRY_RUN:-false}"
VERBOSE="${VERBOSE:-false}"
SKIP_PYTHON="${SKIP_PYTHON:-false}"
SKIP_UV="${SKIP_UV:-false}"
SKIP_VSCODE="${SKIP_VSCODE:-false}"
SKIP_MCP="${SKIP_MCP:-false}"
INSTALL_FROM_LOCAL="${INSTALL_FROM_LOCAL:-false}"

# Progress tracking
CURRENT_STEP=0
TOTAL_STEPS=5
INSTALL_START_EPOCH=""

###############################################################################
# Logging
###############################################################################

LOG_ROOT="${HOME}/.forge-mcp-installer"
LOG_DIR="${LOG_ROOT}/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_FILE:-$LOG_DIR/install_$(date '+%Y%m%d_%H%M%S').log}"

###############################################################################
# Colour palette
# shellcheck disable=SC2034
###############################################################################

if [[ -t 1 ]]; then
  RED='\033[0;31m'
  GREEN='\033[0;32m'
  YELLOW='\033[1;33m'
  BLUE='\033[0;34m'
  MAGENTA='\033[0;35m'
  CYAN='\033[0;36m'
  BOLD='\033[1m'
  DIM='\033[2m'
  NC='\033[0m'
else
  RED='' GREEN='' YELLOW='' BLUE='' MAGENTA='' CYAN='' BOLD='' DIM='' NC=''
fi

###############################################################################
# Logging helpers
###############################################################################

_strip_ansi() { sed 's/\x1b\[[0-9;]*m//g'; }

_log_raw() {
  local msg
  msg="[$(date '+%Y-%m-%d %H:%M:%S')] $*"
  echo -e "$msg" | _strip_ansi >>"$LOG_FILE"
  echo -e "$msg"
}

log()     { _log_raw "    $*"; }
debug()   { [[ "$VERBOSE" == true ]] && _log_raw "${DIM}DBG $*${NC}" || true; }
success() { _log_raw "${GREEN} ✔  $*${NC}"; }
warn()    { _log_raw "${YELLOW} ⚠  $*${NC}"; }
info()    { _log_raw "${CYAN} ℹ  $*${NC}"; }
fail()    { _log_raw "${RED} ✖  $*${NC}"; return 1; }
die()     { _log_raw "${RED} ✖  $*${NC}"; exit 1; }

###############################################################################
# Spinner — delegates to TUI when loaded, fallback otherwise
###############################################################################

_SPINNER_PID=""

spinner_start() {
  local msg="${1:-Working...}"
  if declare -F tui_spinner_start >/dev/null 2>&1; then
    tui_spinner_start "$msg"
    return
  fi
  if [[ ! -t 1 ]]; then
    log "$msg"
    return
  fi
  (
    trap 'exit 0' TERM
    local -a frames=("⠋" "⠙" "⠹" "⠸" "⠼" "⠴" "⠦" "⠧" "⠇" "⠏")
    local i=0 len=${#frames[@]}
    while true; do
      printf '\r  %s %s\033[K' "${frames[$((i % len))]}" "$msg"
      i=$((i + 1))
      sleep 0.1
    done
  ) &
  _SPINNER_PID=$!
  disown "$_SPINNER_PID" 2>/dev/null || true
}

spinner_stop() {
  if declare -F tui_spinner_stop >/dev/null 2>&1; then
    tui_spinner_stop
    return
  fi
  if [[ -n "${_SPINNER_PID:-}" ]] && kill -0 "$_SPINNER_PID" 2>/dev/null; then
    kill "$_SPINNER_PID" 2>/dev/null || true
    wait "$_SPINNER_PID" 2>/dev/null || true
    printf '\r\033[K'
  fi
  _SPINNER_PID=""
}

###############################################################################
# Elapsed time helper
###############################################################################

elapsed_time() {
  local start_epoch="${1:?}"
  local end_epoch
  end_epoch="$(date +%s)"
  local secs=$((end_epoch - start_epoch))
  local mins=$((secs / 60))
  local rem=$((secs % 60))
  if (( mins > 0 )); then
    printf '%dm %02ds' "$mins" "$rem"
  else
    printf '%ds' "$rem"
  fi
}

###############################################################################
# Section header (progress aware)
###############################################################################

section() {
  CURRENT_STEP=$((CURRENT_STEP + 1))
  local title="$1"
  local icon="${2:-⚙}"

  if declare -F tui_section >/dev/null 2>&1; then
    tui_section "$title" "${CURRENT_STEP}/${TOTAL_STEPS}" "$icon"
  else
    echo
    log "${BOLD}[${CURRENT_STEP}/${TOTAL_STEPS}] ${icon}  ${title}${NC}"
  fi
}

###############################################################################
# Command runner (dry-run aware)
###############################################################################

run_cmd() {
  debug "CMD: $*"
  if [[ "$DRY_RUN" == true ]]; then
    info "[dry-run] $*"
    return 0
  fi
  "$@"
}

###############################################################################
# Interactive helpers
###############################################################################

confirm() {
  local prompt="$1"
  local default="${2:-y}"

  if [[ "$NON_INTERACTIVE" == true ]]; then
    [[ "$default" == "y" ]] && return 0 || return 1
  fi

  if declare -F tui_confirm >/dev/null 2>&1; then
    tui_confirm "$prompt" "$default"
    return
  fi

  local yn
  while true; do
    printf '  %s [%s]: ' "$prompt" "$default"
    read -r yn
    yn="${yn:-$default}"
    case "${yn,,}" in
      y|yes) return 0 ;;
      n|no)  return 1 ;;
      *)     echo "  Please answer y or n." ;;
    esac
  done
}

prompt_value() {
  local prompt="$1"
  local default="$2"
  local varname="$3"

  if [[ "$NON_INTERACTIVE" == true ]]; then
    printf -v "$varname" '%s' "$default"
    return
  fi

  if declare -F tui_input >/dev/null 2>&1; then
    tui_input "$prompt" "$default" "$varname"
    return
  fi

  local value
  printf '  %s [%s]: ' "$prompt" "$default"
  read -r value
  value="${value:-$default}"
  printf -v "$varname" '%s' "$value"
}

###############################################################################
# Lock file management
###############################################################################

acquire_lock() {
  if [[ -f "$LOCK_FILE" ]]; then
    local pid
    pid="$(cat "$LOCK_FILE" 2>/dev/null)"
    if kill -0 "$pid" 2>/dev/null; then
      fail "Another installer instance is running (PID ${pid}). Remove ${LOCK_FILE} if stale."
    fi
    warn "Stale lock file found — removing."
    rm -f "$LOCK_FILE"
  fi
  echo $$ > "$LOCK_FILE"
}

release_lock() {
  rm -f "$LOCK_FILE" 2>/dev/null || true
}

###############################################################################
# OS detection helpers
###############################################################################

OS_TYPE=""
ARCH_TYPE=""
PYTHON_CMD=""
PYTHON_VERSION=""
UV_CMD=""
UV_VERSION=""
VSCODE_CMD=""

detect_os() {
  local uname_out
  uname_out="$(uname -s)"
  case "$uname_out" in
    Darwin*) OS_TYPE="macos" ;;
    Linux*)  OS_TYPE="linux" ;;
    *)       OS_TYPE="unknown" ;;
  esac
}

detect_arch() {
  local arch
  arch="$(uname -m)"
  case "$arch" in
    x86_64|amd64)  ARCH_TYPE="x86_64" ;;
    arm64|aarch64) ARCH_TYPE="arm64" ;;
    *)             ARCH_TYPE="$arch" ;;
  esac
}

###############################################################################
# Version comparison
###############################################################################

version_ge() {
  # Returns 0 if $1 >= $2 using semantic version comparison
  local v1="$1" v2="$2"
  printf '%s\n%s' "$v1" "$v2" | sort -V | head -1 | grep -qx "$v2"
}

###############################################################################
# Require command helper
###############################################################################

require_command() {
  local cmd="$1"
  local install_hint="${2:-}"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    if [[ -n "$install_hint" ]]; then
      fail "Required command '${cmd}' not found. ${install_hint}"
    else
      fail "Required command '${cmd}' not found."
    fi
  fi
}
