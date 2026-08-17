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
- Runtime readiness on current `main`: `/readyz` requires canonical state and both canonical tmux sessions to be live and pass the managed transport-policy-v3 attestation used by attach admission. This gate is read-only and does not create or repair sessions.
- Clerk/PTY lease boundary: post-attach initial resize, received terminal frames, PTY input writes and PTY output publication are fenced against the verified Clerk lease.
- Effects: generic host `process.exec` is fail-closed; admitted effects must pass the ClayVerse effect boundary. EntityOS remains an optional digest-bound internal execution/security/runtime substrate, not the product endpoint.
- Real terminal evidence: the predecessor reapply mechanism was first falsified under real tmux 3.6a. A later authorized Vercel Sandbox run, deployment `dpl_6z5oXV29Q4TgRonAgs9TaEmxfB5T`, executed terminal blob `c185009f8af84e1288747d8352645777a36b2053` and focused-test blob `b6bb645dd07645f21ca2e5574f8392c9f13beafc` at bound old head `ef61bfb85ab59291c3b0b33d024aa098b1f29089` and passed pre-policy upgrade, already-hardened reapply, new-server second source, direct multi-argv fake-Claude launch, plus assertions that mixed/unknown and empty diagnostics remain fail-closed. Network was deny-all during the candidate test. This is strong **component/mechanism PASS at that bound old head**, not exact-current or whole-product PASS; native Claude and the OCI product image were not tested.
- Retained repair: draft PR #611 is the single retained tmux-3.6a repair lane at head `6a27ddab361938b4ab875610b7a51ac9e845c744`. Its product delta remains exactly `the artefact/clayverse/terminal_sessions.py` plus `the artefact/tests/test_terminal_tmux_control_timeouts.py`, with the same live-evidenced blobs above. Canonical `main` advanced after #611 rejoined `e9631e32c4317d6a05e4522096c987b442900968`, so #611 is again ancestry-stale/non-mergeable and exact #611 runtime remains **UNOBSERVED**. Closed PR #612 carried the same repair/test blobs plus older living-status/evidence material and is now superseded for coordination; its historical runtime receipt remains evidence at its original bound scope.
- Execution bridge: retained `gschaidergabriel/Dr.-Unterweger` PR #846 is at bridge head `17efb3fe28691359bbee47ee7e20522b6075b326` and binds its runtime receipt marker to exact PR #611 head `6a27ddab361938b4ab875610b7a51ac9e845c744` without changing candidate product bytes. Its exact-head Vercel trigger was build-rate-limited before Sandbox start, so it receives zero exact-current runtime credit.
- Daytona remains the owner-authorized fallback when Vercel is blocked before assertions. The fallback is **connector-independent**: Daytona's documented HTTPS API/SDK/CLI is the provider interface, so absence of a native ChatGPT plugin/connector is not evidence that Daytona itself is unavailable or that the account has no credit. This ChatGPT controller currently lacks both Daytona DNS egress and an injected `DAYTONA_API_KEY`, so it is blocked before provider contact and contributes zero Daytona runtime credit.
- Remaining major acceptance gates include rejoining the retained #611 two-file candidate to then-current `main`, one exact-head authorized isolated real-tmux rerun, exact OCI build/runtime receipt, real Clerk JWT + browser WebSocket PTY verification, authenticated interactive native Claude Code verification for both canonical user homes, automatic hook lifecycle integration, persistence/recovery, managed-Claude process identity in live tmux, and live dual-session concurrency/fencing.

### Latest cycle delta

**2026-08-17 17:27 +07:00 — `NO_CHANGE` product code; duplicate live-verified tmux lane retired and living state refreshed**

- Rejoined canonical research `main` at `2fefc099a65da5c275eaa1468abef87f4e9b245c` before this status write and refreshed overlapping open PRs.
- Verified PR #611 head `6a27ddab361938b4ab875610b7a51ac9e845c744` still carries only the retained terminal repair and focused test, with terminal blob `c185009f8af84e1288747d8352645777a36b2053` and test blob `b6bb645dd07645f21ca2e5574f8392c9f13beafc`.
- Verified PR #612 carried the same repair/test blobs and the old-head real-tmux evidence but was ancestry-stale/non-mergeable. Closed #612 unmerged so one retained semantic tmux repair lane remains; no runtime evidence was promoted or discarded by that coordination action.
- Current-main comparison shows #611 has diverged again after parallel `main` movement. Therefore no merge/rebase promotion was attempted from byte identity or old-head component evidence alone.
- Rechecked execution surfaces: the connected Vercel tool exports documentation only, not Sandbox lifecycle execution. Dr.-Unterweger PR #846 remains the exact #611 bridge, while its most recent exact-head trigger is build-rate-limited before Sandbox start. Daytona remains blocked from this controller before provider contact by missing credential injection and DNS egress, not by connector absence.
- `NO_CHANGE` to ClayVerse product/runtime code, runtime evidence class, and whole-product acceptance. The next discriminator is an ancestry-current #611 rejoin followed by one actually-started authorized isolated exact-head real-tmux rerun; only then may focused/adjacent regressions and promotion proceed.

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

Focused isolated tests have exercised bounded source mechanisms, and real Vercel Sandbox execution has both falsified the predecessor tmux reapply behavior and verified the byte-identical repair component at an older bound head under tmux 3.6a, but **whole-product PASS is not claimed**. Exact current retained repair runtime and the exact current product still require authorized isolated evidence: exact repair rerun, OCI build/image identity, startup/readiness, real Clerk JWT plus browser WebSocket PTY, authenticated native Claude Code for both user homes, managed hook lifecycle, UnifiedDB persistence/recovery, accepted effect/EntityOS behavior where admitted, and live dual-session concurrency/generation fencing.

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