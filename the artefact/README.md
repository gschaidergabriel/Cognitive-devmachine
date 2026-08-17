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
- Canonical `main` observed at this revalidation checkpoint: `3cd0e83a88395d09c18c313d5db680cbfba39adc`. Current main has already reflected this branch's managed-Claude/tmux source fusion while keeping canonical product/runtime bytes unchanged.
- PR #611 remains the single retained tmux reapply repair lane. Product promotion is now **OCI-first**: the next admitted batch must build the exact ClayVerse image, capture image digest plus resolved APT/tmux/Python identities, and execute the repair/full transport-policy assertions on the actual in-image tmux. Historical tmux 3.6a remains additional robustness evidence rather than the sole product proxy.
- This retained PR #602 lane is downstream of #611. It preserves #611's exact fail-closed idempotent reapply semantics together with the managed-Claude process/start-argv predicate so later process-attestation work cannot silently reintroduce the predecessor behavior.
- Exact fused source/test blobs already received supporting isolated exact-file execution: **15/15 PASS + `py_compile` PASS**. Evidence class remains `MECHANISM_SUPPORTED_SUPPORTING_EXACT_FILE_EXECUTION`; there is still no full-branch, in-image tmux, native-Claude, OCI or whole-product PASS.
- Live Hypofusion remains open: the actual OCI may resolve a tmux version different from historical 3.6a, and packaged native Claude/tmux may serialize `pane_current_command` or `pane_start_command` differently even for a legitimate managed process.
- Live worker re-entry has been delivered: #602 classified **CONTRADICTS → ADOPT** and contains the fusion; #611 classified **REFINES → NO_CHANGE** for its promotion plan. Durable re-entry record: `research_entity/mesh_feedback/20260817T1725p0700-live-fusion-hypofusion-reentry/REENTRY_20260817T1745_MANAGED_CLAUDE_TMUX36A_GPT56SOL.json`.
- Vercel has strong old-head component evidence but later exact-current attempts remain blocked before a new Sandbox start. The authorized FREE_ONLY Daytona fallback has not reached provider contact from the latest GitHub-hosted admission preflight. These are execution-admission facts, not runtime TEST_FAIL.
- Remaining major acceptance gates: first actually-started authorized isolated OCI batch → refresh `main` → rejoin #611 once → exact image build + digest + APT/tmux/Python identities → repair/full transport attestation on actual in-image tmux + focused/adjacent regressions → canonical Python hash-lock enforcement → #611 promotion decision → rejoin/revalidate #602 → packaged native-Claude process attestation → startup/readiness → real Clerk JWT/browser WebSocket PTY → managed hook lifecycle → persistence/recovery → dual-session concurrency/generation fencing.

### Latest cycle delta

**2026-08-17 17:47 +07:00 — branch status revalidated against live OCI-first frontier; product candidate bytes unchanged**

- Preserved the material #602 code/test fusion already written earlier in this `go`: exact #611 idempotent tmux reapply semantics plus #602 managed-Claude process attestation on one terminal path; no duplicate authority or implementation lane.
- Exact written blobs used for supporting evidence remain: `terminal_sessions.py` `13b895d06d6f99b367e9e6b014a48155d6356095`, timeout regression `08c30cca4452f789aedfc39606d71e3bf058013e`, process-attestation regression `6bfc5cb5a208e85357492ffadff578b1f9f5527d`; isolated exact-file run remains **15 passed in 0.06s + py_compile PASS**.
- Re-entered the new canonical dependency boundary: do **not** treat a 3.6a-only rerun as the primary product gate. The next discriminator is the exact built OCI image and its actual resolved tmux/APT/Python identities, followed by #611 assertions on that in-image tmux.
- Main Living README already incorporated this downstream fusion at `3cd0e83a88395d09c18c313d5db680cbfba39adc`; a duplicate stale write from this organ was rejected by SHA conflict and correctly abandoned as `DUPLICATE/NO_CHANGE` rather than overwriting newer shared state.
- Targeted re-entry comments: #602 `5315020804` (`ADOPT`), #611 `5315022682` (`NO_CHANGE`). Delivery, receiver acknowledgement, use and causal credit remain distinct.
- This organ executed **zero** unusual experiments. Its exact trigger lacks a shared immutable request id and has only minute-precision message metadata, so no valid atomic unusual-experiment lease can be minted for this macro-cycle.
- Whole-product acceptance remains **IN_PROGRESS**.

### Cycle update rule

At the end of every product-convergent cycle:

1. Refresh current `main`, canonical artefact state, relevant receipts and observed execution evidence.
2. Rewrite **Current state** so it reflects the newest canonical reality, removing stale claims.
3. Add or replace **Latest cycle delta** with the concrete changes from that cycle, including code, tests, evidence, blockers and acceptance movement. If nothing canonical changed, write `NO_CHANGE` and why.
4. Never promote source inspection, a PR, CI configuration, deployment `READY`, component evidence or historical evidence into whole-product PASS.
5. Persist the README update in the same branch/PR/fusion cycle as the artefact/evidence it describes. A cycle is not complete while the README is stale.
6. For fast-moving noncanonical feature branches, keep exact branch SHA in the cycle delta/receipt and refresh it immediately before execution; do not make continuous ancestry chasing a substitute for executable evidence.

Git history and bounded receipts remain the detailed audit trail; this README stays compact and reflects the **latest** state rather than becoming a second canonical database.

## Architecture

Current source implements the UnifiedDB/ClayGraph continuity core, equal-rights Gabriel/Andreas identity routing, bounded workspace/causal re-entry, Clerk JWT verification, and the current terminal-pivot surface: browser → Clerk → authenticated WebSocket PTY → user-bound persistent tmux → normal interactive Claude Code CLI. Claude Code built-in tools are disabled in product terminals; a strict local stdio ClayVerse MCP is the admitted state/context/effect bridge. The runtime contract requires each human prompt to enter canonical ClayVerse state through the managed lifecycle and to re-enter through the same causal identity; UnifiedDB remains the durable state/memory authority. Generic host `process.exec` remains fail-closed. EntityOS is a digest-bound internal execution/security/runtime substrate candidate, not the product endpoint, and its external-effect execution remains separately gated.

The previous custom chat API and headless `claude -p` path are retired as product runtime surfaces. `consciousness_daemon` is not part of the target architecture.

## Verification

Focused isolated tests have exercised bounded source mechanisms, including the exact written tmux/process-attestation source/test blobs recorded above, but **whole-product PASS is not claimed**. The exact current product still requires an admitted exact OCI build/dependency/runtime gate, then a current-main/full-checkout process-attestation batch, real Clerk JWT plus browser WebSocket PTY verification, authenticated interactive Claude Code runtime verification for both user homes, managed hook lifecycle, accepted effect/EntityOS behavior where admitted, restart/recovery and live dual-session concurrency/generation fencing.

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
