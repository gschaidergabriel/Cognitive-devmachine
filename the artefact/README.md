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
- Runtime readiness: `/readyz` now requires canonical state **and** both canonical tmux sessions to be live and pass the same managed transport-policy attestation used by attach admission; this is source/mechanism hardening, not live OCI/runtime acceptance.
- Managed Claude lifecycle candidate on this branch: canonical turn provenance carries Claude `prompt_id`; duplicate `UserPromptSubmit`, `Stop`, `StopFailure`, and repeated-Stop cleanup are fenced by prompt identity inside the existing UnifiedDB transaction path. This remains a **Draft PR source candidate**, not merged/runtime-verified product behavior.
- Effects: generic host `process.exec` is fail-closed; admitted effects must go through the ClayVerse effect boundary. EntityOS remains an optional digest-bound internal execution/security/runtime substrate, not the product endpoint.
- Current execution admission: exact current-head whole-runtime evidence remains unobserved. Vercel execution is currently blocked by the free daily deployment cap; the authorized Daytona fallback is currently blocked by orchestration-network/DNS before provider contact. These are execution-admission blockers, not product test failures.
- Python dependency supply chain: an exact hash-lock generator workflow exists, but no successful generator run has been observed and `requirements.lock.txt` is not yet present on canonical `main`; no unverified manual lock is admitted.
- Remaining major acceptance gates include an exact authorized isolated regression of the managed hook lifecycle, packaged Claude Code hook-payload verification, an actually generated/verified Python hash lock, exact OCI build/runtime receipt, real Clerk JWT + browser WebSocket PTY verification, authenticated interactive Claude Code verification for both canonical user homes, persistence/recovery, and live dual-session concurrency/fencing.

### Latest cycle delta

**2026-08-17 — managed Claude prompt-identity fusion rejoined; missing Stop-guard regression recovered**

- Retained one canonical candidate lane: Draft PR #454. It upgrades managed lifecycle correlation from long-lived Claude `session_id` alone to transactional `(session_id, prompt_id)` fencing without creating a second turn/state authority.
- The candidate now rejects duplicate active prompt delivery before predecessor retirement inside the canonical `BEGIN IMMEDIATE` admission transaction and re-checks prompt identity for `Stop` / `StopFailure` inside completion/abort transactions.
- Adversarial fusion found that the retained lane had omitted the adjacent `test_terminal_hook_stop_guard.py` update required once `prompt_id` became mandatory at the managed hook boundary. The unique prompt-aware donor regression was fused into #454; older duplicate PR #373 was then closed as superseded.
- Current official Claude Code hook documentation supports the chosen identity field: `prompt_id` is a common hook input identifying the active user prompt and requires Claude Code v2.1.196 or later. ClayVerse pins 2.1.233, but exact packaged 2.1.233 payload behavior is still unverified runtime evidence.
- The candidate was repeatedly rejoined onto advancing canonical `main`, including current readiness/EntityOS hardening and the mandatory living-README cycle law; no overlapping canonical main source was discarded.
- GitHub Verify, Identity Guard, and Python lock-generator jobs observed on the candidate failed before visible step execution (`steps=null`), so they provide neither product-test failure nor PASS evidence.
- Vercel remains blocked by the current free Preview daily cap. Daytona remains authorized fallback but the available orchestration environment could not resolve Daytona/PyPI DNS before provider contact; runtime credit remains zero.
- Supply-chain review found the Python hash-lock generator workflow present but no successful generator run and no canonical `requirements.lock.txt`. No synthetic/unverified lock was manufactured.
- The unusual-experiment slot was **COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT** because this `go` exposes no shared immutable request id and only minute-precision immutable message time to this organ.
- Whole-product acceptance remains unchanged: **IN_PROGRESS**. PR #454 remains Draft until exact authorized isolated regressions plus packaged Claude hook-payload verification execute.

### Cycle update rule

At the end of every product-convergent cycle:

1. Refresh current `main`, canonical artefact state, relevant receipts and observed execution evidence.
2. Rewrite **Current state** so it reflects the newest canonical reality, removing stale claims.
3. Add or replace **Latest cycle delta** with the concrete changes from that cycle, including code, tests, evidence, blockers and acceptance movement. If nothing canonical changed, write `NO_CHANGE` and why.
4. Never promote source inspection, a PR, CI configuration, deployment `READY`, component evidence or historical evidence into whole-product PASS.
5. Persist the README update in the same branch/PR/fusion cycle as the artefact/evidence it describes. A cycle is not complete while the README is stale.

Git history and bounded receipts remain the detailed audit trail; this README stays compact and reflects the **latest** state rather than becoming a second canonical database.

## Architecture

Current source implements the UnifiedDB/ClayGraph continuity core, equal-rights Gabriel/Andreas identity routing, bounded workspace/causal re-entry, Clerk JWT verification, and the current terminal-pivot surface: browser → Clerk → authenticated WebSocket PTY → user-bound persistent tmux → normal interactive Claude Code CLI. Claude Code built-in tools are disabled in product terminals; a strict local stdio ClayVerse MCP is the admitted state/context/effect bridge. The runtime contract requires each human prompt to enter canonical ClayVerse state through the managed turn lifecycle and to re-enter through completion/failure handling; UnifiedDB remains the durable state/memory authority. Generic host `process.exec` remains fail-closed. EntityOS is a digest-bound internal execution/security/runtime substrate candidate, not the product endpoint, and its external-effect execution remains separately gated.

The previous custom chat API and headless `claude -p` path are retired as product runtime surfaces. `consciousness_daemon` is not part of the target architecture.

## Verification

Focused isolated tests have exercised bounded source mechanisms, but **whole-product PASS is not claimed**. The exact current candidate still requires a full authorized isolated test run, exact OCI build/runtime receipt, real Clerk JWT plus browser WebSocket PTY verification, authenticated interactive Claude Code runtime verification for both user homes, automatic managed-hook lifecycle integration, accepted embedded EntityOS runtime evidence, and restart/recovery plus live dual-session concurrency/fencing validation.

GitHub-hosted Actions are not current runtime evidence while jobs fail before visible step execution.

## Local isolated source checks

Where an authorized isolated Python environment is available:

```bash
python -m pytest -q
PYTHONPATH=. CLAYVERSE_STATE_ROOT=/tmp/clayverse-state python -m clayverse.service --once
```

These source checks do not substitute for an exact container build/runtime gate.

## Container source

`Dockerfile` + `compose.yaml` define the single runtime container. The Docker build context is default-deny and allowlists only consumed product inputs, including the runtime Claude contract and digest-bound staged EntityOS artifact. Persistent ClayVerse state and workspace are externalized as scoped volumes, while the application image runs non-root with a read-only root filesystem in Compose, `no-new-privileges`, and dropped Linux capabilities.
