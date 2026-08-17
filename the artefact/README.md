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
- Real terminal evidence: the predecessor reapply mechanism was first falsified under real tmux 3.6a. Authorized Vercel Sandbox deployment `dpl_6z5oXV29Q4TgRonAgs9TaEmxfB5T` later executed terminal blob `c185009f8af84e1288747d8352645777a36b2053` and focused-test blob `b6bb645dd07645f21ca2e5574f8392c9f13beafc` at bound old head `ef61bfb85ab59291c3b0b33d024aa098b1f29089` and passed pre-policy upgrade, already-hardened reapply, new-server second source, direct multi-argv fake-Claude launch, plus mixed/unknown/empty fail-closed assertions under deny-all network. This is strong **component/mechanism PASS at that bound old head**, not exact-current or whole-product PASS; native Claude and the OCI product image were not tested.
- Retained repair: draft PR #611 is the single semantic tmux-3.6a repair lane. Immediately before this living-status write it was ancestry-rejoined to canonical `main` `6f274dab83836175145d89e68d2ee28a75c32575` at head `2957e80228815ac266635981a55f22bc15dc9ed4`, with exactly two changed paths: `the artefact/clayverse/terminal_sessions.py` and `the artefact/tests/test_terminal_tmux_control_timeouts.py`. This status-only write itself advances `main` without changing those repair bytes, so #611 must be rejoined **once more to then-current `main` immediately before the exact runtime discriminator**. Do not infer runtime PASS from byte identity or the older bound-head PASS.
- Execution bridge: retained `gschaidergabriel/Dr.-Unterweger` PR #846 reached bridge head `4310f2ef3fef7fa9680158ff53a7978e18fdc622`, binding the staged #611 head `2957e80228815ac266635981a55f22bc15dc9ed4` without changing candidate bytes. Vercel reports `Deployment rate limited — retry in 24 hours.` before Sandbox start; zero exact-current runtime credit exists. At the next admitted run, first rejoin #611 to then-current `main`, then rebind the bridge to that resulting exact head and execute immediately before another status-only `main` write.
- GitHub identity guard on staged #611 head `2957e80228815ac266635981a55f22bc15dc9ed4` again failed with no visible job steps. This is runner/admission evidence only and carries zero product-test credit.
- Daytona remains the owner-authorized fallback when Vercel is blocked before assertions. The fallback is **connector-independent**: Daytona's documented HTTPS API/SDK/CLI is the provider interface, so absence of a native ChatGPT plugin/connector is not evidence that Daytona itself is unavailable or that the account has no credit. This ChatGPT controller currently lacks Daytona DNS egress and an approved injected `DAYTONA_API_KEY` path, so it is blocked before provider contact and contributes zero Daytona runtime credit; provider/account availability remains unobserved.
- Coordination is converged: PR #603 is closed superseded, PR #612 is closed as a duplicate repair lane, and PR #614 is closed as a duplicate/stale status lane. PR #611 remains the sole retained repair candidate.
- Remaining major acceptance gates include one final #611 ancestry rejoin plus exact-head authorized isolated real-tmux rerun, exact OCI build/runtime receipt, real Clerk JWT + browser WebSocket PTY verification, authenticated interactive native Claude Code verification for both canonical user homes, automatic hook lifecycle integration, persistence/recovery, managed-Claude process identity in live tmux, and live dual-session concurrency/fencing.

### Latest cycle delta

**2026-08-17 17:30 +07:00 — `NO_CHANGE` product code; #611 rejoined and bridge rebound, exact execution still blocked before Sandbox start**

- Refreshed canonical `main` through `6f274dab83836175145d89e68d2ee28a75c32575`, preserving the corrected Daytona classification and the single-lane tmux coordination state.
- Parallel coordination rejoined PR #611 to that exact `main` at staged head `2957e80228815ac266635981a55f22bc15dc9ed4`; comparison showed `behind_by=0` and exactly the two intended repair/test paths with unchanged terminal/test blobs.
- Parallel bridge work rebound Dr.-Unterweger PR #846 to that staged head at bridge commit `4310f2ef3fef7fa9680158ff53a7978e18fdc622`.
- Vercel immediately rejected that exact-head trigger with `Deployment rate limited — retry in 24 hours.` before Sandbox start, so no exact-current PASS or FAIL was observed and no duplicate trigger was spent.
- GitHub identity guard run `32020465304` / job `95358887718` failed with no visible steps, again providing zero executable product credit.
- Preserved the old-head evidence boundary: `dpl_6z5oXV29Q4TgRonAgs9TaEmxfB5T` remains a real-tmux component/mechanism PASS only at old bound head `ef61bfb85ab59291c3b0b33d024aa098b1f29089`.
- Established a rebase-stable execution sequence: because this mandatory README/PROGRAM_STATE status write itself advances `main`, the next admitted execution must **rejoin #611 once to then-current `main`, rebind the bridge to that exact resulting head, and execute immediately before any further status-only main write**. This prevents an endless status/rebase loop while retaining exact-head evidence law.
- `NO_CHANGE` to ClayVerse product/runtime code and whole-product acceptance. No unusual experiment was executed; the macro-cycle remained deterministic regression/coordination work.
- Durable bounded receipt: `receipts/2026-08-17_GO_1730_TMUX_REJOIN_STAGING_BLOCKED_GPT56SOL.json`.
- Next gate: once an authorized isolated surface admits execution, perform the one final ancestry rejoin + bridge rebind and require under real tmux 3.6a: pre-policy upgrade PASS, already-hardened second reapply PASS, new-server second source PASS, direct multi-argv transport PASS, and mixed/unknown/empty diagnostic fail-closed PASS. Then run focused + adjacent regressions and only then consider repair promotion before OCI/native-Claude/readiness/restart/concurrency acceptance.

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

Focused isolated tests have exercised bounded source mechanisms, and real Vercel Sandbox execution has both falsified the predecessor tmux reapply behavior and verified the byte-identical repair component at an older bound head under tmux 3.6a, but **whole-product PASS is not claimed**. Exact retained-repair runtime and the exact current product still require authorized isolated evidence: exact repair rerun, OCI build/image identity, startup/readiness, real Clerk JWT plus browser WebSocket PTY, authenticated native Claude Code for both user homes, managed hook lifecycle, UnifiedDB persistence/recovery, accepted effect/EntityOS behavior where admitted, and live dual-session concurrency/generation fencing.

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
