#!/usr/bin/env bash
# shellcheck disable=SC2034
# =============================================================================
# lib/tui.sh — Terminal User Interface library for Forge MCP Installer
# =============================================================================
# Adapted from GLaDOS Installer TUI.
# Provides: box drawing, progress bars, step tracker, spinners, styled prompts,
# banner, completion/failure screens, health rows.
# =============================================================================

[[ -n "${_FORGE_TUI_LOADED:-}" ]] && return 0
readonly _FORGE_TUI_LOADED=1

###############################################################################
# Extended colour palette
###############################################################################

TUI_ACCENT='\033[38;5;208m'        # Orange (Forge theme)
TUI_ACCENT2='\033[38;5;39m'        # Electric blue
TUI_ACCENT3='\033[38;5;214m'       # Amber
TUI_SUCCESS='\033[38;5;78m'        # Soft green
TUI_WARNING='\033[38;5;220m'       # Gold
TUI_ERROR='\033[38;5;196m'         # Bright red
TUI_MUTED='\033[38;5;243m'         # Grey
TUI_WHITE='\033[38;5;255m'         # Bright white
TUI_HEADER_BG='\033[48;5;236m'     # Dark grey background
TUI_HIGHLIGHT='\033[38;5;117m'     # Light cyan
TUI_ORANGE='\033[38;5;208m'        # Orange

TUI_BOLD='\033[1m'
TUI_DIM='\033[2m'
TUI_ITALIC='\033[3m'
TUI_UNDERLINE='\033[4m'
TUI_RESET='\033[0m'

if [[ ! -t 1 ]]; then
  TUI_ACCENT='' TUI_ACCENT2='' TUI_ACCENT3='' TUI_SUCCESS='' TUI_WARNING=''
  TUI_ERROR='' TUI_MUTED='' TUI_WHITE='' TUI_HEADER_BG='' TUI_HIGHLIGHT=''
  TUI_ORANGE='' TUI_BOLD='' TUI_DIM='' TUI_ITALIC='' TUI_UNDERLINE=''
  TUI_RESET=''
fi

###############################################################################
# Terminal geometry
###############################################################################

tui_term_width() {
  local w
  w="$(tput cols 2>/dev/null || echo 80)"
  (( w < 40 )) && w=40
  (( w > 120 )) && w=120
  echo "$w"
}

###############################################################################
# Unicode box-drawing characters
###############################################################################

readonly BOX_TL='╭' BOX_TR='╮' BOX_BL='╰' BOX_BR='╯'
readonly BOX_H='─' BOX_V='│'
readonly BOX_LT='├' BOX_RT='┤'

readonly BOX2_TL='╔' BOX2_TR='╗' BOX2_BL='╚' BOX2_BR='╝'
readonly BOX2_H='═' BOX2_V='║'

readonly BOXH_H='━'

readonly BLOCK_FULL='█' BLOCK_EMPTY='░'

# Status icons
readonly ICON_CHECK='✔' ICON_CROSS='✖' ICON_WARN='⚠' ICON_INFO='ℹ'
readonly ICON_ARROW='▸' ICON_DOT='●' ICON_RING='○' ICON_STAR='★'
readonly ICON_GEAR='⚙' ICON_BOLT='⚡' ICON_PACKAGE='📦'
readonly ICON_CHART='📊' ICON_SPARKLE='✨' ICON_HAMMER='🔨'
readonly ICON_SNAKE='🐍' ICON_VSCODE='💻' ICON_ROCKET='🚀'
readonly ICON_SHIELD='🛡' ICON_CLOCK='🕐' ICON_LINK='🔗'

###############################################################################
# Internal helpers
###############################################################################

_tui_repeat() {
  local char="$1" count="$2"
  (( count <= 0 )) && return
  local _buf
  printf -v _buf '%*s' "$count" ''
  printf '%s' "${_buf// /$char}"
}

_tui_strip_ansi() {
  printf '%s' "$1" | sed 's/\x1b\[[0-9;]*m//g'
}

###############################################################################
# Box drawing
###############################################################################

tui_box() {
  local title="${1:-}"; shift
  local w
  w="$(tui_term_width)"
  local inner=$((w - 4))
  local color="${TUI_BOX_COLOR:-$TUI_ACCENT}"

  printf '%b  %s' "$color" "$BOX_TL"
  _tui_repeat "$BOX_H" "$inner"
  printf '%s%b\n' "$BOX_TR" "$TUI_RESET"

  if [[ -n "$title" ]]; then
    local stripped
    stripped="$(_tui_strip_ansi "$title")"
    local pad=$((inner - ${#stripped} - 2))
    (( pad < 0 )) && pad=0
    printf '%b  %s %b%b%s%b' "$color" "$BOX_V" "$TUI_BOLD" "$TUI_WHITE" "$title" "$TUI_RESET"
    printf '%b' "$color"
    _tui_repeat ' ' "$pad"
    printf ' %s%b\n' "$BOX_V" "$TUI_RESET"

    printf '%b  %s' "$color" "$BOX_LT"
    _tui_repeat "$BOX_H" "$inner"
    printf '%s%b\n' "$BOX_RT" "$TUI_RESET"
  fi

  local line
  for line in "$@"; do
    [[ -z "$line" ]] && { printf '%b  %s' "$color" "$BOX_V"; _tui_repeat ' ' "$inner"; printf '%s%b\n' "$BOX_V" "$TUI_RESET"; continue; }
    local stripped
    stripped="$(_tui_strip_ansi "$line")"
    local pad=$((inner - ${#stripped} - 2))
    (( pad < 0 )) && pad=0
    printf '%b  %s %b%b' "$color" "$BOX_V" "$TUI_RESET" "$line"
    _tui_repeat ' ' "$pad"
    printf '%b %s%b\n' "$color" "$BOX_V" "$TUI_RESET"
  done

  printf '%b  %s' "$color" "$BOX_BL"
  _tui_repeat "$BOX_H" "$inner"
  printf '%s%b\n' "$BOX_BR" "$TUI_RESET"
}

###############################################################################
# Horizontal divider
###############################################################################

tui_divider() {
  local style="${1:-single}" color="${2:-$TUI_MUTED}"
  local w
  w="$(tui_term_width)"
  local inner=$((w - 4))

  printf '  %b' "$color"
  case "$style" in
    double) _tui_repeat "$BOX2_H" "$inner" ;;
    heavy)  _tui_repeat "$BOXH_H" "$inner" ;;
    dots)   _tui_repeat "·" "$inner" ;;
    *)      _tui_repeat "$BOX_H" "$inner" ;;
  esac
  printf '%b\n' "$TUI_RESET"
}

###############################################################################
# Progress bar
###############################################################################

tui_progress() {
  local current="$1" total="$2" label="${3:-}"
  local bar_width=30
  local pct=$((current * 100 / total))
  local filled=$((current * bar_width / total))
  local empty=$((bar_width - filled))

  local bar_color="$TUI_ACCENT2"
  (( pct >= 50 )) && bar_color="$TUI_ACCENT"
  (( pct >= 80 )) && bar_color="$TUI_SUCCESS"

  printf '\r  %b' "$bar_color"
  _tui_repeat "$BLOCK_FULL" "$filled"
  printf '%b' "$TUI_MUTED"
  _tui_repeat "$BLOCK_EMPTY" "$empty"
  printf '%b %b%3d%%%b' "$TUI_RESET" "$TUI_BOLD" "$pct" "$TUI_RESET"
  [[ -n "$label" ]] && printf '  %b%s%b' "$TUI_MUTED" "$label" "$TUI_RESET"
  printf '\033[K'
}

tui_progress_done() { printf '\n'; }

###############################################################################
# Step tracker
###############################################################################

declare -a _TUI_STEPS=()
declare -a _TUI_STEP_STATUS=()

tui_steps_init() {
  _TUI_STEPS=("$@")
  _TUI_STEP_STATUS=()
  local i
  for i in "${!_TUI_STEPS[@]}"; do
    _TUI_STEP_STATUS[i]="pending"
  done
}

tui_step_active()  { _TUI_STEP_STATUS[$1]="active"; }
tui_step_done()    { _TUI_STEP_STATUS[$1]="done"; }
tui_step_failed()  { _TUI_STEP_STATUS[$1]="failed"; }
tui_step_skipped() { _TUI_STEP_STATUS[$1]="skipped"; }

tui_steps_render() {
  local total=${#_TUI_STEPS[@]}
  local i status icon color label

  echo
  for i in "${!_TUI_STEPS[@]}"; do
    status="${_TUI_STEP_STATUS[$i]}"
    label="${_TUI_STEPS[$i]}"

    case "$status" in
      done)    icon="${TUI_SUCCESS}${ICON_CHECK}${TUI_RESET}"; color="$TUI_SUCCESS" ;;
      active)  icon="${TUI_ACCENT2}${ICON_ARROW}${TUI_RESET}"; color="$TUI_ACCENT2" ;;
      failed)  icon="${TUI_ERROR}${ICON_CROSS}${TUI_RESET}";   color="$TUI_ERROR" ;;
      skipped) icon="${TUI_MUTED}${ICON_RING}${TUI_RESET}";    color="$TUI_MUTED" ;;
      *)       icon="${TUI_MUTED}${ICON_RING}${TUI_RESET}";    color="$TUI_MUTED" ;;
    esac

    printf '  %b  %b%s%b\n' "$icon" "$color" "$label" "$TUI_RESET"
    if (( i < total - 1 )); then
      local next_status="${_TUI_STEP_STATUS[$((i+1))]}"
      local conn_color="$TUI_MUTED"
      [[ "$next_status" == "done" || "$next_status" == "active" ]] && conn_color="$TUI_ACCENT"
      printf '  %b│%b\n' "$conn_color" "$TUI_RESET"
    fi
  done
  echo
}

###############################################################################
# Section header
###############################################################################

tui_section() {
  local title="$1" step="${2:-}" icon="${3:-$ICON_GEAR}"
  local w
  w="$(tui_term_width)"
  local inner=$((w - 4))

  echo
  printf '  %b%s' "$TUI_ACCENT" "$BOX_TL"
  _tui_repeat "$BOX_H" "$inner"
  printf '%s%b\n' "$BOX_TR" "$TUI_RESET"

  local left_content="${icon}  ${title}"
  local right_content=""
  [[ -n "$step" ]] && right_content="[ ${step} ]"

  local stripped_left stripped_right
  stripped_left="$(_tui_strip_ansi "$left_content")"
  stripped_right="$(_tui_strip_ansi "$right_content")"
  local pad=$((inner - ${#stripped_left} - ${#stripped_right} - 2))
  (( pad < 0 )) && pad=0

  printf '  %b%s%b ' "$TUI_ACCENT" "$BOX_V" "$TUI_RESET"
  printf '%b%b%s%b' "$TUI_BOLD" "$TUI_WHITE" "$left_content" "$TUI_RESET"
  _tui_repeat ' ' "$pad"
  printf '%b%s%b' "$TUI_MUTED" "$right_content" "$TUI_RESET"
  printf ' %b%s%b\n' "$TUI_ACCENT" "$BOX_V" "$TUI_RESET"

  printf '  %b%s' "$TUI_ACCENT" "$BOX_BL"
  _tui_repeat "$BOX_H" "$inner"
  printf '%s%b\n' "$BOX_BR" "$TUI_RESET"
}

###############################################################################
# Animated spinner
###############################################################################

_TUI_SPINNER_PID=""

readonly -a SPIN_DOTS=("⠋" "⠙" "⠹" "⠸" "⠼" "⠴" "⠦" "⠧" "⠇" "⠏")

tui_spinner_start() {
  local msg="${1:-Working...}"
  [[ ! -t 1 ]] && { log "$msg"; return; }

  (
    set +eEu
    trap 'exit 0' TERM; trap '' ERR
    local -a frames=("${SPIN_DOTS[@]}")
    local i=0 len=${#frames[@]}
    while true; do
      printf '\r  %b%s%b %s\033[K' \
        "$TUI_ACCENT2" "${frames[$((i % len))]}" "$TUI_RESET" "$msg"
      i=$((i + 1))
      sleep 0.1
    done
  ) &
  _TUI_SPINNER_PID=$!
  disown "$_TUI_SPINNER_PID" 2>/dev/null || true
}

tui_spinner_stop() {
  if [[ -n "${_TUI_SPINNER_PID:-}" ]] && kill -0 "$_TUI_SPINNER_PID" 2>/dev/null; then
    kill "$_TUI_SPINNER_PID" 2>/dev/null || true
    wait "$_TUI_SPINNER_PID" 2>/dev/null || true
    printf '\r\033[K'
  fi
  _TUI_SPINNER_PID=""
}

tui_spin_exec() {
  local msg="$1"; shift
  tui_spinner_start "$msg"
  if "$@"; then
    tui_spinner_stop
    return 0
  else
    local rc=$?
    tui_spinner_stop
    return $rc
  fi
}

###############################################################################
# Styled prompts
###############################################################################

tui_confirm() {
  local prompt="$1" default="${2:-y}"
  [[ "$NON_INTERACTIVE" == true ]] && { [[ "$default" == "y" ]] && return 0 || return 1; }
  local hint
  if [[ "$default" == "y" ]]; then
    hint="${TUI_BOLD}Y${TUI_RESET}${TUI_MUTED}/n${TUI_RESET}"
  else
    hint="${TUI_MUTED}y/${TUI_RESET}${TUI_BOLD}N${TUI_RESET}"
  fi
  local yn
  while true; do
    printf '  %b%s%b %s [%b]: ' "$TUI_ACCENT2" "$ICON_ARROW" "$TUI_RESET" "$prompt" "$hint"
    read -r yn
    yn="${yn:-$default}"
    case "${yn,,}" in
      y|yes) return 0 ;;
      n|no)  return 1 ;;
      *)     printf '  %b%s  Please answer y or n.%b\n' "$TUI_WARNING" "$ICON_WARN" "$TUI_RESET" ;;
    esac
  done
}

tui_input() {
  local prompt="$1" default="$2" varname="$3"
  [[ "$NON_INTERACTIVE" == true ]] && { printf -v "$varname" '%s' "$default"; return; }
  local value
  printf '  %b%s%b %s [%b%s%b]: ' \
    "$TUI_ACCENT2" "$ICON_ARROW" "$TUI_RESET" "$prompt" \
    "$TUI_MUTED" "$default" "$TUI_RESET"
  read -r value
  value="${value:-$default}"
  printf -v "$varname" '%s' "$value"
}

###############################################################################
# Status / key-value displays
###############################################################################

tui_status_line() {
  local label="$1" value="$2" status="${3:-info}"
  local icon color
  case "$status" in
    ok|pass|done) icon="$ICON_CHECK"; color="$TUI_SUCCESS" ;;
    warn)         icon="$ICON_WARN";  color="$TUI_WARNING" ;;
    error|fail)   icon="$ICON_CROSS"; color="$TUI_ERROR" ;;
    skip)         icon="$ICON_RING";  color="$TUI_MUTED" ;;
    active)       icon="$ICON_ARROW"; color="$TUI_ACCENT2" ;;
    *)            icon="$ICON_INFO";  color="$TUI_HIGHLIGHT" ;;
  esac
  printf '  %b%s%b  %-22s %b%s%b\n' "$color" "$icon" "$TUI_RESET" "$label" "$color" "$value" "$TUI_RESET"
}

tui_kv() {
  local key="$1" value="$2" icon="${3:-}"
  if [[ -n "$icon" ]]; then
    printf '  %s  %b%-18s%b  %b%s%b\n' "$icon" "$TUI_MUTED" "$key" "$TUI_RESET" "$TUI_WHITE" "$value" "$TUI_RESET"
  else
    printf '      %b%-18s%b  %b%s%b\n' "$TUI_MUTED" "$key" "$TUI_RESET" "$TUI_WHITE" "$value" "$TUI_RESET"
  fi
}

tui_kv_inline() {
  local key="$1" value="$2"
  printf '%b%-18s%b  %b' "$TUI_MUTED" "$key" "$TUI_RESET" "$value"
}

###############################################################################
# Health-check row
###############################################################################

tui_health_row() {
  local label="$1" value="$2" ok="${3:-true}"
  if [[ "$ok" == true ]]; then
    printf '  %b%s%b  %-22s %b%s%b\n' "$TUI_SUCCESS" "$ICON_CHECK" "$TUI_RESET" "$label" "$TUI_SUCCESS" "$value" "$TUI_RESET"
  else
    printf '  %b%s%b  %-22s %b%s%b\n' "$TUI_ERROR" "$ICON_CROSS" "$TUI_RESET" "$label" "$TUI_ERROR" "$value" "$TUI_RESET"
  fi
}

###############################################################################
# Notification bar
###############################################################################

tui_notify() {
  local msg="$1" level="${2:-info}"
  local color icon
  case "$level" in
    success) color="$TUI_SUCCESS"; icon="$ICON_CHECK" ;;
    warn)    color="$TUI_WARNING"; icon="$ICON_WARN"  ;;
    error)   color="$TUI_ERROR";   icon="$ICON_CROSS" ;;
    *)       color="$TUI_ACCENT2"; icon="$ICON_INFO"  ;;
  esac
  local w
  w="$(tui_term_width)"
  local inner=$((w - 4))

  printf '\n  %b' "$color"
  _tui_repeat "$BOXH_H" "$inner"
  printf '%b\n' "$TUI_RESET"
  printf '  %b%s  %s%b\n' "$color" "$icon" "$msg" "$TUI_RESET"
  printf '  %b' "$color"
  _tui_repeat "$BOXH_H" "$inner"
  printf '%b\n\n' "$TUI_RESET"
}

###############################################################################
# Forge MCP ASCII Banner
###############################################################################

tui_forge_banner() {
  clear 2>/dev/null || true
  local w
  w="$(tui_term_width)"

  local -a logo=(
    "   ███████╗ ██████╗ ██████╗  ██████╗ ███████╗"
    "   ██╔════╝██╔═══██╗██╔══██╗██╔════╝ ██╔════╝"
    "   █████╗  ██║   ██║██████╔╝██║  ███╗█████╗  "
    "   ██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══╝  "
    "   ██║     ╚██████╔╝██║  ██║╚██████╔╝███████╗"
    "   ╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝"
  )

  local -a grad=(
    '\033[38;5;208m'   # Orange
    '\033[38;5;214m'   # Light orange
    '\033[38;5;220m'   # Gold
    '\033[38;5;214m'   # Light orange
    '\033[38;5;208m'   # Orange
    '\033[38;5;202m'   # Dark orange
  )

  echo
  local i
  for i in "${!logo[@]}"; do
    printf '%b%s%b\n' "${grad[$i]}" "${logo[$i]}" "$TUI_RESET"
  done

  local inner=$((w - 4))
  echo
  printf '  %b' "$TUI_MUTED"
  _tui_repeat "$BOX_H" "$inner"
  printf '%b\n' "$TUI_RESET"

  printf '  %b%s MCP Server  %b·%b  %s PR Review  %b·%b  %s VS Code Agent Mode%b\n' \
    "$TUI_ACCENT2" "$ICON_HAMMER" \
    "$TUI_MUTED" "$TUI_ACCENT2" "$ICON_SHIELD" \
    "$TUI_MUTED" "$TUI_ACCENT2" "$ICON_VSCODE" \
    "$TUI_RESET"

  printf '  %b' "$TUI_MUTED"
  _tui_repeat "$BOX_H" "$inner"
  printf '%b\n' "$TUI_RESET"

  echo
  printf '  %b%b%s%b  %bv%s%b    %b%s%b\n' \
    "$TUI_BOLD" "$TUI_WHITE" "$INSTALLER_NAME" "$TUI_RESET" \
    "$TUI_MUTED" "$INSTALLER_VERSION" "$TUI_RESET" \
    "$TUI_DIM" "$(date '+%Y-%m-%d %H:%M')" "$TUI_RESET"
  echo
}

###############################################################################
# Installation plan card
###############################################################################

tui_plan_card() {
  TUI_BOX_COLOR="$TUI_ACCENT" tui_box "${ICON_CHART}  Installation Plan" \
    "" \
    "$(tui_kv_inline 'Python'     "$( [[ "$SKIP_PYTHON" == true ]] && echo "${TUI_MUTED}skip${TUI_RESET}" || echo "≥ ${MIN_PYTHON_VERSION}" )")" \
    "$(tui_kv_inline 'uv'         "$( [[ "$SKIP_UV"     == true ]] && echo "${TUI_MUTED}skip${TUI_RESET}" || echo 'install/verify' )")" \
    "$(tui_kv_inline 'VS Code'    "$( [[ "$SKIP_VSCODE" == true ]] && echo "${TUI_MUTED}skip${TUI_RESET}" || echo 'configure mcp.json' )")" \
    "$(tui_kv_inline 'MCP Server' "$( [[ "$SKIP_MCP"    == true ]] && echo "${TUI_MUTED}skip${TUI_RESET}" || echo 'uv sync + verify' )")" \
    "$(tui_kv_inline 'Source'     "$( [[ "$INSTALL_FROM_LOCAL" == true ]] && echo "${TUI_ACCENT2}local${TUI_RESET}" || echo "${TUI_ACCENT2}${FORGE_MCP_REPO}${TUI_RESET}" )")" \
    "" \
    "$(tui_kv_inline 'Dry run'    "${DRY_RUN}")" \
    "$(tui_kv_inline 'Log file'   "${TUI_DIM}${LOG_FILE}${TUI_RESET}")"
}

###############################################################################
# Completion screen
###############################################################################

tui_completion_screen() {
  local elapsed="$1"
  local w
  w="$(tui_term_width)"
  local inner=$((w - 4))

  echo
  printf '  %b' "$TUI_SUCCESS"
  _tui_repeat "$BOX2_H" "$inner"
  printf '%b\n' "$TUI_RESET"

  local msg="${ICON_SPARKLE}  Forge MCP is ready!  ${ICON_SPARKLE}"
  local stripped
  stripped="$(_tui_strip_ansi "$msg")"
  local pad=$(( (inner - ${#stripped}) / 2 ))
  (( pad < 0 )) && pad=0

  printf '  %b%b' "$TUI_SUCCESS" "$TUI_BOLD"
  _tui_repeat ' ' "$pad"
  printf '%s%b\n' "$msg" "$TUI_RESET"

  printf '  %b%bCompleted %s steps in %s%b\n' \
    "$TUI_SUCCESS" "$TUI_DIM" "$TOTAL_STEPS" "$elapsed" "$TUI_RESET"

  printf '  %b' "$TUI_SUCCESS"
  _tui_repeat "$BOX2_H" "$inner"
  printf '%b\n' "$TUI_RESET"
}

###############################################################################
# Failure screen
###############################################################################

tui_failure_screen() {
  local exit_code="$1"
  local w
  w="$(tui_term_width)"
  local inner=$((w - 4))

  echo
  printf '  %b' "$TUI_ERROR"
  _tui_repeat "$BOX2_H" "$inner"
  printf '%b\n' "$TUI_RESET"

  printf '  %b%b  %s  Installation failed (exit code %d)%b\n' \
    "$TUI_ERROR" "$TUI_BOLD" "$ICON_CROSS" "$exit_code" "$TUI_RESET"
  printf '  %b     Log: %s%b\n' "$TUI_ERROR" "$LOG_FILE" "$TUI_RESET"

  printf '  %b' "$TUI_ERROR"
  _tui_repeat "$BOX2_H" "$inner"
  printf '%b\n' "$TUI_RESET"
}
