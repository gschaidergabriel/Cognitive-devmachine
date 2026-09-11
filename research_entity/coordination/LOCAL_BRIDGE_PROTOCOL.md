# Local Bridge Protocol — real host execution for ChatGPT-FranKenstein

Status: **ai-core-node LIVE and tested** (2026-09-12). andreas-MACO **not yet built** — no reachable SSH credential from this session; documented as next step, not attempted/faked.

## What this is

The existing VPS bridge (`bridge_daemon.py`, `chatgpt-vps-control`/`chatgpt-vps-results`/`chatgpt-vps-work/*`) executes inside the claylab `clay-direct-dev` sandbox on 72.61.19.188 — a container, not either of Gabriel's or Andreas' actual machines. This protocol is the analogous channel for the **real local host** `ai-core-node`, so ChatGPT-FranKenstein has the same kind of real file/shell/screenshot access there that Claude Code already has.

Daemon: `~/.claude/star/local_bridge_daemon.py`, running as systemd user service `frankenstein-local-bridge.service` (enabled, `Restart=on-failure`, polls every ~20s).

Branches (already existed on origin since 2026-08-24, previously unserviced — this daemon is what finally makes them real): `chatgpt-local-control` (commands in), `chatgpt-local-results` (receipts out), both on `gschaidergabriel/clay-global-research-entity`.

⚠️ Known rough edge: the daemon's own working clone (`~/.claude/star/local_bridge_state/repo`) is polled/force-checked-out every ~20s by the running service. Don't use that exact directory for interactive/manual git work in parallel — it will silently discard uncommitted or unpushed local commits on the next poll. Use a separate clone for anything manual (this doc was recovered from exactly that mistake during the build).

## Command schema

Write a file to `local_bridge/commands/<command_id>.json` on `chatgpt-local-control` and push:

```json
{"schema": "CLAY_LOCAL_COMMAND/v1", "command_id": "<unique-id>", "op": "exec", "command": "shell command here", "cwd": "/optional/dir", "timeout_seconds": 120}
```

## Supported `op` values

- `exec` — real bash on the real host. `command` (required), `cwd` (default: home dir), `timeout_seconds` (default 120, max 3600).
- `status` — host/time snapshot, no args.
- `read_file` — `{"path": "..."}`, returns content (truncated at 256KB) + sha256/bytes/truncated in `meta`.
- `write_text` — `{"path": "...", "content": "..."}`, writes real bytes, returns sha256/bytes in `meta`.
- `screenshot` — `{"name": "optional-label"}`, real `scrot` capture of the actual desktop, PNG saved under `~/.claude/star/local_bridge_state/screenshots/`, `meta.path`/`meta.sha256`/`meta.bytes` in the receipt so the image can be fetched/verified. This is the new capability Gabriel specifically asked for — screenshots flowing back through the same git channel for evaluation.

A small deny-list (`DENY_PATTERNS` in the daemon source) blocks a handful of unambiguously catastrophic shell patterns (`rm -rf /`, `mkfs.*`, raw `dd ... of=/dev/sdX`, fork bombs) — everything else runs, matching the "real capability, narrow deny-list" model already used for Andreas' own Claude Code setup, not a heavy permission gate.

## Result schema

Receipt lands at `local_bridge/results/receipts/<command_id>.json` on `chatgpt-local-results` (plus `local_bridge/results/LATEST.json` and stdout/stderr logs):

```json
{"schema": "CLAY_LOCAL_RECEIPT/v1", "command_id": "...", "command_sha256": "...", "host": "ai-core-node", "started_at": "...", "finished_at": "...", "status": "PASS|FAIL|TIMEOUT|ERROR", "exit_code": 0, "op": "exec", "stdout_tail": "...", "stderr_tail": "...", "meta": {}, "execution_boundary": "REAL_LOCAL_HOST_AI_CORE_NODE_NOT_SANDBOXED"}
```

Idempotent: each `command_id` is recorded in a local sqlite table and only ever executed once, even across daemon restarts or repeated polls of the same branch state.

## Verified real (2026-09-12), not just written

- `exec`: real command pushed, real stdout (`hallo-von-ai-core-node`, real hostname, real ISO timestamp) came back, receipt landed on origin (`git ls-remote` confirmed the commit is live on GitHub, not just local).
- `screenshot`: real capture, `file` confirmed valid PNG, 2704x1050, matches the actual display.
- Malformed pre-existing command files from Gabriel's 2026-08-24 manual testing on this same branch are skipped safely (JSON parse errors caught, logged, do not crash the poll loop) rather than fixed retroactively or hidden.

## Not yet done (be accurate, don't assume this covers andreas-MACO)

Andreas' machine (`andreas-MACO`, Tailscale `100.92.234.52`) was not reachable with any credential available in this session (`Permission denied (publickey,password)`). Building the equivalent bridge there needs either a working SSH key/password supplied through a channel that isn't the chat transcript, or Andreas/Gabriel setting it up directly on that machine. This file will need a second "andreas-MACO LIVE" status line once that happens — don't claim it before it's real.

## Browser access for Gabriel (part of the same request, separately scoped)

Gabriel also asked to work from a browser himself, at the same level as Claude Code, reusing this bridge. Not built in this pass — the EntityOS webapp's "Terminal" tab (`https://entityos.frank.ink`) is the natural place to wire this in (command box → write `CLAY_LOCAL_COMMAND/v1` → poll for the matching receipt → render `stdout_tail`/screenshot), but that's real frontend work that needs its own scoped session, not squeezed into this one alongside the daemon build. Documented here so it isn't lost, not faked as done.
