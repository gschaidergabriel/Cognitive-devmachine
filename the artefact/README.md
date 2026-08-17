# the artefact — ClayVerse single-container candidate

This directory is the canonical product workspace for the current ClayVerse endpoint: **one OCI/Docker-compatible container image** containing one persistent central ClayVerse entity.

## Living cycle status

**This section is mandatory living state. It must be refreshed in every product-convergent work cycle after canonical code/evidence fusion and before that cycle is considered complete.** A stale README means the cycle is incomplete; detailed evidence remains in Git history and bounded receipts.

### Current state

- Program: **ClayVerse single-container**
- Stage: **CLAYVERSE_ARTIFACT**
- Acceptance: **IN_PROGRESS** — no whole-product PASS is claimed.
- Canonical state authority: **UnifiedDB**; ClayGraph remains derived/rebuildable projection only.
- User/runtime path: Clerk-authenticated browser → authenticated WebSocket PTY → user-bound persistent tmux → normal interactive Claude Code CLI.
- Runtime cognition: Claude Code is inference/cognition only; it is not canonical durable memory or identity.
- Runtime readiness: `/readyz` requires canonical state and both canonical tmux sessions to be live and pass the managed transport-policy-v3 attestation used by attach admission. This gate is read-only and does not create or repair sessions.
- Clerk/PTY lease boundary: post-attach initial resize, received terminal frames, PTY input writes and PTY output publication are fenced against the verified Clerk lease.
- Effects: generic host `process.exec` is fail-closed; admitted effects must pass the ClayVerse effect boundary. EntityOS remains an optional digest-bound internal execution/security/runtime substrate, not the product endpoint.
- Predecessor terminal evidence: exact Vercel Sandbox execution against terminal blob `185a748f80011b324b2c4786644ad42ff369203e` and managed-tmux blob `fd3a0a3b5f0b595c0e15d9f36991148eed67df7d` reached real tmux 3.6a and failed on the new-session second `source-file` because default key tables were already absent. That predecessor result remains an exact component runtime FAIL.
- Repair evidence: retained PR #603 uses terminal blob `c185009f8af84e1288747d8352645777a36b2053` and focused test blob `b6bb645dd07645f21ca2e5574f8392c9f13beafc`. Vercel deployment `dpl_6z5oXV29Q4TgRonAgs9TaEmxfB5T` actually started an isolated Sandbox with tmux `3.6a-1.amzn2023.0.1`, Python `3.13.13-1.amzn2023.0.2`, SQLite `3.40.0`, switched the product probe to `DENY_ALL`, and observed PASS for pre-policy upgrade, already-hardened reapply, new-server second source and direct multi-argv fake-Claude launch. The same probe rejected mixed/unknown and empty nonzero diagnostics. This is **EXACT COMPONENT LIVE-RUNTIME PASS at the terminal/policy blob scope**.
- Evidence boundary: the execution summary carried the older PR #603 head label `ef61bfb85ab59291c3b0b33d024aa098b1f29089`, but the executed terminal/policy blobs are byte-identical to the current rejoined repair. Credit therefore binds to exact component bytes, not to an exact-current full-branch or whole-container run. Native Claude Code and the OCI product image were explicitly not tested.
- Rejoin status: PR #603 has been rejoined through canonical `main` `4d7fd30e8b226dea51c1e7ce3e34ca4a3359e505` while retaining only the two intended repair/test product blobs before this evidence/README update.
- Remaining major acceptance gates now move past the real-tmux reapply discriminator to repair promotion plus exact OCI build/image identity, native Claude Code in both canonical homes, real Clerk JWT/browser/WebSocket PTY, automatic managed hooks, persistence/recovery and live dual-session concurrency/generation fencing.

### Latest cycle delta

**2026-08-17 17:18 +07:00 — real tmux 3.6a repair discriminator PASS; repair rejoined and evidence synchronized**

- Refreshed canonical `main` and overlapping work; avoided duplicating the existing #603 repair lane.
- Rejoined PR #603 onto then-current `main` `4d7fd30e8b226dea51c1e7ce3e34ca4a3359e505` with a two-parent commit while preserving exactly the candidate terminal blob `c185009f8af84e1288747d8352645777a36b2053` and focused test blob `b6bb645dd07645f21ca2e5574f8392c9f13beafc`.
- The retained Vercel execution path reopened and deployment `dpl_6z5oXV29Q4TgRonAgs9TaEmxfB5T` reached real tmux 3.6a in an actually-started Sandbox rather than stopping at provider admission.
- Observed PASS markers: `PREPOLICY_UPGRADE_REAPPLY`, `ALREADY_HARDENED_REAPPLY_IDEMPOTENT`, `NEW_SERVER_SECOND_SOURCE_IDEMPOTENT`, and `DIRECT_MULTI_ARGV_FAKE_CLAUDE_LAUNCH`.
- The probe also asserted that exact expected missing-table diagnostics are the only tolerated nonzero reapply result; mixed expected+unknown diagnostics and empty nonzero diagnostics remain fail-closed.
- Network policy was `DENY_ALL` during the tested product path and the Sandbox stopped cleanly.
- Scope is intentionally narrow: fake Claude only, identity dependency stub only, no native Claude, no OCI image, no Clerk/browser and no whole-product acceptance.
- No unusual experiment was consumed; this was regression-only re-entry of the already-defined tmux falsifier.
- Durable bounded receipt: `receipts/2026-08-17_GO_1718_TMUX36A_REPAIR_LIVE_PASS_GPT56SOL.json`.
- Next gate: promote the now-runtime-supported rejoined tmux repair without weakening its fail-closed policy; then spend isolated execution on the exact OCI/native-Claude/readiness/restart/concurrency path rather than repeating this already-discriminated component regression.

### Cycle update rule

At the end of every product-convergent cycle:

1. Refresh current `main`, canonical artefact state, relevant receipts and observed execution evidence.
2. Rewrite **Current state** so it reflects the newest canonical reality, removing stale claims.
3. Add or replace **Latest cycle delta** with the concrete changes from that cycle, including code, tests, evidence, blockers and acceptance movement. If nothing canonical changed, write `NO_CHANGE` and why.
4. Never promote source inspection, a PR, CI configuration, deployment `READY`, component evidence or historical evidence into whole-product PASS.
5. Persist the README update in the same branch/PR/fusion cycle as the artefact/evidence it describes.

Git history and bounded receipts remain the detailed audit trail; this README stays compact and reflects the **latest** state rather than becoming a second canonical database.

## Architecture

Current source implements the UnifiedDB/ClayGraph continuity core, equal-rights Gabriel/Andreas identity routing, bounded workspace/causal re-entry, Clerk JWT verification, and the terminal surface: browser → Clerk → authenticated WebSocket PTY → user-bound persistent tmux → normal interactive Claude Code CLI. Claude Code built-in tools are disabled in product terminals; a strict local stdio ClayVerse MCP is the admitted state/context/effect bridge. UnifiedDB remains the durable state/memory authority. Generic host `process.exec` remains fail-closed. EntityOS is a digest-bound internal execution/security/runtime substrate candidate, not the product endpoint.

The previous custom chat API and headless `claude -p` path are retired as product runtime surfaces. `consciousness_daemon` is not part of the target architecture.

## Verification

Real Vercel Sandbox execution now both falsified the predecessor tmux reapply behavior and verified the bounded repair under real tmux 3.6a at exact component-byte scope, but **whole-product PASS is not claimed**. The exact current product still requires authorized isolated full-path evidence: exact OCI build/image identity, startup/readiness, real Clerk JWT plus browser WebSocket PTY, authenticated native Claude Code for both user homes, managed hook lifecycle, UnifiedDB persistence/recovery, accepted effect/EntityOS behavior where admitted, and live dual-session concurrency/generation fencing.

GitHub-hosted Actions are not runtime evidence when jobs fail before visible execution. Vercel deployment state alone is likewise not runtime PASS; only an actually started Sandbox command/assertion path is executable evidence at its exact source/environment scope.

## Local isolated source checks

Where an **authorized** isolated Python environment is available:

```bash
python -m pytest -q
PYTHONPATH=. CLAYVERSE_STATE_ROOT=/tmp/clayverse-state python -m clayverse.service --once
```

These source checks do not substitute for an exact container build/runtime gate.

## Container source

`Dockerfile` + `compose.yaml` define the single runtime container. The Docker build context is default-deny and allowlists only consumed product inputs, including the runtime Claude contract and digest-bound staged EntityOS artifact. Persistent ClayVerse state and workspace are externalized as scoped volumes, while the application image runs non-root with a read-only root filesystem in Compose, `no-new-privileges`, and dropped Linux capabilities.
