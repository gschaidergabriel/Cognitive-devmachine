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
- Runtime readiness: current `main` requires canonical state plus both live canonical tmux sessions and transport-policy-v3 attestation. This branch extends the same admission path to require exactly one live pane whose foreground process and recorded start argv match the exact managed Claude launch contract. This remains a source candidate until exact isolated tmux/native-Claude/OCI execution is observed.
- Clerk/PTY lease boundary: post-attach initial resize, received terminal frames, PTY input writes and PTY output publication are fenced against the verified Clerk lease; the focused attach-expiry resize regression is retained on current `main`.
- Effects: generic host `process.exec` is fail-closed; admitted effects must go through the ClayVerse effect boundary. `EffectJournal.begin()` rejects foreign or already-consumed episode causal identity before a new `PENDING` effect can be journaled. EntityOS remains an optional digest-bound internal execution/security/runtime substrate, not the product endpoint.
- Current execution admission: exact current-head whole-runtime evidence remains unobserved. Vercel execution is currently blocked by the free daily deployment cap; the authorized Daytona fallback is currently blocked from this ChatGPT execution surface by orchestration/network/DNS before provider contact. These are execution-admission blockers, not product test failures.
- Remaining major acceptance gates include an exact OCI build/runtime receipt, real Clerk JWT + browser WebSocket PTY verification, authenticated interactive Claude Code verification for both canonical user homes, automatic hook lifecycle integration, persistence/recovery, exact managed-Claude process identity in live tmux, and live dual-session concurrency/fencing.

### Latest cycle delta

**2026-08-17 — managed Claude process identity/readiness source candidate on current terminal spine**

- Rebased the retained process-attestation lane directly onto current `main` `62de4777f77936c0ce4540b97a682414158e8a62`, after live tmux transport-policy-v3 readiness, policy reapply/control timeouts, Clerk lease fences, effect causal-spine hardening and the living-status contract had landed.
- Added one retained process discriminator: exactly one live pane, `pane_current_command=claude`, and `pane_start_command` parsing exactly to the sanitized managed ClayVerse launch argv. Existing or newly-created sessions fail closed when this process contract does not attest.
- Extended the already-canonical live+policy readiness concept so both canonical perspectives must satisfy the exact managed Claude process predicate before `/readyz` can advertise product readiness.
- Repaired adjacent tests that still encoded the superseded shell-string tmux launch assumption, and separated lower-layer tmux-policy tests from the new process-identity layer.
- Preserved the strongest counterhypothesis: exact packaged tmux/native Claude may represent `pane_current_command` or `pane_start_command` differently for a legitimate process. Do not weaken the predicate speculatively; resolve it in exact isolated OCI/live-tmux execution.
- The exact rebased r5 branch is **not runtime-verified**. Earlier equivalent bounded source reconstructions passed focused regressions, but those do not establish exact r5, live tmux/native-Claude or OCI behavior.
- No unusual experiment was executed for this `go`: shared trigger identity is only minute precision, so the atomic experiment protocol remains `COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT` rather than inventing a timestamp.
- Superseded process-attestation lanes, including closed draft PR #598, must not be fused alongside this retained lane.
- Whole-product acceptance remains unchanged: **IN_PROGRESS**.

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

Focused isolated tests have exercised bounded source mechanisms, but **whole-product PASS is not claimed**. The exact current head still requires a full authorized isolated test run, exact OCI build/runtime receipt, real Clerk JWT plus browser WebSocket PTY verification, authenticated interactive Claude Code runtime verification for both user homes, full ClayVerse MCP begin/effect/complete integration, accepted embedded EntityOS runtime evidence, and restart/recovery plus live dual-session concurrency/fencing validation.

GitHub-hosted Actions are not current runtime evidence while jobs are blocked before execution by the account billing/spending state.

## Local isolated source checks

Where an authorized isolated Python environment is available:

```bash
python -m pytest -q
PYTHONPATH=. CLAYVERSE_STATE_ROOT=/tmp/clayverse-state python -m clayverse.service --once
```

These source checks do not substitute for an exact container build/runtime gate.

## Container source

`Dockerfile` + `compose.yaml` define the single runtime container. The Docker build context is default-deny and allowlists only consumed product inputs, including the runtime Claude contract and digest-bound staged EntityOS artifact. Persistent ClayVerse state and workspace are externalized as scoped volumes, while the application image runs non-root with a read-only root filesystem in Compose, `no-new-privileges`, and dropped Linux capabilities.
