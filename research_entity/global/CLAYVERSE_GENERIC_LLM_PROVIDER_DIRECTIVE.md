# CLAYVERSE GENERIC LLM PROVIDER DIRECTIVE

**Authority date:** 2026-08-18 00:27 +07:00  
**Authority:** newest explicit owner directive. This supersedes any older ClayVerse text that makes Mistral, GLM or another token/API model a unique mandatory product provider.

## Product law

ClayVerse is designed around the native **Claude Code terminal path**, but its cognition boundary MUST NOT be coupled to Claude or to any one remote model provider.

The one ClayVerse entity, UnifiedDB authority, EntityOS execution boundary, EffectGate/EffectJournal, terminal continuum, snapshots/recovery and ingress/egress laws remain identical regardless of which admitted inference engine is selected.

Two provider families are admitted:

1. **Claude Code native terminal provider** — normal interactive Claude Code CLI running inside the managed ClayVerse PTY/tmux continuum and authenticated through its direct terminal login/session flow.
2. **Generic token/API providers** — remote or local model APIs that implement an explicitly audited ClayVerse inference adapter. Mistral is the first real acceptance/test profile. GLM and other APIs are examples of additional providers, not separate architectures.

## Generic API contract

A token/API provider has inference authority only.

Canonical loop:

`UnifiedDB/context -> selected API adapter -> provider -> response -> ClayVerse re-ingest -> policy/authority validation -> EffectGate/EntityOS/managed terminal -> result -> UnifiedDB causal re-entry`

Provider output MUST be persisted/re-ingested as a proposal before any requested effect is admitted. A provider response is never an effect receipt and never self-authorizes terminal, filesystem, EntityOS or external actions.

Provider switching MUST NOT fork the entity, session, memory or global generation.

## Adapter law

ClayVerse MUST expose a stable inference-adapter interface so additional APIs can be integrated without changing UnifiedDB, EntityOS, EffectGate or the causal loop.

Providers using the bounded `chat-completions-json-v1` contract may use the shared generic adapter. APIs with different protocols require an explicit audited adapter implementing the same ClayVerse inference result contract.

Dynamic loading of arbitrary unreviewed provider code is forbidden. "Any API" means the core architecture is provider-independent and new protocols can be added through bounded adapters, not that arbitrary remote code receives execution authority.

## Secret law

Provider credentials are transient runtime secrets.

- never commit or bake them into the OCI image;
- never persist them in UnifiedDB, ClayGraph, snapshots, workspace, receipts or logs;
- never expose them to EntityOS commands or model-visible context;
- inject them only through the admitted runtime secret boundary;
- reacquire/reinject them after full appliance recreation rather than restoring them from ClayVerse durable state;
- errors/logs may contain status/type/digests but never credential values.

## Mistral first-provider test

Mistral is the first real generic-API acceptance provider because it offers a standard HTTPS chat-completions API with bearer-token authentication. It is a **test profile**, not a unique ClayVerse authority.

The current first-stage configuration is conceptually:

- profile: `mistral`;
- token secret: `MISTRAL_API_KEY`;
- model: explicitly selected at runtime;
- provider response constrained to the ClayVerse decision protocol;
- no direct provider tools/shell/filesystem/EntityOS authority.

A direct Mistral API request outside ClayVerse produces no product evidence.

## Two-stage provider acceptance

### Stage 1 — direct/internal API injection

First test the provider inside an authorized disposable sandbox without the real browser/user ingress. Inject the provider credential transiently and run one or more canonical ClayVerse turns through:

`provider request -> model response -> UnifiedDB pre-effect re-ingest -> generation check -> optional safe EffectGate/EntityOS effect -> causal outcome re-entry`.

Capture all useful **sanitized** logs and receipts: provider/model identity, request/response digests, turn/session/causal/workspace IDs, generations, EffectJournal/effect IDs, terminal stdout/stderr/exit status where an effect runs, checkpoint/state hash, recovery events and failure classifications. Never log the provider token.

Stage 1 grants no Clerk/browser/user-auth credit and cannot produce whole-product PASS.

### Stage 2 — real-user pass-through

Only after Stage 1 succeeds, exercise the same selected API provider through the normal authenticated ClayVerse ingress as a real user:

`Clerk -> WebSocket -> user-bound ClayVerse PTY/tmux/session identity -> same UnifiedDB turn/generation -> selected API provider -> response re-ingest -> EffectGate/EntityOS -> result re-entry -> user-visible output`.

This stage must prove that provider substitution does not bypass or fork the canonical user/session/global-generation, terminal, effect, persistence or recovery laws.

## Final acceptance

Final ClayVerse acceptance is provider-agnostic. Claude Code must satisfy its native terminal contract. At least one admitted token/API provider must satisfy the complete generic provider path, with Mistral currently designated as the first concrete acceptance provider unless a later owner directive selects another.

Any older statement that says `Mistral is the mandatory unique provider`, `GLM is the mandatory unique provider`, or that an API model can bypass UnifiedDB/EffectGate is superseded by this directive.
