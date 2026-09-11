# Local Bridge Protocol — real host execution for ChatGPT-FranKenstein

Status (2026-09-12): **ai-core-node LIVE**, **andreas-MACO LIVE** (both real, both
verified end-to-end this session — see "Verified real" below). Per-machine branches,
not the old generic pair — see "Branch naming" below for why and what changed.

## What this is

The existing VPS bridge (`bridge_daemon.py`, `chatgpt-vps-control`/`chatgpt-vps-results`/
`chatgpt-vps-work/*`) executes inside the claylab `clay-direct-dev` sandbox on
72.61.19.188 — a container, not either of Gabriel's or Andreas' actual machines. This
protocol is the analogous channel for the **real local hosts**, so ChatGPT-FranKenstein
has the same kind of real file/shell/screenshot access there that Claude Code already
has — on BOTH of Gabriel's and Andreas' actual machines now, not just one.

Daemon: `~/.claude/star/local_bridge_daemon.py` — **the identical file on both
machines**, byte-for-byte. What differs between the two installs is environment only
(`LOCAL_BRIDGE_MACHINE_ID`, `LOCAL_BRIDGE_OWNER`, set in each machine's own systemd
user-unit `Environment=` lines), never the source. Runs as systemd **user** service
`frankenstein-local-bridge.service` on each machine (enabled, `Restart=on-failure`,
polls every ~20s). Neither install needs root/sudo to run (andreas-MACO's user does
happen to have passwordless sudo available, but the daemon itself never uses it).

## Branch naming (per-machine, not generic — decided 2026-09-12)

The original branches (`chatgpt-local-control`/`chatgpt-local-results`) were generic,
not machine-scoped. With a second machine (andreas-MACO) joining the same mechanism,
generic names would mean either machine could accidentally execute the other's queued
commands, or (proven live during this build — see incident note below) a daemon
pointed at the wrong branch by a missing/forgotten env var silently re-executes the
other machine's history under its own hostname. Chosen fix: **one branch pair per
machine**, machine identity baked into the branch name itself as the primary
separation, PLUS explicit fields in every payload (next section) as a second,
independent line of defense that doesn't depend on anyone tracking which branch they're
looking at.

| Machine | Owner | Control branch (commands in) | Results branch (receipts out) |
|---|---|---|---|
| `ai-core-node` | gabriel | `chatgpt-local-ai-core-node-control` | `chatgpt-local-ai-core-node-results` |
| `andreas-maco` | andreas | `chatgpt-local-andreas-maco-control` | `chatgpt-local-andreas-maco-results` |

Migration done 2026-09-12: the old `chatgpt-local-control`/`chatgpt-local-results`
branches (all of ai-core-node's real history since 2026-08-24) were pushed to the new
`chatgpt-local-ai-core-node-*` names (full history preserved, not squashed), the daemon
config updated to match, and the old generic branch names deleted from origin — so
there is exactly one live name per machine, not two parallel truths.

All four branches live on `gschaidergabriel/clay-global-research-entity`.

⚠️ **Known rough edge, still true on both machines:** each daemon's own working clone
(`~/.claude/star/local_bridge_state/repo`) is polled/force-checked-out every ~20s by the
running service. Don't use that exact directory for interactive/manual git work in
parallel — it will silently discard uncommitted or unpushed local commits on the next
poll. Use a separate clone for anything manual.

⚠️ **Incident from this build, kept here as a warning, not just a footnote:** while
setting up andreas-MACO, the daemon was invoked manually once *without* the
`LOCAL_BRIDGE_MACHINE_ID`/`LOCAL_BRIDGE_OWNER` env vars set (defaults silently fell back
to `ai-core-node`/`gabriel`). It fetched and re-executed all 26 of ai-core-node's real
historical commands — physically on andreas-MACO's hardware — and pushed receipts
mislabeled `host: "ai-core-node"` onto the real `chatgpt-local-ai-core-node-results`
branch, overwriting the correct original receipts. Caught by diffing the pushed commit
against known-good history; fixed with `git revert` (commit `ea5ba08d5`, restoring the
original 2026-09-11 receipts byte-for-byte). Lesson embedded in the schema now (see
next section): never trust the branch name alone to say who a payload is from — always
also check `machine_id`/`owner` in the payload itself, because exactly this kind of
operator/env mistake can put the right content on the wrong branch.

## ⭐⭐⭐ Attribution is a hard requirement, not decoration (Gabriel, 2026-09-12)

Gabriel's own words on why: ChatGPT-FranKenstein should eventually see **both**
machines' state "wie bei mir, aber dennoch getrennt — es muss immer klar sein was wie
wo wann." Concretely: **whoever consumes these branches (ChatGPT-FranKenstein or
anyone else) must never merge or compare a fact from one machine with a fact from the
other without preserving which machine/owner it came from.** Branch name is one signal
but is NOT sufficient by itself — see the incident above, where the branch name was
right but the payload content was from the wrong machine. Every command and every
receipt therefore carries explicit fields:

- `machine_id`: `"ai-core-node"` or `"andreas-maco"`
- `owner`: `"gabriel"` or `"andreas"`

both set from the daemon's own environment (`LOCAL_BRIDGE_MACHINE_ID`/
`LOCAL_BRIDGE_OWNER`), never inferred from the branch name at read time. **Rule for any
consumer, including future ChatGPT-FranKenstein sessions reading both branch pairs
together: read `machine_id`/`owner` off every individual receipt before treating its
content as fact about that machine — do not assume it from which branch you happened to
fetch it from.**

## Command schema

Write a file to `local_bridge/commands/<command_id>.json` on the target machine's
control branch and push:

```json
{"schema": "CLAY_LOCAL_COMMAND/v1", "command_id": "<unique-id>", "op": "exec", "command": "shell command here", "cwd": "/optional/dir", "timeout_seconds": 120}
```

## Supported `op` values

- `exec` — real bash on the real host. `command` (required), `cwd` (default: home dir), `timeout_seconds` (default 120, max 3600).
- `status` — host/time snapshot, no args. Now includes `owner` alongside `host`.
- `read_file` — `{"path": "..."}`, returns content (truncated at 256KB) + sha256/bytes/truncated in `meta`.
- `write_text` — `{"path": "...", "content": "..."}`, writes real bytes, returns sha256/bytes in `meta`.
- `screenshot` — `{"name": "optional-label"}`, real desktop capture, PNG saved under
  `~/.claude/star/local_bridge_state/screenshots/`, `meta.path`/`meta.sha256`/`meta.bytes`
  in the receipt. **Works on ai-core-node (X11, `scrot`). Does NOT currently work on
  andreas-MACO** — that machine's active session is GNOME-on-Wayland; `scrot` isn't
  even installed (X11-only tool), and both `gnome-screenshot` (hangs/no-ops over a
  non-interactive SSH+systemd-user session) and the `org.gnome.Shell.Screenshot`
  D-Bus portal (`AccessDenied`) were tried and confirmed not to work headlessly there.
  Documented honestly rather than faked — fixing this would need either a proper
  logind/portal grant for the systemd user session or a different capture path
  (e.g. a small helper running inside Andreas' actual logged-in session), not attempted
  in this pass.

A small deny-list (`DENY_PATTERNS` in the daemon source) blocks a handful of unambiguously catastrophic shell patterns (`rm -rf /`, `mkfs.*`, raw `dd ... of=/dev/sdX`, fork bombs) — everything else runs, matching the "real capability, narrow deny-list" model already used for Andreas' own Claude Code setup, not a heavy permission gate.

## Result schema

Receipt lands at `local_bridge/results/receipts/<command_id>.json` on the matching
results branch (plus `local_bridge/results/LATEST.json` and stdout/stderr logs):

```json
{"schema": "CLAY_LOCAL_RECEIPT/v1", "command_id": "...", "command_sha256": "...", "host": "andreas-maco", "owner": "andreas", "machine_id": "andreas-maco", "started_at": "...", "finished_at": "...", "status": "PASS|FAIL|TIMEOUT|ERROR", "exit_code": 0, "op": "exec", "stdout_tail": "...", "stderr_tail": "...", "meta": {}, "execution_boundary": "REAL_LOCAL_HOST_ANDREAS_MACO_NOT_SANDBOXED"}
```

Idempotent: each `command_id` is recorded in a local sqlite table (one DB per machine,
never shared) and only ever executed once, even across daemon restarts or repeated
polls of the same branch state.

## GitHub access per machine

- **ai-core-node**: pushes via the existing `gh`-issued token already used for the rest
  of Gabriel's work on this machine.
- **andreas-maco**: has its own narrowly-scoped SSH deploy key
  (`~/.ssh/id_ed25519_clay_research_entity`, GitHub deploy-key title
  `andreas-maco-local-bridge`, read-write, added 2026-09-12), used via an SSH config
  `Host github-clay-research-entity` alias — matching the existing pattern on that
  machine of one dedicated deploy key per repo (see its `~/.ssh/config`: separate keys
  already existed there for its own "brain" repo, the `clay` program, `frankenstein`,
  and `self-integration`; this is the same pattern, just for this repo).

## Verified real (2026-09-12), not just written

**ai-core-node:**
- `exec`: real command pushed to `chatgpt-local-ai-core-node-control`, real stdout
  (hostname, ISO timestamp) came back on `chatgpt-local-ai-core-node-results`,
  confirmed live on GitHub via fresh clone (not just local state).
- `screenshot`: real capture, confirmed valid PNG, 2704x1050, matches the actual display.
- Attribution fields verified present on a real receipt: `"host": "ai-core-node"`,
  `"owner": "gabriel"`, `"machine_id": "ai-core-node"`.
- Malformed pre-existing command files from Gabriel's 2026-08-24 manual testing are
  skipped safely (JSON parse errors caught, logged, do not crash the poll loop).

**andreas-maco:**
- Real user (`andreas@100.92.234.52`, confirmed via `whoami`/`hostname`) — the earlier
  `genuinos@...` credential was simply wrong, not a real blocker.
- Environment surveyed before building anything: Python 3.14.4, no root/sudo *needed*
  (though available), FranKenstein there runs Andreas' own voice mode inside a
  `systemd-nspawn` container (`entityos-vm.service`, root-managed, separate from this
  bridge which runs as Andreas' own user service on the host).
- Daemon deployed as `frankenstein-local-bridge.service` (systemd **user** unit, no
  root), `LOCAL_BRIDGE_MACHINE_ID=andreas-maco`, `LOCAL_BRIDGE_OWNER=andreas`.
- `exec`: real command pushed to `chatgpt-local-andreas-maco-control`, real stdout
  (`hallo-von-andreas-maco`, hostname `andreas-MACO`, user `andreas`, real timestamp)
  came back on `chatgpt-local-andreas-maco-results`, confirmed via fresh clone.
  Receipt carries `"host": "andreas-maco"`, `"owner": "andreas"`,
  `"machine_id": "andreas-maco"`, `"execution_boundary": "REAL_LOCAL_HOST_ANDREAS_MACO_NOT_SANDBOXED"`.
- `screenshot`: attempted honestly, does **not** work yet (see op list above) —
  Wayland/portal restriction on that session, not faked as working.

## General FranKenstein-state update on andreas-MACO (same pass, Gabriel: "volles update... alles")

Beyond the bridge itself, a comprehensive currency check was run across every
FranKenstein-related repo/runtime-directory found on andreas-MACO:

- `~/frankenstein-repo`, `~/self-integration`, `~/frank-repo`: all already at parity
  with their origins (0 ahead/0 behind) at the git level. `frankenstein-repo` has one
  genuine, deliberately-untouched local WIP diff (`f2wp1207_grid10_turn_loop.py`,
  a cell-competition-history table Andreas' agent is mid-way through) — left alone, not
  discarded, not committed on his behalf.
- `~/andreas-claude`: found 1 local commit ahead + 7 behind + a month-old abandoned
  `git rebase` (from 2026-08-12, confirmed stale, nothing in progress). Aborted the
  stale rebase, merged origin cleanly (no conflicts — untracked personal-knowledge
  files were untouched), pushed. Now 0 ahead/0 behind.
- `/var/lib/entityos/voice` (the actual runtime code for Andreas' voice mode, vendored
  copy, not a git repo): compared file-by-file by content hash against the canonical
  source (`~/entityos-repo` on ai-core-node, public `gschaidergabriel/EntityOS`, current
  with its own origin). Found genuine two-way drift, reviewed line-by-line per file
  before touching anything (no blind overwrite):
  - Copied **canonical → andreas-MACO** (canonical had real, later, measured bugfixes
    Andreas' copy lacked — verified each diff was a strict superset, not a rewrite of
    something Andreas had customized): `entitaet.py`, `aufmerksamkeit.py`, `buehne.py`,
    `gespraech_loop.py`, `regie.py`, `verkoerperung.py`, `wiederholung.py`,
    `innenwelt/workspace_broadcast.py`, plus two files Andreas' copy was missing
    entirely (`erinnern.py`, `ziele.py` — the goal-pursuit feature `entitaet.py`
    depends on).
  - **Left untouched**: `hoeren.py` — Andreas' copy has a real local improvement
    (prefers a hash-verified locally-cached Whisper model) that canonical lacks;
    overwriting it would have been a regression, not an update.
  - No live process was running (`gespraech_loop.py`/`llama-server` both absent from
    `ps`), so nothing needed restarting — the safety rule "`gespraech.aktiv` stays 0
    until a human turns it on" was not violated.

## Browser access for Gabriel (separately scoped, not yet built)

Gabriel also asked to work from a browser himself, at the same level as Claude Code,
reusing this bridge. The EntityOS webapp's "Terminal" tab
(`https://entityos.frank.ink`) is the natural place to wire this in (command box →
write `CLAY_LOCAL_COMMAND/v1` with a machine selector → poll for the matching receipt
on that machine's results branch → render `stdout_tail`/screenshot). Status of this
piece tracked separately in this same work session — see the coordinator's report for
current state; not duplicated here to avoid two sources of truth going stale
independently.
