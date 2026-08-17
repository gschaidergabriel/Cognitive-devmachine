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
- Real terminal evidence: Vercel Sandbox execution against predecessor terminal blob `185a748f80011b324b2c4786644ad42ff369203e` and managed-tmux blob `fd3a0a3b5f0b595c0e15d9f36991148eed67df7d` reached real tmux 3.6a. Pre-policy persistent-server upgrade succeeded; the new-session path then failed because the second managed `source-file` returned already-removed default-key-table diagnostics. This is an **exact component live-runtime FAIL for the predecessor reapply mechanism**, not whole-product failure.
- Retained repair: draft PR #611 is now the single code/test repair lane, reconstructed from and ancestry-rejoined through canonical `main` `4d7fd30e8b226dea51c1e7ce3e34ca4a3359e505`. Its terminal blob remains exactly `c185009f8af84e1288747d8352645777a36b2053` and its focused test blob remains exactly `b6bb645dd07645f21ca2e5574f8392c9f13beafc`. It tolerates only the exact known tmux-3.6a already-removed-table diagnostics and retains independent full effective-state attestation. It is **not canonical and not runtime-verified**. Stale-ancestry PR #603 is closed unmerged as superseded, avoiding a second retained repair path.
- Execution bridge: retained `gschaidergabriel/Dr.-Unterweger` PR #846 is currently at head `49204d3f20bbb86a153f83d29cda2ddadf062b4f`. The earlier deployment `dpl_5fhrwfPFEo4bM947eUR2Bnwe3fK5` failed in the build step on the temporary Node-24 bridge parser before `Sandbox.create`, so it provides zero ClayVerse repair credit. The current retained bridge head has Vercel combined status `failure` with the explicit `upgradeToPro=build-rate-limit` target; therefore the post-repair exact rerun is still **ADMISSION_BLOCKED_BEFORE_SANDBOX_START**.
- Daytona remains the owner-authorized fallback only when a FREE_ONLY executable surface is actually available. No executable Daytona sandbox connector/provider path is exposed in this session, so no Daytona provider contact or runtime credit exists.
- Remaining major acceptance gates include the real-tmux PR #611 discriminator, exact OCI build/runtime receipt, real Clerk JWT + browser WebSocket PTY verification, authenticated interactive native Claude Code verification for both canonical user homes, automatic hook lifecycle integration, persistence/recovery, managed-Claude process identity in live tmux, and live dual-session concurrency/fencing.

### Latest cycle delta

**2026-08-17 17:14 +07:00 — tmux repair candidate rejoined to current `main`; runtime evidence unchanged**

- Began from canonical `main` `37b36ba7af90b5337852a0c6daf21313b6a1d170` and identified stale ancestry, rather than repair semantics, as the remaining source-side issue around PR #603.
- Reconstructed the repair on fresh branch `go/tmux-source-reapply-idempotent-livefix-20260817-1714-r2` with byte-identical terminal blob `c185009f8af84e1288747d8352645777a36b2053` and focused test blob `b6bb645dd07645f21ca2e5574f8392c9f13beafc`; the initial source diff contained only those two intended product/test paths.
- While the cycle was running, canonical `main` advanced to `4d7fd30e8b226dea51c1e7ce3e34ca4a3359e505` via a parallel NO_CHANGE execution-admission refresh. Its four intervening commits touched only `PROGRAM_STATE`, this living README and a receipt, with **no terminal product overlap**.
- Ancestry-rejoined that newer `main` into the repair lane in merge commit `5464a84de7304912e21d5e013e88b6c369f48202`, preserving the exact repair/test blobs and the newer canonical program/evidence state.
- Opened replacement draft PR #611 and closed stale PR #603 unmerged as superseded. This leaves one retained repair candidate rather than two parallel semantic paths.
- No repair runtime PASS/FAIL was manufactured: the retained Vercel bridge remains blocked by the post-parser-fix `build-rate-limit` before Sandbox start, and no executable Daytona fallback path is available here. A duplicate Preview was not spent.
- No unusual experiment was executed. This work is deterministic regression/source convergence, and the shared trigger identity exposes only minute precision, so the atomic experiment lease remains `COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT`.
- Durable bounded receipt: `receipts/2026-08-17_GO_1714_TMUX_REPAIR_CURRENT_MAIN_REJOIN_GPT56SOL.json`.
- Next gate: execute the exact PR #611 candidate under real tmux 3.6a in an admitted isolated Sandbox and require all five markers: pre-policy upgrade PASS, already-hardened second reapply PASS, new-server second source PASS, direct multi-argv transport PASS, and mixed/unknown diagnostic fail-closed PASS. Only then refresh then-current `main`, rerun focused + adjacent regressions, and consider promotion before OCI/native-Claude/readiness/restart/concurrency acceptance.

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

Focused isolated tests have exercised bounded source mechanisms, and real Vercel Sandbox execution has falsified one exact tmux reapply behavior under tmux 3.6a, but **whole-product PASS is not claimed**. The exact current product still requires authorized isolated full-path evidence: exact OCI build/image identity, startup/readiness, real Clerk JWT plus browser WebSocket PTY, authenticated native Claude Code for both user homes, managed hook lifecycle, UnifiedDB persistence/recovery, accepted effect/EntityOS behavior where admitted, and live dual-session concurrency/generation fencing.

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
