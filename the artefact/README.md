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
- Effects: generic host `process.exec` is fail-closed; admitted effects must go through the ClayVerse effect boundary. EntityOS remains an optional digest-bound internal execution/security/runtime substrate, not the product endpoint.
- Current execution admission: exact current-head whole-runtime evidence remains unobserved. Vercel execution is currently blocked by the free daily deployment cap; the authorized Daytona fallback is currently blocked by orchestration-network/DNS before provider contact. These are execution-admission blockers, not product test failures.
- Remaining major acceptance gates include an exact OCI build/runtime receipt, real Clerk JWT + browser WebSocket PTY verification, authenticated interactive Claude Code verification for both canonical user homes, automatic hook lifecycle integration, persistence/recovery, and live dual-session concurrency/fencing.

### Latest cycle delta

**2026-08-17 — README cycle contract introduced**

- The README is now the human-readable living status surface for `the artefact/`.
- Every product-convergent cycle must update this section with the newest state and the cycle delta; `NO_CHANGE` must be written explicitly when a cycle produces no canonical artefact/status change.
- The latest merged artefact hardening before this README refresh fixed EntityOS child execution to a fixed `/usr/bin:/bin` PATH instead of inheriting a mutable parent PATH. Supporting exact-file regression evidence was 3/3 PASS, but this does **not** grant OCI/runtime, EntityOS-admission, or whole-product PASS.
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
