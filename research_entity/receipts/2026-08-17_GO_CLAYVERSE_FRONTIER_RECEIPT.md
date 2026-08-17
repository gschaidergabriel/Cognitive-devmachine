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
- `808cccaa0c9847ed022e21c22f27aed6f4bfffb4` made canonical `entityos.exec` calls automatically acquire a fenced lease when the caller does not supply one, with a unique holder per attempt and exact-identity cleanup.
- `f3bb1d5cce5ee954273085872d72780bc83b8807` added deterministic automatic-lease and collision regressions.
- Adversarial review rejected caller-controlled target labels as lease authority: relabeling the same real effect could otherwise evade target-hash serialization.
- `c01a23a0ba69c4c81edb6c171fc908744c64c1fb` therefore hardened the automatic resource to the conservative global `effect:entityos.exec` fence.
- `dd2c290ae0eb7adcb81ce643a47deb627fec1053` added regressions proving target relabeling cannot bypass the fence and exact cleanup cannot delete a replacement owner.

## Adversarial / second-order findings

1. A stale-SHA write to `service.py` was rejected with HTTP 409 while another worker changed the same file. No stale overwrite was forced.
2. The current `ARCHITECTURE.md` still defines ephemeral one-turn tool-less Claude Code cognition as the canonical cognition path.
3. Newer main also contains `the artefact/clayverse/terminal_sessions.py`, a tmux-based two-permanent-terminal candidate. At the observed head, `service.py` does not import or instantiate that manager. Therefore it is not promoted here as the canonical runtime path; architecture/integration remains to be explicitly reconciled.
4. The single bounded unusual experiment remains `the artefact/tests/test_unusual_experiment.py` (cross-user crash/reopen ABA fencing). The PTY final-output case and the EntityOS effect-fence cases are regression-only.
5. A lease keyed by caller-supplied `target` was rejected as an unsafe proxy for the real execution resource. Current automatic `entityos.exec` execution is deliberately serialized globally until narrower resource semantics are admitted and proven.

## Execution evidence

No whole-product executable PASS is claimed in this receipt.

- The connected Vercel tool surface in this session exposes deployments/logs/docs but no Vercel Sandbox create/run/stop action, so an isolated Sandbox could not actually be started here.
- Current GitHub-hosted artifact workflow runs continue to terminate before any job step; no pytest/build/runtime command from those runs was observed executing.
- No VPS, self-hosted runner, production host, or deployment READY state was substituted for Sandbox evidence.
- No secrets were copied into source, logs, or this receipt.
- A focused isolated non-Vercel source-bound discriminator was run for the changed `effects.py` mechanism. The executed bytes reproduced Git blob `cd5d2a367f9338971ccd33f34373cd5d6574f6ee` exactly. With the current SQLite lease acquisition semantics reproduced in the harness, it observed: `effect:entityos.exec` present during execution; a unique per-attempt holder; same-session nested acquisition rejected; successful completion removed only its exact lease; a relabelled target remained blocked by an incumbent lease before bridge execution; and replacement ownership survived stale-result cleanup. This is bounded mechanism evidence only, not a full repository pytest run, Vercel Sandbox evidence, or OCI/runtime acceptance.
- The first attempt at that focused discriminator failed in the scratch harness before the module could execute because the temporary module was not registered before Python dataclass processing. It receives zero PASS credit; the corrected rerun is the evidence summarized above.

Status of exact-current-head full tests/build/runtime: `BLOCKED_UNEXECUTED`.

Post-fusion main observed after the effect work: `f0ba800618408936c41ddd1cc8ecc0ac85d9e5ba`; the hardened `effects.py` blob remained `cd5d2a367f9338971ccd33f34373cd5d6574f6ee` at that head.

## Next exact executable discriminator

On the first available authorized Vercel Sandbox executor:

1. stage the exact then-current private GitHub revision without exposing reusable credentials inside the VM;
2. record and assert the exact source SHA;
3. run the full `the artefact` pytest suite as one coordinated batch, including the single ABA unusual experiment and all PTY/effect-fence regressions;
4. build/probe the exact ClayVerse OCI candidate only through an explicitly supported Sandbox toolchain and record inability as a blocker if that facility is unavailable;
5. include live two-user contention over the canonical effect path and prove only one `entityos.exec` crosses the boundary at a time while stale/replacement outcomes remain non-verified;
6. capture command identity, exit codes, logs, artifact/image digest where produced, runtime/state/restart observations, and Sandbox stop result;
7. persist observed Sandbox truth back to GitHub without generalizing it to a later head.

Outcome: source/product convergence improved; the canonical EntityOS effect boundary now has a label-independent global serialization fence in source, while empirical whole-container acceptance remains blocked on an actual exact-identity isolated Sandbox run.
