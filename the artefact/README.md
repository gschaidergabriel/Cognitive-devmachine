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
- Runtime readiness: `/readyz` requires canonical state and both canonical tmux sessions to be live and pass the managed transport-policy-v3 attestation used by attach admission; this remains broader product-runtime acceptance work, not whole-container PASS.
- Clerk/PTY lease boundary: post-attach initial resize, received terminal frames, PTY input writes and PTY output publication are fenced against the verified Clerk lease; the focused attach-expiry resize regression is retained on current `main`.
- Effects: generic host `process.exec` is fail-closed; admitted effects must go through the ClayVerse effect boundary. `EffectJournal.begin()` rejects foreign or already-consumed episode causal identity before a new `PENDING` effect can be journaled. EntityOS remains an optional digest-bound internal execution/security/runtime substrate, not the product endpoint.
- **Observed live tmux result:** an exact-byte Vercel Sandbox run reached real tmux 3.6a and SQLite-capable Python. Upgrading an intentionally pre-policy persistent Gabriel server to transport-policy v3 passed, but creating Andreas then re-sourcing the already-loaded destructive v3 policy failed because tmux 3.6a reports already-removed key tables as errors. This is a real component/runtime failure of the predecessor terminal mechanism, not provider admission failure.
- **Current repair gate:** PR #603 keeps the managed tmux file as the single policy source and tolerates only exact missing-default-key-table diagnostics, while every unknown/mixed/empty error remains fatal and the complete v3 effective-state attestation remains mandatory. The repair is **SOURCE CANDIDATE only** until the same real-tmux falsifier reruns successfully and the branch is rejoined to then-current `main`.
- Current execution admission: Vercel Sandbox executed the predecessor probe successfully up to the product failure, but no new Vercel Preview has yet been observed for the staged repair rerun. GitHub Actions still fail before visible steps (`runner_id=0`, `steps=[]`). The authorized Daytona fallback has no new provider-contact/runtime evidence for this repair rerun.
- Remaining major acceptance gates include an exact OCI build/runtime receipt, real Clerk JWT + browser WebSocket PTY verification, authenticated interactive Claude Code verification for both canonical user homes, automatic hook lifecycle integration, persistence/recovery, managed-Claude process identity in live tmux, and live dual-session concurrency/fencing.

### Latest cycle delta

**2026-08-17 — real tmux 3.6a falsification → bounded idempotent reapply repair candidate**

- Reopened the previously source-only terminal assumption under real tmux rather than accepting mock regressions as runtime truth.
- Vercel Sandbox provisioned tmux 3.6a and Python 3.13.13; SQLite 3.40.0 worked, eliminating the earlier bare-runtime `_sqlite3` blocker for this bounded mechanism path.
- Exact predecessor terminal blob `185a748f80011b324b2c4786644ad42ff369203e` plus policy blob `fd3a0a3b5f0b595c0e15d9f36991148eed67df7d` upgraded a live unsafe persistent Gabriel server in ~15 ms, then failed on Andreas when the already-loaded policy was sourced a second time: `table prefix/copy-mode/copy-mode-vi doesn't exist`.
- Added PR #603 repair candidate: exact candidate terminal blob `c185009f8af84e1288747d8352645777a36b2053`; only the four expected missing-default-table diagnostics may be treated as idempotent, and the full policy attestation remains the final admission authority.
- Added focused source regressions for expected-only, mixed/unknown and empty nonzero `source-file` diagnostics, plus a durable failure/candidate receipt. These tests are not promoted to runtime PASS because current GitHub runners still fail before steps.
- Staged the identical real-tmux regression rerun through the existing Vercel execution bridge. No second Preview has yet appeared, so the candidate remains draft/unmerged rather than converting design confidence into a false runtime claim.
- No unusual experiment was executed for this `go`: shared trigger identity is only minute precision, so the atomic experiment protocol remains `COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT` rather than inventing a timestamp.
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

Focused isolated tests have exercised bounded source mechanisms, and a real Vercel tmux probe has now falsified one predecessor terminal assumption, but **whole-product PASS is not claimed**. The exact current head still requires the repaired real-tmux rerun, full authorized isolated test run, exact OCI build/runtime receipt, real Clerk JWT plus browser WebSocket PTY verification, authenticated interactive Claude Code runtime verification for both user homes, full ClayVerse MCP begin/effect/complete integration, accepted embedded EntityOS runtime evidence, and restart/recovery plus live dual-session concurrency/fencing validation.

GitHub-hosted Actions are not current runtime evidence while jobs are blocked before step execution.

## Local isolated source checks

Where an authorized isolated Python environment is available:

```bash
python -m pytest -q
PYTHONPATH=. CLAYVERSE_STATE_ROOT=/tmp/clayverse-state python -m clayverse.service --once
```

These source checks do not substitute for an exact container build/runtime gate.

## Container source

`Dockerfile` + `compose.yaml` define the single runtime container. The Docker build context is default-deny and allowlists only consumed product inputs, including the runtime Claude contract and digest-bound staged EntityOS artifact. Persistent ClayVerse state and workspace are externalized as scoped volumes, while the application image runs non-root with a read-only root filesystem in Compose, `no-new-privileges`, and dropped Linux capabilities.
