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

The single retained Vercel controller is Draft PR **#810**. Its current source candidate implements the Tier-2 carrier as:

`sanitize old guest to declared tier2-transfer -> create Vercel Sandbox snapshot -> delete source sandbox -> create distinct persistent:false replacement sandbox from the snapshot -> remeasure declared snapshot/workspace/OCI identities -> generation-fenced recovery -> fresh HCP-WIF provider-secret reacquisition -> second cognition`.

Current Vercel primary documentation explicitly states that deleting a named sandbox removes the sandbox and sessions while snapshots remain until expiry or explicit snapshot deletion. Therefore the earlier claim that sandbox deletion necessarily deletes its snapshots is superseded. The Vercel snapshot is now an **independent post-delete durable-carrier candidate at the platform-lifecycle level**, not runtime proof by itself.

The current PR #810 exact head is still not deployment-verified. Vercel currently reports **`Deployment rate limited — retry in 24 hours.`** for the current head, and the connected project shows no newer preview deployment after the last stale failed preview. No source-guard, snapshot-delete/recreate, exact-OCI or live-provider runtime credit is transferred from older READY deployments.

No current authorized Vercel runtime log indicates an already-running replacement acceptance sequence that can be resumed. Daytona is the authorized fallback execution provider under current project law, but no Daytona execution surface is exposed to this worker. Therefore the current hard frontier is **execution admission**, not a demonstrated Tier-2 semantic failure.

The safe next sequence is:

`restore authorized isolated execution admission (current Vercel deploy capacity or Daytona) -> run exact current PR #810 source guards -> execute PR #686 private-source/EntityOS fetch in authorized Sandbox -> full regression -> exact OCI build/digest -> provider Stage 1 -> EffectGate/EntityOS + Tier-1 recovery -> Vercel snapshot carrier -> delete old sandbox -> create distinct new persistent:false sandbox from the snapshot -> remeasure exact declared state/workspace/OCI identities -> fresh provider secret reacquisition -> second cognition -> Stage 2 Clerk/WebSocket real-user pass-through`.

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
- **#810** retained Vercel Sandbox controller — single OCI orchestration lane; snapshot-carrier source candidate exists, but exact current deployment admission is Vercel build-rate-limited.

## Testing authority

`TESTING_STRATEGY.md` remains mandatory. Evidence ladder:

`SOURCE_INSPECTED -> STATIC_CONTRACT_PASS -> FOCUSED_TEST_PASS -> ADJACENT_REGRESSION_PASS -> COMPONENT_RUNTIME_PASS -> MULTICOMPONENT_INTEGRATION_PASS -> EXACT_OCI_COMPONENT_PASS -> EXACT_MICROVM_COMPONENT_PASS -> WHOLE_CLAYVERSE_PASS`.

A higher class is never inferred from a lower one.

## Latest cycle delta — 2026-08-18 01:37 +07:00

- refreshed canonical Research and corrected the immutable PR #686 identity to `9dd7da1c...` / `47c09ff6...`;
- corrected a false Vercel lifecycle assumption using current primary documentation: manual Sandbox snapshots survive named-sandbox deletion until expiry or explicit snapshot deletion;
- observed PR #810 source convergence from `fork/persistent:true` toward an explicit snapshot carrier followed by source deletion and a distinct `persistent:false` replacement sandbox;
- preserved strict evidence separation: the snapshot carrier is a source/platform-lifecycle candidate only, not Tier-2 runtime PASS;
- observed the current exact PR #810 Vercel status fail closed with `Deployment rate limited — retry in 24 hours.`; no new preview/source-guard/runtime credit exists for that head;
- checked current Vercel preview runtime logs and found no already-running acceptance execution to resume;
- Daytona remains the authorized fallback, but no Daytona execution surface is available to this worker;
- the globally shared unusual-experiment slot was already consumed before this organ joined this macro-cycle, so no second unusual experiment was created;
- no product semantic bytes were changed in this cycle; this README refresh records the current execution frontier and epistemic correction;
- no whole-product PASS is claimed.

## Verification

ClayVerse remains **IN_PROGRESS**. The durable-carrier *availability* blocker has narrowed: Vercel snapshots are a legitimate post-delete carrier candidate according to current platform lifecycle semantics. The exact discriminator is now executable: prove the current PR #810 source guards and then the full snapshot -> delete old guest -> create distinct replacement -> exact-identity restore/recovery -> fresh-provider-cognition path in an authorized isolated runtime. Current Vercel deployment rate limiting prevents that discriminator from running here, and no fallback execution surface is connected.