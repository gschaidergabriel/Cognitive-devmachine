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
- Retained repair: draft PR #611 is intentionally **frozen** at exact head `6a27ddab361938b4ab875610b7a51ac9e845c744`. At the freeze point its diff against canonical `main` contained exactly two paths — `the artefact/clayverse/terminal_sessions.py` and `the artefact/tests/test_terminal_tmux_control_timeouts.py` — with terminal blob `c185009f8af84e1288747d8352645777a36b2053` and focused-test blob `b6bb645dd07645f21ca2e5574f8392c9f13beafc`. Status-only changes on `main` must not move this head before its exact-head discriminator executes; otherwise runtime identity would become a moving target. Exact PR #611 runtime remains **UNOBSERVED**.
- Execution bridge: retained `gschaidergabriel/Dr.-Unterweger` PR #846 is rebound by bridge commit `17efb3fe28691359bbee47ee7e20522b6075b326` to frozen PR #611 head `6a27ddab361938b4ab875610b7a51ac9e845c744` without changing candidate bytes. Vercel reports `Deployment rate limited — retry in 24 hours.` for that bridge commit before Sandbox start, so it receives zero exact-current runtime credit.
- Daytona remains the owner-authorized fallback when Vercel is blocked before assertions. The fallback is **connector-independent**: Daytona's documented HTTPS API/SDK/CLI is the provider interface, so absence of a native ChatGPT plugin/connector is not evidence that Daytona itself is unavailable or that the account has no credit. This ChatGPT controller currently lacks both Daytona DNS egress and an approved injected `DAYTONA_API_KEY` path, so it is blocked before provider contact and contributes zero Daytona runtime credit; provider/account availability remains unobserved.
- Coordination is converged on one repair lane: PR #603 and duplicate PR #612 are closed unmerged; duplicate status PR #614 is also closed. PR #611 is the retained repair candidate.
- Remaining major acceptance gates include the exact frozen PR #611 real-tmux rerun, exact OCI build/runtime receipt, real Clerk JWT + browser WebSocket PTY verification, authenticated interactive native Claude Code verification for both canonical user homes, automatic hook lifecycle integration, persistence/recovery, managed-Claude process identity in live tmux, and live dual-session concurrency/fencing.

### Latest cycle delta

**2026-08-17 17:26 +07:00 — exact PR #611 head frozen and execution bridge rebound; exact-head runtime remains admission-blocked**

- Rejoined canonical research `main` at `2fefc099a65da5c275eaa1468abef87f4e9b245c`, preserving the newer Daytona surface-classification correction: no native ChatGPT connector is not evidence of provider unavailability or absent account credit.
- Converged the retained tmux repair to exact PR #611 head `6a27ddab361938b4ab875610b7a51ac9e845c744`. At freeze, its current-main diff contained only the terminal repair and its focused regression file, with unchanged terminal/test blobs.
- Preserved the strongest actual runtime evidence: Vercel deployment `dpl_6z5oXV29Q4TgRonAgs9TaEmxfB5T` PASSed the byte-identical repair component under real tmux 3.6a at the older bound head `ef61bfb85ab59291c3b0b33d024aa098b1f29089`. This remains bounded old-head component/mechanism evidence only.
- Rebound retained bridge PR #846 to frozen PR #611 via bridge commit `17efb3fe28691359bbee47ee7e20522b6075b326`. Its Vercel status is explicitly `Deployment rate limited — retry in 24 hours.` before Sandbox start; therefore the frozen exact head still has zero runtime PASS/FAIL credit.
- Established the freeze rule: **do not move PR #611 for status-only `main` advances before the exact-head discriminator executes**. After an exact-head PASS, refresh then-current `main`, run focused plus adjacent regressions, and only then consider promotion.
- Daytona fallback remains mechanism-supported but this controller is blocked before provider contact by unavailable approved secret injection and DNS egress. No Daytona sandbox command executed.
- `NO_CHANGE` to canonical ClayVerse product/runtime code and whole-product acceptance. This delta is coordination/evidence binding only.
- No unusual experiment was executed; the shared user-trigger lease could not be uniquely and safely acquired, so the macro-cycle stayed deterministic regression/coordination work.
- Durable bounded receipt: `receipts/2026-08-17_GO_1726_PR611_EXACT_HEAD_FREEZE_REBIND_BLOCKED_GPT56SOL.json`.
- Next gate: when an authorized isolated execution surface admits the frozen target, run bridge head `17efb3fe28691359bbee47ee7e20522b6075b326` against PR #611 head `6a27ddab361938b4ab875610b7a51ac9e845c744` under real tmux 3.6a and reproduce pre-policy upgrade, already-hardened reapply, new-server second source, direct multi-argv transport and mixed/unknown/empty fail-closed assertions. Only then refresh `main` and evaluate promotion before OCI/native-Claude/readiness/restart/concurrency acceptance.

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

Focused isolated tests have exercised bounded source mechanisms, and real Vercel Sandbox execution has both falsified the predecessor tmux reapply behavior and verified the byte-identical repair component at an older bound head under tmux 3.6a, but **whole-product PASS is not claimed**. Exact frozen PR #611 runtime and the exact current product still require authorized isolated evidence: exact repair rerun, OCI build/image identity, startup/readiness, real Clerk JWT plus browser WebSocket PTY, authenticated native Claude Code for both user homes, managed hook lifecycle, UnifiedDB persistence/recovery, accepted effect/EntityOS behavior where admitted, and live dual-session concurrency/generation fencing.

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
