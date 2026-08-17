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
- exercised closure commit: `5e5adce0591058608bbd7381ecf570a39b282f0d`
- exercised closure tree: `1e02285d77b08e6edd86f9017d0ceac5db262cf2`
- retained #611 blobs: `c185009f8af84e1288747d8352645777a36b2053` + `b6bb645dd07645f21ca2e5574f8392c9f13beafc`
- predecessor #622 execution blobs: `ad34476c0092b7e724240c927a7cb14858d1a8dc` + `ed77f5c9446295fa973512ddf7e9d11ea3292010`

That exercised closure remains the authority only for the already-observed Sandbox-admission/credential-boundary result. It is stale for future compute because retained #622 advanced.

A **prepared next execution closure** has now been materialized on the existing `go/oci-execution-closure-20260817-1919-sol` lane:

- closure commit: `218b51cad87e3907d1dd45adc7998c736be23cdb`
- closure tree: `f16c87737cf74ef0703a1fc0a51fd99298450cd1`
- base `main` observed at construction: `ce60e3544caceda22ae349021c952328cf62692b`
- parents: current-at-construction main + previous exercised closure `5e5adce…`
- composition: retained #611 two blobs + current #622 `SOURCE_LOCK`/workflow/source-binding-test blobs.

This prepared closure is **SOURCE COMPOSITION ONLY** with zero runtime credit. Living README/receipt/state commits can move repository `main` without changing product-relevant container/test bytes; therefore the controller must still refresh product-relevant identity once immediately before the next real private-source-capable execution rather than chasing every documentation-only head movement.

Current PR810 hardening binds retained-runner blob `1298ca8002704414f86cd0c036d44e5b32be2918`, fences the Sandbox lifetime at **2,700,000 ms** above the retained explicit-step ceiling of **2,490,000 ms**, and at head `a86f4355…` adds a fail-closed Vercel Sandbox-v2 provider-identity contract requiring both `sandbox.name` and the current VM session id. The provider-identity delta is source-only until an actually-started bound deployment observes it.

PR810 has intentionally **not** been rebound yet to `218b51c…`: any source commit on that retained branch auto-triggers a Vercel Preview, and without the required host-side private-GitHub credential that would only repeat the already-established credential failure. Rebind once after credential provisioning (or if product-relevant bytes move again before that run).

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

`refresh/rebind then-current product-relevant Research + #611 + #622 once → exact closure → Sandbox.create → host-side exact private Research + EntityOS source verification → verified archives into disposable Sandbox → reconstruct/attest/reproduce locked EntityOS → stage exact EntityOS → full source regression → exact OCI build → image digest + APT/tmux/Claude/Python identities → deny-all network → in-image #611 transport-policy checks for gabriel/andreas → hardened service --once → execute/materialize/verify #622 canonical Python hash lock including complete generator-bootstrap hash closure → Docker --require-hashes only after accepted lock evidence → rebuild/rebind exact image → #611 promotion → rejoin/revalidate #602 → packaged native-Claude attestation → startup/readiness → real Clerk JWT/browser WebSocket PTY → managed hook lifecycle → persistence/recovery → dual-session concurrency/global-generation fencing`.

Whole-product PASS requires the complete admitted product path. Source inspection, PRs, CI definitions, Vercel build admission, `Sandbox.create`, deployment READY, historical evidence or component PASS do not imply ClayVerse PASS.

### Unusual-experiment accounting

- This `go` has no safely shared immutable request/turn identity for an atomic unusual-experiment lease, so **0 valid unusual experiments** were executed.
- Deterministic source composition, provenance/hash hardening, guard/timeout/provider-identity hardening, provider-state verification and same-lineage replication are ordinary execution/regression work.
- No VPS/self-hosted/production test path and no Together API were used.

### Latest cycle delta

**2026-08-17 19:31 +07:00 — `NO_CHANGE` canonical ClayVerse product/runtime bytes; next OCI execution closure refreshed to current #622 resolver-wheel binding, immediate credential blocker unchanged**

- PR **#622** remains the single retained Python-lock lane at `08f1fe82211676d5140723eeccc225b05bb6ea5f`; its resolver wheel is source-locked before install while transitive generator bootstrap hash closure remains explicitly open.
- Existing exercised OCI closure `5e5adce…` is retained as exact provenance for the already-observed Sandbox-admission/credential result only.
- The existing 19:19 execution-closure lane was advanced to `218b51cad87e3907d1dd45adc7998c736be23cdb` / tree `f16c87737cf74ef0703a1fc0a51fd99298450cd1`, combining current-at-construction `main`, unchanged #611 repair bytes and current #622 `SOURCE_LOCK`/workflow/test blobs. Previous closure ancestry is preserved as second parent.
- PR810 was **not** source-rebound immediately because that would auto-trigger another Vercel Preview while `GITHUB_READ_TOKEN` is still absent, producing retry-only compute with no new discriminator. Rebind exactly once after the approved host-side Preview credential exists and after one final product-relevant-byte refresh.
- Strongest actual runtime evidence remains `Sandbox.create=PASS_CREATED` followed by fail-closed missing host-side `GITHUB_READ_TOKEN` before private source fetch; source/OCI runtime credit remains **0**.
- Same-tree auxiliary closure duplication created during concurrent fusion was anti-entropically collapsed back onto the already-fused execution identity before this new #622 rebind; no second product/controller/resolver authority remains.
- No unusual experiment was executed; no secret was exposed; no VPS/self-hosted/production/Together path was used.
- Durable closure receipt: `the artefact/receipts/2026-08-17_GO_1931_OCI_CLOSURE_REBIND_CURRENT_PR622_GPT56SOL.json`.
- Current supply-chain refinement receipt: `the artefact/receipts/2026-08-17_GO_1929_PYTHON_LOCK_GENERATOR_BOOTSTRAP_TRUST_GPT56SOL.json`.
- Whole-product acceptance remains **IN_PROGRESS**.

### Cycle update rule

1. Refresh current `main`, artefact state, active overlapping PRs/receipts and exact execution evidence.
2. Rewrite this current-state surface so stale dynamic claims are removed.
3. Record the concrete latest-cycle delta; use `NO_CHANGE` when canonical product bytes did not change.
4. Never promote source/component/controller/provider evidence into whole-product PASS.
5. Keep detailed evidence in Git history/receipts rather than making this README a competing state database.
6. Rebind fast-moving execution closures immediately before real compute; distinguish product-relevant byte movement from documentation/receipt-only head churn and do not create retry-only or duplicate semantic paths merely to chase admission.

## Architecture

Current source implements the UnifiedDB/ClayGraph continuity core, equal-rights Gabriel/Andreas perspectives, Clerk JWT verification, browser WebSocket PTY, persistent user-bound tmux, normal interactive Claude Code, managed lifecycle hooks, bounded retrieval/workspace coordination, effect-only MCP/EffectGate, restart/recovery and optional digest-bound internal EntityOS substrate. UnifiedDB remains the sole durable canonical cognition/state authority.

The retired custom chat API/headless `claude -p` path and a separate `consciousness_daemon` are not product runtime surfaces.

## Verification

Authorized isolated evidence exists for multiple bounded source/components, but **whole-product PASS is not claimed**. The exact OCI path has reached Sandbox admission repeatedly and is blocked before private-source staging by the missing host-side read credential. The retained Python lock-generator lane has advanced source-side since the last exercised OCI closure; a refreshed next closure exists but remains unexecuted until the approved credential prerequisite is satisfied.

## Container source

`Dockerfile` + `compose.yaml` define the single runtime container. The build context is default-deny/allowlisted; persistent state/workspace live in scoped volumes. The admitted Compose profile runs non-root with a read-only root filesystem, `no-new-privileges` and dropped Linux capabilities. Supply-chain acceptance remains open until exact build identities and current APT/Python integrity gates are closed.
