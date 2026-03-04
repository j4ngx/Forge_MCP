#!/usr/bin/env bash
# shellcheck disable=SC2034
# =============================================================================
# lib/tui.sh — Terminal User Interface library for Forge MCP Installer
# =============================================================================
# Professional TUI with 256-colour palette, Unicode box drawing, animated
# spinners, progress bars with sub-block precision, step tracker pipeline,
# interactive menus, styled prompts, and themed screens.
#
# Adapted from GLaDOS Installer TUI — https://github.com/j4ngx/GLaDos-Installer
# =============================================================================

[[ -n "${_FORGE_TUI_LOADED:-}" ]] && return 0
readonly _FORGE_TUI_LOADED=1

###############################################################################
# Extended 256-colour palette                                                 #
###############################################################################

TUI_ACCENT='\033[38;5;208m'        # — Orange (Forge brand)
TUI_ACCENT2='\033[38;5;39m'        # — Electric blue
TUI_ACCENT3='\033[38;5;214m'       # — Amber / gold
TUI_SUCCESS='\033[38;5;78m'        # — Soft green
TUI_WARNING='\033[38;5;220m'       # — Gold
TUI_ERROR='\033[38;5;196m'         # — Bright red
TUI_MUTED='\033[38;5;243m'         # — Grey
TUI_WHITE='\033[38;5;255m'         # — Bright white
TUI_HEADER_BG='\033[48;5;236m'     # — Dark grey background
TUI_HIGHLIGHT='\033[38;5;117m'     # — Light cyan
TUI_ORANGE='\033[38;5;208m'        # — Orange alias
TUI_FIRE='\033[38;5;202m'          # — Dark orange / fire
TUI_EMBER='\033[38;5;166m'         # — Deep ember red-orange
TUI_GOLD='\033[38;5;220m'          # — Gold
TUI_STEEL='\033[38;5;249m'         # — Steel / light grey

TUI_BOLD='\033[1m'
TUI_DIM='\033[2m'
TUI_ITALIC='\033[3m'
TUI_UNDERLINE='\033[4m'
TUI_BLINK='\033[5m'
TUI_REVERSE='\033[7m'
TUI_RESET='\033[0m'

# Graceful degradation for non-TTY environments
if [[ ! -t 1 ]]; then
  TUI_ACCENT='' TUI_ACCENT2='' TUI_ACCENT3='' TUI_SUCCESS='' TUI_WARNING=''
  TUI_ERROR='' TUI_MUTED='' TUI_WHITE='' TUI_HEADER_BG='' TUI_HIGHLIGHT=''
  TUI_ORANGE='' TUI_FIRE='' TUI_EMBER='' TUI_GOLD='' TUI_STEEL=''
  TUI_BOLD='' TUI_DIM='' TUI_ITALIC='' TUI_UNDERLINE='' TUI_BLINK=''
  TUI_REVERSE='' TUI_RESET=''
fi

###############################################################################
# Terminal geometry                                                           #
###############################################################################

tui_term_width() {
  local w
  w="$(tput cols 2>/dev/null || echo 80)"
  (( w < 40 )) && w=40
  (( w > 120 )) && w=120
  echo "$w"
}

###############################################################################
# Unicode box-drawing characters                                              #
###############################################################################

# Rounded corners
readonly BOX_TL='╭' BOX_TR='╮' BOX_BL='╰' BOX_BR='╯'
readonly BOX_H='─'  BOX_V='│'
readonly BOX_LT='├' BOX_RT='┤'

# Double-line
readonly BOX2_TL='╔' BOX2_TR='╗' BOX2_BL='╚' BOX2_BR='╝'
readonly BOX2_H='═'  BOX2_V='║'

# Heavy
readonly BOXH_H='━' BOXH_V='┃'

# Block elements (sub-block precision: 1/8 → full)
readonly BLK_1='▏' BLK_2='▎' BLK_3='▍' BLK_4='▌'
readonly BLK_5='▋' BLK_6='▊' BLK_7='▉' BLK_8='█'
readonly BLOCK_FULL='█' BLOCK_EMPTY='░'

###############################################################################
# Status icons                                                                #
###############################################################################

readonly ICON_CHECK='✔'    ICON_CROSS='✖'    ICON_WARN='⚠'     ICON_INFO='ℹ'
readonly ICON_ARROW='▸'    ICON_DOT='●'      ICON_RING='○'     ICON_STAR='★'
readonly ICON_GEAR='⚙'     ICON_BOLT='⚡'     ICON_PACKAGE='📦'
readonly ICON_CHART='📊'   ICON_SPARKLE='✨'  ICON_HAMMER='🔨'
readonly ICON_SNAKE='🐍'   ICON_VSCODE='💻'   ICON_ROCKET='🚀'
readonly ICON_SHIELD='🛡'   ICON_CLOCK='🕐'    ICON_LINK='🔗'
readonly ICON_FIRE='🔥'    ICON_GLOBE='🌐'    ICON_LOCK='🔒'
readonly ICON_KEY='🔑'     ICON_WRENCH='🔧'   ICON_ANVIL='⚒'

###############################################################################
# Internal helpers                                                            #
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

_tui_center() {
  local text="$1"
  local w
  w="$(tui_term_width)"
  local stripped
  stripped="$(_tui_strip_ansi "$text")"
  local pad=$(( (w - ${#stripped}) / 2 ))
  (( pad < 0 )) && pad=0
  _tui_repeat ' ' "$pad"
  printf '%b\n' "$text"
}

###############################################################################
# Box drawing — rounded corners                                               #
###############################################################################

tui_box() {
  local title="${1:-}"; shift
  local w
  w="$(tui_term_width)"
  local inner=$((w - 4))
  local color="${TUI_BOX_COLOR:-$TUI_ACCENT}"

  # Top border
  printf '%b  %s' "$color" "$BOX_TL"
  _tui_repeat "$BOX_H" "$inner"
  printf '%s%b\n' "$BOX_TR" "$TUI_RESET"

  # Title row (optional)
  if [[ -n "$title" ]]; then
    local stripped
    stripped="$(_tui_strip_ansi "$title")"
    local pad=$((inner - ${#stripped} - 2))
    (( pad < 0 )) && pad=0
    printf '%b  %s %b%b%s%b' "$color" "$BOX_V" "$TUI_BOLD" "$TUI_WHITE" "$title" "$TUI_RESET"
    printf '%b' "$color"
    _tui_repeat ' ' "$pad"
    printf ' %s%b\n' "$BOX_V" "$TUI_RESET"

    # Separator
    printf '%b  %s' "$color" "$BOX_LT"
    _tui_repeat "$BOX_H" "$inner"
    printf '%s%b\n' "$BOX_RT" "$TUI_RESET"
  fi

  # Content rows
  local line
  for line in "$@"; do
    if [[ -z "$line" ]]; then
      printf '%b  %s' "$color" "$BOX_V"
      _tui_repeat ' ' "$inner"
      printf '%s%b\n' "$BOX_V" "$TUI_RESET"
      continue
    fi
    local stripped
    stripped="$(_tui_strip_ansi "$line")"
    local pad=$((inner - ${#stripped} - 2))
    (( pad < 0 )) && pad=0
    printf '%b  %s %b%b' "$color" "$BOX_V" "$TUI_RESET" "$line"
    _tui_repeat ' ' "$pad"
    printf '%b %s%b\n' "$color" "$BOX_V" "$TUI_RESET"
  done

  # Bottom border
  printf '%b  %s' "$color" "$BOX_BL"
  _tui_repeat "$BOX_H" "$inner"
  printf '%s%b\n' "$BOX_BR" "$TUI_RESET"
}

###############################################################################
# Box drawing — double-line (emphasis box)                                    #
###############################################################################

tui_box_double() {
  local title="${1:-}"; shift
  local w
  w="$(tui_term_width)"
  local inner=$((w - 4))
  local color="${TUI_BOX_COLOR:-$TUI_ACCENT2}"

  printf '%b  %s' "$color" "$BOX2_TL"
  _tui_repeat "$BOX2_H" "$inner"
  printf '%s%b\n' "$BOX2_TR" "$TUI_RESET"

  if [[ -n "$title" ]]; then
    local stripped
    stripped="$(_tui_strip_ansi "$title")"
    local pad=$((inner - ${#stripped} - 2))
    (( pad < 0 )) && pad=0
    printf '%b  %s %b%b%s%b' "$color" "$BOX2_V" "$TUI_BOLD" "$TUI_WHITE" "$title" "$TUI_RESET"
    printf '%b' "$color"
    _tui_repeat ' ' "$pad"
    printf ' %s%b\n' "$BOX2_V" "$TUI_RESET"

    printf '%b  %s' "$color" "$BOX2_V"
    _tui_repeat "$BOX2_H" "$inner"
    printf '%s%b\n' "$BOX2_V" "$TUI_RESET"
  fi

  local line
  for line in "$@"; do
    if [[ -z "$line" ]]; then
      printf '%b  %s' "$color" "$BOX2_V"
      _tui_repeat ' ' "$inner"
      printf '%s%b\n' "$BOX2_V" "$TUI_RESET"
      continue
    fi
    local stripped
    stripped="$(_tui_strip_ansi "$line")"
    local pad=$((inner - ${#stripped} - 2))
    (( pad < 0 )) && pad=0
    printf '%b  %s %b%b' "$color" "$BOX2_V" "$TUI_RESET" "$line"
    _tui_repeat ' ' "$pad"
    printf '%b %s%b\n' "$color" "$BOX2_V" "$TUI_RESET"
  done

  printf '%b  %s' "$color" "$BOX2_BL"
  _tui_repeat "$BOX2_H" "$inner"
  printf '%s%b\n' "$BOX2_BR" "$TUI_RESET"
}

###############################################################################
# Horizontal dividers                                                         #
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
# Progress bar — sub-block precision (8 gradations per cell)                  #
###############################################################################

tui_progress() {
  local current="$1" total="$2" label="${3:-}"
  local bar_width=30
  (( total == 0 )) && total=1

  local pct=$((current * 100 / total))
  (( pct > 100 )) && pct=100

  # Sub-block precision: compute filled eighths
  local filled_eighths=$((current * bar_width * 8 / total))
  local full_blocks=$((filled_eighths / 8))
  local remainder=$((filled_eighths % 8))
  local has_partial=0
  (( remainder > 0 )) && has_partial=1
  local empty=$((bar_width - full_blocks - has_partial))
  (( empty < 0 )) && empty=0

  # Colour transitions
  local bar_color="$TUI_ACCENT2"
  (( pct >= 50 )) && bar_color="$TUI_ACCENT"
  (( pct >= 80 )) && bar_color="$TUI_SUCCESS"

  # Sub-block character map
  local -a sub_blocks=("" "$BLK_1" "$BLK_2" "$BLK_3" "$BLK_4" "$BLK_5" "$BLK_6" "$BLK_7")

  printf '\r  %b' "$bar_color"
  _tui_repeat "$BLOCK_FULL" "$full_blocks"

  if (( remainder > 0 )); then
    printf '%s' "${sub_blocks[$remainder]}"
  fi

  printf '%b' "$TUI_MUTED"
  _tui_repeat "$BLOCK_EMPTY" "$empty"
  printf '%b %b%3d%%%b' "$TUI_RESET" "$TUI_BOLD" "$pct" "$TUI_RESET"
  [[ -n "$label" ]] && printf '  %b%s%b' "$TUI_MUTED" "$label" "$TUI_RESET"
  printf '\033[K'
}

tui_progress_done() { printf '\n'; }

###############################################################################
# Step tracker pipeline                                                       #
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
  local done_count=0

  # Count completed
  for i in "${!_TUI_STEPS[@]}"; do
    [[ "${_TUI_STEP_STATUS[$i]}" == "done" ]] && (( done_count++ ))
  done

  echo
  # Header with progress counter
  printf '  %b%b%s  Installation Progress%b  %b[%d/%d]%b\n' \
    "$TUI_BOLD" "$TUI_WHITE" "$ICON_CHART" "$TUI_RESET" \
    "$TUI_MUTED" "$done_count" "$total" "$TUI_RESET"
  tui_divider "dots"
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

    local num=$((i + 1))
    printf '  %b  %b%b%d%b  %b%s%b\n' \
      "$icon" "$TUI_DIM" "$color" "$num" "$TUI_RESET" \
      "$color" "$label" "$TUI_RESET"

    # Connector line between steps
    if (( i < total - 1 )); then
      local next_status="${_TUI_STEP_STATUS[$((i + 1))]}"
      local conn_color="$TUI_MUTED"
      [[ "$next_status" == "done" || "$next_status" == "active" ]] && conn_color="$TUI_ACCENT"
      printf '     %b│%b\n' "$conn_color" "$TUI_RESET"
    fi
  done
  echo
}

###############################################################################
# Section header                                                              #
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
# Animated spinners — 7 styles                                                #
###############################################################################

_TUI_SPINNER_PID=""

readonly -a SPIN_DOTS=("⠋" "⠙" "⠹" "⠸" "⠼" "⠴" "⠦" "⠧" "⠇" "⠏")
readonly -a SPIN_BRAILLE=("⣾" "⣽" "⣻" "⢿" "⡿" "⣟" "⣯" "⣷")
readonly -a SPIN_ARROWS=("←" "↖" "↑" "↗" "→" "↘" "↓" "↙")
readonly -a SPIN_BOUNCE=("⠁" "⠂" "⠄" "⡀" "⢀" "⠠" "⠐" "⠈")
readonly -a SPIN_PULSE=("░" "▒" "▓" "█" "▓" "▒")
readonly -a SPIN_EARTH=("🌍" "🌎" "🌏")
readonly -a SPIN_MOON=("🌑" "🌒" "🌓" "🌔" "🌕" "🌖" "🌗" "🌘")

tui_spinner_start() {
  local msg="${1:-Working...}"
  local style="${2:-dots}"

  [[ ! -t 1 ]] && { log "$msg"; return; }

  (
    set +eEu
    trap 'exit 0' TERM
    trap '' ERR

    local -a frames
    case "$style" in
      braille) frames=("${SPIN_BRAILLE[@]}") ;;
      arrows)  frames=("${SPIN_ARROWS[@]}") ;;
      bounce)  frames=("${SPIN_BOUNCE[@]}") ;;
      pulse)   frames=("${SPIN_PULSE[@]}") ;;
      earth)   frames=("${SPIN_EARTH[@]}") ;;
      moon)    frames=("${SPIN_MOON[@]}") ;;
      *)       frames=("${SPIN_DOTS[@]}") ;;
    esac

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

# Convenience: run a command with spinner
tui_spin_exec() {
  local msg="$1"; shift
  local style="${TUI_SPIN_STYLE:-dots}"
  tui_spinner_start "$msg" "$style"
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
# Styled interactive prompts                                                  #
###############################################################################

# Yes/No confirmation
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

# Value input
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

# Numbered selection menu
tui_select() {
  local result_var="$1"; shift
  local prompt="$1"; shift
  local -a options=("$@")
  local count=${#options[@]}

  echo
  printf '  %b%b%s%b\n' "$TUI_BOLD" "$TUI_WHITE" "$prompt" "$TUI_RESET"
  tui_divider "dots"

  local i
  for i in "${!options[@]}"; do
    printf '  %b%s%b  %b%d%b  %s\n' \
      "$TUI_ACCENT" "$ICON_DOT" "$TUI_RESET" \
      "$TUI_BOLD" $((i + 1)) "$TUI_RESET" \
      "${options[$i]}"
  done
  echo

  while true; do
    printf '  %b%s%b Enter choice [1-%d]: ' \
      "$TUI_ACCENT2" "$ICON_ARROW" "$TUI_RESET" "$count"
    local choice
    read -r choice
    if [[ "$choice" =~ ^[0-9]+$ ]] && (( choice >= 1 && choice <= count )); then
      printf -v "$result_var" '%s' "${options[$((choice - 1))]}"
      return 0
    fi
    printf '  %b%s  Invalid selection.%b\n' "$TUI_WARNING" "$ICON_WARN" "$TUI_RESET"
  done
}

# Checklist (multi-select toggle)
tui_checklist() {
  local result_var="$1"; shift
  local prompt="$1"; shift
  local -a options=("$@")
  local count=${#options[@]}

  # Default: all selected
  local -a selected=()
  local i
  for i in "${!options[@]}"; do
    selected[i]=1
  done

  if [[ "$NON_INTERACTIVE" == true ]]; then
    local result=""
    for i in "${!options[@]}"; do
      (( selected[i] )) && result+="${options[$i]}|"
    done
    printf -v "$result_var" '%s' "${result%|}"
    return
  fi

  echo
  printf '  %b%b%s%b\n' "$TUI_BOLD" "$TUI_WHITE" "$prompt" "$TUI_RESET"
  printf '  %bToggle with number, Enter to confirm%b\n' "$TUI_MUTED" "$TUI_RESET"
  tui_divider "dots"

  while true; do
    for i in "${!options[@]}"; do
      local marker
      if (( selected[i] )); then
        marker="${TUI_SUCCESS}${ICON_CHECK}${TUI_RESET}"
      else
        marker="${TUI_MUTED}${ICON_RING}${TUI_RESET}"
      fi
      printf '  %b  %b%d%b  %s\n' \
        "$marker" "$TUI_BOLD" $((i + 1)) "$TUI_RESET" "${options[$i]}"
    done
    echo

    printf '  %b%s%b Toggle [1-%d] or Enter to confirm: ' \
      "$TUI_ACCENT2" "$ICON_ARROW" "$TUI_RESET" "$count"
    local input
    read -r input

    # Empty = confirm
    if [[ -z "$input" ]]; then
      local result=""
      for i in "${!options[@]}"; do
        (( selected[i] )) && result+="${options[$i]}|"
      done
      printf -v "$result_var" '%s' "${result%|}"
      return 0
    fi

    if [[ "$input" =~ ^[0-9]+$ ]] && (( input >= 1 && input <= count )); then
      local idx=$((input - 1))
      if (( selected[idx] )); then
        selected[idx]=0
      else
        selected[idx]=1
      fi
    else
      printf '  %b%s  Invalid input.%b\n' "$TUI_WARNING" "$ICON_WARN" "$TUI_RESET"
    fi

    # Clear the list for re-render (move cursor up)
    local lines_to_clear=$((count + 2))
    local l
    for l in $(seq 1 "$lines_to_clear"); do
      printf '\033[A\033[K'
    done
  done
}

###############################################################################
# Status displays                                                             #
###############################################################################

# Dashboard status line
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

# Key-value pair
tui_kv() {
  local key="$1" value="$2" icon="${3:-}"
  if [[ -n "$icon" ]]; then
    printf '  %s  %b%-18s%b  %b%s%b\n' \
      "$icon" "$TUI_MUTED" "$key" "$TUI_RESET" "$TUI_WHITE" "$value" "$TUI_RESET"
  else
    printf '      %b%-18s%b  %b%s%b\n' \
      "$TUI_MUTED" "$key" "$TUI_RESET" "$TUI_WHITE" "$value" "$TUI_RESET"
  fi
}

# Inline key-value (for box content lines)
tui_kv_inline() {
  local key="$1" value="$2"
  printf '%b%-18s%b  %b' "$TUI_MUTED" "$key" "$TUI_RESET" "$value"
}

# Health-check row
tui_health_row() {
  local label="$1" value="$2" ok="${3:-true}"
  if [[ "$ok" == true ]]; then
    printf '  %b%s%b  %-22s %b%s%b\n' \
      "$TUI_SUCCESS" "$ICON_CHECK" "$TUI_RESET" "$label" "$TUI_SUCCESS" "$value" "$TUI_RESET"
  else
    printf '  %b%s%b  %-22s %b%s%b\n' \
      "$TUI_ERROR" "$ICON_CROSS" "$TUI_RESET" "$label" "$TUI_ERROR" "$value" "$TUI_RESET"
  fi
}

# Quick command hint
tui_command_hint() {
  local desc="$1" cmd="$2"
  printf '    %b%s%b  %b%s%b\n' \
    "$TUI_MUTED" "$desc" "$TUI_RESET" \
    "$TUI_ACCENT2" "$cmd" "$TUI_RESET"
}

###############################################################################
# Notification bar                                                            #
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
# Typewriter effect                                                           #
###############################################################################

tui_typewriter() {
  local text="$1" delay="${2:-0.03}"
  [[ ! -t 1 ]] && { printf '%s\n' "$text"; return; }
  local i
  for (( i=0; i<${#text}; i++ )); do
    printf '%s' "${text:$i:1}"
    sleep "$delay"
  done
  printf '\n'
}

###############################################################################
# Countdown timer                                                             #
###############################################################################

tui_countdown() {
  local secs="$1" msg="${2:-Starting in}"
  [[ ! -t 1 ]] && return
  while (( secs > 0 )); do
    printf '\r  %b%s%b %s %b%d%bs...  \033[K' \
      "$TUI_ACCENT2" "$ICON_CLOCK" "$TUI_RESET" \
      "$msg" "$TUI_BOLD" "$secs" "$TUI_RESET"
    sleep 1
    secs=$((secs - 1))
  done
  printf '\r\033[K'
}

###############################################################################
# Forge MCP ASCII banner                                                      #
###############################################################################

tui_forge_banner() {
  clear 2>/dev/null || true
  local w
  w="$(tui_term_width)"

  # Large FORGE ASCII art with fire gradient
  local -a logo=(
    "  ███████╗  ██████╗  ██████╗   ██████╗  ███████╗"
    "  ██╔════╝ ██╔═══██╗ ██╔══██╗ ██╔════╝  ██╔════╝"
    "  █████╗   ██║   ██║ ██████╔╝ ██║  ███╗ █████╗  "
    "  ██╔══╝   ██║   ██║ ██╔══██╗ ██║   ██║ ██╔══╝  "
    "  ██║      ╚██████╔╝ ██║  ██║ ╚██████╔╝ ███████╗"
    "  ╚═╝       ╚═════╝  ╚═╝  ╚═╝  ╚═════╝  ╚══════╝"
  )

  # Smaller MCP subtitle
  local -a subtitle=(
    "          ███╗   ███╗  ██████╗ ██████╗ "
    "          ████╗ ████║ ██╔════╝ ██╔══██╗"
    "          ██╔████╔██║ ██║      ██████╔╝"
    "          ██║╚██╔╝██║ ██║      ██╔═══╝ "
    "          ██║ ╚═╝ ██║ ╚██████╗ ██║     "
    "          ╚═╝     ╚═╝  ╚═════╝ ╚═╝     "
  )

  # Fire gradient: dark ember → orange → gold
  local -a grad_forge=(
    '\033[38;5;202m'
    '\033[38;5;208m'
    '\033[38;5;214m'
    '\033[38;5;220m'
    '\033[38;5;214m'
    '\033[38;5;208m'
  )

  # Blue gradient for MCP
  local -a grad_mcp=(
    '\033[38;5;39m'
    '\033[38;5;75m'
    '\033[38;5;111m'
    '\033[38;5;75m'
    '\033[38;5;39m'
    '\033[38;5;33m'
  )

  echo
  local i
  for i in "${!logo[@]}"; do
    printf '%b%s%b\n' "${grad_forge[$i]}" "${logo[$i]}" "$TUI_RESET"
  done
  echo
  for i in "${!subtitle[@]}"; do
    printf '%b%s%b\n' "${grad_mcp[$i]}" "${subtitle[$i]}" "$TUI_RESET"
  done

  # Feature tagline
  local inner=$((w - 4))
  echo
  printf '  %b' "$TUI_MUTED"
  _tui_repeat "$BOX_H" "$inner"
  printf '%b\n' "$TUI_RESET"

  printf '  %b%s PR Review  %b·%b  %s Apply Issues  %b·%b  %s Scaffold  %b·%b  %s Commit & PR%b\n' \
    "$TUI_ACCENT2" "$ICON_SHIELD" \
    "$TUI_MUTED" "$TUI_ACCENT2" "$ICON_WRENCH" \
    "$TUI_MUTED" "$TUI_ACCENT2" "$ICON_PACKAGE" \
    "$TUI_MUTED" "$TUI_ACCENT2" "$ICON_ROCKET" \
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
# Installation plan card                                                      #
###############################################################################

tui_plan_card() {
  local w
  w="$(tui_term_width)"

  TUI_BOX_COLOR="$TUI_ACCENT" tui_box "${ICON_CHART}  Installation Plan" \
    "" \
    "$(tui_kv_inline 'Python'     "$( [[ "$SKIP_PYTHON" == true ]] && echo "${TUI_MUTED}skip${TUI_RESET}" || echo "≥ ${MIN_PYTHON_VERSION}" )")" \
    "$(tui_kv_inline 'uv'         "$( [[ "$SKIP_UV"     == true ]] && echo "${TUI_MUTED}skip${TUI_RESET}" || echo 'install / verify' )")" \
    "$(tui_kv_inline 'VS Code'    "$( [[ "$SKIP_VSCODE" == true ]] && echo "${TUI_MUTED}skip${TUI_RESET}" || echo 'configure mcp.json' )")" \
    "$(tui_kv_inline 'MCP Server' "$( [[ "$SKIP_MCP"    == true ]] && echo "${TUI_MUTED}skip${TUI_RESET}" || echo 'uv sync + verify' )")" \
    "" \
    "$(tui_kv_inline 'Source'     "$( [[ "$INSTALL_FROM_LOCAL" == true ]] && echo "${TUI_ACCENT2}local copy${TUI_RESET}" || echo "${TUI_ACCENT2}${FORGE_MCP_REPO}${TUI_RESET}" )")" \
    "$(tui_kv_inline 'Branch'     "${TUI_ACCENT2}${FORGE_MCP_BRANCH}${TUI_RESET}")" \
    "$(tui_kv_inline 'Install dir' "${TUI_DIM}${FORGE_MCP_DIR:-~/Projects/forge_mcp}${TUI_RESET}")" \
    "" \
    "$(tui_kv_inline 'Dry run'    "$( [[ "$DRY_RUN" == true ]] && echo "${TUI_WARNING}yes${TUI_RESET}" || echo "${TUI_MUTED}no${TUI_RESET}" )")" \
    "$(tui_kv_inline 'Log file'   "${TUI_DIM}${LOG_FILE}${TUI_RESET}")"
}

###############################################################################
# Completion screen                                                           #
###############################################################################

tui_completion_screen() {
  local elapsed="$1"
  local w
  w="$(tui_term_width)"
  local inner=$((w - 4))

  echo
  # Top double border
  printf '  %b' "$TUI_SUCCESS"
  _tui_repeat "$BOX2_H" "$inner"
  printf '%b\n' "$TUI_RESET"

  # Centered success message
  local msg="${ICON_SPARKLE}  Forge MCP is ready!  ${ICON_SPARKLE}"
  local stripped
  stripped="$(_tui_strip_ansi "$msg")"
  local pad=$(( (inner - ${#stripped}) / 2 ))
  (( pad < 0 )) && pad=0

  printf '  %b%b' "$TUI_SUCCESS" "$TUI_BOLD"
  _tui_repeat ' ' "$pad"
  printf '%s%b\n' "$msg" "$TUI_RESET"

  # Elapsed time — centered
  local elapsed_msg="Completed ${TOTAL_STEPS} steps in ${elapsed}"
  local stripped_elapsed
  stripped_elapsed="$(_tui_strip_ansi "$elapsed_msg")"
  local epad=$(( (inner - ${#stripped_elapsed}) / 2 ))
  (( epad < 0 )) && epad=0
  printf '  %b%b' "$TUI_SUCCESS" "$TUI_DIM"
  _tui_repeat ' ' "$epad"
  printf '%s%b\n' "$elapsed_msg" "$TUI_RESET"

  # Bottom double border
  printf '  %b' "$TUI_SUCCESS"
  _tui_repeat "$BOX2_H" "$inner"
  printf '%b\n' "$TUI_RESET"
}

###############################################################################
# Failure screen                                                              #
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
  printf '  %b     Re-run the installer — completed steps are skipped.%b\n' \
    "$TUI_ERROR" "$TUI_RESET"

  printf '  %b' "$TUI_ERROR"
  _tui_repeat "$BOX2_H" "$inner"
  printf '%b\n' "$TUI_RESET"
}

###############################################################################
# Summary screens                                                             #
###############################################################################

tui_summary_dashboard() {
  local elapsed="$1"

  echo
  TUI_BOX_COLOR="$TUI_ACCENT" tui_box "${ICON_CHART}  Installation Summary" \
    "" \
    "$(tui_kv_inline 'Install dir'  "${FORGE_MCP_DIR:-N/A}")" \
    "$(tui_kv_inline 'Python'       "${PYTHON_VERSION:-not checked}")" \
    "$(tui_kv_inline 'uv'           "${UV_VERSION:-not checked}")" \
    "$(tui_kv_inline 'VS Code'      "$(command -v "${VSCODE_CMD:-code}" 2>/dev/null || echo 'not found')")" \
    "$(tui_kv_inline 'Duration'     "$elapsed")" \
    "$(tui_kv_inline 'Log'          "${TUI_DIM}${LOG_FILE}${TUI_RESET}")" \
    ""
}

tui_next_steps_card() {
  echo
  TUI_BOX_COLOR="$TUI_ACCENT2" tui_box "${ICON_ROCKET}  Next Steps" \
    "" \
    "${TUI_BOLD}1.${TUI_RESET}  Open VS Code in the project:" \
    "" \
    "$(tui_command_hint '' "code ${FORGE_MCP_DIR:-~/Projects/forge_mcp}")" \
    "" \
    "${TUI_BOLD}2.${TUI_RESET}  The MCP server is configured in ${TUI_DIM}mcp.json${TUI_RESET}." \
    "    Copilot Chat auto-discovers the forge_mcp tools." \
    "" \
    "${TUI_BOLD}3.${TUI_RESET}  In Copilot Agent Mode try a tool:" \
    "" \
    "$(tui_command_hint '' "\"Review the PR diff I just pasted\"")" \
    "$(tui_command_hint '' "\"Apply issue #42 to this repo\"")" \
    "$(tui_command_hint '' "\"Scaffold a new Python project\"")" \
    ""
}
