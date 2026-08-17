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

The Kubernetes/Kata reference profile remains a deployment option and must retain its fail-closed contracts: default-deny networking, current-supported runtime/hypervisor configuration, read-only root, declared volumes, no host authority, distinct `/healthz` liveness and `/readyz` readiness, image-authoritative EntityOS identity, and real Tier-2 full sandbox/VM replacement rather than an in-place container restart. Its state/workspace PVCs use `ReadWriteOncePod`, not node-scoped `ReadWriteOnce`; final Kubernetes evidence must identify an admitted CSI stack that actually enforces single-Pod writable attachment and must show that an overlapping stale/replacement Pod cannot acquire the same writable ClayVerse claims.

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

Mistral is a **mandatory token/API inference provider for the final test-of-tests**.

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

This cycle closed additional deployment-source gaps. The StatefulSet keeps the normal client-facing `clayverse` Service separate from the required `clayverse-headless` governing Service, and both persistent claims use `ReadWriteOncePod`. The deployment contract and manifest require the admitted CSI stack to prove the single-Pod writer fence by rejecting an overlapping stale/replacement writable attachment. Durable bounded receipts include `receipts/2026-08-17_GO_2304_STATEFULSET_HEADLESS_GOVERNING_SERVICE_GPT56SOL.json`, `receipts/2026-08-17_GO_2311_RWOP_SINGLE_WRITER_RECOVERY_FENCE_GPT56SOL.json`, and `receipts/2026-08-17_GO_2300_MICROVM_TIER2_FULL_SANDBOX_REPLACEMENT_GPT56SOL.json`. These are source/mechanism hardening, not Kubernetes/Kata/CSI runtime PASS.

The Mistral implementation obligation has progressed beyond documentation. Current `clayverse/adapters.py` contains the `MistralInference` boundary and the shared `clayverse/inference_protocol.py` accepts only schema-validated `entityos.exec`/`state.noop` effect intents; `process.exec` is rejected before EffectGate. An earlier exact Git slice for the adapter/protocol/test path passed its focused isolated regression; later parallel hardening added redirect refusal and exception-context secret sanitization, so that older focused PASS remains bounded to its exact historical blobs and is not promoted to current-head runtime credit.

The causal spine is now explicitly hardened around the owner-required ordering: `ClayVerseEngine` persists the assistant/provider proposal to UnifiedDB with `phase=pre-effect-reingest`, reasoning generation and workspace episode identity **before** any requested effect can reach EffectGate. A denied effect re-enters afterward as a separate causal/system event. The internal `final_acceptance_probe.py` and `python -m clayverse.service --mistral-once` use the same UnifiedDB/engine/EffectGate path rather than creating a second chat or state authority; the probe serializes only IDs/generations/content hashes and a strictly validated non-secret Mistral receipt, and explicitly grants neither auth credit nor whole-product PASS. Current source tests additionally fence reasoning/session/entity-generation equality, workspace-episode identity and stale-generation rejection. Durable receipt: `receipts/2026-08-17_GO_2249_MISTRAL_CAUSAL_REINGEST_GPT56SOL.json`.

## Testing authority

`TESTING_STRATEGY.md` makes the final evidence ladder:

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

The connected Vercel surface available to this organ can inspect/document the platform but exposes no direct Sandbox create/exec or secret-mutation action. The precise next executable step is external to this worker's connected tool authority: make the scoped read-only `GITHUB_READ_TOKEN` available to the retained Vercel Preview/controller through an authorized secret-management surface, then retrigger #810. Once exact private-source identity is established, continue in the same accepted path through exact OCI build/runtime, approved Vault acquisition of `MISTRAL_API_KEY`, invoke the canonical in-image Mistral probe for a real turn bound to the same turn/session/generation, verify response re-ingestion before EffectGate/EntityOS, perform full Tier-2 Sandbox/appliance recreation from the same digest, recover canonical state under a new generation, reacquire rather than recover the Mistral secret, reject stale/no-replay paths, and execute the required second real Mistral turn.

Durable re-entry receipts: `receipts/2026-08-17_GO_2315_VERCEL_FIRECRACKER_MISTRAL_GATE_REENTRY_GPT56SOL.json`, `receipts/2026-08-17_GO_2300_MICROVM_TIER2_FULL_SANDBOX_REPLACEMENT_GPT56SOL.json`, `receipts/2026-08-17_GO_2320_VERCEL_FIRECRACKER_CREDENTIAL_GATE_RECHECK_GPT56SOL.json`, and `receipts/2026-08-17_GO_2249_MISTRAL_CAUSAL_REINGEST_GPT56SOL.json`.

## Latest cycle delta — 2026-08-17 23:28 +07:00

- refreshed live owner authority and adopted the mandatory final Vercel Firecracker + exact OCI + Vault/Mistral test-of-tests;
- corrected the stale credential interpretation: scoped read-only `GITHUB_READ_TOKEN` forwarding into the disposable authorized Sandbox is allowed, while historical token-missing runs remain valid evidence;
- retained the Tier-2 recovery discriminator: in-place container/Pod restart cannot masquerade as full appliance recovery; the full sandbox/VM identity must change for Tier-2 credit;
- preserved compatible parallel MicroVM hardening instead of overwriting it, including rolling Kata security, headless StatefulSet governance, `ReadWriteOncePod`, CSI/node-local network caveats and image-authoritative EntityOS identity;
- repaired the canonical causal order so the model/provider assistant proposal is re-ingested into UnifiedDB before EffectGate can execute any requested effect;
- fused the Mistral provider into one canonical `adapters.MistralInference` path, removed the transient duplicate path, and preserved parallel redirect/exception-context secret hardening;
- added the internal final-sandbox Mistral probe on the same UnifiedDB/engine/EffectGate path plus `service --mistral-once`; it is deliberately not a second public chat/auth/state authority and explicitly grants `auth_credit:false` / `whole_product_pass:false`;
- added source falsifiers for persisted Mistral receipt identity, reasoning/session/entity generations, workspace-episode identity, required verified effect and stale-generation failure;
- current direct-main commit had no PR-triggered GitHub Actions run, so no CI/runtime credit was inferred for the newest probe bytes;
- the connected Vercel plugin still exposes no Sandbox create/exec or secret-mutation action to this organ, so no final Firecracker/OCI/Vault/Mistral runtime was fabricated;
- wrote `receipts/2026-08-17_GO_2249_MISTRAL_CAUSAL_REINGEST_GPT56SOL.json` with exact evidence boundaries and zero current final-runtime credit;
- no unusual experiment was executed because the cross-worker atomic experiment-lease protocol could not derive a shared immutable trigger identity from this interface and therefore failed closed;
- no whole-product PASS is claimed.

## Latest cycle delta — 2026-08-18 00:19 +07:00

This section supersedes older frontier wording where the source identity differs.

- refreshed canonical `main` to `958e3c5fa2406b42d187727e2adb6099b6ed0aa2` before selecting work;
- rejected another Mistral implementation as the highest-information move because PR #680 already freezes the canonical Mistral Engine spine; the next discriminator is exact integrated execution;
- created provenance-preserving fusion commit `ad9ba42328127b34b634294704dd434ac2522c49`, tree `0f064668db56cbf584bb6bdad5df74e634b6c4e0`, with PR #680 as the full product base and exact retained execution-relevant bytes from #611, #622 and #623;
- deliberately excluded donor README/receipt files so stale coordination text cannot become a competing semantic path;
- persisted `research_entity/receipts/2026-08-18_GO_FINAL_EXECUTION_CLOSURE_GPT56SOL_0019.md` and branch `gpt56sol/go-final-execution-closure-20260818-0019`;
- the retained Vercel PR #810 controller is still bound to the older research closure `5e5adce0591058608bbd7381ecf570a39b282f0d`; it must be rebound to this cycle's final refreshed branch head/tree before any credential-bearing execution is admissible;
- no exact OCI build, OCI digest, Firecracker guest execution of this closure, Vault/Mistral cognition, Clerk browser/PTY acceptance, Tier-2 recreation or whole-product PASS is claimed yet;
- unusual-experiment count for this organ remains `0` because no shared immutable trigger identity/atomic experiment reservation was available; exactly-once semantics therefore fail closed rather than risk duplicate experiment consumption.

## Verification

ClayVerse remains **IN_PROGRESS**. Whole-product PASS requires the complete exact-digest test-of-tests to execute successfully with durable evidence. Source, documentation, focused tests, Sandbox creation and isolated API calls are not substitutes.
