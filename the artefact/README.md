# the artefact — ClayVerse single-container candidate

Canonical product workspace for ClayVerse: **one immutable OCI/Docker-compatible ClayVerse image** implementing one persistent central entity with UnifiedDB as canonical durable authority.

## Current product state

- Program: **ClayVerse single-container**
- Stage: **CLAYVERSE_ARTIFACT**
- Acceptance: **IN_PROGRESS** — no whole-product PASS is claimed.
- Release object: **one exact immutable ClayVerse OCI image digest**.
- UnifiedDB is canonical state/world/memory/data/wiki authority; ClayGraph is derived/rebuildable only.
- Gabriel and Andreas are equal-rights perspectives into the same central entity and one global live generation.
- Complete accepted EntityOS is mandatory inside the final image but is not the product endpoint.
- Root filesystem is read-only; durable writes are limited to declared persistent state/workspace surfaces and scratch to bounded tmpfs/RAM.
- Claude Code remains the managed interactive terminal-native product surface where admitted; token/API models remain inference only and never become state/effect authority.
- `consciousness_daemon` is excluded.

## Canonical machine loop

`INGRESS -> UnifiedDB canonicalize/record -> retrieval/context -> selected LLM -> response re-ingested -> policy/authority validation -> EffectGate/EntityOS -> managed result -> UnifiedDB causal re-entry -> repeat -> EGRESS`

Model output never self-authorizes execution.

## Outer isolation

Final acceptance requires the exact accepted OCI digest behind an **independent guest-kernel VM/microVM boundary**.

The Kubernetes/Kata reference profile remains a deployment option and must retain its fail-closed contracts: default-deny networking, current-supported runtime/hypervisor configuration, read-only root, declared volumes, no host authority, distinct `/healthz` liveness and `/readyz` readiness, image-authoritative EntityOS identity, and real Tier-2 full sandbox/VM replacement rather than an in-place container restart. Its state/workspace PVCs now use `ReadWriteOncePod`, not node-scoped `ReadWriteOnce`; final Kubernetes evidence must identify an admitted CSI stack that actually enforces single-Pod writable attachment and must show that an overlapping stale/replacement Pod cannot acquire the same writable ClayVerse claims.

For the mandatory final sandbox acceptance run, the **Vercel Sandbox Firecracker microVM itself may serve as the independent guest-kernel envelope** when its guest identity/kernel is attested and the exact accepted ClayVerse OCI digest runs inside it through Docker/OCI runtime. A second nested KVM guest is not required merely to satisfy the guest-kernel invariant.

## Final test of tests — mandatory owner gate

Current authority:

`research_entity/global/CLAYVERSE_FINAL_SANDBOX_TEST_OF_TESTS_DIRECTIVE.md`

The final acceptance test is a real end-to-end execution:

`Vercel Sandbox Firecracker microVM`
`-> securely acquire/verify exact private source as required`
`-> build/reproduce exact ClayVerse OCI digest`
`-> Docker/OCI runtime inside the Sandbox guest`
`-> run EXACT accepted ClayVerse image`
`-> retrieve Mistral API token at runtime from approved Vault/secret store`
`-> inject token transiently into ClayVerse`
`-> real Mistral cognition through canonical UnifiedDB turn`
`-> response re-ingested before any effect`
`-> safe EffectGate/EntityOS round-trip`
`-> causal outcome re-entry`
`-> persistence + two-user/global-generation checks`
`-> Tier-1 recovery`
`-> full appliance/Sandbox recreation from SAME image digest`
`-> UnifiedDB/WAL/snapshot/EffectJournal recovery under new generation`
`-> reacquire Mistral token from Vault`
`-> reject stale results / no blind replay`
`-> real Mistral cognition again after recovery`
`-> final auth/terminal/concurrency gates`
`-> WHOLE_CLAYVERSE_PASS only if the complete admitted vector succeeds`.

`fully functional` means this integrated path actually operates. A green build, a live process, one direct API response, one component test or one container-only run is insufficient.

## Mistral provider/secret law

Mistral is now a **mandatory token/API inference provider for the final test-of-tests**.

- credential is acquired at runtime from the approved Vault/secret store;
- credential is transient and never committed, baked into the image, persisted in UnifiedDB/ClayGraph/snapshots/workspace, or written to logs/receipts;
- secret is reacquired after full appliance recreation rather than recovered from ClayVerse state;
- Mistral receives no direct PTY/filesystem/EntityOS/EffectGate authority;
- Mistral output is bound to the same canonical turn/session/global generation and re-ingested before action authority;
- a direct Mistral API call outside ClayVerse creates no product evidence.

Existing Claude Code/GLM research lanes remain bounded functionality unless separately superseded. The Mistral final gate does not fork ClayVerse or introduce another canonical authority.

## GitHub source-token correction

Current authority:

`research_entity/global/VERCEL_SANDBOX_GITHUB_READ_TOKEN_FORWARDING_DIRECTIVE.md`

The former rule **"GITHUB_READ_TOKEN must never enter the Sandbox" is superseded**.

A scoped read-only `GITHUB_READ_TOKEN` **may be securely injected into the authorized disposable Vercel Sandbox** to fetch the exact private Research/EntityOS inputs. It must never be committed, logged, persisted or baked into the OCI image. Exact requested Git/object/artifact identities must be verified before assertions receive provenance credit.

Historical Vercel runs that stopped because the token was absent remain valid historical observations, but token forwarding itself is no longer policy-blocked.

## Runtime details for the final Vercel run

- Vercel Sandbox admission has already been observed through the retained #810 bridge; Sandbox creation itself is not the unresolved product assertion.
- Docker-inside-Sandbox is the intended final test mechanism.
- HTTPS from the inner Docker container must use the admitted trust path for the Vercel Sandbox proxy CA or equivalent, so a TLS infrastructure error is not mislabeled as ClayVerse/Mistral semantic failure.
- Network egress remains narrow/reviewed: only required auth/provider/test paths are opened; representative non-admitted flows remain denied.
- Mistral secret presence is not evidence by itself; real canonical cognition must succeed before and after recovery.

## Retained convergence lanes

- **#611** tmux idempotent-reapply/policy-attestation — exact in-image runtime remains the promotion discriminator.
- **#622** Python hash-lock generator — source candidate; accepted product lock requires real isolated execution.
- **#623** auth/identity/readiness/reauth drift — bounded source/mechanism candidate until exact runtime execution.
- **#602** managed native-Claude process attestation — downstream of exact terminal/runtime acceptance.
- **#810** retained Vercel Sandbox controller — single execution bridge/controller lane; do not create a duplicate controller merely to bypass credentials.

## Current source convergence

Parallel work before this owner update had already strengthened the MicroVM deployment contract around current-supported Kata/runtime/hypervisor identity, runtime-mutating annotation fences, non-root persistent-volume semantics, image-authoritative EntityOS digest binding, and full Pod/Kata-sandbox Tier-2 replacement. Those source changes remain bounded by their own exact receipts; no runtime credit is transferred to later bytes without execution.

This cycle closed two additional deployment-source gaps. The StatefulSet now keeps the normal client-facing `clayverse` Service separate from the required `clayverse-headless` governing Service, and both persistent claims use `ReadWriteOncePod`. The deployment contract and manifest now require the admitted CSI stack to prove the single-Pod writer fence by rejecting an overlapping stale/replacement writable attachment. Durable bounded receipts are `receipts/2026-08-17_GO_2304_STATEFULSET_HEADLESS_GOVERNING_SERVICE_GPT56SOL.json` and `receipts/2026-08-17_GO_2311_RWOP_SINGLE_WRITER_RECOVERY_FENCE_GPT56SOL.json`. These are source/mechanism hardening, not Kubernetes/Kata/CSI runtime PASS.

The Mistral implementation obligation has also progressed beyond documentation: current `clayverse/adapters.py` contains a `MistralInference` boundary and `tests/test_mistral_inference.py` contains deterministic fences for explicit runtime model/secret, fixed API endpoint/JSON mode, secret non-retention, allowed effect-intent shape, `process.exec` rejection, transport-error redaction, and malformed/oversized-response fail-closed behavior. This remains a **source candidate with tests present** until the exact final OCI executes real Mistral cognition with a runtime-acquired secret and repeats it after Tier-2 recreation.

## Testing authority

`TESTING_STRATEGY.md` now makes the final evidence ladder:

`SOURCE_INSPECTED`
`-> STATIC_CONTRACT_PASS`
`-> FOCUSED_TEST_PASS`
`-> ADJACENT_REGRESSION_PASS`
`-> COMPONENT_RUNTIME_PASS`
`-> MULTICOMPONENT_INTEGRATION_PASS`
`-> EXACT_OCI_COMPONENT_PASS`
`-> EXACT_MICROVM_COMPONENT_PASS`
`-> FINAL_SANDBOX_TEST_OF_TESTS_PASS`
`-> WHOLE_CLAYVERSE_PASS`.

A higher class is never inferred from a lower one.

## Current execution frontier

The host-only-token policy blocker is gone, but the latest observed retained Vercel controller run still did not receive the token. Deployment `dpl_G5m2brg1e29g5QysdZxye7Dgkysi` created Sandbox `tomato-weary-porpoise-K4wNz6`, observed a Firecracker guest-kernel identity (`Linux 6.12.76`, `x86_64`) and then stopped before source staging with `github_secret_forwarded_to_sandbox:false` / `BLOCKED_MISSING_GITHUB_READ_TOKEN`. Accordingly, that run earns bounded outer guest-kernel component evidence but **zero private-source or OCI runtime credit**.

The connected Vercel surface available to this organ can inspect projects/deployments/logs but exposes no environment-secret mutation action. The precise next execution step is therefore external to this worker's connected tool authority: provision the scoped read-only `GITHUB_READ_TOKEN` to the retained Vercel Preview/controller environment through an authorized secret-management surface, then retrigger #810. After exact private-source identity is established, continue directly through exact OCI build/runtime, approved Vault Mistral-token acquisition, real canonical Mistral cognition, EffectGate/EntityOS re-entry, full Tier-2 Sandbox/appliance recreation, secret reacquisition, stale-result/no-replay checks, and the final auth/terminal/concurrency vector.

Durable re-entry receipt: `receipts/2026-08-17_GO_2315_VERCEL_FIRECRACKER_MISTRAL_GATE_REENTRY_GPT56SOL.json`.

## Latest cycle delta — 2026-08-17 23:15 +07:00

- refreshed live owner authority and switched the final acceptance target to the current Vercel Firecracker + exact OCI + Vault/Mistral test-of-tests rather than the stale bootstrap interpretation;
- verified that scoped `GITHUB_READ_TOKEN` forwarding is now explicitly authorized, while the latest real retained controller run still lacked the provisioned token;
- observed real Vercel Sandbox guest-kernel evidence (`Linux 6.12.76`, `x86_64`) for deployment `dpl_G5m2brg1e29g5QysdZxye7Dgkysi`, but the run stopped before private-source staging and therefore has zero OCI/product runtime credit;
- repaired StatefulSet governing-Service semantics and added a single-Pod writable PVC recovery fence using `ReadWriteOncePod`, bound through template, deployment contract, manifest, regression and receipts;
- confirmed a current Mistral source adapter plus fail-closed deterministic tests are already present, so the Mistral frontier is now real final-image/provider/recovery execution rather than first implementation;
- no unusual experiment was executed because the cross-worker atomic experiment-lease protocol could not derive a shared immutable trigger identity from this interface and therefore failed closed;
- no whole-product PASS is claimed.

## Verification

ClayVerse remains **IN_PROGRESS**. Whole-product PASS requires the complete exact-digest test-of-tests to execute successfully with durable evidence. Source, documentation, component tests, Sandbox creation and isolated API calls are not substitutes.