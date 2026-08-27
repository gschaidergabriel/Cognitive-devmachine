# Local multi-session coordination (room + browser tab allocation)

**Why this exists:** on a single machine, multiple independent Claude Code /
"Frankenstein" sessions can run in parallel. Without coordination they
collide — the concrete incident that triggered this: two sessions drove the
same shared Chrome tab (browser automation against ChatGPT) at the same time,
with zero mutual awareness. This directory holds the fix, portable to any
machine running multiple concurrent Claude Code sessions (ai-core-node,
andreas-maco, etc).

Two independent pieces, same design pattern (session-id resolution + flock'd
JSON registry file), silent/background, no user-visible prompts:

## 1. `room/` — single local coordination registry

One registry (`~/.claude/room/state.json`), NOT multiple topic-rooms like this
repo's own `tools/research_room.py`. Every local session:
- announces what it's doing (`lane`)
- sees a shared bulletin of notes from other sessions (fresh cross-session info)
- one session is deterministically elected `CHIEF` (oldest `joined_at` among
  currently-active sessions — never random) to hold overview / resolve conflicts

Runs automatically via a `PostToolUse` hook calling `clay-room-heartbeat` on
every tool call (auto-joins on first call, silent, no stdout, must never break
the hook chain — see `roomlib.py` for the pid-liveness grace-period bug found
and fixed during build/test: a hook-call pid can be a short-lived wrapper that
exits right after the call, so pid-death alone is not trusted as an instant
kill signal — it's combined with heartbeat staleness).

## 2. `browser_lock/` — per-session browser tabs (NOT exclusive lock)

Every session gets its OWN tab in the shared gstack `browse` daemon (headed
Chrome, e.g. on a virtual display) instead of fighting over one tab. Sessions
run in parallel, each confined to its own tab id.

## Install on a new machine

```bash
mkdir -p ~/.claude/room ~/.claude/browser_lock
cp room/roomlib.py ~/.claude/room/roomlib.py
cp browser_lock/tablib.py ~/.claude/browser_lock/tablib.py
cp bin/clay-room-* bin/clay-browser-tab-* ~/.local/bin/
chmod +x ~/.local/bin/clay-room-* ~/.local/bin/clay-browser-tab-*
```

Then add to `~/.claude/settings.json` under `hooks.PostToolUse` (merge into
the existing `"*"` matcher's `hooks` array if one already exists — do not
overwrite other hooks like an existing stall-watchdog heartbeat):

```json
{
  "type": "command",
  "command": "/home/<user>/.local/bin/clay-room-heartbeat",
  "timeout": 5
}
```

`browser_lock` has no hook — it's called explicitly by whatever code drives
the browser: `clay-browser-tab-acquire "<purpose>"` before use, switch onto
the returned tab id (`browse tab <id>`) before every action, then
`clay-browser-tab-release` when done. See docstrings in
`bin/clay-browser-tab-acquire` for the full usage contract.

## Manual inspection

- `clay-room-status` — who's chief, active sessions + lanes, recent bulletin notes.
- `clay-browser-tab-status` — session→tab assignments, unowned tabs, orphan cleanup.

## Provenance

Built + tested on ai-core-node, 2026-08-26, by Claude Code (worker
`claudecode-ai-core-node` in this repo's `clay` research room) at the project
owner's direction, after the tab-collision incident above. Test evidence
(join/chief-election, worker-join, cross-session notes, chief-failure
re-election, clean leave, orphan pruning) was run with real parallel session
simulation via env-var session-id overrides
(`CLAY_ROOM_SESSION_ID`/`CLAY_BROWSER_SESSION_ID`), not fabricated.
