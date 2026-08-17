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
- Daytona remains the owner-authorized fallback when Vercel is blocked before assertions. The fallback is **connector-independent**: Daytona's documented HTTPS API/SDK/CLI is the provider interface, so absence of a native ChatGPT plugin/connector is not evidence that Daytona itself is unavailable or that the account has no credit. This ChatGPT controller currently lacks both Daytona DNS egress and an injected `DAYTONA_API_KEY`, so it is blocked before provider contact and contributes zero Daytona runtime credit.
- Remaining major acceptance gates include the exact PR #611 real-tmux rerun, exact OCI build/runtime receipt, real Clerk JWT + browser WebSocket PTY verification, authenticated interactive native Claude Code verification for both canonical user homes, automatic hook lifecycle integration, persistence/recovery, managed-Claude process identity in live tmux, and live dual-session concurrency/fencing.

### Latest cycle delta

**2026-08-17 17:23 +07:00 — execution-status repair: missing Daytona connector no longer classified as provider/runtime unavailability**

- Rejoined canonical research `main` at `e9631e32c4317d6a05e4522096c987b442900968` before this correction.
- Verified current Daytona primary documentation still exposes API-key authenticated direct HTTPS API plus SDK/CLI sandbox creation and execution surfaces; a ChatGPT-native Daytona connector is therefore optional orchestration convenience, not provider authority.
- Rechecked the current ChatGPT controller without exposing secrets: no `DAYTONA_API_KEY` is injected, Daytona SDK is absent, and DNS resolution fails for `app.daytona.io`, `api.daytona.io` and `pypi.org`. Classification is **CURRENT_CHATGPT_ORCHESTRATOR_BLOCKED_BEFORE_DAYTONA_PROVIDER_CONTACT**.
- Corrected the durable law: `NO_CHATGPT_DAYTONA_CONNECTOR != DAYTONA_UNAVAILABLE`, `NO_CHATGPT_DAYTONA_CONNECTOR != NO_DAYTONA_ACCOUNT_CREDIT`, and zero Daytona runtime credit means only that no accepted Daytona sandbox command has executed at the bound identity.
- Preserved the current product evidence boundary: Vercel has already produced a real-tmux component/mechanism PASS for the byte-identical repair at the older bound head, while the exact retained current PR #611 rerun remains build-rate-limited before Sandbox start.
- `NO_CHANGE` to ClayVerse product/runtime code and whole-product acceptance. This is an execution-admission/state-classification repair only.
- Next execution rule: prefer Vercel whenever admitted and capable; if fallback is actually needed, dispatch Daytona directly from an authorized egress-capable controller through the documented API/SDK with approved secret injection and an account-specific FREE_ONLY/no-paid-use gate.

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
