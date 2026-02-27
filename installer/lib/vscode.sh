#!/usr/bin/env bash
# =============================================================================
# lib/vscode.sh — VS Code configuration for Forge MCP Installer
# =============================================================================
# Detects VS Code, locates user settings directory, writes/updates mcp.json.
# =============================================================================

[[ -n "${_FORGE_VSCODE_LOADED:-}" ]] && return 0
readonly _FORGE_VSCODE_LOADED=1

###############################################################################
# Constants
###############################################################################

VSCODE_MCP_SERVER_NAME="${VSCODE_MCP_SERVER_NAME:-forge_mcp}"

###############################################################################
# Locate VS Code user data directory
###############################################################################

_vscode_user_data_dir() {
  local dir=""
  if [[ "$OS_TYPE" == "macos" ]]; then
    dir="${HOME}/Library/Application Support/Code/User"
    [[ -d "$dir" ]] || dir="${HOME}/Library/Application Support/Code - Insiders/User"
  else
    dir="${HOME}/.config/Code/User"
    [[ -d "$dir" ]] || dir="${HOME}/.config/Code - Insiders/User"
    # Flatpak installation
    [[ -d "$dir" ]] || dir="${HOME}/.var/app/com.visualstudio.code/config/Code/User"
  fi
  echo "$dir"
}

###############################################################################
# Build mcp.json server entry
###############################################################################

_build_mcp_json_entry() {
  local server_dir="$1"
  local uv_cmd
  uv_cmd="$(resolve_uv_cmd)"
  cat <<EOF
{
  "servers": {
    "${VSCODE_MCP_SERVER_NAME}": {
      "type": "stdio",
      "command": "${uv_cmd}",
      "args": ["--directory", "${server_dir}", "run", "server.py"]
    }
  }
}
EOF
}

###############################################################################
# Merge our server into existing mcp.json (or create it)
###############################################################################

_merge_mcp_json() {
  local mcp_json_path="$1" server_dir="$2"

  if [[ -f "$mcp_json_path" ]]; then
    debug "Existing mcp.json found at ${mcp_json_path}"

    # Check if already configured
    if grep -q "\"${VSCODE_MCP_SERVER_NAME}\"" "$mcp_json_path" 2>/dev/null; then
      info "Server '${VSCODE_MCP_SERVER_NAME}' already in mcp.json — updating entry…"
    fi

    # Use Python to merge JSON (safe & handles comments)
    local py="${PYTHON_CMD:-python3}"
    local uv_cmd
    uv_cmd="$(resolve_uv_cmd)"
    "$py" - "$mcp_json_path" "$server_dir" "$VSCODE_MCP_SERVER_NAME" "$uv_cmd" <<'PYEOF'
import json, sys, re

mcp_path, server_dir, server_name, uv_cmd = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]

# Read existing (strip single-line comments — VS Code JSONC)
with open(mcp_path, "r") as f:
    raw = f.read()

cleaned = re.sub(r'//.*', '', raw)

try:
    data = json.loads(cleaned)
except json.JSONDecodeError:
    data = {"servers": {}}

if "servers" not in data:
    data["servers"] = {}

data["servers"][server_name] = {
    "type": "stdio",
    "command": uv_cmd,
    "args": ["--directory", server_dir, "run", "server.py"]
}

with open(mcp_path, "w") as f:
    json.dump(data, f, indent=2)
    f.write("\n")

print(f"Updated {mcp_path}")
PYEOF
  else
    debug "Creating new mcp.json at ${mcp_json_path}"
    mkdir -p "$(dirname "$mcp_json_path")"
    _build_mcp_json_entry "$server_dir" > "$mcp_json_path"
  fi
}

###############################################################################
# Configure VS Code
###############################################################################

configure_vscode() {
  if [[ "$SKIP_VSCODE" == true ]]; then
    info "Skipping VS Code configuration (--skip-vscode)"
    return 0
  fi

  local user_dir
  user_dir="$(_vscode_user_data_dir)"

  if [[ ! -d "$user_dir" ]]; then
    warn "VS Code user directory not found at: ${user_dir}"
    if ! tui_confirm "Create VS Code settings directory?"; then
      info "Skipping VS Code configuration"
      return 0
    fi
    run_cmd mkdir -p "$user_dir"
  fi

  local mcp_json="${user_dir}/mcp.json"
  local server_dir="${FORGE_MCP_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"

  info "Configuring VS Code MCP server…"
  debug "  mcp.json:   ${mcp_json}"
  debug "  server dir: ${server_dir}"

  if [[ "$DRY_RUN" == true ]]; then
    info "[DRY RUN] Would write server entry to ${mcp_json}"
    return 0
  fi

  # Back up existing file
  if [[ -f "$mcp_json" ]]; then
    local backup="${mcp_json}.backup.$(date +%s)"
    cp "$mcp_json" "$backup"
    debug "Backup saved to ${backup}"
  fi

  _merge_mcp_json "$mcp_json" "$server_dir"

  if [[ -f "$mcp_json" ]] && grep -q "$VSCODE_MCP_SERVER_NAME" "$mcp_json" 2>/dev/null; then
    success "VS Code mcp.json configured with '${VSCODE_MCP_SERVER_NAME}'"
    return 0
  fi

  fail "Failed to write VS Code mcp.json"
  return 1
}

###############################################################################
# Verify VS Code can see the server
###############################################################################

verify_vscode_config() {
  local user_dir
  user_dir="$(_vscode_user_data_dir)"
  local mcp_json="${user_dir}/mcp.json"

  if [[ -f "$mcp_json" ]] && grep -q "$VSCODE_MCP_SERVER_NAME" "$mcp_json" 2>/dev/null; then
    tui_health_row "VS Code mcp.json" "configured" true
    return 0
  fi

  tui_health_row "VS Code mcp.json" "missing or incomplete" false
  return 1
}
