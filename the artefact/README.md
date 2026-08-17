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

Draft PR **#683** (`gpt56sol/generic-llm-api-provider-20260818`) is the current provider-generalization lane.

It adds:

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
- generic canonical integration tests adapted from the existing Mistral probe.

### Exact focused evidence

The exact current PR #683 `api_providers.py`, exact current `inference_protocol.py` and exact generic provider tests were reconstructed and executed in an isolated OpenAI Linux sandbox. Git blob identities were checked before the run:

- `api_providers.py`: `60a49d31422e00a35c72eb078fe17cc694c0795b`
- `test_generic_api_provider.py`: `79ce6b469d9ac140a28777fdb15b6c2738d6e003`
- `inference_protocol.py`: `cd5856ac58f4e86c4c045fda8099b7783e6724cf`

**15/15 PASS + py_compile PASS.**

Covered: Mistral profile, generic compatible profile, allowed EntityOS intent, forbidden `process.exec`, HTTPS endpoint-smuggling rejection, arbitrary secret-env rejection, non-stop response rejection, HTTP-error secret redaction, malformed/oversized responses, non-finite WORLD rejection, duplicate/non-finite provider JSON rejection, returned-model identity mismatch rejection, runtime credential exclusion from model-visible context, provider credential-echo rejection and redirect refusal.

This is `FOCUSED_TEST_PASS`, not full UnifiedDB integration or runtime PASS.

### Current live-provider boundary

No `MISTRAL_API_KEY` or generic API token is available in this worker's current isolated runtime. Therefore **no real provider request was fabricated or claimed**.

The retained exact-OCI Vercel controller remains fail-closed before credential spend: the newest observed controller head has no accepted current READY deployment, Vercel reports a build-rate-limit failure, and the live PR #682 runtime-freeze head has materially advanced beyond the Research commit currently bound by that controller. The older READY deployment is not eligible for current runtime credit.

The safe next sequence is:

`deliberately settle/freeze current PR #682 product bytes -> rebind the single retained PR #810 controller once -> exact current READY deployment -> transient scoped GitHub read token -> private source + EntityOS fetch inside authorized Sandbox -> full regression -> exact OCI build/digest -> provider Stage 1 -> EffectGate/EntityOS + recovery -> same-digest Tier-2 recreation -> provider cognition again -> Stage 2 Clerk/WebSocket real-user pass-through`.

Runtime/private-source/exact-OCI/live-provider/whole-product credit remains zero until those exact stages actually execute.

## Outer isolation / appliance law

Final acceptance still requires the exact accepted ClayVerse OCI digest behind an independent guest-kernel VM/microVM boundary. The same image must retain read-only root, declared volumes only, no host authority, complete accepted EntityOS, managed Linux terminal and Tier-1/Tier-2 recovery.

A normal container-only provider PASS is supporting evidence only. Final acceptance must prove the same provider-independent ClayVerse laws on the exact accepted image inside the admitted microVM/sandbox envelope.

## Retained convergence lanes

- **#611** tmux idempotent-reapply/policy-attestation — exact in-image runtime remains the promotion discriminator.
- **#622** Python hash-lock generator — source candidate; accepted product lock requires real isolated execution.
- **#623** auth/identity/readiness/reauth drift — bounded source/mechanism candidate until exact runtime execution.
- **#602** managed native-Claude process attestation — downstream of exact terminal/runtime acceptance.
- **#682** dedicated final-Mistral runtime-freeze lane — source candidate still moving; settle deliberately before final controller rebind.
- **#683** generic API inference provider — hardened focused-test candidate; real provider + full canonical integration remain open.
- **#810** retained Vercel Sandbox controller — single OCI orchestration lane; current exact deployment admission remains blocked and old READY evidence is stale.

## Testing authority

`TESTING_STRATEGY.md` remains mandatory. Evidence ladder:

`SOURCE_INSPECTED -> STATIC_CONTRACT_PASS -> FOCUSED_TEST_PASS -> ADJACENT_REGRESSION_PASS -> COMPONENT_RUNTIME_PASS -> MULTICOMPONENT_INTEGRATION_PASS -> EXACT_OCI_COMPONENT_PASS -> EXACT_MICROVM_COMPONENT_PASS -> WHOLE_CLAYVERSE_PASS`.

A higher class is never inferred from a lower one.

## Latest cycle delta — 2026-08-18 00:47 +07:00

- hardened the existing generic provider boundary instead of creating a second inference path;
- added canonical JSON fail-closed handling, duplicate-key rejection and exact returned-model identity;
- fused parallel runtime-secret fences preventing credentials from entering model-visible context or provider output;
- added explicit regressions for all new fences and executed exact focused bytes: **15/15 PASS + py_compile PASS**;
- preserved the result in PR #683 coordination; no live provider or whole-product claim was made;
- Vercel deployment `dpl_EW4vnoqUCTz5bt5otUeUjxox5GBf` reached `vercel-build` on controller commit `533b6d593b4e604cff0164f8b4538a6eda1bc544` and failed source guard on a stale expected endpoint blob; follow-up `05e4eb77780231418f466e7d9cc44936c9c8e7f5` corrects that guard but Vercel reports `Deployment rate limited — retry in 24 hours.`;
- current PR #682 has again materially advanced beyond the Research SHA bound by the latest controller source, so no credential should be spent on an old READY deployment;
- no unusual experiment was executed because shared immutable trigger identity remains unavailable;
- no whole-product PASS is claimed.

## Verification

ClayVerse remains **IN_PROGRESS**. The generic provider boundary is now more strictly fail-closed and has stronger exact focused evidence, but the real product discriminator remains the exact current one-container/microVM run with private source, complete EntityOS, exact OCI digest, real provider cognition, recovery/recreation, and authenticated user-path validation.
