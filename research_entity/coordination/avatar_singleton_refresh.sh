#!/usr/bin/env bash
set -euo pipefail

# Canonical production-avatar singleton keeper for ai-core-node.
# Owner law 2026-09-12: one production Chrome/window, visible on physical screen 2;
# reuse+refresh the existing subject, open via the existing buehne daemon only if absent.

export DISPLAY="${DISPLAY:-:0}"
TITLE='FranKenstein -- live'
PID_FILE='/home/ai-core-node/.claude/star/visual/chrome.pid'
SCREEN2_X0=1680
SCREEN2_X1=2704
TARGET_X=1847
TARGET_Y=168
TARGET_W=746
TARGET_H=449
API='http://127.0.0.1:8788/api/schalten'

command -v xdotool >/dev/null 2>&1 || { echo 'ERROR: xdotool missing' >&2; exit 20; }

find_windows() {
  xdotool search --name "^${TITLE}$" 2>/dev/null || true
}

mapfile -t wins < <(find_windows)

# Never launch Chrome directly. The existing daemon is the single lifecycle owner.
# If the production subject is absent, ask that daemon to switch the stage on once.
if ((${#wins[@]} == 0)); then
  if command -v curl >/dev/null 2>&1; then
    curl -fsS -X POST -H 'Content-Type: application/json' --data '{"an":true}' "$API" >/dev/null
  else
    echo 'ERROR: production window absent and curl unavailable; refusing ad-hoc Chrome launch' >&2
    exit 21
  fi
  for _ in {1..20}; do
    sleep 0.25
    mapfile -t wins < <(find_windows)
    ((${#wins[@]} > 0)) && break
  done
fi

((${#wins[@]} > 0)) || { echo 'ERROR: buehne daemon did not create production window' >&2; exit 22; }

# Strongest identity: prefer the X11 window whose PID matches the daemon-owned chrome.pid.
# This avoids keeping a worker-spawned duplicate merely because both windows happen to sit
# on screen 2. Window IDs are ephemeral; PID_FILE is refreshed by the canonical daemon.
keep=''
tracked_pid=''
if [[ -r "$PID_FILE" ]]; then
  tracked_pid="$(tr -dc '0-9' < "$PID_FILE")"
fi
if [[ "$tracked_pid" =~ ^[0-9]+$ ]]; then
  for wid in "${wins[@]}"; do
    wpid="$(xdotool getwindowpid "$wid" 2>/dev/null || true)"
    if [[ "$wpid" == "$tracked_pid" ]]; then
      keep="$wid"
      break
    fi
  done
fi

# Second-best identity: an already-existing production-title window on physical screen 2.
if [[ -z "$keep" ]]; then
  for wid in "${wins[@]}"; do
    geom="$(xdotool getwindowgeometry --shell "$wid" 2>/dev/null || true)"
    x="$(printf '%s\n' "$geom" | sed -n 's/^X=//p' | head -1)"
    if [[ "$x" =~ ^-?[0-9]+$ ]] && (( x >= SCREEN2_X0 && x < SCREEN2_X1 )); then
      keep="$wid"
      break
    fi
  done
fi

# Last resort: preserve an existing instance and move it; never replace it just for geometry.
[[ -n "$keep" ]] || keep="${wins[0]}"

# Close only confirmed duplicate windows with the exact production title.
for wid in "${wins[@]}"; do
  [[ "$wid" == "$keep" ]] && continue
  xdotool windowclose "$wid" 2>/dev/null || true
done

# Keep the singleton on screen 2 at the measured production geometry.
xdotool windowmap "$keep" 2>/dev/null || true
xdotool windowsize "$keep" "$TARGET_W" "$TARGET_H" 2>/dev/null || true
xdotool windowmove "$keep" "$TARGET_X" "$TARGET_Y" 2>/dev/null || true
xdotool windowraise "$keep" 2>/dev/null || true

# Normal update path: refresh the existing singleton, never spawn a new production Chrome.
xdotool key --clearmodifiers --window "$keep" ctrl+r
sleep 0.35

mapfile -t after < <(find_windows)
printf 'AVATAR_SINGLETON_OK keep=%s tracked_pid=%s windows=%s target=%sx%s+%s+%s display=%s\n' \
  "$keep" "${tracked_pid:-unknown}" "${#after[@]}" "$TARGET_W" "$TARGET_H" "$TARGET_X" "$TARGET_Y" "$DISPLAY"

# Fail closed if a duplicate somehow survived.
((${#after[@]} == 1)) || exit 23
