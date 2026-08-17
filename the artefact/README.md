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
- Dr.-Unterweger draft PR **#810** remains the **single retained OCI/Vercel execution controller**. No parallel OCI controller or second EntityOS staging path is admitted.

### Exact current OCI execution identity

The current ephemeral execution closure is based on canonical Research `main` `f7eb4df7600b0f4de1a6381a04acf5d1057d8f9b` and composes exactly the retained #611 + fused #622 execution-relevant bytes:

- closure commit: `5e5adce0591058608bbd7381ecf570a39b282f0d`
- closure tree: `1e02285d77b08e6edd86f9017d0ceac5db262cf2`
- PR810 controller head observed for the admitted run: `5d89ebb4d7a15c679a6c37861fb3a1352cc812df`
- Vercel deployment: `dpl_21efibLYnww6hhrEMp5SAh6enCsQ`

This closure is execution provenance only, not a second permanent product branch or authority.

### Current executable evidence / blocker

The newest PR810 run materially advances the execution boundary:

1. Vercel cloned exact controller head `5d89ebb4…`, installed dependencies and entered `npm run vercel-build`.
2. Guard v3 admitted the retained runner source/provenance contract.
3. Current-target patch v4 rebound the runner to exact Research closure `5e5adce…` / tree `1e02285d…`.
4. **`Sandbox.create` succeeded** (`sandbox_admission=PASS_CREATED`). Therefore the prior Vercel deployment/Sandbox-admission blocker is superseded for this exact run.
5. The controller then failed closed **before private Research/EntityOS source fetch** because `GITHUB_READ_TOKEN` was absent from the Vercel build environment: `PRIVATE_SOURCE_STAGE_BLOCKED:GITHUB_READ_TOKEN_MISSING`.
6. The disposable Sandbox was stopped successfully.

Classification: **SANDBOX_ADMITTED_PRIVATE_SOURCE_CREDENTIAL_BLOCKED_BEFORE_SOURCE_FETCH**.

This is not ClayVerse TEST_FAIL. No private source bytes were fetched, no EntityOS reconstruction ran, no source regression ran, no OCI image was built, no image digest/dependency inventory was produced, and no in-image #611/service assertion ran. `source_runtime_credit=0`; `oci_runtime_credit=0`.

The credential must remain host-side and must never be forwarded into the Sandbox. The next execution prerequisite is to provision `GITHUB_READ_TOKEN` as an appropriate sensitive Preview credential for the retained PR810 execution branch without exposing its value.

### Remaining acceptance path

After the credential prerequisite is satisfied, continue on the same retained #810 controller:

`exact current closure → Sandbox.create → host-side exact private Research + EntityOS source verification → verified archive bytes into disposable Sandbox → reconstruct/attest/reproduce locked EntityOS → stage exact EntityOS into ClayVerse source → full exact source regression → exact OCI build → image digest + APT/tmux/Claude/Python identities → network deny-all → in-image #611 double-reapply + full transport-policy attestation for gabriel/andreas → hardened service --once → execute/materialize/verify #622 canonical Python hash lock → switch Docker to --require-hashes only after accepted lock evidence → rebuild/rebind exact image → #611 promotion decision → rejoin/revalidate #602 → packaged native-Claude attestation → startup/readiness → real Clerk JWT/browser WebSocket PTY → managed hook lifecycle → persistence/recovery → dual-session concurrency/global-generation fencing`.

Whole-product PASS requires the complete admitted product path. Source inspection, a PR, a CI definition, Vercel build admission, `Sandbox.create`, deployment READY, historical evidence or component PASS do not imply ClayVerse PASS.

### Unusual-experiment accounting

- This `go` has no safely shared immutable request/turn identity for an atomic unusual-experiment lease, so the cycle remains **COORDINATION_BLOCKED_NO_VALID_UNUSUAL_EXPERIMENT** with **0 valid unusual experiments executed**.
- Deterministic source composition, provider-state verification and credential-boundary observation are ordinary execution work, not unusual experiments.
- No VPS/self-hosted/production test path and no Together API were used.

### Latest cycle delta

**2026-08-17 19:24 +07:00 — `NO_CHANGE` canonical ClayVerse product/runtime bytes; exact current Vercel Sandbox admission verified and blocker moved to missing host-side private-source credential**

- Refreshed canonical Research and fused the exact execution closure around current `main` + retained #611 + fused #622 bytes. Concurrent CAS prevented duplicate overwrites; one closure tree remains authoritative for this run.
- PR810 was rebound on its retained single controller lane to the exact current closure; no second OCI controller or EntityOS staging implementation was created.
- Vercel deployment `dpl_21efibLYnww6hhrEMp5SAh6enCsQ` reached a real disposable Sandbox. `Sandbox.create` passed.
- The next fail-closed boundary fired correctly because `GITHUB_READ_TOKEN` was not present in the Vercel build environment. Private Research/EntityOS source fetch did not start and the Sandbox was stopped.
- This reclassifies the executable frontier from provider/Sandbox admission uncertainty to one concrete prerequisite: **provision the sensitive Preview private-GitHub read credential, then rerun the same retained controller**.
- No source/OCI runtime credit is awarded yet; whole-product acceptance remains **IN_PROGRESS**.
- Durable receipt: `the artefact/receipts/2026-08-17_GO_1924_PR810_SANDBOX_ADMISSION_PRIVATE_SOURCE_TOKEN_BLOCK_GPT56SOL.json`.

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

Authorized isolated evidence exists for multiple bounded source/components, but **whole-product PASS is not claimed**. The current exact OCI path has now reached Sandbox admission but is blocked before private-source staging by the missing host-side read credential.

## Container source

`Dockerfile` + `compose.yaml` define the single runtime container. The build context is default-deny/allowlisted; persistent state/workspace live in scoped volumes. The admitted Compose profile runs non-root with a read-only root filesystem, `no-new-privileges` and dropped Linux capabilities. Supply-chain acceptance remains open until exact build identities and current APT/Python integrity gates are closed.
