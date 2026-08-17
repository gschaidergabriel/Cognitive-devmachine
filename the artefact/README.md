# the artefact — ClayVerse single-container candidate

This directory is the canonical product workspace for the current ClayVerse endpoint: **one OCI/Docker-compatible container image** containing one persistent central ClayVerse entity.

## Living cycle status

**This section is mandatory living state. It must be refreshed in every product-convergent work cycle after canonical code/evidence fusion and before that cycle is considered complete.** It records both the newest known state and what changed in the just-finished cycle. A stale README means the cycle is not complete.

### Current state

- Program: **ClayVerse single-container**
- Stage: **CLAYVERSE_ARTIFACT**
- Acceptance: **IN_PROGRESS** — no whole-product PASS is claimed.
- Canonical state authority: **UnifiedDB**; ClayGraph remains derived/rebuildable projection only.
- User/runtime path: Clerk-authenticated browser → authenticated WebSocket PTY → user-bound persistent tmux → normal interactive Claude Code CLI.
- Runtime cognition: Claude Code is inference/cognition only; it is not canonical durable memory or identity.
- Runtime readiness: `/readyz` requires canonical state **and** both canonical tmux sessions to be live and pass the same managed transport-policy-v3 attestation used by attach admission. This is a read-only readiness gate and does not create or repair sessions.
- Clerk/PTY lease boundary: post-attach initial resize, received terminal frames, PTY input writes and PTY output publication are fenced against the verified Clerk lease; the focused attach-expiry resize regression is retained on current `main`.
- Effects: generic host `process.exec` is fail-closed; admitted effects must go through the ClayVerse effect boundary. `EffectJournal.begin()` rejects foreign or already-consumed episode causal identity before a new `PENDING` effect can be journaled. EntityOS remains an optional digest-bound internal execution/security/runtime substrate, not the product endpoint.
- Terminal runtime evidence: an exact-byte Vercel Sandbox regression using current-main terminal blob `185a748f80011b324b2c4786644ad42ff369203e` and managed-tmux blob `fd3a0a3b5f0b595c0e15d9f36991148eed67df7d` reached real tmux 3.6a. Pre-policy persistent-server upgrade succeeded, but the new-session path then failed when the second managed `source-file` returned tmux's missing-key-table diagnostics. This remains a **real component runtime FAIL for the current-main predecessor reapply mechanism**, not provider-admission failure and not whole-product failure.
- Terminal repair status: draft PR #603 at observed head `ef61bfb85ab59291c3b0b33d024aa098b1f29089` narrowly tolerates only the exact already-removed v3 key-table diagnostics while retaining the mandatory independent effective-state attestation. The repair is **not canonical and not runtime-verified**. During this cycle an exact rerun was retriggered through retained bridge PR #846: one build failed before `Sandbox.create` on a temporary bridge parser error, that bridge-only parser defect was repaired, and the newest exact bridge-fix head is again Vercel rate-limited before Sandbox start. These bridge/admission outcomes give PR #603 zero PASS/FAIL credit.
- Execution surface: Vercel Git-preview → `@vercel/sandbox` execution is confirmed and was observed admitted again during this cycle by a separate bounded non-ClayVerse-product run that actually executed under `DENY_ALL`. Therefore a blanket claim that Vercel Sandbox remained continuously unavailable was stale. The newest exact PR #603 bridge-fix head is nevertheless currently blocked before Sandbox start by Vercel build-rate limiting. The owner-authorized FREE_ONLY Daytona fallback remains the next provider fallback when admitted, but this organ observed no Daytona dispatch surface or runtime execution for this repair and assigns it zero runtime credit.
- Remaining major acceptance gates include the real-tmux #603 discriminator, exact OCI build/runtime receipt, real Clerk JWT + browser WebSocket PTY verification, authenticated interactive **native** Claude Code verification for both canonical user homes, automatic hook lifecycle integration, persistence/recovery, managed-Claude process identity in live tmux, and live dual-session concurrency/fencing.

### Latest cycle delta

**2026-08-17 — #603 rerun admission reclassification + execution-bridge repair**

- **Canonical product-code delta: `NO_CHANGE`.** PR #603 remains intentionally Draft/unmerged because its exact real-tmux repair rerun has still not reached product assertions. No second terminal policy implementation was created.
- Refreshed the execution surface instead of trusting the earlier rate-limit snapshot: Vercel deployment `dpl_D9dvKLk37x99xcNE2M9qsCkvA4MM` actually entered a Sandbox and executed a bounded separate regression under `DENY_ALL`, proving that Sandbox admission had reopened during this cycle. Its unrelated later export/stop-attestation failure gives no ClayVerse product credit.
- The retained PR #846 bridge then retriggered the exact current PR #603 candidate (`ef61bfb85ab59291c3b0b33d024aa098b1f29089`, terminal blob `c185009f8af84e1288747d8352645777a36b2053`). Vercel deployment `dpl_Cu8hEPnRsYVTGmnBG8vUypVuQHAc` reached the build but failed **before `Sandbox.create`** because an over-escaped backtick in the temporary JavaScript execution bridge caused `SyntaxError: Unexpected identifier 'unbind'`. Classification: bridge parser failure, zero product-test credit.
- Parallel work repaired only that temporary bridge parser path while preserving the same product candidate and same falsifier. A stale write attempt from this organ received GitHub 409 and was correctly not forced over the newer shared branch.
- The newest exact bridge head `07beb9b5ef4f61b3281a7c0aa702dda789d6da34` is now rejected by Vercel with `Deployment rate limited — retry in 24 hours.` before Sandbox start. The exact #603 repair therefore remains **runtime unverified**, not PASS and not FAIL.
- Daytona remains the owner-authorized FREE_ONLY fallback, but no admitted Daytona provider action/runtime was available to this organ; no bypass of the free-credit/credential contract was attempted and no Daytona result is claimed.
- No unusual experiment was executed for this `go`: no shared immutable request/turn id is exposed and the user-message timestamp available to this organ has only minute precision, so the atomic experiment protocol requires `COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT`.
- Next exact gate: when an authorized isolated execution slot is admitted, run the same PR #603 real-tmux 3.6a discriminator and require pre-policy upgrade PASS, already-hardened second reapply PASS, new-server second source PASS, direct multi-argv transport PASS, and mixed/unknown diagnostic fail-closed. Merge #603 only after that exact rerun passes; then continue to OCI/native-Claude/readiness/restart/concurrency acceptance.
- Whole-product acceptance remains **IN_PROGRESS**.

### Cycle update rule

At the end of every product-convergent cycle:

1. Refresh current `main`, canonical artefact state, relevant receipts and observed execution evidence.
2. Rewrite **Current state** so it reflects the newest canonical reality, removing stale claims.
3. Add or replace **Latest cycle delta** with the concrete changes from that cycle, including code, tests, evidence, blockers and acceptance movement. If nothing canonical changed, write `NO_CHANGE` and why.
4. Never promote source inspection, a PR, CI configuration, deployment `READY`, component evidence or historical evidence into whole-product PASS.
5. Persist the README update in the same branch/PR/fusion cycle as the artefact/evidence it describes. A cycle is not complete while the README is stale.

Git history and bounded receipts remain the detailed audit trail; this README stays compact and reflects the **latest** state rather than becoming a second canonical database.

## Architecture

Current source implements the UnifiedDB/ClayGraph continuity core, equal-rights Gabriel/Andreas identity routing, bounded workspace/causal re-entry, Clerk JWT verification, and the current terminal-pivot surface: browser → Clerk → authenticated WebSocket PTY → user-bound persistent tmux → normal interactive Claude Code CLI. Claude Code built-in tools are disabled in product terminals; a strict local stdio ClayVerse MCP is the admitted state/context/effect bridge. The runtime contract requires each human prompt to enter canonical ClayVerse state through `begin_turn` and to re-enter through `complete_turn`; UnifiedDB remains the durable state/memory authority. Generic host `process.exec` remains fail-closed. EntityOS is a digest-bound internal execution/security/runtime substrate candidate, not the product endpoint, and its external-effect execution remains separately gated.

The previous custom chat API and headless `claude -p` path are retired as product runtime surfaces. `consciousness_daemon` is not part of the target architecture.

## Verification

Focused isolated tests have exercised bounded source mechanisms, and real Vercel Sandbox execution has falsified one exact current-main predecessor tmux reapply behavior under tmux 3.6a, but **whole-product PASS is not claimed**. The exact #603 repair rerun has not yet reached its product assertions. The current head still requires a full authorized isolated test run, exact OCI build/runtime receipt, real Clerk JWT plus browser WebSocket PTY verification, authenticated interactive native Claude Code runtime verification for both user homes, full ClayVerse MCP begin/effect/complete integration, accepted embedded EntityOS runtime evidence, and restart/recovery plus live dual-session concurrency/fencing validation.

GitHub-hosted Actions are not runtime evidence when jobs fail before visible execution. Vercel deployment state alone is likewise not runtime PASS; only the actually observed Sandbox command/assertion path is executable evidence at its exact source/environment scope.

## Local isolated source checks

Where an authorized isolated Python environment is available:

```bash
python -m pytest -q
PYTHONPATH=. CLAYVERSE_STATE_ROOT=/tmp/clayverse-state python -m clayverse.service --once
```

These source checks do not substitute for an exact container build/runtime gate.

## Container source

`Dockerfile` + `compose.yaml` define the single runtime container. The Docker build context is default-deny and allowlists only consumed product inputs, including the runtime Claude contract and digest-bound staged EntityOS artifact. Persistent ClayVerse state and workspace are externalized as scoped volumes, while the application image runs non-root with a read-only root filesystem in Compose, `no-new-privileges`, and dropped Linux capabilities.
