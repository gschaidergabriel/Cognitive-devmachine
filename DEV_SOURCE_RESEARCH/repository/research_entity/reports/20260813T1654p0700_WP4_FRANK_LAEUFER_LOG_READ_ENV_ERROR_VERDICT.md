# WP4 frank-laeufer log read: 3 red gate = ENV error, not real verdict

Source: read-only ssh to frank-api (31.97.117.141), `sudo cat` on
`/root/frank-laeufer/log/`. No write on the remote host. Package:
`/home/ai-core-node/gabriel-claude/arbeit/fertig/20260813-164423-wp4/`.

## Context
wp1 found 3 commit-status labels marked red on GitHub: `claycode-opaque-parser-fidelity-v1`,
`claycode-runtime-nominal-boundary-oob-vps`, `frank-provider-fence-fresh-main-vps`.
These are not GitHub Actions — they are posted by our own script
`/home/ai-core-node/gabriel-claude/bin/frank-laeufer/laeufer.py` running on
host frank-api, exit code rc=1. wp1 could not read the log directory
(permission denied). wp4 got in with `sudo`.

## Log directory census (live measured)
- total `.log` files in `/root/frank-laeufer/log/`: **2058**
- oldest: `clay-wp02-v18-committed-replay-561-181a2f95.log`, mtime **2026-08-12T23:35:20Z**
- newest: `laeufer.log`, mtime **2026-08-13T09:42:56Z** (this is the combined
  runner log, not a per-gate file)

## Per-gate verdict

### claycode-opaque-parser-fidelity-v1 — VERDICT: ENV
File: `claycode-opaque-parser-fidelity-v1-3-b0f21517.log` (2026-08-13T06:27:32Z).
Step reached: `Bind changed bytes and compile`, then `ENDE(1)`. Quote:

    sha256sum: runtime/clay_wp04_type_effect_v1/FRANK_STRUCTURED_V1.lark: No such file or directory

4 target files missing in total at this step. The actual gate step
("Opaque versus plain parser fidelity") is marked `UEBERSPRUNGEN
(vorheriger Fehler)` — skipped, never executed. This is a shell-level
missing-file error before any research-content check, same shape as the
known frank-central-state bug (missing `state/*.sqlite`, wrong branch).
Population: of 305 logs for this gate, 142 end `TOR_RC=1`; the newest log
(PR 571, sha `dcd06ec6`) is a clean `TOR_RC=0` pass with structured
`status:PASS_CLAYCODE_OPAQUE_PARSER_FIDELITY_GATE` JSON.

### claycode-runtime-nominal-boundary-oob-vps — VERDICT: ENV
File: `claycode-runtime-nominal-boundary-oob-vps-3-b0f21517.log`
(2026-08-13T06:27:38Z). Step reached: `Bind bytes and compile`, then
`ENDE(1)`. Quote:

    sha256sum: runtime/claycode_eval_v1/admitted_evaluator.py: No such file or directory

7 target files missing at this step. Gate step ("Replay consumed
counterworld as ordinary repair regression") = `UEBERSPRUNGEN`, never run.
Population: 305 total logs, 142 end `TOR_RC=1`.

### frank-provider-fence-fresh-main-vps — VERDICT: ENV
File: `frank-provider-fence-fresh-main-vps-3-b0f21517.log`
(2026-08-13T06:27:27Z). Step reached: `Bind exact bytes and environment`,
then `ENDE(1)`. Quote:

    fatal: could not open 'runtime/state/effect_execution_fence.py' for reading: No such file or directory

Many more `runtime/state/*` and `tests/*` files reported missing the same
way (git object read, not filesystem `sha256sum`), last line before exit:
`[Errno 2] No such file or directory: 'runtime/state/effect_execution_fence.py'`.
9 downstream gate steps = `UEBERSPRUNGEN`, none run. Population: 305 total
logs, 108 end `TOR_RC=1`.

## Conclusion
All 3 gate, in their most recent failing log, never reach their own
assertion logic. They die earlier, at a bind/checkout step, because files
expected in the pinned commit tree (sha `b0f215179da4ff2584da95e36264317f15d7a371`,
PR #3) are not present. This is the same class of bug as the earlier
frank-central-state finding (missing `state/*.sqlite`, wrong branch) — an
environment/checkout problem in the runner, not a real research verdict
about gate content. The newest run of the same 3 gate (PR 571, sha
`dcd06ec6`) passes clean, so the ENV failure correlates with older/stale
PR shas rather than being a permanent break — open point, not verified
in this package (see evidence file `open_verification`).
