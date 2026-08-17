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
- Terminal runtime evidence: an exact-byte Vercel Sandbox regression using current-main predecessor terminal blob `185a748f80011b324b2c4786644ad42ff369203e` and managed-tmux blob `fd3a0a3b5f0b595c0e15d9f36991148eed67df7d` reached real tmux 3.6a. Pre-policy persistent-server upgrade succeeded, but the new-session path then failed when the second managed `source-file` returned tmux's missing-key-table diagnostics. This is a **real component runtime FAIL for the predecessor reapply mechanism**, not provider-admission failure and not whole-product failure.
- Terminal repair status: draft PR #603 retains terminal blob `c185009f8af84e1288747d8352645777a36b2053`; its observed PR head is `ef61bfb85ab59291c3b0b33d024aa098b1f29089`. The repair narrowly tolerates only exact already-removed v3 key-table diagnostics while retaining the mandatory independent effective-state attestation. It is **not canonical and not runtime-verified**. Rejoin with then-current `main` remains mandatory before promotion.
- Execution surface: retained Dr.-Unterweger bridge PR #846 did receive a fresh Vercel Preview for exact retrigger head `f3eff0ef179961110f338e18159ab47a46e69fd9`. That build failed **before `Sandbox.create`** because the bridge runner itself had a Node 24 template-literal parse error (`Unexpected identifier 'unbind'`); this is a harness failure with zero ClayVerse test credit. A single retained bridge-only parser repair now rewrites only the malformed escaped-backtick harness bytes before import and leaves the candidate product bytes unchanged; a redundant parallel bootstrap was removed. The observed retained bridge head `49204d3f20bbb86a153f83d29cda2ddadf062b4f` is again Vercel `build-rate-limit` blocked before Sandbox start. Daytona remains the owner-authorized standard fallback, but this controller still cannot resolve Daytona/PyPI DNS and has no installed Daytona SDK/connector, so no provider contact or Daytona runtime credit exists.
- Remaining major acceptance gates include the real-tmux #603 discriminator, exact OCI build/runtime receipt, real Clerk JWT + browser WebSocket PTY verification, authenticated interactive **native** Claude Code verification for both canonical user homes, automatic hook lifecycle integration, persistence/recovery, managed-Claude process identity in live tmux, and live dual-session concurrency/fencing.

### Latest cycle delta

**2026-08-17 16:55 +07:00 — `NO_CHANGE` product code; #603 rerun admitted, bridge parser defect isolated and repaired**

- `NO_CHANGE` to canonical ClayVerse product code and whole-product acceptance. The highest-information gate is still the unchanged real-tmux 3.6a discriminator for repair PR #603; changing that candidate without a measured repair defect would invalidate the exact falsifier rather than increase convergence.
- Refreshed and rejoined canonical research state through `main` `9d32c7de1c57937b45abdb3370386bec53224bd3` before this cycle write.
- Reopened execution truth rather than preserving the prior rate-limit assumption: Vercel admitted exact bridge retrigger head `f3eff0ef179961110f338e18159ab47a46e69fd9` as deployment `dpl_Cu8hEPnRsYVTGmnBG8vUypVuQHAc`, cloned the intended branch and entered `npm run vercel-build`.
- The admitted rerun then failed during Node parsing with `Unexpected identifier 'unbind'`, before any Vercel Sandbox was created. Classification: **HARNESS_PARSE_FAILURE_BEFORE_SANDBOX_START / zero product PASS-or-FAIL credit**.
- The parser defect was localized to doubled-backslash-plus-backtick bytes inside the execution bridge's JavaScript template literal. The retained single bridge-fix path repairs only that harness encoding in memory before importing the existing runner; the exact ClayVerse terminal blob `c185009f8af84e1288747d8352645777a36b2053` and managed-tmux policy blob `fd3a0a3b5f0b595c0e15d9f36991148eed67df7d` remain unchanged.
- A redundant concurrent bootstrap implementation was removed so the bridge keeps one execution semantics. The observed retained PR #846 head is `49204d3f20bbb86a153f83d29cda2ddadf062b4f`; its newest Vercel status is again `build-rate-limit` before build/Sandbox start, so the post-fix repair remains runtime-unobserved.
- Daytona fallback was rechecked without exposing credentials: this controller cannot resolve `pypi.org`, `app.daytona.io` or `api.daytona.io`, and the Daytona SDK is absent. Classification remains **ORCHESTRATION_NETWORK_BLOCKED_BEFORE_DAYTONA_PROVIDER_CONTACT**, not Daytona-unavailable and not a ClayVerse test failure.
- No unusual experiment was executed: the shared trigger identity available here has only minute precision and no immutable unique request id, so the atomic experiment protocol remains `COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT`. The tmux rerun is regression-only.
- Durable detailed evidence for this adjudication is `receipts/2026-08-17_GO_1655_TMUX_BRIDGE_PARSE_ADJUDICATION_GPT56SOL.json`.
- Next gate: when Vercel admission or an admitted Daytona provider-contact path becomes available, execute the unchanged repair against real tmux 3.6a and require pre-policy upgrade, already-hardened reapply, new-server second-source, direct multi-argv fake-Claude, and mixed/unknown-diagnostic fail-closed behavior. Only after that PASS: rejoin then-current `main`, run focused + adjacent regressions, and promote before OCI/native-Claude/readiness/restart/concurrency acceptance.

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

Focused isolated tests have exercised bounded source mechanisms, and real Vercel Sandbox execution has falsified one exact predecessor tmux reapply behavior under tmux 3.6a, but **whole-product PASS is not claimed**. The repair itself remains runtime-unobserved because the fresh rerun exposed a bridge parser failure before Sandbox creation and the post-fix retrigger is admission-blocked. The exact current product still requires a full authorized isolated test run, exact OCI build/runtime receipt, real Clerk JWT plus browser WebSocket PTY verification, authenticated interactive native Claude Code runtime verification for both user homes, full ClayVerse MCP begin/effect/complete integration, accepted embedded EntityOS runtime evidence, and restart/recovery plus live dual-session concurrency/fencing validation.

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
