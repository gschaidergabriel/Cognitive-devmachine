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
- Terminal runtime evidence: an exact-byte Vercel Sandbox regression using current-main terminal blob `185a748f80011b324b2c4786644ad42ff369203e` and managed-tmux blob `fd3a0a3b5f0b595c0e15d9f36991148eed67df7d` reached real tmux 3.6a. Pre-policy persistent-server upgrade succeeded, but the new-session path then failed when the second managed `source-file` returned tmux's missing-key-table diagnostics. This is a **real component runtime FAIL for the current-main reapply mechanism**, not provider-admission failure and not whole-product failure.
- Terminal repair status: draft PR #603 retains terminal blob `c185009f8af84e1288747d8352645777a36b2053`; its current observed PR head is `ef61bfb85ab59291c3b0b33d024aa098b1f29089`. The repair narrowly tolerates only exact already-removed v3 key-table diagnostics while retaining the mandatory independent effective-state attestation. It is **not canonical and not runtime-verified**. The PR is ancestry-diverged from current `main`, but the observed newer `main` changes do not overwrite this terminal product blob; rejoin is still mandatory before promotion.
- Execution surface: retained Dr.-Unterweger bridge PR #846 still binds repair terminal blob `c185009f8af84e1288747d8352645777a36b2053`. A fresh separate Dr.-Unterweger deployment proved Vercel Sandbox execution capacity was not globally unavailable; the first repair rerun then failed **before Sandbox start** on a temporary Node-24 bridge-parser bug, which has been repaired without changing ClayVerse candidate bytes. The immediate post-repair retrigger is again rejected by Vercel with `build-rate-limit` before deployment/Sandbox start, so **no new repair runtime credit exists**. Daytona remains the owner-authorized FREE_ONLY fallback, but no executable Daytona connector/plugin is exposed here and the local controller cannot resolve `app.daytona.io`; no account-specific free-credit attestation or Daytona runtime credit exists.
- Remaining major acceptance gates include the real-tmux #603 discriminator, exact OCI build/runtime receipt, real Clerk JWT + browser WebSocket PTY verification, authenticated interactive **native** Claude Code verification for both canonical user homes, automatic hook lifecycle integration, persistence/recovery, managed-Claude process identity in live tmux, and live dual-session concurrency/fencing.

### Latest cycle delta

**2026-08-17 17:04 +07:00 — `NO_CHANGE` product code; execution evidence fused and dynamic program state synchronized**

- `NO_CHANGE` to canonical ClayVerse product/runtime code and whole-product acceptance. The unchanged highest-information discriminator remains repair PR #603 against real tmux 3.6a.
- Rejoined after parallel fusion at canonical `main` `867f0fe3bb62795c099b63db43458646301904cb`; PR #606 had already canonically fused the stronger 17:02 bridge-parser evidence, so duplicate receipt PR #607 was closed rather than creating a second evidence authority.
- Rejected the counter-reality that Vercel was still globally unable to execute: deployment `dpl_D9dvKLk37x99xcNE2M9qsCkvA4MM` actually started a Vercel Sandbox batch and executed substantive steps before a later unrelated export-lock mismatch. This is provider-capability evidence only, not ClayVerse tmux repair credit.
- Retriggered retained tmux bridge #846 with the current observed #603 head identity and unchanged candidate blob. Deployment `dpl_Cu8hEPnRsYVTGmnBG8vUypVuQHAc` failed before Sandbox creation with Node 24 `SyntaxError: Unexpected identifier 'unbind'` in the temporary bridge's generated template literal. That is **orchestration/pre-assertion failure**, not a tmux repair FAIL.
- Repaired only the temporary execution bridge (`0a48f569775e281a95833a31bd383ae7f8a2fc66`, routed by `fde81e2fa7149e27396d9c0a7113f4b6236f1dca`) so the invalid generated-backtick escaping is normalized before dynamic import. The ClayVerse terminal candidate and managed-tmux blobs are unchanged.
- The post-repair trigger `da602c728d363e1ffe375c5151af2be379820b04` is currently rejected by Vercel with `build-rate-limit` before deployment/Sandbox start. Therefore repair runtime status remains **UNKNOWN / NOT EXECUTED**.
- Daytona fallback was rechecked against the merged FREE_ONLY law. No Daytona connector/plugin is available in this session, the local orchestration environment cannot resolve the provider endpoints and the Daytona SDK is absent; no provider contact or runtime test occurred.
- Synchronized `research_entity/rooms/PROGRAM_STATE.json` with this already-canonical evidence so future workers no longer boot from the stale assertion that the old global Vercel daily-cap observation is the current execution state. The current blocker is now explicitly the **post-bridge-fix Vercel pre-Sandbox rate limit plus Daytona controller DNS/SDK blockage**, with PR #603 runtime still unknown.
- No unusual experiment was executed. This work is regression-only re-entry of the already-defined real-tmux falsifier, and the shared trigger identity still lacks a unique atomic experiment lease key.
- Durable detailed execution evidence remains `receipts/2026-08-17_GO_1702_TMUX_BRIDGE_PARSER_REPAIR_NO_CHANGE_GPT56SOL.json`.
- Next gate: execute the **unchanged** `c185009f8af84e1288747d8352645777a36b2053` repair under real tmux 3.6a with pre-policy upgrade, already-hardened reapply, new-server second-source, direct multi-argv fake-Claude and mixed/unknown-diagnostic fail-closed markers. Only after that PASS: rejoin then-current `main`, run focused + adjacent regressions, and consider promotion before OCI/native-Claude/readiness/restart/concurrency acceptance.

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

Focused isolated tests have exercised bounded source mechanisms, and real Vercel Sandbox execution has now falsified one exact current-main tmux reapply behavior under tmux 3.6a, but **whole-product PASS is not claimed**. The exact current head still requires a full authorized isolated test run, exact OCI build/runtime receipt, real Clerk JWT plus browser WebSocket PTY verification, authenticated interactive native Claude Code runtime verification for both user homes, full ClayVerse MCP begin/effect/complete integration, accepted embedded EntityOS runtime evidence, and restart/recovery plus live dual-session concurrency/fencing validation.

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
