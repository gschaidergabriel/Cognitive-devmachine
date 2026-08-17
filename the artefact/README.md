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

- Draft PR **#611** is the single retained tmux idempotent-reapply repair lane. Exact retained blobs: `c185009f8af84e1288747d8352645777a36b2053` + `b6bb645dd07645f21ca2e5574f8392c9f13beafc`.
- Draft PR **#622** is the single retained Python hash-lock generator lane. Exact fused blobs: `ad34476c0092b7e724240c927a7cb14858d1a8dc` + `ed77f5c9446295fa973512ddf7e9d11ea3292010`. No canonical lock bytes are accepted yet and Docker is not yet on `--require-hashes`.
- Draft PR **#602** remains downstream managed native-Claude process attestation after successful in-image #611 validation.
- Dr.-Unterweger draft PR **#810** remains the **single retained OCI/Vercel controller**. Current observed PR head is `a86f4355d02dc34331a3746128b6c3b959977439`. No parallel OCI controller or second EntityOS staging path is admitted.

### Exact current OCI execution identity

Current Research execution closure:

- canonical Research base: `f7eb4df7600b0f4de1a6381a04acf5d1057d8f9b`
- closure commit: `5e5adce0591058608bbd7381ecf570a39b282f0d`
- closure tree: `1e02285d77b08e6edd86f9017d0ceac5db262cf2`
- retained #611 blobs: `c185009f8af84e1288747d8352645777a36b2053` + `b6bb645dd07645f21ca2e5574f8392c9f13beafc`
- fused #622 blobs: `ad34476c0092b7e724240c927a7cb14858d1a8dc` + `ed77f5c9446295fa973512ddf7e9d11ea3292010`

The closure is execution provenance only, not a second permanent product authority.

Current PR810 hardening binds retained-runner blob `1298ca8002704414f86cd0c036d44e5b32be2918`, fences the Sandbox lifetime at **2,700,000 ms** above the retained explicit-step ceiling of **2,490,000 ms**, and at head `a86f4355…` adds a fail-closed Vercel Sandbox-v2 provider-identity contract requiring both `sandbox.name` and the current VM session id. The provider-identity delta is source-only until an actually-started bound deployment observes it.

### Current executable evidence / blocker

The strongest actually-started bound run is Vercel deployment **`dpl_7BkVnngPJUPiVyrqwFarGFZDevAG`** on PR810 controller commit **`2e5505983172e582a50f4f72bebd561bc650ff5a`**.

Observed in that run:

1. Vercel cloned exact controller source, installed dependencies and entered `npm run vercel-build`.
2. **Guard v4** admitted the exact retained-runner source binding, including retained-runner blob `1298ca8…`.
3. **Current-target patch v5** bound Research closure `5e5adce…` / tree `1e02285d…` and the 2,700,000 ms Sandbox budget.
4. **`Sandbox.create` succeeded** (`sandbox_admission=PASS_CREATED`). Provider/Sandbox admission is therefore empirically open for this exact bound run.
5. The controller then failed closed **before private Research/EntityOS source fetch** because `GITHUB_READ_TOKEN` was absent from the Vercel build environment: `source_stage=BLOCKED_MISSING_GITHUB_READ_TOKEN`, error `PRIVATE_SOURCE_STAGE_BLOCKED:GITHUB_READ_TOKEN_MISSING`.
6. The disposable Sandbox was stopped successfully.
7. `source_runtime_credit=0`; `oci_runtime_credit=0`.

This reproduces the same credential boundary already seen on earlier admitted PR810 runs. Classification: **SANDBOX_ADMISSION_PASS_PRIVATE_SOURCE_CREDENTIAL_BLOCK_REPLICATED**.

This is **not** ClayVerse TEST_FAIL. Private source fetch, EntityOS reconstruction, full source regression, OCI build/image digest, dependency inventory, in-image #611 behavior and `service --once` remain unobserved at the current product boundary.

The blocker is now precise: provision **`GITHUB_READ_TOKEN` as an appropriate sensitive Vercel Preview credential for the retained PR810 branch**, without exposing its value and without forwarding it into the Sandbox. Only verified host-side archive bytes may cross the boundary.

### Remaining acceptance path

After that credential prerequisite, continue on the same retained #810 controller:

`exact closure → Sandbox.create → host-side exact private Research + EntityOS source verification → verified archives into disposable Sandbox → reconstruct/attest/reproduce locked EntityOS → stage exact EntityOS → full source regression → exact OCI build → image digest + APT/tmux/Claude/Python identities → deny-all network → in-image #611 transport-policy checks for gabriel/andreas → hardened service --once → execute/materialize/verify #622 canonical Python hash lock → Docker --require-hashes only after accepted lock evidence → rebuild/rebind exact image → #611 promotion → rejoin/revalidate #602 → packaged native-Claude attestation → startup/readiness → real Clerk JWT/browser WebSocket PTY → managed hook lifecycle → persistence/recovery → dual-session concurrency/global-generation fencing`.

Whole-product PASS requires the complete admitted product path. Source inspection, PRs, CI definitions, Vercel build admission, `Sandbox.create`, deployment READY, historical evidence or component PASS do not imply ClayVerse PASS.

### Unusual-experiment accounting

- This `go` has no safely shared immutable request/turn identity for an atomic unusual-experiment lease, so **0 valid unusual experiments** were executed.
- Deterministic source composition, guard/timeout/provider-identity hardening, provider-state verification and same-lineage replication are ordinary execution/regression work.
- No VPS/self-hosted/production test path and no Together API were used.

### Latest cycle delta

**2026-08-17 19:29 +07:00 — `NO_CHANGE` canonical ClayVerse product/runtime bytes; PR810 provider identity fenced source-side, credential blocker unchanged**

- Exact Research closure remains one current-main-at-bind-time composition of #611 + fused #622; no duplicate semantic lane is retained.
- A redundant same-tree execution closure created during the 19:20 coordination race was collapsed back to active closure commit `5e5adce0591058608bbd7381ecf570a39b282f0d`; it does not remain a competing source identity.
- PR810 remains the single retained OCI controller. Current head `a86f4355…` retains the current closure binding, retained-runner blob fence and Sandbox timeout budget, and additionally requires observable Vercel Sandbox-v2 `sandbox.name` + current session id before proceeding.
- No deployment has yet bound head `a86f4355…`; therefore the provider-identity delta receives **zero runtime credit**.
- Latest actually-started bound deployment remains `dpl_7BkVnngPJUPiVyrqwFarGFZDevAG` on `2e550598…`: guard v4, patch v5 and `Sandbox.create` passed, then execution stopped exactly at absent host-side `GITHUB_READ_TOKEN` before private source fetch, with cleanup confirmed and zero source/OCI runtime credit.
- The current discriminator remains credential provisioning, not retry-only controller churn. The connected Vercel tool surface exposes deployment/log/project operations but no environment-variable write action; plugin search found no alternative installed capability for setting the secret.
- No secret was exposed or forwarded. No unusual experiment, VPS, self-hosted/production test, or Together path was used.
- Current credential-boundary confirmation receipt: `the artefact/receipts/2026-08-17_GO_1926_PR810_V5_CREDENTIAL_BLOCK_CONFIRMATION_GPT56SOL.json`.
- Strongest replication receipt: `the artefact/receipts/2026-08-17_GO_1925_PR810_SANDBOX_CREDENTIAL_BLOCK_REPLICATION_GPT56SOL.json`.
- Earlier first-admission receipt: `the artefact/receipts/2026-08-17_GO_1924_PR810_SANDBOX_ADMISSION_PRIVATE_SOURCE_TOKEN_BLOCK_GPT56SOL.json`.
- Whole-product acceptance remains **IN_PROGRESS**.

### Cycle update rule

1. Refresh current `main`, artefact state, active overlapping PRs/receipts and exact execution evidence.
2. Rewrite this current-state surface so stale dynamic claims are removed.
3. Record the concrete latest-cycle delta; use `NO_CHANGE` when canonical product bytes did not change.
4. Never promote source/component/controller/provider evidence into whole-product PASS.
5. Keep detailed evidence in Git history/receipts rather than making this README a competing state database.
6. Rebind fast-moving execution closures immediately before real compute; do not create retry-only or duplicate semantic paths merely to chase admission.

## Architecture

Current source implements the UnifiedDB/ClayGraph continuity core, equal-rights Gabriel/Andreas perspectives, Clerk JWT verification, browser WebSocket PTY, persistent user-bound tmux, normal interactive Claude Code, managed lifecycle hooks, bounded retrieval/workspace coordination, effect-only MCP/EffectGate, restart/recovery and optional digest-bound internal EntityOS substrate. UnifiedDB remains the sole durable canonical cognition/state authority.

The retired custom chat API/headless `claude -p` path and a separate `consciousness_daemon` are not product runtime surfaces.

## Verification

Authorized isolated evidence exists for multiple bounded source/components, but **whole-product PASS is not claimed**. The exact current OCI path has now reached Sandbox admission repeatedly and is blocked before private-source staging by the missing host-side read credential.

## Container source

`Dockerfile` + `compose.yaml` define the single runtime container. The build context is default-deny/allowlisted; persistent state/workspace live in scoped volumes. The admitted Compose profile runs non-root with a read-only root filesystem, `no-new-privileges` and dropped Linux capabilities. Supply-chain acceptance remains open until exact build identities and current APT/Python integrity gates are closed.
