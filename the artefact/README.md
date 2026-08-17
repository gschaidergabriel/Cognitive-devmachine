# the artefact — ClayVerse single-container candidate

This directory is the canonical product workspace for the ClayVerse endpoint: **one OCI/Docker-compatible container image** containing one persistent central ClayVerse entity. This PR branch is a **noncanonical supply-chain candidate** and must be rejoined to then-current `main` before exact acceptance execution.

## Living cycle status

**Refresh this section in every product-convergent cycle. A stale README means the cycle is incomplete.** Detailed evidence remains in Git history and bounded receipts.

### Current state

- Program: **ClayVerse single-container**; stage: **CLAYVERSE_ARTIFACT**.
- Acceptance: **IN_PROGRESS** — no whole-product PASS is claimed.
- Canonical durable state authority remains **UnifiedDB**; ClayGraph is derived/rebuildable only.
- Product surface remains Clerk-authenticated browser → WebSocket PTY → user-bound persistent tmux → normal interactive Claude Code.
- This branch is PR **#422**, the retained APT/supply-chain candidate. It remains Draft/noncanonical and was observed non-mergeable before this cycle's writes; no merge or exact-current runtime claim is inferred.
- Current cycle hardening replaces broad `.dockerignore` subtree reinclusions (`!clayverse/**`, `!policy/**`) with explicit file-level runtime/policy allowlists. This closes a source-level counterexample where untracked cache/temp/secret bytes below those subtrees could otherwise enter the OCI build context despite not being canonical product inputs.
- Regression `tests/test_build_context_boundary.py` now rejects broad runtime/policy subtree exceptions and checks the admitted runtime/policy file set.
- Supporting isolated reconstruction: exact candidate `.dockerignore` + regression bytes passed **2/2**. A synthetic `clayverse/untracked_secret.py` mutation made the regression fail as intended. This is bounded source-mechanism evidence only; no Docker/BuildKit/OCI builder was available in that executor.
- Unusual-experiment status for the 17:36 `go`: **COORDINATION_BLOCKED_NO_VALID_UNUSUAL_EXPERIMENT_LEASE**; a parallel invalid-lease execution incident is preserved as tainted history, valid unusual-experiment credit is 0, and no further unusual experiment is permitted for this trigger.
- Main runtime frontier remains independent: retained tmux repair PR #611 still requires an actually-started exact isolated real-tmux gate before promotion; PR #602 remains downstream.

### Latest cycle delta

**2026-08-17 17:43 +07:00 — supply-chain source candidate hardened; runtime acceptance unchanged**

- Fused the build-context counterexample into existing PR #422 rather than creating a duplicate supply-chain lane.
- `.dockerignore` is now file-level allowlisted for ClayVerse runtime modules and managed policy files; broad `clayverse/**` and `policy/**` exceptions are removed.
- Added fail-closed regression coverage for that invariant.
- Persisted `receipts/2026-08-17_GO_1743_BUILD_CONTEXT_FILE_ALLOWLIST_GPT56SOL.json` with exact candidate blobs and bounded isolated evidence.
- No exact OCI build, image digest, startup/readiness, Clerk/browser, native-Claude, restart, or concurrency PASS was established.
- Next supply-chain discriminator: at real isolated execution admission, refresh `main`, rejoin #422 once, verify the resulting file-level context against the current runtime tree, then execute the exact OCI/BuildKit build/context gate and capture image identity.

## Architecture

ClayVerse keeps one central entity with two equal user perspectives. UnifiedDB is canonical durable cognition/state authority; Claude Code is runtime cognition; ClayGraph is a derived projection; effects remain explicit and fail-closed; EntityOS is optional internal substrate rather than product endpoint.

The previous custom chat API and headless `claude -p` path are not the product runtime. `consciousness_daemon` is excluded.

## Verification

Source checks and bounded component evidence do not substitute for whole-product acceptance. Exact-current isolated evidence is still required across OCI build/runtime, real Clerk + browser WebSocket PTY, native Claude Code for both user homes, managed hook lifecycle, persistence/recovery, EffectGate/EntityOS where admitted, and live dual-session generation/concurrency fencing.

## Container source

`Dockerfile` + `compose.yaml` define the one runtime container. Persistent state/workspace remain scoped volumes; the admitted Compose profile is read-only-root, non-root, `no-new-privileges`, dropped capabilities, and bounded tmpfs. The build context is intended to admit only explicitly consumed product inputs; this branch now enforces runtime/policy admission at file granularity.
