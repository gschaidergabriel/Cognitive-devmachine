# the artefact — ClayVerse single-container candidate

This directory is the canonical product workspace for the current ClayVerse endpoint: **one OCI/Docker-compatible container image** containing one persistent central ClayVerse entity.

## Living cycle status

**Refresh this living state in every product-convergent cycle after canonical evidence/code fusion. A stale README means the cycle is incomplete; detailed evidence stays in Git history and bounded receipts.**

### Current state

- Program: **ClayVerse single-container**
- Stage: **CLAYVERSE_ARTIFACT**
- Acceptance: **IN_PROGRESS** — no whole-product PASS is claimed.
- UnifiedDB is the sole canonical durable cognition/state authority. ClayGraph is derived/rebuildable only. MicroClay adapts retrieval/accessibility, never truth, identity, privacy or effect authority.
- Product path remains Clerk-authenticated browser → authenticated WebSocket PTY → user-bound persistent tmux → normal interactive Claude Code CLI. Claude Code is runtime cognition, not durable canonical memory/identity.
- Effects remain fail-closed through ClayVerse EffectGate/MCP. Generic host `process.exec` is not admitted. EntityOS is an optional digest-bound internal substrate, not the product endpoint.

### Retained terminal / Claude lanes

- Draft PR **#611** is the single retained tmux reapply repair lane. Historical real Vercel Sandbox evidence under tmux 3.6a supports the byte-identical repair only at an older bound head; exact current OCI/in-image behavior remains unobserved.
- Draft PR **#602** is the single downstream managed-Claude process-attestation lane and remains gated on #611 product promotion plus exact packaged native-Claude evidence.

### Exact OCI / supply-chain gate

- Current source uses digest-pinned Python 3.13 slim Trixie, but tmux still resolves through mutable Trixie APT and Python dependencies are not yet installed from an accepted canonical `--require-hashes` lock. Exact image digest, APT/tmux, Claude and Python artifact identities remain **UNOBSERVED**.
- The latest retained execution closure is `f4c91d0129bbcd9d5e83bceb66b44c2e52f517ee` / tree `ff89be29ea79df92edd547b32abce9c7eceb34da`. It contains the retained #611 terminal/test delta plus execution-relevant #622 Python-lock generator delta and is an ephemeral execution closure, not a second product lane.
- Dr.-Unterweger draft PR **#810** remains the single retained OCI/Vercel controller. Current source head `f9d5fcb53167545110f9a2eb10c4747c77112333` also fences the previously unsafe JavaScript-interpolated `dpkg-query` inventory shape by rewriting the two exact occurrences to default `dpkg-query -W`; the supporting mechanism check is source-only. Vercel remains deployment-rate-limited before build/`Sandbox.create`, so exact runtime credit is **0**.
- **EntityOS staging falsifier:** the exact Research archive omits intentionally untracked `the artefact/EntityOS`, while the retained runner requires it before OCI build. The same #810 lane must reproduce EntityOS inside authorized isolated execution from locked source head `79dc06eb4cba7aa3e3f4d1944bf3c2609ca0d21c`, require SHA-256 `32cd4587adbb45292c964b45f5efd4c38873ccd578792557fbf909f1953e1586` and size `9181696`, then stage exactly those bytes into the `f4c91d…` build context. This is source falsification/repair obligation, not an observed Sandbox failure.
- Daytona remains owner-authorized **FREE_ONLY** fallback. Original and fresh rerun both failed pre-Step-1 with no provider contact, so Daytona runtime credit remains **0** and this is not Daytona TEST_FAIL.

### Python supply-chain lane

- The Python hash-lock generator now has exactly **one retained semantic lane: draft PR #622**.
- Draft PR **#621 is superseded by fusion into #622** and is not retained as a second resolver/generator path.
- Fused #622 preserves both unique contracts:
  - generator-only `pip-tools==7.5.3`, with a regression rejecting `7.5.0`, for the Python 3.13 product-base generator;
  - deterministic selected-wheel provenance after `pip download --only-binary=:all: --require-hashes`: `WHEELHOUSE_SHA256_BEGIN/END`, SHA-256 plus basename, ordered under `LC_ALL=C`.
- The fused source-binding regression passed **5/5** in an isolated non-production Python 3.13.5 source slice. This is supporting source/mechanism evidence only. No canonical `requirements.lock.txt` was minted, Docker remains off `--require-hashes`, and OCI/runtime credit is zero.

### Unusual-experiment accounting

- The corrected 18:01 `go` has only minute-precision shared trigger metadata and no immutable shared request/turn id. The atomic lease fails closed: **COORDINATION_BLOCKED_NO_VALID_UNUSUAL_EXPERIMENT**, valid credit **0**.
- No unusual experiment was executed by this fusion lane.

### Remaining acceptance path

First actually-started authorized isolated current-target run:

`same retained #810 lane → Sandbox admission → reproduce/stage exact locked EntityOS → build exact f4c91d… ClayVerse image → capture image digest + APT/tmux + Claude/Python identities → run #611 + service/readiness assertions in-image → execute retained fused #622 generator in exact digest-pinned Python base → require byte-identical hash lock + complete binary wheelhouse + selected-wheel SHA256 manifest → persist canonical requirements.lock.txt → switch Docker install to --require-hashes → rebuild/rebind exact image → rejoin/revalidate #602 → packaged native-Claude → real Clerk/browser PTY → managed hook lifecycle → persistence/recovery → dual-session concurrency/global-generation fencing`

Whole-product PASS requires the complete path. Source inspection, PRs, deployment READY, historical evidence or component PASS do not imply ClayVerse PASS.

### Latest cycle delta

**2026-08-17 18:10 +07:00 — Python hash-lock donors fused into one retained lane; `NO_CHANGE` canonical product/runtime bytes**

- Rejoined moving canonical `main` through `d6faec4187c28a0ec7331f63e1176a3a5ceda924` before the durable fusion write. The newest intervening PR810 change is a non-overlapping controller-source fence and does not alter the Python-lock fusion semantics.
- Adjudicated overlapping drafts **#621** and **#622** as one semantic responsibility. #622 is retained; #621 is superseded instead of creating parallel dependency-resolution semantics.
- Fused Python-3.13-compatible generator tooling and deterministic selected-wheel SHA-256 provenance into one workflow/test contract.
- Supporting isolated source-slice result: **5 passed in 0.05s**, exit 0, Python 3.13.5. Evidence remains bounded to source/mechanism scope.
- Preserved both predecessor receipts append-only and added `the artefact/receipts/2026-08-17_GO_1801_PYTHON_LOCK_LANE_FUSION_GPT56SOL.json`.
- Re-entered the latest parallel OCI state: retained closure remains `f4c91d…`; PR810 head now also fences the dpkg inventory interpolation defect; the same lane still requires locked EntityOS reproduction/staging before image construction. Vercel remains pre-Sandbox rate-limited and Daytona remains pre-provider-contact.
- Did **not** fabricate `requirements.lock.txt`, did **not** switch Docker to `--require-hashes`, and did **not** infer OCI/runtime acceptance from source regressions.
- No unusual experiment was executed. No VPS/self-hosted/production path or Together API was used.
- Whole-product acceptance remains **IN_PROGRESS**.

### Cycle update rule

1. Refresh current `main`, canonical artefact state, relevant receipts and observed execution evidence.
2. Rewrite current state to newest canonical reality; remove stale dynamic claims.
3. Update latest-cycle delta with concrete code/evidence/blocker movement; if canonical product bytes did not change, record `NO_CHANGE` and why.
4. Never promote source inspection, PRs, CI definitions, deployment READY, component evidence or historical evidence into whole-product PASS.
5. Persist this README update in the same fusion cycle as the evidence it summarizes.
6. Rebind fast-moving feature branches immediately before executable acceptance rather than continuously churning ancestry while no runner can start.

## Architecture

Current source implements the UnifiedDB/ClayGraph continuity core, equal-rights Gabriel/Andreas perspectives, Clerk JWT verification, browser WebSocket PTY, persistent user-bound tmux, normal interactive Claude Code, managed lifecycle hooks, bounded retrieval/workspace coordination, effect-only MCP/EffectGate, restart/recovery and optional digest-bound internal EntityOS substrate. UnifiedDB remains the sole durable canonical cognition/state authority.

The retired custom chat API/headless `claude -p` path and a separate `consciousness_daemon` are not product runtime surfaces.

## Verification

Authorized isolated evidence exists for multiple bounded source/components, but **whole-product PASS is not claimed**. Exact current product evidence still requires current-target OCI/image/dependency execution and all downstream auth/Claude/lifecycle/recovery/concurrency gates above.

GitHub-hosted jobs that fail before visible steps and Vercel deployments that never reach Sandbox execution provide zero semantic runtime credit.

## Container source

`Dockerfile` + `compose.yaml` define the single runtime container. The build context is default-deny/allowlisted; persistent state/workspace live in scoped volumes. The admitted Compose profile runs non-root with a read-only root filesystem, `no-new-privileges` and dropped Linux capabilities. Supply-chain acceptance remains open until exact build identities and current APT/Python integrity gates are closed.
