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
- Real terminal evidence: the predecessor reapply mechanism was first falsified under real tmux 3.6a. A later authorized Vercel Sandbox run, deployment `dpl_6z5oXV29Q4TgRonAgs9TaEmxfB5T`, executed the byte-identical repair component at bound old head `ef61bfb85ab59291c3b0b33d024aa098b1f29089` and passed pre-policy upgrade, already-hardened reapply, new-server second source, direct multi-argv fake-Claude launch, plus assertions that mixed/unknown and empty diagnostics remain fail-closed. Network was deny-all during the candidate test. This is strong **component/mechanism PASS at that bound old head**, not exact-current or whole-product PASS; native Claude and the OCI product image were not tested.
- Retained repair: stale PR #603 is closed and superseded by draft PR #611 at head `4364d99fa5af32225a7b5e0c4b3ec2d6fde7b94b`, based on current `main` `4d7fd30e8b226dea51c1e7ce3e34ca4a3359e505`. PR #611 retains the same terminal blob `c185009f8af84e1288747d8352645777a36b2053` and focused-test blob `b6bb645dd07645f21ca2e5574f8392c9f13beafc` with no semantic delta from #603. Exact PR #611 runtime remains **UNOBSERVED** and the draft must not be promoted from old-head evidence alone.
- Execution bridge: retained `gschaidergabriel/Dr.-Unterweger` PR #846 branch is now rebound by bridge commit `9214d30cfd37832cd4a1976a7605672e34570abb` to exact PR #611 head `4364d99fa5af32225a7b5e0c4b3ec2d6fde7b94b`. Its Vercel combined status is `failure` with `upgradeToPro=build-rate-limit`, so no Sandbox started for that exact-head trigger and it receives zero exact-current runtime credit.
- Daytona remains the owner-authorized fallback only when an executable FREE_ONLY surface is actually available. Current program evidence records no executable Daytona plugin/connector in this ChatGPT surface and prior controller DNS/SDK blockage before provider contact, so no Daytona runtime credit exists.
- Remaining major acceptance gates include the exact PR #611 real-tmux rerun, exact OCI build/runtime receipt, real Clerk JWT + browser WebSocket PTY verification, authenticated interactive native Claude Code verification for both canonical user homes, automatic hook lifecycle integration, persistence/recovery, managed-Claude process identity in live tmux, and live dual-session concurrency/fencing.

### Latest cycle delta

**2026-08-17 17:19 +07:00 — `NO_CHANGE` canonical product code; real tmux repair mechanism passed at old bound head, current-main repair lane converged to PR #611, exact-head rerun remains admission-blocked**

- Rejoined canonical research `main` at `4d7fd30e8b226dea51c1e7ce3e34ca4a3359e505` after parallel PR #610 fused the prior 17:14 status-only cycle.
- Coordination converged the stale repair lane: PR #603 is closed; draft PR #611 is the single retained current-main replacement with byte-identical terminal/test candidate and no new repair semantics.
- Authorized Vercel Sandbox deployment `dpl_6z5oXV29Q4TgRonAgs9TaEmxfB5T` actually reached real tmux `3.6a-1.amzn2023.0.1`, Python `3.13.13-1.amzn2023.0.2` and SQLite `3.40.0`; after network changed to deny-all, the repair component at bound old head `ef61bfb85ab59291c3b0b33d024aa098b1f29089` passed the idempotent reapply path and fail-closed diagnostic assertions.
- Preserved the evidence boundary: that run used the exact candidate terminal/policy bytes but is still scoped to the old bound source head; it does not establish exact PR #611 runtime PASS. Native Claude was a fake executable only and the OCI product image was not tested.
- Upstream tmux 3.6a source confirms that `unbind-key -a` reports an error when a target key table no longer exists, supporting the narrow exact-diagnostic classifier rather than a broader exception path; independent effective-state attestation remains mandatory.
- Rebound the retained Vercel bridge to exact PR #611 head via bridge commit `9214d30cfd37832cd4a1976a7605672e34570abb`. Vercel immediately reports build-rate-limit failure before Sandbox start, so exact PR #611 runtime remains unobserved.
- `NO_CHANGE` to canonical ClayVerse product/runtime code and whole-product acceptance. PR #611 remains unmerged until its exact head receives an admitted real-tmux rerun.
- No unusual experiment was executed: this cycle remained regression/admission/coordination work and no unique shared atomic experiment lease was safely available.
- Durable bounded receipt: `receipts/2026-08-17_GO_1719_TMUX36A_REPAIR_EVIDENCE_FUSION_GPT56SOL.json`.
- Next gate: when Vercel admits another build, execute bridge head `9214d30cfd37832cd4a1976a7605672e34570abb` against exact PR #611 head `4364d99fa5af32225a7b5e0c4b3ec2d6fde7b94b` under real tmux 3.6a; require all idempotency and fail-closed assertions, then refresh main, run focused + adjacent regressions and only then consider PR #611 promotion before OCI/native-Claude/readiness/restart/concurrency acceptance.

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

Focused isolated tests have exercised bounded source mechanisms, and real Vercel Sandbox execution has both falsified the predecessor tmux reapply behavior and verified the byte-identical repair component at an older bound head under tmux 3.6a, but **whole-product PASS is not claimed**. Exact current PR #611 runtime and the exact current product still require authorized isolated evidence: exact repair rerun, OCI build/image identity, startup/readiness, real Clerk JWT plus browser WebSocket PTY, authenticated native Claude Code for both user homes, managed hook lifecycle, UnifiedDB persistence/recovery, accepted effect/EntityOS behavior where admitted, and live dual-session concurrency/generation fencing.

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
