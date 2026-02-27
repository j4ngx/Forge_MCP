#!/usr/bin/env bash
# =============================================================================
# lib/python.sh — Python & uv installation for Forge MCP Installer
# =============================================================================
# Ensures Python ≥ 3.11 and uv are available.
# Handles: brew (macOS), apt (Debian/Ubuntu), asdf plugin detection.
# =============================================================================

[[ -n "${_FORGE_PYTHON_LOADED:-}" ]] && return 0
readonly _FORGE_PYTHON_LOADED=1

###############################################################################
# Install Python if missing or too old
###############################################################################

install_python() {
  # Already satisfied?
  if [[ -n "${PYTHON_CMD:-}" ]] && version_ge "${PYTHON_VERSION:-0}" "$MIN_PYTHON_VERSION"; then
    success "Python ${PYTHON_VERSION} already satisfies ≥ ${MIN_PYTHON_VERSION}"
    return 0
  fi

  info "Python ≥ ${MIN_PYTHON_VERSION} not found — installing…"

  if [[ "$OS_TYPE" == "macos" ]]; then
    _install_python_macos
  else
    _install_python_linux
  fi

  # Verify
  local py
  for py in python3 python; do
    if command -v "$py" &>/dev/null; then
      local ver
      ver="$("$py" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')" || continue
      if version_ge "$ver" "$MIN_PYTHON_VERSION"; then
        PYTHON_CMD="$py"
        PYTHON_VERSION="$ver"
        success "Python ${PYTHON_VERSION} installed"
        return 0
      fi
    fi
  done

  fail "Python ≥ ${MIN_PYTHON_VERSION} could not be installed"
  return 1
}

_install_python_macos() {
  if command -v brew &>/dev/null; then
    run_cmd brew install python@3.12
  else
    warn "Homebrew not found — installing Homebrew first…"
    run_cmd /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    # Ensure brew is in PATH for the rest of the session
    eval "$(/opt/homebrew/bin/brew shellenv 2>/dev/null || /usr/local/bin/brew shellenv 2>/dev/null)"
    run_cmd brew install python@3.12
  fi
}

_install_python_linux() {
  if command -v apt-get &>/dev/null; then
    run_cmd sudo apt-get update -qq
    run_cmd sudo apt-get install -y python3 python3-venv python3-pip
  elif command -v dnf &>/dev/null; then
    run_cmd sudo dnf install -y python3 python3-pip
  elif command -v pacman &>/dev/null; then
    run_cmd sudo pacman -Sy --noconfirm python python-pip
  else
    fail "Unsupported package manager. Please install Python ≥ ${MIN_PYTHON_VERSION} manually."
    return 1
  fi
}

###############################################################################
# Install uv
###############################################################################

install_uv() {
  # Already satisfied?
  if [[ -n "${UV_CMD:-}" ]]; then
    success "uv ${UV_VERSION:-} already installed"
    return 0
  fi

  info "Installing uv…"

  if command -v brew &>/dev/null && [[ "$OS_TYPE" == "macos" ]]; then
    run_cmd brew install uv
  else
    # Official standalone installer
    run_cmd curl -LsSf https://astral.sh/uv/install.sh | sh
    # Add to PATH for this session
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
  fi

  if command -v uv &>/dev/null; then
    UV_CMD="uv"
    UV_VERSION="$(uv --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')" || UV_VERSION="unknown"
    success "uv ${UV_VERSION} installed"
    return 0
  fi

  fail "uv could not be installed"
  return 1
}

###############################################################################
# Orchestration: ensure both Python and uv
###############################################################################

setup_python_env() {
  local rc=0

  if [[ "$SKIP_PYTHON" != true ]]; then
    install_python || rc=1
  else
    info "Skipping Python install (--skip-python)"
  fi

  if [[ "$SKIP_UV" != true ]]; then
    install_uv || rc=1
  else
    info "Skipping uv install (--skip-uv)"
  fi

  return "$rc"
}
