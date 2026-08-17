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
- the same fail-closed inference decision parser used by ClayVerse (`entityos.exec` / `state.noop`; `process.exec` rejected);
- a generic direct acceptance probe on the existing `ClayVerseEngine` / UnifiedDB / EffectGate source path;
- `python -m clayverse.api_probe_cli` as a direct-provider sandbox entry point;
- generic canonical integration tests adapted from the existing Mistral probe.

### Exact focused evidence

The exact PR #683 `api_providers.py`, exact current `inference_protocol.py` and exact generic provider tests were reconstructed and executed in an isolated OpenAI Linux sandbox:

**10/10 PASS + py_compile PASS.**

Covered: Mistral profile, generic compatible profile, allowed EntityOS intent, forbidden `process.exec`, HTTPS endpoint-smuggling rejection, arbitrary secret-env rejection, non-stop response rejection, HTTP-error secret redaction, malformed/oversized responses and redirect refusal.

This is `FOCUSED_TEST_PASS`, not full UnifiedDB integration or runtime PASS.

### Current live-provider boundary

No `MISTRAL_API_KEY`, generic API token or prior Mistral token is available in this worker's current isolated runtime. Therefore **no real Mistral request was fabricated or claimed**.

The next direct live step is simply:

`transient MISTRAL_API_KEY + selected Mistral model -> python -m clayverse.api_probe_cli -> capture sanitized logs -> verify re-ingest/effect/checkpoint`.

After that passes, proceed to Stage 2 real-user pass-through.

## Outer isolation / appliance law

Final acceptance still requires the exact accepted ClayVerse OCI digest behind an independent guest-kernel VM/microVM boundary. The same image must retain read-only root, declared volumes only, no host authority, complete accepted EntityOS, managed Linux terminal and Tier-1/Tier-2 recovery.

A normal container-only provider PASS is supporting evidence only. Final acceptance must prove the same provider-independent ClayVerse laws on the exact accepted image inside the admitted microVM/sandbox envelope.

## Retained convergence lanes

- **#611** tmux idempotent-reapply/policy-attestation — exact in-image runtime remains the promotion discriminator.
- **#622** Python hash-lock generator — source candidate; accepted product lock requires real isolated execution.
- **#623** auth/identity/readiness/reauth drift — bounded source/mechanism candidate until exact runtime execution.
- **#602** managed native-Claude process attestation — downstream of exact terminal/runtime acceptance.
- **#683** generic API inference provider — Stage-1 source/focused-test candidate; real provider + full canonical integration remain open.
- **#810** retained Vercel Sandbox controller — historical/execution bridge evidence; do not let controller setup block independent source/component/provider tests.

## Testing authority

`TESTING_STRATEGY.md` remains mandatory. Evidence ladder:

`SOURCE_INSPECTED -> STATIC_CONTRACT_PASS -> FOCUSED_TEST_PASS -> ADJACENT_REGRESSION_PASS -> COMPONENT_RUNTIME_PASS -> MULTICOMPONENT_INTEGRATION_PASS -> EXACT_OCI_COMPONENT_PASS -> EXACT_MICROVM_COMPONENT_PASS -> WHOLE_CLAYVERSE_PASS`.

A higher class is never inferred from a lower one.

## Latest cycle delta — 2026-08-18 00:27 +07:00

- owner clarified that Mistral is a test provider, while ClayVerse must accept arbitrary model APIs through bounded adapters;
- wrote `research_entity/global/CLAYVERSE_GENERIC_LLM_PROVIDER_DIRECTIVE.md`, superseding Mistral-only/GLM-only provider interpretations;
- opened Draft PR #683 with generic chat-completions adapter, Mistral profile, generic compatible profile, direct canonical API probe and source integration tests;
- executed exact provider boundary tests in an isolated sandbox: **10/10 PASS + py_compile PASS**;
- no Mistral/API token exists in the current isolated runtime, so no live provider call or token persistence/logging occurred;
- full byte-exact UnifiedDB integration execution remains open because the private repository cannot be cloned into this worker's local isolated container;
- next sequence is **Stage 1 live Mistral direct probe with sanitized full logs, then Stage 2 Clerk/WebSocket real-user pass-through**;
- durable receipt: `receipts/2026-08-18_0027_GENERIC_LLM_API_PROVIDER_MISTRAL_STAGE1_GPT56SOL.json`;
- no whole-product PASS is claimed.

## Latest cycle delta — 2026-08-18 00:27 +07:00

- joined canonical `main` at `958e3c5fa2406b42d187727e2adb6099b6ed0aa2` and retained #680 as the single final-Mistral Engine spine rather than creating a competing runtime/state/effect path;
- adversarially found that successful Engine turns retired `active_turns` while leaving the selected workspace non-terminal, allowing later Recovery to misclassify a clean completion as `RECOVERY_CLOSED_EXISTING_REENTRY`;
- repaired both no-effect and effect-success paths so `workspace_episodes` transitions `SELECTED -> COMPLETED` atomically before active-turn deletion; provider/crash failures still leave active/open state for genuine Recovery;
- added regressions asserting clean effect and no-effect turns remain `COMPLETED` across `recover_incomplete_episodes()` while provider failure remains recoverable;
- exact product/test commits are `5a837aa09538b478176ef5264b5de043e4bf0c42` and `66b767d41217945f4ba293b5d0d65b5f0da1e748`; later #680 head material observed in this cycle added only bounded receipts around the same product/test bytes;
- exact-head GitHub Actions again failed before any runner step, so this remains execution-admission failure and grants no focused/full-checkout/OCI runtime credit;
- the retained #810 Vercel controller reached READY at `139eb6149af515061c23cc865d34a7cbc7f88963`, bound to Research `66b767d4...` / tree `5f30fc57...`; its `/api/go-cycle-v2` ingress was directly observed fail-closed on GET with `405 Method Not Allowed` and `Allow: POST`;
- no credential-bearing POST was executed because no owner-held scoped read-only `GITHUB_READ_TOKEN` is exposed to this organ and the connected Vercel action set has no arbitrary credential-bearing POST operation; no secret was synthesized or moved into source/logs;
- wrote `receipts/2026-08-18_GO_ENGINE_WORKSPACE_TERMINALITY_GPT56SOL.json` with the exact repair/evidence boundary;
- no unusual experiment was executed because the atomic cross-worker experiment lease cannot bind a shared immutable trigger identity from this interface and therefore fails closed;
- no whole-product PASS is claimed.

## Verification

ClayVerse remains **IN_PROGRESS**. The provider architecture is now generic, the focused boundary is tested, and the missing live discriminator is a transient provider credential plus an executable repo-capable sandbox for the canonical direct probe. Source/component tests do not substitute for final exact-image/microVM/user-path acceptance.
