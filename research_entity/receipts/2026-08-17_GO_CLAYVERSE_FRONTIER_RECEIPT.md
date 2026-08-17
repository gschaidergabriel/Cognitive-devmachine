# GO ClayVerse frontier receipt — 2026-08-17

Trigger: `go`

Observed pre-receipt research `main`: `427dd9623b11e79e8038e6fb4ac7bf508ec162ac`.

## Authority / product boundary

- Current product endpoint is the single-container ClayVerse artifact in `main/the artefact/`.
- EntityOS is an optional internal execution/security/runtime substrate, not the top-level release endpoint.
- UnifiedDB remains the central persistent authority; ClayGraph is derived/rebuildable.

## Durable deltas produced/fused in this macro-cycle

- `081ae2f` hardened PTY lifecycle and bounded nonblocking I/O.
- `f7d5287` added terminal lifecycle/user-boundary regressions.
- `962e2b3` preserved final buffered PTY output after child exit until drain.
- `626ddb5` locked that drain behavior in regression coverage.
- `bc339f8` made the automatic ClayVerse OCI workflow require the full pytest candidate suite before image gates.
- `17843d8` explicitly classified the PTY exit/drain case as regression-only so it does not consume an additional unusual-experiment slot.
- Parallel main work was fused rather than overwritten: serialized HTTP mutation lane; tool-dark permanent Claude terminal policy; sealed managed MCP baseline.

## Adversarial / second-order findings

1. A stale-SHA write to `service.py` was rejected with HTTP 409 while another worker changed the same file. No stale overwrite was forced.
2. The current `ARCHITECTURE.md` still defines ephemeral one-turn tool-less Claude Code cognition as the canonical cognition path.
3. Newer main also contains `the artefact/clayverse/terminal_sessions.py`, a tmux-based two-permanent-terminal candidate. At the observed head, `service.py` does not import or instantiate that manager. Therefore it is not promoted here as the canonical runtime path; architecture/integration remains to be explicitly reconciled.
4. The single bounded unusual experiment remains `the artefact/tests/test_unusual_experiment.py` (cross-user crash/reopen ABA fencing). The PTY final-output case is regression-only.

## Execution evidence

No executable PASS is claimed in this receipt.

- The connected Vercel tool surface in this session exposes deployments/logs/docs but no Vercel Sandbox create/run/stop action, so an isolated Sandbox could not actually be started here.
- Current GitHub-hosted artifact workflow runs continue to terminate before any job step; no pytest/build/runtime command from those runs was observed executing.
- No VPS, self-hosted runner, production host, or deployment READY state was substituted for Sandbox evidence.
- No secrets were copied into source, logs, or this receipt.

Status of exact-current-head tests/build/runtime: `BLOCKED_UNEXECUTED`.

## Next exact executable discriminator

On the first available authorized Vercel Sandbox executor:

1. stage the exact then-current private GitHub revision without exposing reusable credentials inside the VM;
2. record and assert the exact source SHA;
3. run the full `the artefact` pytest suite as one coordinated batch, including the single ABA unusual experiment and PTY regressions;
4. build/probe the exact ClayVerse OCI candidate only through an explicitly supported Sandbox toolchain and record inability as a blocker if that facility is unavailable;
5. capture command identity, exit codes, logs, artifact/image digest where produced, runtime/state/restart observations, and Sandbox stop result;
6. persist observed Sandbox truth back to GitHub without generalizing it to a later head.

Outcome: source/product convergence improved; empirical whole-container acceptance remains blocked on an actual exact-identity isolated Sandbox run.
