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

The Kubernetes/Kata reference profile remains a deployment option and must retain its fail-closed contracts: default-deny networking, current-supported runtime/hypervisor configuration, read-only root, declared volumes, no host authority, distinct `/healthz` liveness and `/readyz` readiness, image-authoritative EntityOS identity, and real Tier-2 full sandbox/VM replacement rather than an in-place container restart.

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

The new owner requirements add a separate concrete implementation obligation: **the exact final product image must provide and exercise an admitted Mistral runtime inference/secret path**. Current source/policy convergence alone does not prove that path exists or works.

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

The previous host-only-token policy blocker is gone. The next real execution requires a scoped `GITHUB_READ_TOKEN` to be **available/injectable**, then the retained Vercel path can fetch/verify the exact current private source and execute the final build/runtime sequence.

After exact source/OCI construction, the strongest new product discriminator is the **full Vercel Firecracker + Docker + Vault Mistral end-to-end path**, including Mistral cognition before and after Tier-2 recreation, secret non-persistence, causal effect re-entry, two-user generation fencing and final auth/terminal gates.

## Latest cycle delta — 2026-08-17 23:03 +07:00

- owner explicitly authorized forwarding scoped `GITHUB_READ_TOKEN` into the disposable Vercel Sandbox;
- durable token-forwarding directive committed;
- owner defined the final **test of tests** as Vercel Firecracker microVM + exact ClayVerse OCI + runtime Vault Mistral token + fully functional causal/recovery path;
- durable final test-of-tests directive committed;
- `TESTING_STRATEGY.md` now binds real Mistral inference before/after Tier-2 recovery, Vault secret reacquisition, exact OCI-in-microVM execution and the stronger evidence ladder;
- no whole-product runtime result is claimed from these source/policy changes.

## Latest cycle delta — 2026-08-17 23:10 +07:00

- fresh-main rejoin identified a missing machine-readable bridge between canonical `RecoveryIntegrityError` and the external Tier-2 full-appliance replacer;
- ClayVerse now has a source candidate `clayverse.tier2-fatal/v1` with reserved exit code **86**, allowlisted `RECOVERY_INTEGRITY_ERROR`, SHA-256-only detail binding, `replay_external_effects=false`, and no raw failure-text emission;
- `service.py` maps canonical recovery-integrity failure to that fail-closed exit path and closes UnifiedDB before returning;
- the Kubernetes/Kata reference profile exposes `/dev/termination-log` with `terminationMessagePolicy: File` as bounded diagnostic transport, while **exit 86 remains authoritative even if diagnostic writing fails**;
- exact Git blob identity was matched before isolated execution: signal tests **4/4 PASS**, service dispatch integration **1/1 PASS**, `py_compile` PASS;
- source manifest now binds the Tier-2 fatal signal to the full-sandbox replacement gate;
- this is **mechanism-supported source evidence only**: no outer Vercel controller has yet observed exit 86 and destroyed/recreated the Firecracker Sandbox, and no exact OCI/Mistral/recovery test-of-tests PASS is claimed;
- compatible startup-probe lane #647 must be fused rather than overwritten before promotion.

## Verification

ClayVerse remains **IN_PROGRESS**. Whole-product PASS requires the complete exact-digest test-of-tests to execute successfully with durable evidence. Source, documentation, component tests, Sandbox creation and isolated API calls are not substitutes.
