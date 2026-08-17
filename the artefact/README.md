# the artefact — ClayVerse single-container candidate

This directory is the canonical product workspace for the current ClayVerse endpoint: **one OCI/Docker-compatible container image** containing one persistent central ClayVerse entity.

## Living cycle status

**Refresh this living state in every product-convergent cycle after canonical evidence/code fusion. A stale README means the cycle is incomplete; detailed evidence stays in Git history and bounded receipts.**

### Current state

- Program: **ClayVerse single-container**
- Stage: **CLAYVERSE_ARTIFACT**
- Acceptance: **IN_PROGRESS** — no whole-product PASS is claimed.
- UnifiedDB is the sole durable canonical cognition/state authority. ClayGraph is derived/rebuildable only. MicroClay adapts retrieval/accessibility, never truth, identity, privacy or effect authority.
- Canonical user path remains Clerk-authenticated browser → authenticated WebSocket PTY → user-bound persistent tmux → normal interactive Claude Code CLI. Claude Code is runtime cognition, not durable identity/memory authority.
- Effects remain fail-closed through ClayVerse EffectGate/MCP. Generic host `process.exec` is not admitted. EntityOS is an optional digest-bound internal execution/security substrate, not the product endpoint.
- Current build/test/runtime validation remains authorized isolated-sandbox-only. VPS/self-hosted/production testing and Together are forbidden.

### Retained convergence lanes

- Draft PR **#611** is the single retained tmux idempotent-reapply repair lane. Exact retained blobs are `c185009f8af84e1288747d8352645777a36b2053` (`terminal_sessions.py`) and `b6bb645dd07645f21ca2e5574f8392c9f13beafc` (focused test). Historical real-tmux evidence is bounded component evidence only.
- Draft PR **#622** is the single retained Python hash-lock generator lane. Exact fused blobs are `ad34476c0092b7e724240c927a7cb14858d1a8dc` (workflow) and `ed77f5c9446295fa973512ddf7e9d11ea3292010` (source-binding test). It uses generator-only `pip-tools==7.5.3`, double `pip-compile --generate-hashes`, full binary `--require-hashes` download verification and deterministic selected-wheel SHA-256 provenance. No canonical `requirements.lock.txt` is accepted yet and Docker has not been switched to `--require-hashes`.
- Draft PR **#602** remains the downstream managed native-Claude process-attestation lane and stays behind successful in-image #611 validation.
- Dr.-Unterweger draft PR **#810** remains the **single retained OCI/Vercel execution controller**. Current observed head is `036c5e2d4d00df94ab60dcaac001415b4be3d74f`. No parallel OCI controller or second EntityOS staging path is admitted.

### Exact current OCI execution identity

The current ephemeral execution closure is based on canonical Research `main` `f7eb4df7600b0f4de1a6381a04acf5d1057d8f9b` and composes exactly the retained #611 + fused #622 execution-relevant bytes:

- closure commit: `5e5adce0591058608bbd7381ecf570a39b282f0d`
- closure tree: `1e02285d77b08e6edd86f9017d0ceac5db262cf2`
- first admitted PR810 controller head: `5d89ebb4d7a15c679a6c37861fb3a1352cc812df`
- first admitted deployment: `dpl_21efibLYnww6hhrEMp5SAh6enCsQ`
- current PR810 guard-v4 head: `036c5e2d4d00df94ab60dcaac001415b4be3d74f`
- guard-v4 replication deployment: `dpl_HWjU1DGTiXaMcYD4mT5waFsT53Us`
- retained runner exact Git blob bound by guard v4: `1298ca8002704414f86cd0c036d44e5b32be2918`

This closure is execution provenance only, not a second permanent product branch or authority.

### Current executable evidence / blocker

Two actually-started Vercel executions on the same exact Research closure now establish the same boundary:

1. Vercel cloned the exact PR810 controller heads, installed dependencies and entered `npm run vercel-build`.
2. The first admitted run (`5d89ebb4…`) passed guard v3; the current replication (`036c5e2d…`) passed **guard v4**, which additionally verifies the complete retained-runner Git blob before marker checks/wrapper execution.
3. Current-target patch v4 rebound the retained runner to exact Research closure `5e5adce…` / tree `1e02285d…` in both runs.
4. **`Sandbox.create` succeeded in both runs** (`sandbox_admission=PASS_CREATED`). The prior provider/Sandbox-admission blocker is therefore superseded for this exact closure/controller path.
5. Both runs then failed closed **before private Research/EntityOS source fetch** because `GITHUB_READ_TOKEN` was absent from the Vercel build environment: `PRIVATE_SOURCE_STAGE_BLOCKED:GITHUB_READ_TOKEN_MISSING`.
6. The disposable Sandbox was stopped successfully in both runs.

Classification: **SANDBOX_ADMISSION_REPLICATED_PRIVATE_SOURCE_CREDENTIAL_BLOCKED_BEFORE_SOURCE_FETCH**.

The second result is a deterministic same-lineage replication, not independent product validation. It weakens the counterhypothesis that the first credential block was merely incomplete retained-runner source binding, because guard v4 first binds the full retained-runner blob and then reaches the same missing-credential boundary.

This is not ClayVerse TEST_FAIL. No private source bytes were fetched, no EntityOS reconstruction ran, no source regression ran, no OCI image was built, no image digest/dependency inventory was produced, and no in-image #611/service assertion ran. `source_runtime_credit=0`; `oci_runtime_credit=0`.

The credential must remain host-side and must never be forwarded into the Sandbox. The next execution prerequisite is to provision `GITHUB_READ_TOKEN` as an appropriate sensitive Vercel Preview credential for the retained PR810 execution branch without exposing its value. After that, execute the same retained controller once; do not add retry-only commits or a parallel execution path.

### Remaining acceptance path

After the credential prerequisite is satisfied, continue on the same retained #810 controller:

`exact current closure → Sandbox.create → host-side exact private Research + EntityOS source verification → verified archive bytes into disposable Sandbox → reconstruct/attest/reproduce locked EntityOS → stage exact EntityOS into ClayVerse source → full exact source regression → exact OCI build → image digest + APT/tmux/Claude/Python identities → network deny-all → in-image #611 double-reapply + full transport-policy attestation for gabriel/andreas → hardened service --once → execute/materialize/verify #622 canonical Python hash lock → switch Docker to --require-hashes only after accepted lock evidence → rebuild/rebind exact image → #611 promotion decision → rejoin/revalidate #602 → packaged native-Claude attestation → startup/readiness → real Clerk JWT/browser WebSocket PTY → managed hook lifecycle → persistence/recovery → dual-session concurrency/global-generation fencing`.

Whole-product PASS requires the complete admitted product path. Source inspection, a PR, a CI definition, Vercel build admission, `Sandbox.create`, deployment READY, historical evidence or component PASS do not imply ClayVerse PASS.

### Unusual-experiment accounting

- This `go` has no safely shared immutable request/turn identity for an atomic unusual-experiment lease, so the cycle remains **COORDINATION_BLOCKED_NO_VALID_UNUSUAL_EXPERIMENT** with **0 valid unusual experiments executed**.
- Deterministic source composition, provider-state verification, guard hardening and same-path replication are ordinary execution/regression work, not unusual experiments.
- No VPS/self-hosted/production test path and no Together API were used.

### Latest cycle delta

**2026-08-17 19:24 +07:00 — `NO_CHANGE` canonical ClayVerse product/runtime bytes; Sandbox admission replicated under full retained-runner blob binding, blocker remains missing host-side private-source credential**

- Refreshed canonical Research and fused the exact execution closure around current `main` + retained #611 + fused #622 bytes. Concurrent work converged on one retained closure tree rather than creating a second semantic execution lane.
- PR810 remained the single retained controller and advanced from the first admitted head `5d89ebb4…` to current guard-v4 head `036c5e2d…`; guard v4 now binds retained-runner Git blob `1298ca8…` in addition to the existing provenance/marker fences.
- Vercel deployments `dpl_21efibLYnww6hhrEMp5SAh6enCsQ` and `dpl_HWjU1DGTiXaMcYD4mT5waFsT53Us` both reached a real disposable Sandbox and recorded `Sandbox.create=PASS_CREATED` on the same exact Research closure.
- Both then failed closed on absent `GITHUB_READ_TOKEN` before any private Research/EntityOS source fetch; both Sandboxes were stopped. The replication confirms the credential boundary but provides **0 source/OCI runtime credit**.
- The executable frontier is now concrete: **provision the sensitive host-side Vercel Preview private-GitHub read credential, then execute the same retained controller once**. No third retry was started by this organ.
- No unusual experiment was executed because the shared trigger identity is not sufficient for a valid atomic lease. Whole-product acceptance remains **IN_PROGRESS**.
- Primary receipt: `the artefact/receipts/2026-08-17_GO_1924_PR810_SANDBOX_ADMISSION_PRIVATE_SOURCE_TOKEN_BLOCK_GPT56SOL.json`.
- Guard-v4 replication receipt: `the artefact/receipts/2026-08-17_GO_1924_PR810_GUARD_V4_CREDENTIAL_BLOCK_REPLICATION_GPT56SOL.json`.

### Cycle update rule

1. Refresh current `main`, current artefact state, active overlapping PRs/receipts and exact execution evidence.
2. Rewrite this current-state surface so stale dynamic claims are removed.
3. Record the concrete latest-cycle delta; use `NO_CHANGE` when canonical product bytes did not change.
4. Never promote source/component/controller/provider evidence into whole-product PASS.
5. Keep detailed evidence in Git history/receipts rather than making this README a competing state database.
6. Rebind fast-moving execution closures immediately before real compute, but do not create retry-only or duplicate semantic lanes merely to chase provider admission.

## Architecture

Current source implements the UnifiedDB/ClayGraph continuity core, equal-rights Gabriel/Andreas perspectives, Clerk JWT verification, browser WebSocket PTY, persistent user-bound tmux, normal interactive Claude Code, managed lifecycle hooks, bounded retrieval/workspace coordination, effect-only MCP/EffectGate, restart/recovery and optional digest-bound internal EntityOS substrate. UnifiedDB remains the sole durable canonical cognition/state authority.

The retired custom chat API/headless `claude -p` path and a separate `consciousness_daemon` are not product runtime surfaces.

## Verification

Authorized isolated evidence exists for multiple bounded source/components, but **whole-product PASS is not claimed**. The exact current OCI path has now reached Sandbox admission twice on the same closure and is blocked before private-source staging by the missing host-side read credential.

## Container source

`Dockerfile` + `compose.yaml` define the single runtime container. The build context is default-deny/allowlisted; persistent state/workspace live in scoped volumes. The admitted Compose profile runs non-root with a read-only root filesystem, `no-new-privileges` and dropped Linux capabilities. Supply-chain acceptance remains open until exact build identities and current APT/Python integrity gates are closed.
