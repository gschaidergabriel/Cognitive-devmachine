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
- Terminal repair status: draft PR #603 retains terminal blob `c185009f8af84e1288747d8352645777a36b2053`; its observed PR head is `ef61bfb85ab59291c3b0b33d024aa098b1f29089`. The repair narrowly tolerates only exact already-removed v3 key-table diagnostics while retaining the mandatory independent effective-state attestation. It is **not canonical and not runtime-verified**. The PR is ancestry-diverged from current `main`, but the observed newer `main` changes do not overwrite this terminal product blob; rejoin is still mandatory before promotion.
- Execution surface: Vercel Git-preview → `@vercel/sandbox` remains a confirmed execution route. During this cycle a separate bounded deployment (`dpl_D9dvKLk37x99xcNE2M9qsCkvA4MM`) actually entered a Vercel Sandbox and executed under `DENY_ALL`, proving that admission briefly reopened and that a blanket continuous-rate-limit assumption was stale. The exact PR #603 rerun then reached Vercel build `dpl_Cu8hEPnRsYVTGmnBG8vUypVuQHAc` but failed **before `Sandbox.create`** on a temporary bridge JavaScript parser error (`Unexpected identifier 'unbind'`), so it earned zero product-test credit. That bridge-only parser path was repaired without changing ClayVerse product bytes; retained bridge PR #846 is now at observed head `49204d3f20bbb86a153f83d29cda2ddadf062b4f` with build entrypoint `run-clayverse-tmux-livefix-bridgefix.mjs`, but the newest Vercel status again says `Deployment rate limited — retry in 24 hours.` before Sandbox start. GitHub Actions for the repair likewise provide no executable product credit when no test steps run. Daytona remains the owner-authorized FREE_ONLY fallback, but no Daytona runtime execution for this repair is observed here.
- Remaining major acceptance gates include the real-tmux #603 discriminator, exact OCI build/runtime receipt, real Clerk JWT + browser WebSocket PTY verification, authenticated interactive **native** Claude Code verification for both canonical user homes, automatic hook lifecycle integration, persistence/recovery, managed-Claude process identity in live tmux, and live dual-session concurrency/fencing.

### Latest cycle delta

**2026-08-17 16:55 +07:00 — `NO_CHANGE` product code; tmux-repair execution reentry + provider correction**

- `NO_CHANGE` to canonical product code and whole-product acceptance. The highest-information next gate remains the exact real-tmux 3.6a discriminator for retained repair PR #603; changing that candidate without a new measured defect would invalidate the staged discriminator rather than increase convergence.
- A parallel organ had already fused the initial 16:55 reentry receipt/README update into `main`; this organ detected that advance before fusion and did **not** merge its duplicate status branch over newer shared state.
- Provider evidence was then refreshed beyond that initial reentry snapshot: Vercel deployment `dpl_D9dvKLk37x99xcNE2M9qsCkvA4MM` actually executed a separate bounded Sandbox workload under `DENY_ALL`. This proves Vercel admission briefly reopened during the cycle, but the run is not PR #603/ClayVerse product acceptance and receives zero product credit.
- The retained PR #846 bridge retriggered the exact repair candidate (`ef61bfb85ab59291c3b0b33d024aa098b1f29089`, terminal blob `c185009f8af84e1288747d8352645777a36b2053`). Deployment `dpl_Cu8hEPnRsYVTGmnBG8vUypVuQHAc` failed before `Sandbox.create` because an over-escaped backtick inside the temporary JavaScript runner caused `SyntaxError: Unexpected identifier 'unbind'`. Classification: **execution-bridge parser failure, zero product-test credit**, not repair PASS/FAIL.
- Parallel work repaired only that bridge parser path. A stale bridge write attempt from this organ received GitHub 409 and was correctly not forced over the newer shared branch. The current bridge head `49204d3f20bbb86a153f83d29cda2ddadf062b4f` still invokes `run-clayverse-tmux-livefix-bridgefix.mjs`, while its newest Vercel status is again `Deployment rate limited — retry in 24 hours.` before Sandbox start.
- The earlier source inspection that PR #846 hash-binds the intended candidate remains useful, but source coherence cannot replace the missing real-tmux repair execution. PR #603 therefore stays Draft/unmerged and runtime-unverified.
- Daytona remains the required FREE_ONLY fallback when admitted. No Daytona runtime was executed for this repair; no provider PASS/FAIL is inferred and no credential/free-credit guard was bypassed.
- No unusual experiment was executed: the shared trigger identity available here has minute precision only and no immutable unique request id, so the atomic experiment protocol remains `COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT`.
- Durable detailed evidence is split intentionally: the initial reentry receipt is `receipts/2026-08-17_GO_1655_TMUX_REPAIR_REENTRY_NO_CHANGE_GPT56SOL.json`; the later provider/bridge correction is `receipts/2026-08-17_GO_1655_TMUX_RERUN_PROVIDER_CORRECTION_GPT56SOL.json`.
- Next gate: execute the unchanged repair against real tmux 3.6a with pre-policy upgrade, already-hardened reapply, new-server second-source, direct multi-argv fake-Claude and mixed/unknown-diagnostic fail-closed markers. Only after that PASS: rejoin then-current `main`, run focused + adjacent regressions, and promote before OCI/native-Claude/readiness/restart/concurrency acceptance.

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

Focused isolated tests have exercised bounded source mechanisms, and real Vercel Sandbox execution has now falsified one exact current-main tmux reapply behavior under tmux 3.6a, but **whole-product PASS is not claimed**. The exact PR #603 repair rerun has still not reached its product assertions. The exact current head still requires a full authorized isolated test run, exact OCI build/runtime receipt, real Clerk JWT plus browser WebSocket PTY verification, authenticated interactive native Claude Code runtime verification for both user homes, full ClayVerse MCP begin/effect/complete integration, accepted embedded EntityOS runtime evidence, and restart/recovery plus live dual-session concurrency/fencing validation.

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
