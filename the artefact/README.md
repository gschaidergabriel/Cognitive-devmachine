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
- Effects: generic host `process.exec` is fail-closed; admitted effects must pass the ClayVerse effect boundary. EntityOS remains an optional digest-bound internal execution/security/runtime substrate, not the product endpoint.
- Predecessor terminal mechanism: current `main` at rejoin still carried terminal blob `185a748f80011b324b2c4786644ad42ff369203e`; its second managed tmux `source-file` is an exact component live-runtime FAIL on real tmux 3.6a when default key tables are already absent.
- Repair runtime evidence: terminal blob `c185009f8af84e1288747d8352645777a36b2053` is now **exact-component live-runtime VERIFIED** in Vercel Sandbox under tmux `3.6a-1.amzn2023.0.1`, Python `3.13.13-1.amzn2023.0.2`, SQLite `3.40.0`, with network set to `DENY_ALL` before the product test. Required markers passed for pre-policy upgrade, already-hardened reapply, new-server second source, direct multi-argv launch, and fail-closed unknown/mixed/empty diagnostics.
- Rejoin status: the verified repair and focused test blob `b6bb645dd07645f21ca2e5574f8392c9f13beafc` are rejoined on fresh branch `go/tmux-reapply-liveverified-current-main-20260817-1717-sol` from canonical `main` `4d7fd30e8b226dea51c1e7ce3e34ca4a3359e505`. This avoids promoting the ancestry-diverged historical PR #603 branch blindly.
- Scope limit: the live repair run used a fake Claude executable only to attest direct argv/environment transport. **Native Claude Code, the exact OCI image, Clerk/browser PTY, restart/recovery, and dual-session concurrency were not tested by this run.**
- Remaining immediate promotion gate: focused + adjacent deterministic source regressions on the rejoined candidate. After that, the next high-value product gates are managed native-Claude process attestation and exact OCI build/runtime acceptance.

### Latest cycle delta

**2026-08-17 17:17 +07:00 — tmux 3.6a repair discriminator PASSED and live-verified candidate rejoined to current main**

- Refreshed overlapping work and rejoined after parallel `main` advanced to `4d7fd30e8b226dea51c1e7ce3e34ca4a3359e505`.
- Found that the retained temporary Vercel bridge still had two provenance/orchestration faults: invalid Node-24 escaped backticks and a stale embedded candidate-head marker. Hardened the bridge fail-closed without changing ClayVerse candidate bytes; bridge commit `fff4b86192e15368b58584f1a026f3eb0d23aad6` binds the runtime to PR #603 head `ef61bfb85ab59291c3b0b33d024aa098b1f29089`.
- Vercel deployment `dpl_6z5oXV29Q4TgRonAgs9TaEmxfB5T` actually started an isolated Sandbox and completed the exact real-tmux discriminator. Product-test network was `DENY_ALL`.
- Observed PASS markers: `PREPOLICY_UPGRADE_REAPPLY`, `ALREADY_HARDENED_REAPPLY_IDEMPOTENT`, `NEW_SERVER_SECOND_SOURCE_IDEMPOTENT`, and `DIRECT_MULTI_ARGV_FAKE_CLAUDE_LAUNCH`; unknown/mixed and empty nonzero diagnostics remained fail-closed.
- Rejoined exactly the verified terminal blob `c185009f8af84e1288747d8352645777a36b2053` plus focused test blob `b6bb645dd07645f21ca2e5574f8392c9f13beafc` onto a fresh current-main branch. No second semantic terminal path was created.
- Durable receipt: `receipts/2026-08-17_GO_1717_TMUX36A_REPAIR_LIVE_VERIFIED_GPT56SOL.json`.
- No unusual experiment was consumed; this was regression-only execution of the already-defined real-tmux falsifier.
- Whole-product acceptance remains **IN_PROGRESS**. A component runtime PASS is not an OCI/native-Claude/Clerk/recovery/concurrency PASS.
- Next gate: run focused + adjacent deterministic regressions on the rejoined branch. Promote only if they pass, then advance to managed native-Claude process identity and exact OCI/runtime acceptance.

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

The tmux 3.6a reapply repair now has exact bounded live-component evidence, but **whole-product PASS is not claimed**. The exact product still requires authorized isolated full-path evidence: exact OCI build/image identity, startup/readiness, real Clerk JWT plus browser WebSocket PTY, authenticated native Claude Code for both user homes, managed hook lifecycle, UnifiedDB persistence/recovery, accepted effect/EntityOS behavior where admitted, and live dual-session concurrency/generation fencing.

GitHub-hosted Actions are not runtime evidence when jobs fail before visible execution. Vercel deployment state alone is likewise not runtime PASS; the evidence above comes from the actually started Sandbox command/assertion path.

## Local isolated source checks

Where an **authorized** isolated Python environment is available:

```bash
python -m pytest -q
PYTHONPATH=. CLAYVERSE_STATE_ROOT=/tmp/clayverse-state python -m clayverse.service --once
```

These source checks do not substitute for an exact container build/runtime gate.

## Container source

`Dockerfile` + `compose.yaml` define the single runtime container. The Docker build context is default-deny and allowlists only consumed product inputs, including the runtime Claude contract and digest-bound staged EntityOS artifact. Persistent ClayVerse state and workspace are externalized as scoped volumes, while the application image runs non-root with a read-only root filesystem in Compose, `no-new-privileges`, and dropped Linux capabilities.
