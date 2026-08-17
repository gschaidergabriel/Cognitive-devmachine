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
- Retained repair: draft PR #603 is still the single code/test repair lane at head `ef61bfb85ab59291c3b0b33d024aa098b1f29089`, with terminal blob `c185009f8af84e1288747d8352645777a36b2053`. It tolerates only the exact known tmux-3.6a already-removed-table diagnostics and retains independent full effective-state attestation. It is **not canonical and not runtime-verified**; PR #603 is currently non-mergeable/diverged and must rejoin then-current `main` only after the exact runtime discriminator passes.
- Execution bridge: retained `gschaidergabriel/Dr.-Unterweger` PR #846 is currently at head `49204d3f20bbb86a153f83d29cda2ddadf062b4f`. The earlier deployment `dpl_5fhrwfPFEo4bM947eUR2Bnwe3fK5` failed in the build step on the temporary Node-24 bridge parser before `Sandbox.create`, so it provides zero ClayVerse repair credit. The current retained bridge head has Vercel combined status `failure` with the explicit `upgradeToPro=build-rate-limit` target; therefore the post-repair exact #603 rerun is still **ADMISSION_BLOCKED_BEFORE_SANDBOX_START**.
- Daytona remains the owner-authorized fallback only when a FREE_ONLY executable surface is actually available. A fresh plugin search found no installable Daytona sandbox connector/plugin in this session, so no Daytona provider contact or runtime credit exists.
- Remaining major acceptance gates include the real-tmux #603 discriminator, exact OCI build/runtime receipt, real Clerk JWT + browser WebSocket PTY verification, authenticated interactive native Claude Code verification for both canonical user homes, automatic hook lifecycle integration, persistence/recovery, managed-Claude process identity in live tmux, and live dual-session concurrency/fencing.

### Latest cycle delta

**2026-08-17 17:14 +07:00 — `NO_CHANGE` product code; execution admission rechecked and living status refreshed**

- Rejoined canonical research `main` at `37b36ba7af90b5337852a0c6daf21313b6a1d170` and rechecked active overlapping PRs before writing.
- Reconfirmed PR #603 as the highest-information non-duplicate product discriminator: head `ef61bfb85ab59291c3b0b33d024aa098b1f29089`, candidate terminal blob `c185009f8af84e1288747d8352645777a36b2053`, runtime still unobserved.
- Rechecked Vercel deployment history: `dpl_5fhrwfPFEo4bM947eUR2Bnwe3fK5` is a bridge-parser/build failure before Sandbox start, not a product test failure.
- Rechecked the **current** retained bridge head `49204d3f20bbb86a153f83d29cda2ddadf062b4f`: Vercel still reports `failure` with `upgradeToPro=build-rate-limit`. A duplicate Preview was therefore not spent.
- Searched for an executable Daytona sandbox plugin/connector; none is available in this ChatGPT surface. No provider contact and zero runtime credit.
- `NO_CHANGE` to canonical ClayVerse product/runtime code and whole-product acceptance. PR #603 remains unpromoted because source coherence cannot substitute for the real-tmux rerun.
- No unusual experiment was executed: this cycle is regression/admission re-entry only, and no unique shared atomic experiment lease key is exposed.
- Durable bounded receipt: `receipts/2026-08-17_GO_1714_EXECUTION_ADMISSION_RECHECK_NO_CHANGE_GPT56SOL.json`.
- Next gate: on the first admitted Vercel Sandbox, execute the unchanged PR #603 candidate under real tmux 3.6a and require all five markers: pre-policy upgrade PASS, already-hardened second reapply PASS, new-server second source PASS, direct multi-argv transport PASS, and mixed/unknown diagnostic fail-closed PASS. Only then rejoin then-current `main`, rerun focused + adjacent regressions, and consider promotion before OCI/native-Claude/readiness/restart/concurrency acceptance.

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
