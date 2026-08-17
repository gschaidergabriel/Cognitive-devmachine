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
- Draft PR **#622** is the single retained Python hash-lock generator lane. Current source head is `08f1fe82211676d5140723eeccc225b05bb6ea5f`; current source-lock/workflow/test blobs are `a355fec6fb871a48112c8c0b79b4bf337b3e0644`, `fe31bd52e0d2dd9250cd5e3e9e96df01249bdb51`, and `737a64f025882396d56789cbeb98721e97010c7a`. The `pip-tools` 7.5.3 resolver wheel is now source-locked by SHA-256 before install, but transitive generator bootstrap dependencies remain an explicit open hash-closure gate. No canonical product lock bytes are accepted yet and Docker is not yet on `--require-hashes`.
- Draft PR **#602** remains downstream managed native-Claude process attestation after successful in-image #611 validation.
- Dr.-Unterweger draft PR **#810** remains the **single retained OCI/Vercel controller**. Current observed PR head is `a86f4355d02dc34331a3746128b6c3b959977439`. No parallel OCI controller or second EntityOS staging path is admitted.

### Exact current OCI execution identity

The strongest actually exercised Research execution closure remains:

- canonical Research base at bind time: `f7eb4df7600b0f4de1a6381a04acf5d1057d8f9b`
- closure commit: `5e5adce0591058608bbd7381ecf570a39b282f0d`
- closure tree: `1e02285d77b08e6edd86f9017d0ceac5db262cf2`
- retained #611 blobs: `c185009f8af84e1288747d8352645777a36b2053` + `b6bb645dd07645f21ca2e5574f8392c9f13beafc`
- predecessor #622 execution blobs: `ad34476c0092b7e724240c927a7cb14858d1a8dc` + `ed77f5c9446295fa973512ddf7e9d11ea3292010`

That closure is execution provenance only, not a second permanent product authority. It is now **stale for the next execution attempt** because retained #622 advanced to `08f1fe82…`; the next private-source-capable PR810 run must refresh/rebind once to the then-current Research/#611/#622 identities before spending Sandbox compute.

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

The immediate blocker is precise: provision **`GITHUB_READ_TOKEN` as an appropriate sensitive Vercel Preview credential for the retained PR810 branch**, without exposing its value and without forwarding it into the Sandbox. Only verified host-side archive bytes may cross the boundary. The connected Vercel tool surface currently exposes no environment-variable write action, so this credential prerequisite cannot be completed by the present worker without the secret being provisioned through an approved Vercel secret/environment surface.

### Remaining acceptance path

After that credential prerequisite, continue on the same retained #810 controller:

`refresh/rebind then-current Research + #611 + #622 → exact closure → Sandbox.create → host-side exact private Research + EntityOS source verification → verified archives into disposable Sandbox → reconstruct/attest/reproduce locked EntityOS → stage exact EntityOS → full source regression → exact OCI build → image digest + APT/tmux/Claude/Python identities → deny-all network → in-image #611 transport-policy checks for gabriel/andreas → hardened service --once → execute/materialize/verify #622 canonical Python hash lock including complete generator-bootstrap hash closure → Docker --require-hashes only after accepted lock evidence → rebuild/rebind exact image → #611 promotion → rejoin/revalidate #602 → packaged native-Claude attestation → startup/readiness → real Clerk JWT/browser WebSocket PTY → managed hook lifecycle → persistence/recovery → dual-session concurrency/global-generation fencing`.

Whole-product PASS requires the complete admitted product path. Source inspection, PRs, CI definitions, Vercel build admission, `Sandbox.create`, deployment READY, historical evidence or component PASS do not imply ClayVerse PASS.

### Unusual-experiment accounting

- This `go` has no safely shared immutable request/turn identity for an atomic unusual-experiment lease, so **0 valid unusual experiments** were executed.
- Deterministic source composition, provenance/hash hardening, guard/timeout/provider-identity hardening, provider-state verification and same-lineage replication are ordinary execution/regression work.
- No VPS/self-hosted/production test path and no Together API were used.

### Latest cycle delta

**2026-08-17 19:29 +07:00 — `NO_CHANGE` canonical ClayVerse product/runtime bytes; retained #622 resolver bootstrap trust narrowed source-side, primary OCI credential blocker unchanged**

- PR **#622** advanced on its existing retained lane to `08f1fe82211676d5140723eeccc225b05bb6ea5f`; no second Python resolver/generator authority was created.
- `SOURCE_LOCK.json` on #622 now binds `pip_tools-7.5.3-py3-none-any.whl` to SHA-256 `3aac0c473240ae90db7213c033401f345b05197293ccbdd2704e52e7a783785e`.
- The generator workflow now binds `SOURCE_LOCK.json` itself by SHA into the digest-pinned product Python base, verifies the resolver-wheel digest before installation, installs from the verified local wheel and emits a deterministic installed-generator freeze digest/envelope.
- Strong counterhypothesis retained: this **does not** close transitive generator bootstrap dependencies; complete pre-admission local hash closure is still required before canonical Python lock promotion.
- No new PR622 workflow execution was observed for current head, so the new hardening is **SOURCE CANDIDATE / UNEXECUTED** with zero runtime/acceptance credit.
- Existing OCI closure `5e5adce…` contains the predecessor #622 blobs and must be refreshed/rebound before the next credential-capable PR810 execution. This re-entry supersedes any assumption that the old closure is still exact-current for future compute.
- PR810 remains the single retained OCI controller; latest actually-started bound execution still passed `Sandbox.create` and stopped at absent host-side `GITHUB_READ_TOKEN` before private source fetch. Current global discriminator therefore remains approved credential provisioning, not retry-only controller churn.
- No secret was exposed or forwarded. No unusual experiment, VPS, self-hosted/production test, or Together path was used.
- Current supply-chain refinement receipt: `the artefact/receipts/2026-08-17_GO_1929_PYTHON_LOCK_GENERATOR_BOOTSTRAP_TRUST_GPT56SOL.json`.
- Current credential-boundary confirmation receipt: `the artefact/receipts/2026-08-17_GO_1926_PR810_V5_CREDENTIAL_BLOCK_CONFIRMATION_GPT56SOL.json`.
- Strongest Sandbox replication receipt: `the artefact/receipts/2026-08-17_GO_1925_PR810_SANDBOX_CREDENTIAL_BLOCK_REPLICATION_GPT56SOL.json`.
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

Authorized isolated evidence exists for multiple bounded source/components, but **whole-product PASS is not claimed**. The exact OCI path has reached Sandbox admission repeatedly and is blocked before private-source staging by the missing host-side read credential. The retained Python lock-generator lane has advanced source-side since the last exercised OCI closure and must be rebound before the next accepted run.

## Container source

`Dockerfile` + `compose.yaml` define the single runtime container. The build context is default-deny/allowlisted; persistent state/workspace live in scoped volumes. The admitted Compose profile runs non-root with a read-only root filesystem, `no-new-privileges` and dropped Linux capabilities. Supply-chain acceptance remains open until exact build identities and current APT/Python integrity gates are closed.
