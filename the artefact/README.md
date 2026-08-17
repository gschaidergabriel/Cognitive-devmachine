# the artefact — ClayVerse single-container candidate

Canonical product workspace for ClayVerse: **one immutable OCI/Docker-compatible ClayVerse image** implementing one persistent central entity with UnifiedDB as canonical durable authority.

## Current product state

- Program: **ClayVerse single-container**
- Stage: **CLAYVERSE_ARTIFACT**
- Acceptance: **IN_PROGRESS** — no whole-product PASS is claimed.
- Release object: **one exact immutable ClayVerse OCI image digest**.
- Final runtime: exact image inside an independent VM/microVM guest-kernel envelope.
- UnifiedDB is canonical state/world/memory/data/wiki authority; ClayGraph is derived/rebuildable only.
- Complete accepted EntityOS is mandatory inside the final image but is not the product endpoint.
- Root filesystem is read-only; durable writes are limited to declared persistent state/workspace surfaces and scratch to bounded tmpfs/RAM.
- Gabriel and Andreas are equal-rights perspectives into the same central entity/global generation.
- Snapshot/WAL/EffectJournal recovery must self-heal without blind external-effect replay.

## Canonical machine loop

`INGRESS -> UnifiedDB canonicalize/record -> retrieval/context -> selected LLM -> response re-ingested -> policy/authority validation -> EffectGate/EntityOS -> managed Linux PTY/tmux execution when admitted -> stdout/stderr/result -> UnifiedDB causal re-entry -> repeat -> EGRESS`

Model output never self-authorizes execution.

## Deterministic autonomy candidate

Autonomous goal pursuit is now specified as a **canonical state-machine contract**, not a model identity claim. The source-candidate controller in `clayverse/autonomy.py` stores bounded goal state inside UnifiedDB, adopts durable objectives only from canonical owner `user` turns, generation-fences stale work, limits steps/retries/effects, preserves `UNKNOWN`, and accepts completion only from an independent verified EffectJournal outcome or explicit owner acknowledgement.

`CLAIM != EVIDENCE`, `PROPOSAL != EXECUTION`, and `MODEL_COMPLETION != GOAL_COMPLETION` are architectural laws. Calling the cognition model "autonomous" or "AGI" grants no capability. The scheduler primitive is `next_runnable()` and must be fused into the existing ClayVerse supervisor/re-entry path; no second consciousness/autonomy daemon is admitted. See `AUTONOMY_ARCHITECTURE.md`.

## LLM provider law

Current authority:

`research_entity/global/CLAYVERSE_GENERIC_LLM_PROVIDER_DIRECTIVE.md`

ClayVerse is **provider-agnostic** at the cognition boundary.

- **Claude Code** remains the preferred native terminal provider: normal interactive CLI inside the managed PTY/tmux continuum, authenticated through its direct terminal login/session flow.
- **Token/API models** use bounded audited inference adapters. They receive inference authority only — never terminal, filesystem, EntityOS, EffectGate, memory or identity authority.
- Mistral is the **first concrete API acceptance/test profile**, not a unique ClayVerse authority.
- GLM or another API may be added through the same provider contract; APIs with different wire protocols receive explicit audited adapters rather than arbitrary runtime plugin code.
- Provider switching must preserve the same UnifiedDB turn/session/global generation and must never fork the entity.
- Provider credentials are transient secrets and never enter UnifiedDB, snapshots, receipts, logs, image layers or model-visible context.

The older statement that Mistral is the unique mandatory final product provider is superseded.

## Two-stage API-provider acceptance

### Stage 1 — direct/internal provider injection

First inject a provider token transiently into an authorized disposable sandbox and run the provider directly through the canonical ClayVerse causal spine:

`UnifiedDB/context -> provider -> response -> UnifiedDB pre-effect re-ingest -> generation check -> optional safe EffectGate/EntityOS effect -> causal result re-entry`.

Capture every useful **sanitized** artifact: provider/model identity, request/response digests, turn/session/workspace/causal IDs, global/session generation, EffectJournal/effect IDs, terminal stdout/stderr/exit status for admitted effects, state checkpoint/hash, recovery/failure events and process logs. Provider tokens are excluded from all captures.

Stage 1 gives no Clerk/browser auth credit and no whole-product PASS.

### Stage 2 — real-user pass-through

Only after Stage 1 succeeds, run the same selected API provider through the normal authenticated user path:

`Clerk -> WebSocket -> canonical user-bound ClayVerse PTY/tmux/session -> same UnifiedDB generation -> selected API provider -> response re-ingest -> EffectGate/EntityOS -> result re-entry -> user-visible output`.

This is the requested "wie ein echter User" discriminator. It must prove that swapping Claude cognition for an API provider does not bypass or change identity, state, terminal, effect, persistence, recovery or concurrency laws.

## Generic API runtime lane

The generic API-provider work originally developed in Draft PR **#683** was fused through the retained runtime-convergence lineage and is now part of the immutable runtime candidate in Draft PR **#686**. PR #683 is closed and is not a separate canonical runtime path.

The fused provider boundary includes:

- a generic bounded `chat-completions-json-v1` adapter;
- a fixed Mistral profile using the official Mistral chat-completions endpoint and `MISTRAL_API_KEY`;
- a configurable OpenAI-compatible profile using a dedicated `CLAYVERSE_LLM_API_TOKEN` secret;
- fixed HTTPS endpoint validation, redirect refusal and secret-redacted failure behavior;
- canonical JSON fences rejecting non-finite values and duplicate object keys;
- exact returned-model versus requested-model identity checking;
- runtime-credential exclusion from model-visible WORLD/observation and provider-response echo fencing;
- the same fail-closed inference decision parser used by ClayVerse (`entityos.exec` / `state.noop`; `process.exec` rejected);
- a generic direct acceptance probe on the existing `ClayVerseEngine` / UnifiedDB / EffectGate source path;
- `python -m clayverse.api_probe_cli` as a direct-provider sandbox entry point;
- focused generic-provider and secret-boundary regression tests.

### Exact focused evidence

At retained PR #682 head `220262b856f024fe43a50098cee557738bf97777`, the following exact blobs were reconstructed and executed in an isolated OpenAI Linux sandbox:

- `api_providers.py`: `60a49d31422e00a35c72eb078fe17cc694c0795b`
- `inference_protocol.py`: `cd5856ac58f4e86c4c045fda8099b7783e6724cf`
- `test_generic_api_provider.py`: `79ce6b469d9ac140a28777fdb15b6c2738d6e003`
- `test_generic_api_provider_secret_boundary.py`: `17e06238c042512039654d75eb22285b29c54f07`

**19/19 PASS + py_compile PASS.**

Covered: Mistral profile, generic compatible profile, allowed EntityOS intent, forbidden `process.exec`, HTTPS endpoint-smuggling rejection, arbitrary secret-env rejection, non-stop response rejection, HTTP-error secret redaction, malformed/oversized responses, non-finite WORLD rejection, duplicate/non-finite provider JSON rejection, returned-model identity mismatch rejection, runtime credential exclusion from model-visible context, provider credential-echo rejection, visible-ASCII token enforcement and redirect refusal.

This is `FOCUSED_TEST_PASS`, not full UnifiedDB integration or runtime PASS. It does not automatically validate the later immutable PR #686 freeze or the complete appliance path.

### Current live-provider / Tier-2 boundary

The immutable runtime candidate is now Draft PR **#686** at exact head `9dd7da1c7f1d2acf29142a74effd2b51282661f7` / tree `47c09ff6d661b3da02743435dd8a343ddef85efd`. Runtime and whole-product credit for that exact freeze remain zero.

The single retained Vercel controller is Draft PR **#810**. A parallel two-stage source candidate attempted to preserve the Tier-2 transfer by restoring a source snapshot into a distinct carrier Sandbox before source deletion, then snapshotting that carrier into a distinct replacement Sandbox. This is materially stronger than direct `snapshot -> delete source -> restore`, but it is still only a source candidate.

The newest relevant official Vercel lifecycle guidance says Sandbox snapshots are tied to the Sandbox that produced them and that deleting that Sandbox deletes its snapshots; Vercel Drives have an independent lifecycle, but Drives are private beta and are not assumed authorized. Older snapshot documentation demonstrates snapshot restore and reuse but does not override this newer delete-lifecycle statement. Therefore **direct snapshot/delete/restore is not an admitted independent durable-carrier mechanism**.

The retained PR #810 Tier-2 source guard has correspondingly converged fail-closed: snapshot-only and fork-only replacement are forbidden for full Tier-2 credit and an independent durable carrier is required. The observed two-stage carrier-Sandbox candidate additionally needs crash-safe, independently recoverable handoff identity before it can be promoted; a random carrier name held only by the live controller is insufficient recovery evidence if the controller fails after source deletion.

The current PR #810 exact head is still not deployment-verified. The connected Vercel project shows no newer preview deployment after the stale failed preview that died in build/source-guard admission; no source-guard, exact-OCI, live-provider or Tier-2 runtime credit is transferred from older READY deployments.

No current authorized Vercel runtime log indicates an already-running replacement acceptance sequence that can be resumed. Daytona remains an authorized fallback under current project law, but no Daytona execution surface is exposed to this worker. Therefore the current hard frontier is **independent crash-safe Tier-2 carrier + exact execution admission**, not a demonstrated ClayVerse product-runtime failure.

The safe next sequence is:

`bind an authorized independently recoverable Tier-2 carrier without assuming private-beta storage -> run exact current PR #810 source guards -> execute PR #686 private-source/EntityOS fetch in authorized Sandbox -> full regression -> exact OCI build/digest -> provider Stage 1 -> EffectGate/EntityOS + Tier-1 recovery -> destroy old guest only after declared transfer is independently recoverable -> create distinct replacement guest -> remeasure exact declared state/workspace/OCI identities -> fresh provider secret reacquisition -> second cognition -> Stage 2 Clerk/WebSocket real-user pass-through`.

Runtime/private-source/exact-OCI/live-provider/Tier-2/whole-product credit remains zero until those exact stages actually execute.

## Outer isolation / appliance law

Final acceptance still requires the exact accepted ClayVerse OCI digest behind an independent guest-kernel VM/microVM boundary. The same image must retain read-only root, declared volumes only, no host authority, complete accepted EntityOS, managed Linux terminal and Tier-1/Tier-2 recovery.

A normal container-only provider PASS is supporting evidence only. Final acceptance must prove the same provider-independent ClayVerse laws on the exact accepted image inside the admitted microVM/sandbox envelope.

## Retained convergence lanes

- **#611** tmux idempotent-reapply/policy-attestation — exact in-image runtime remains the promotion discriminator.
- **#622** Python hash-lock generator — source candidate; accepted product lock requires real isolated execution.
- **#623** auth/identity/readiness/reauth drift — bounded source/mechanism candidate until exact runtime execution.
- **#602** managed native-Claude process attestation — downstream of exact terminal/runtime acceptance.
- **#682** provider-generalization/runtime-convergence ancestry — bounded exact focused provider evidence; no longer the final immutable runtime identity.
- **#683** closed source-development lane — useful ancestry/evidence only; fused into retained lineage, not a second runtime path.
- **#686** immutable runtime candidate freeze — exact Research identity `9dd7da1c...` / tree `47c09ff6...`; current exact runtime credit remains zero.
- **#810** retained Vercel Sandbox controller — single OCI orchestration lane; independent durable-carrier and exact deployment/runtime evidence remain open gates.

## Testing authority

`TESTING_STRATEGY.md` remains mandatory. Evidence ladder:

`SOURCE_INSPECTED -> STATIC_CONTRACT_PASS -> FOCUSED_TEST_PASS -> ADJACENT_REGRESSION_PASS -> COMPONENT_RUNTIME_PASS -> MULTICOMPONENT_INTEGRATION_PASS -> EXACT_OCI_COMPONENT_PASS -> EXACT_MICROVM_COMPONENT_PASS -> WHOLE_CLAYVERSE_PASS`.

A higher class is never inferred from a lower one.

## Latest cycle delta — 2026-08-18 01:39 +07:00

- refreshed canonical Research and corrected the immutable PR #686 identity to `9dd7da1c...` / `47c09ff6...`;
- isolated and repaired a real PR #810 build/source-guard defect: a malformed 38-character retained `RESEARCH_SHA` marker was corrected to the runner's valid 40-character SHA at controller commit `b699ea2c5db4d9f69dd3b222bc4891e0a4d88563`;
- observed the stale pre-fix Vercel preview fail on that exact malformed marker before any ClayVerse product runtime executed, so the failure receives controller/build-admission classification only;
- corrected a conflicting snapshot-lifecycle overclaim using newer official Vercel guidance: direct snapshot/delete/restore is not admitted because snapshots are tied to the producing Sandbox lifecycle;
- observed PR #810 converge its Tier-2 guard to `INDEPENDENT_DURABLE_CARRIER_REQUIRED_SNAPSHOT_AND_FORK_FAIL_CLOSED`;
- retained the two-stage carrier-Sandbox idea only as a candidate requiring crash-safe independently recoverable identity/handoff evidence;
- checked the connected Vercel deployment list and found no new exact-head preview after the stale failed preview; runtime credit remains zero;
- no owner secret or provider credential was used, no second canonical path was created, and no product semantic bytes were changed by this organ;
- the globally shared unusual-experiment slot was already consumed before this organ joined this macro-cycle, so no second unusual experiment was created;
- durable receipt: `the artefact/receipts/2026-08-18_GO_PR810_SHA_GUARD_AND_TIER2_CARRIER_FENCE_GPT56SOL.json`;
- no whole-product PASS is claimed.

## Verification

ClayVerse remains **IN_PROGRESS**. This cycle produced one concrete controller repair and removed a false Tier-2 promotion path. The next exact discriminator is a crash-safe independent carrier bound to the single retained PR #810 controller, followed by an exact-head authorized isolated run of the immutable PR #686 source/OCI/provider/recovery path. Source candidates, deployment READY states and historical component evidence remain insufficient for whole-product PASS.

## Latest cycle delta — 2026-08-18 01:46 +07:00

- **NO_CHANGE to canonical ClayVerse product/runtime bytes** in this cycle; the immutable runtime candidate remains PR #686 at `9dd7da1c7f1d2acf29142a74effd2b51282661f7` / tree `47c09ff6d661b3da02743435dd8a343ddef85efd`.
- retained a non-beta Tier-2 design candidate that transfers only a deterministic chunked/hash-bound declared state/workspace/exact-OCI archive through a disposable data-only carrier, then requires a fresh nonpersistent replacement instead of snapshot/fork inheritance;
- recorded the fresh-replacement tooling counterhypothesis: a clean replacement cannot silently depend on Docker/build tooling inherited from the destroyed guest;
- adversarially found that PR #810 temporarily reintroduced snapshot-derived final replacement and a stale Tier-2 network-policy shape; the retained Tier-2 guard subsequently returned to `INDEPENDENT_DURABLE_CARRIER_REQUIRED_SNAPSHOT_AND_FORK_FAIL_CLOSED`.
- at last exact-head source inspection, the higher-level source guard still required carrier-snapshot markers that the Tier-2 guard forbids, so the mandatory guard chain is fail-closed/unsatisfiable until both guards bind the same independent-carrier contract.
- exact-current Vercel execution remains blocked at deployment admission by the free deployment-rate limit; Daytona fallback is authorized but this worker has neither an exposed provider path nor an admitted `DAYTONA_API_KEY` path, so no isolated product runtime started.
- no provider credential was used, no unusual experiment was added by this organ, and runtime/Tier-2/whole-product credit remains zero.
- durable receipt: `the artefact/receipts/2026-08-18_GO_TIER2_DECLARED_TRANSFER_CLEAN_CARRIER_GPT56SOL.json`.
- no whole-product PASS is claimed.

## Latest cycle delta — 2026-08-18 01:59 +07:00

- **NO_CHANGE to canonical ClayVerse product/runtime bytes**; immutable runtime candidate remains PR #686 `9dd7da1c7f1d2acf29142a74effd2b51282661f7` / tree `47c09ff6d661b3da02743435dd8a343ddef85efd`, with runtime and whole-product credit still zero.
- refreshed the moving retained controller and observed PR #810 at `a656cdaff5472bdf95aca24c071cec3997cd8e44`: deterministic carrier identity, `persistent:true` carrier and typed carrier receipt are now implemented, but replacement still inherits a carrier snapshot while Tier-2 guard v14 forbids snapshot/fork inheritance and generic `persistent:true`; exact source gate therefore remains intentionally fail-closed.
- created bounded donor PR #860, head `d46c47ed6276e743d61a29ce5777b0685a75cd8f`, containing a deterministic persistent declared-transfer carrier helper and source guard. The donor creates a **fresh empty `persistent:false` replacement by verified chunk transfer**, not snapshot/fork cloning, and contains no provider/GitHub credential path.
- adversarial review against current first-party Vercel persistence guidance found and repaired a stop/resume race: donor now bounds `SANDBOX_STOPPING` / `SANDBOX_SNAPSHOTTING` / `SANDBOX_STOPPED` transition retries before declaring the carrier persistence boundary verified.
- donor PR #860 remains a source candidate only, intentionally not a second canonical controller path; it must be adjudicated/fused into retained PR #810 and then closed.
- Vercel status for exact retained head `a656cda...` is still `failure` with build-rate-limit target; no exact-head build, guard execution, Sandbox, OCI, provider, Tier-2 or whole-product runtime credit is granted.
- no owner credential was used and no second unusual experiment was consumed.
- durable receipt: `the artefact/receipts/2026-08-18_GO_TIER2_PERSISTENT_CARRIER_DONOR_SOURCE_GPT56SOL.json`.
- no whole-product PASS is claimed.

## Latest cycle delta — 2026-08-18 deterministic autonomy source lane

- added `clayverse/autonomy.py`: canonical goal-state controller backed by UnifiedDB rather than a prompt persona;
- durable goals are copied from canonical owner `user` turns, so cognition cannot invent the durable objective;
- added hard generation, step, retry and effect fences plus `state.noop` / `entityos.exec` capability allowlisting;
- added independent completion contracts: verified EffectJournal outcome or explicit canonical owner acknowledgement;
- model `complete_candidate` is deliberately non-authoritative;
- updated `runtime_CLAUDE.md` so proactive/autonomous behavior never implies hidden AGI status, memory, access or successful effects;
- added `AUTONOMY_ARCHITECTURE.md` defining scheduler fusion into the existing supervisor/re-entry loop and explicitly excluding a second autonomy/consciousness daemon;
- bounded isolated mechanism harness passed 11/11 before commit; the committed exact-current test suite still requires an authorized full-checkout run against canonical `store.py` before promotion;
- source lane does not claim OCI, microVM, live-provider, effect-round-trip or whole-product PASS.
