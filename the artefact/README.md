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
- Real terminal evidence: the predecessor reapply mechanism was first falsified under real tmux 3.6a. Authorized Vercel Sandbox deployment `dpl_6z5oXV29Q4TgRonAgs9TaEmxfB5T` then executed terminal blob `c185009f8af84e1288747d8352645777a36b2053` and focused-test blob `b6bb645dd07645f21ca2e5574f8392c9f13beafc` at bound old head `ef61bfb85ab59291c3b0b33d024aa098b1f29089` and passed pre-policy upgrade, already-hardened reapply, new-server second source, direct multi-argv fake-Claude launch, plus fail-closed mixed/unknown/empty diagnostic assertions. Network was deny-all during the candidate test. This is strong **component/mechanism PASS at that bound old head**, not exact-current or whole-product PASS; native Claude and the OCI product image were not tested.
- Supporting exact-file regression: after rejecting a first reconstruction with a blob mismatch for zero test credit, a byte-exact isolated reconstruction recomputed the expected terminal/test Git blobs above and ran `tests/test_terminal_tmux_control_timeouts.py` **9/9 PASS**. This is supporting exact-file source regression only; it used a bounded identity stub and is not full-branch, OCI, native-Claude, or whole-product runtime evidence.
- Retained repair: draft PR #611 remains the single retained tmux-3.6a product repair lane at head `6a27ddab361938b4ab875610b7a51ac9e845c744`, with exactly the same two live-evidenced product/test blobs. It is ancestry-stale after parallel `main` status/Daytona/README movement and remains unpromoted.
- Exact-head admission recheck: a temporary latest-main reconstruction carried the same product blobs at product-bearing head `18291f820474507a642e6429616b2b21d0cbd2ce`. Execution-only Dr.-Unterweger PR #848 bound that head via bridge commit `7900ac2d9ad468150f06092927c90700b4b276a1`, but Vercel rejected it **before build/Sandbox start** with `Deployment rate limited — retry in 24 hours.` Runtime test credit is therefore zero. PR #848 was closed unmerged after recording the blocker; no second product semantics were retained.
- Coordination: duplicate ClayVerse PR #612 is closed unmerged; PR #611 remains the single retained semantic repair lane. No new permanent terminal implementation was created by this cycle.
- Daytona remains the owner-authorized fallback when Vercel is blocked before assertions. The fallback is connector-independent, but this ChatGPT controller currently lacks Daytona DNS egress and an injected `DAYTONA_API_KEY`, so it is blocked before provider contact and contributes zero Daytona runtime credit.
- Remaining major acceptance gates include rejoining the retained two-file repair to then-current `main` when execution admission is available, one exact-head authorized isolated real-tmux rerun, exact OCI build/runtime receipt, real Clerk JWT + browser WebSocket PTY verification, authenticated interactive native Claude Code verification for both canonical user homes, automatic hook lifecycle integration, persistence/recovery, managed-Claude process identity in live tmux, and live dual-session concurrency/fencing.

### Latest cycle delta

**2026-08-17 17:30 +07:00 — `NO_CHANGE` product code; supporting 9/9 regression captured and exact-head Vercel admission blocker proven**

- Rejoined canonical `main` at `6f274dab83836175145d89e68d2ee28a75c32575` and verified its changes since the prior repair evidence fusion touch only Daytona/status/README/receipt paths, with no terminal product overlap.
- Preserved PR #611 as the single retained product repair lane; did **not** create another permanent semantic terminal path.
- Counted the supporting isolated regression only after exact Git-blob recomputation matched terminal `c185009f8af84e1288747d8352645777a36b2053` and test `b6bb645dd07645f21ca2e5574f8392c9f13beafc`; focused timeout/reapply suite: **9 passed, exit 0**. The earlier blob-mismatched reconstruction receives zero credit.
- Built a temporary execution-only exact-head bridge for product-bearing head `18291f820474507a642e6429616b2b21d0cbd2ce`; Vercel status on bridge commit `7900ac2d9ad468150f06092927c90700b4b276a1` is explicitly `Deployment rate limited — retry in 24 hours.` No Sandbox started, so exact-head runtime remains **UNOBSERVED**, not failed.
- Closed temporary Dr.-Unterweger PR #848 unmerged after the admission result. Duplicate ClayVerse PR #612 remains closed; #611 remains the retained repair lane.
- Durable receipt: `the artefact/receipts/2026-08-17_GO_1730_TMUX36A_EXACTHEAD_ADMISSION_EVIDENCE_GPT56SOL.json`.
- No unusual experiment was consumed; all work was deterministic regression/falsifier execution and coordination.
- Whole-product acceptance remains **IN_PROGRESS**. The next exact gate is intentionally deferred until an authorized isolated runner can actually start: rejoin the retained repair onto then-current main, bind that exact head, rerun the real tmux 3.6a discriminator, then rerun focused/adjacent regressions before promotion. After that, advance to managed native-Claude process attestation and exact OCI build/start/readiness/restart.

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

Focused isolated tests have exercised bounded source mechanisms, and real Vercel Sandbox execution has both falsified the predecessor tmux reapply behavior and verified the byte-identical repair component at an older bound head under tmux 3.6a, but **whole-product PASS is not claimed**. Exact current retained repair runtime and the exact current product still require authorized isolated evidence: exact repair rerun, OCI build/image identity, startup/readiness, real Clerk JWT plus browser WebSocket PTY, authenticated native Claude Code for both user homes, managed hook lifecycle, UnifiedDB persistence/recovery, accepted effect/EntityOS behavior where admitted, and live dual-session concurrency/generation fencing.

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
