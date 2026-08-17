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
- Research coordination: material deltas now use **Live Fusion** for targeted research/worker re-entry, with **Live Hypofusion** automatically opening an adversarial counterhypothesis lane for material contradiction, promotion, pseudo-replication, persistent-blocker, OOD/security or competing-worker conditions. Exact `fusion` and `hypofusion` commands remain full-depth macro-runs. This coordination layer does not create a second state/effect authority.
- Runtime readiness on current `main`: `/readyz` requires canonical state and both canonical tmux sessions to be live and pass the managed transport-policy-v3 attestation used by attach admission. This gate is read-only and does not create or repair sessions.
- Clerk/PTY lease boundary: post-attach initial resize, received terminal frames, PTY input writes and PTY output publication are fenced against the verified Clerk lease.
- Effects: generic host `process.exec` is fail-closed; admitted effects must pass the ClayVerse effect boundary. EntityOS remains an optional digest-bound internal execution/security/runtime substrate, not the product endpoint.
- Real terminal evidence: the predecessor reapply mechanism was first falsified under real tmux 3.6a. A later authorized Vercel Sandbox run, deployment `dpl_6z5oXV29Q4TgRonAgs9TaEmxfB5T`, executed terminal blob `c185009f8af84e1288747d8352645777a36b2053` and focused-test blob `b6bb645dd07645f21ca2e5574f8392c9f13beafc` at bound old head `ef61bfb85ab59291c3b0b33d024aa098b1f29089` and passed pre-policy upgrade, already-hardened reapply, new-server second source, direct multi-argv fake-Claude launch, plus assertions that mixed/unknown and empty diagnostics remain fail-closed. Network was deny-all during the candidate test. This is strong **component/mechanism PASS at that bound old head**, not exact-current or whole-product PASS; native Claude and the OCI product image were not tested.
- Retained repair: draft PR #611 is the single retained tmux-3.6a repair lane at head `6a27ddab361938b4ab875610b7a51ac9e845c744`. Its product delta remains exactly `the artefact/clayverse/terminal_sessions.py` plus `the artefact/tests/test_terminal_tmux_control_timeouts.py`, with the same live-evidenced blobs above. Canonical `main` advanced after #611 rejoined `e9631e32c4317d6a05e4522096c987b442900968`, so #611 is again ancestry-stale/non-mergeable and exact #611 runtime remains **UNOBSERVED**. Closed PR #612 carried the same repair/test blobs plus older living-status/evidence material and is now superseded for coordination; its historical runtime receipt remains evidence at its original bound scope.
- Execution bridge: retained `gschaidergabriel/Dr.-Unterweger` PR #846 is at bridge head `17efb3fe28691359bbee47ee7e20522b6075b326` and binds its runtime receipt marker to exact PR #611 head `6a27ddab361938b4ab875610b7a51ac9e845c744` without changing candidate product bytes. Its exact-head Vercel trigger was build-rate-limited before Sandbox start, so it receives zero exact-current runtime credit.
- Daytona remains the owner-authorized fallback when Vercel is blocked before assertions. The fallback is **connector-independent**: Daytona's documented HTTPS API/SDK/CLI is the provider interface, so absence of a native ChatGPT plugin/connector is not evidence that Daytona itself is unavailable or that the account has no credit. This ChatGPT controller currently lacks both Daytona DNS egress and an injected `DAYTONA_API_KEY`, so it is blocked before provider contact and contributes zero Daytona runtime credit.
- Remaining major acceptance gates include rejoining the retained #611 two-file candidate to then-current `main`, one exact-head authorized isolated real-tmux rerun, exact OCI build/runtime receipt, real Clerk JWT + browser WebSocket PTY verification, authenticated interactive native Claude Code verification for both canonical user homes, automatic hook lifecycle integration, persistence/recovery, managed-Claude process identity in live tmux, and live dual-session concurrency/fencing.

### Latest cycle delta

**2026-08-17 17:31 +07:00 — `NO_CHANGE` product/runtime code; Live Fusion + conditional Live Hypofusion activated with targeted research/worker re-entry**

- Rejoined canonical research `main` at `6f274dab83836175145d89e68d2ee28a75c32575` after detecting parallel movement during the cycle; stale earlier branch work was not promoted over the newer shared state.
- Added `research_entity/global/LIVE_FUSION_HYPOFUSION_WORKER_REENTRY_DIRECTIVE.md`: every material delta enters Live Fusion, while high-impact contradiction/promotion/shared-ancestry/persistent-blocker/OOD-security/competing-worker conditions automatically open a Live Hypofusion counterhypothesis lane.
- Reused the existing OmniSource and autonomous-swarm re-entry semantics rather than creating a second bus or truth authority. Delivery is explicitly separated from reconstruction, plan revalidation, use, local effect and causal credit.
- Persisted an activation/re-entry receipt plus targeted worker manifest under `research_entity/mesh_feedback/20260817T1725p0700-live-fusion-hypofusion-reentry/`.
- First live re-entry adjudication: PR #611 remains the single retained tmux repair lane and must rejoin then-current `main` before an exact-head real-tmux rerun; PR #612 arrived concurrently already closed as the duplicate code lane with its historical evidence preserved; PR #602 is deferred/revalidated behind the canonical tmux repair and must later face exact OCI/live-tmux/native-Claude process falsification.
- `PROGRAM_STATE.json` now makes the live-reentry directive and receipt boot-discoverable and records that exact `fusion`/`hypofusion` triggers remain the deeper explicit macro-runs.
- `NO_CHANGE` to ClayVerse product runtime code, runtime evidence class or whole-product acceptance. Fusion/Hypofusion can alter research hypotheses, test obligations and worker plans, but cannot mint truth, effect authority or acceptance by consensus.

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
