# the artefact — ClayVerse single-container candidate

This directory is the canonical product workspace for the current ClayVerse endpoint: **one OCI/Docker-compatible container image** containing one persistent central ClayVerse entity.

## Living cycle status

**This section is mandatory living state. It must be refreshed in every product-convergent work cycle after canonical code/evidence fusion and before that cycle is considered complete.** It records both the newest known state and what changed in the just-finished cycle. A stale README means the cycle is not complete.

### Current state

- Program: **ClayVerse single-container**
- Stage: **CLAYVERSE_ARTIFACT**
- Acceptance: **IN_PROGRESS** — no whole-product PASS is claimed.
- Canonical state authority: **UnifiedDB**; ClayGraph remains derived/rebuildable projection only.
- User/runtime path: Clerk-authenticated browser → authenticated WebSocket PTY → user-bound persistent tmux → normal interactive Claude Code CLI.
- Runtime cognition: Claude Code is inference/cognition only; it is not canonical durable memory or identity.
- Runtime readiness: `/readyz` requires canonical state **and** both canonical tmux sessions to be live and pass the same managed transport-policy-v3 attestation used by attach admission. This is a read-only readiness gate and does not create or repair sessions.
- Clerk/PTY lease boundary: post-attach initial resize, received terminal frames, PTY input writes and PTY output publication are fenced against the verified Clerk lease; the focused attach-expiry resize regression is retained on current `main`.
- Effects: generic host `process.exec` is fail-closed; admitted effects must go through the ClayVerse effect boundary. `EffectJournal.begin()` rejects foreign or already-consumed episode causal identity before a new `PENDING` effect can be journaled. EntityOS remains an optional digest-bound internal execution/security/runtime substrate, not the product endpoint.
- Terminal runtime evidence: an exact-byte Vercel Sandbox regression using current-main terminal blob `185a748f80011b324b2c4786644ad42ff369203e` and managed-tmux blob `fd3a0a3b5f0b595c0e15d9f36991148eed67df7d` reached real tmux 3.6a. Pre-policy persistent-server upgrade succeeded, but the new-session path then failed when the second managed `source-file` returned tmux's missing-key-table diagnostics. This is a **real component runtime FAIL for the current-main reapply mechanism**, not provider-admission failure and not whole-product failure.
- Terminal repair status: draft PR #603 narrowly tolerates only the exact already-removed v3 key-table diagnostics while retaining the mandatory independent effective-state attestation. The repair is **not canonical and not runtime-verified**. Its same-falsifier Vercel rerun is currently blocked before Sandbox start by Vercel build-rate limiting.
- Execution surface: Vercel Git-preview → `@vercel/sandbox` execution is confirmed; it is not globally unavailable. A separate confirmed run previously exposed the built-in Python 3.13 `_sqlite3` limitation, and the real-tmux run above proves current Sandbox execution can reach semantic assertions after provisioning. The owner-authorized FREE_ONLY Daytona fallback is merged in the execution bridge, but no Daytona run for this terminal repair is observed here; it requires the dated free-credit attestation and an admitted dispatch path.
- Remaining major acceptance gates include the real-tmux #603 discriminator, exact OCI build/runtime receipt, real Clerk JWT + browser WebSocket PTY verification, authenticated interactive **native** Claude Code verification for both canonical user homes, automatic hook lifecycle integration, persistence/recovery, managed-Claude process identity in live tmux, and live dual-session concurrency/fencing.

### Latest cycle delta

**2026-08-17 — live tmux 3.6a falsifier + readiness/effect convergence**

- Merged terminal/readiness convergence to current `main`: both canonical tmux perspectives must be live and pass the canonical transport-policy-v3 attestation before `/readyz` can advertise readiness. A five-case bounded mechanism discriminator passed; live native-Claude/OCI acceptance remains outstanding.
- Merged/retained the single canonical tmux control hardening path with bounded `has-session`/`source-file`/`new-session` calls and policy reapply; duplicate parallel implementation lanes were closed rather than kept as second semantics. An independent equivalent source slice observed 12/12 supporting regressions before being retired as duplicate evidence.
- Merged effect causal-spine hardening: a foreign episode causal row or already-consumed matching causal identity now fails closed before `EffectJournal.begin()` can journal a new `PENDING` effect.
- Reopened execution truth instead of trusting stale admission assumptions: Vercel Sandbox is confirmed executable. The exact current-main tmux probe reached real tmux 3.6a and **falsified** the reapply mechanism on the new-session second-source path while confirming pre-policy upgrade behavior.
- Draft PR #603 contains the smallest fail-closed repair: tolerate only tmux's exact missing-default-table diagnostics for the four v3 tables, reject empty/mixed/unknown errors, then require the unchanged full v3 state attestation. Do not merge it from source coherence alone.
- The exact #603 real-tmux rerun is staged in the existing single Vercel bridge lane, but the newest branch head is provider-rate-limited before Sandbox start. This is execution-admission blockage for the **repair rerun**, not evidence that the repair passes or fails.
- A temporary diagnostic wrapper lane was closed after the stronger real-runtime path became available; no second execution authority was retained.
- No unusual experiment was executed for this `go`: shared trigger identity is only minute precision, so the atomic experiment protocol remains `COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT` rather than inventing a timestamp.
- Whole-product acceptance remains **IN_PROGRESS**.

### Cycle update rule

At the end of every product-convergent cycle:

1. Refresh current `main`, canonical artefact state, relevant receipts and observed execution evidence.
2. Rewrite **Current state** so it reflects the newest canonical reality, removing stale claims.
3. Add or replace **Latest cycle delta** with the concrete changes from that cycle, including code, tests, evidence, blockers and acceptance movement. If nothing canonical changed, write `NO_CHANGE` and why.
4. Never promote source inspection, a PR, CI configuration, deployment `READY`, component evidence or historical evidence into whole-product PASS.
5. Persist the README update in the same branch/PR/fusion cycle as the artefact/evidence it describes. A cycle is not complete while the README is stale.

Git history and bounded receipts remain the detailed audit trail; this README stays compact and reflects the **latest** state rather than becoming a second canonical database.

## Architecture

Current source implements the UnifiedDB/ClayGraph continuity core, equal-rights Gabriel/Andreas identity routing, bounded workspace/causal re-entry, Clerk JWT verification, and the current terminal-pivot surface: browser → Clerk → authenticated WebSocket PTY → user-bound persistent tmux → normal interactive Claude Code CLI. Claude Code built-in tools are disabled in product terminals; a strict local stdio ClayVerse MCP is the admitted state/context/effect bridge. The runtime contract requires each human prompt to enter canonical ClayVerse state through `begin_turn` and to re-enter through `complete_turn`; UnifiedDB remains the durable state/memory authority. Generic host `process.exec` remains fail-closed. EntityOS is a digest-bound internal execution/security/runtime substrate candidate, not the product endpoint, and its external-effect execution remains separately gated.

The previous custom chat API and headless `claude -p` path are retired as product runtime surfaces. `consciousness_daemon` is not part of the target architecture.

## Verification

Focused isolated tests have exercised bounded source mechanisms, and real Vercel Sandbox execution has now falsified one exact current-main tmux reapply behavior under tmux 3.6a, but **whole-product PASS is not claimed**. The exact current head still requires a full authorized isolated test run, exact OCI build/runtime receipt, real Clerk JWT plus browser WebSocket PTY verification, authenticated interactive native Claude Code runtime verification for both user homes, full ClayVerse MCP begin/effect/complete integration, accepted embedded EntityOS runtime evidence, and restart/recovery plus live dual-session concurrency/fencing validation.

GitHub-hosted Actions are not runtime evidence when jobs fail before visible execution. Vercel deployment state alone is likewise not runtime PASS; only the actually observed Sandbox command/assertion path is executable evidence at its exact source/environment scope.

## Local isolated source checks

Where an authorized isolated Python environment is available:

```bash
python -m pytest -q
PYTHONPATH=. CLAYVERSE_STATE_ROOT=/tmp/clayverse-state python -m clayverse.service --once
```

These source checks do not substitute for an exact container build/runtime gate.

## Container source

`Dockerfile` + `compose.yaml` define the single runtime container. The Docker build context is default-deny and allowlists only consumed product inputs, including the runtime Claude contract and digest-bound staged EntityOS artifact. Persistent ClayVerse state and workspace are externalized as scoped volumes, while the application image runs non-root with a read-only root filesystem in Compose, `no-new-privileges`, and dropped Linux capabilities.
