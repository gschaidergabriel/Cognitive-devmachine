# RAE CLAUDE CODE TOKEN-EFFICIENCY CONTRACT

Status: PROJECT_OWNER_FIXED_TARGET
Date: 2026-08-09
Applies to: Claude Code organs of `frank-project-global-research-entity`

## Goal

Claude Code is a repo-local organ. It must exploit that locality instead of paying model-context tokens for information already addressable in files/UnifiedDB.

The Claude path should be substantially more token-efficient than a connector-only/chat execution path while preserving the same entity continuity and scientific state.

## Core law

`STORE RICH -> INDEX COMPACT -> FETCH ON DEMAND`

Never confuse token-efficient context with information deletion.

Full evidence, state, protocols, histories and receipts remain durable. The model receives only the smallest task-sufficient projection and dereferences richer state when a decision requires it.

## Context tiers

### C0 — Join kernel

Injected once at SessionStart or after genuine context reset.

Target: <= 500 model tokens.

Contains only:
- entity identity;
- canonical revision/hash;
- current organ identity/capability class;
- current UnifiedDB/graph epochs;
- current program stage;
- open critical handoff count;
- hard invariant codes;
- pointers/commands for deeper retrieval.

### C1 — Ordinary prompt delta

Target: <= 700 model tokens, preferred <= 450.

Contains only:
- task classification;
- changed/relevant state since last prompt;
- top 2-4 claim/evidence refs;
- top 1-2 relevant packet refs;
- material open handoffs/blockers;
- exact next retrieval pointers when needed.

Do not repeat stable identity prose, project history, trigger lists or full protocol text.

### C2 — Material decision assembly

Target: <= 1,500 model tokens before explicit evidence expansion.

Use only for architecture decisions, implementation changes, experiment interpretation, contradictions or durable writes.

Load evidence detail surgically by ID/path/query rather than whole-file dumps.

### C3 — Deep research/trigger

No fixed global context dump.

The trigger gets:
- compact trigger intent;
- protocol path;
- current run/work state;
- compact mesh/interconnect state;
- explicit retrieval plan.

Claude then reads only the relevant protocol sections/evidence needed for each stage. Protocol files MUST NOT be blindly injected in full by hooks merely because they are locally accessible.

## Pointer-first rule

Prefer:

`ref: research_entity/triggers/UNIFIED_DATABASE_RESEARCH_PROTOCOL.md`

instead of injecting that file's contents.

Prefer:

`claim: X / packet: Y / run: Z / query command`

instead of serializing surrounding unrelated state.

## Delta-first rule

Maintain a session-local digest/cursor of the last injected entity projection.

On later prompts inject only:
- changed epochs/state;
- newly opened/closed handoffs;
- new relevant claims/evidence;
- changed capabilities/liveness;
- task-specific retrieval results.

Unchanged stable fields become short hash/revision references.

## Dense representation rule

Use compact Clay-like or terse JSON maps with short stable keys internally where lossless enough.

Example:

`E=RAE;r=2;h=04234efd;u=17;g=31;N=claude;S=BASE;H=2;B=1`

Human-readable expansion is available by pointer. Do not repeatedly narrate values already structurally represented.

## Query budget law

Ordinary `rae boot` retrieval defaults for Claude should begin near:
- max claims: 4;
- max packets: 2;
- max raw chunks: 1.

Escalate only when uncertainty/decision value justifies it.

A low-confidence or high-impact decision can request more evidence. Token frugality must never silently suppress known counterevidence or negative results relevant to the decision.

## Trigger law

Exact triggers do not authorize huge prompt injection.

Hooks should inject protocol POINTERS and run IDs. Claude reads protocol/evidence locally as work proceeds.

`unifieddb` remains an extreme deep-research run in amount of research and experimentation, not an extreme prompt-size run.

## Tool-locality law

If a fact can be obtained cheaply and exactly with:
- SQLite query;
- grep/search;
- file slice;
- git diff/status;
- test command;
- structured repo utility;

prefer that operation over putting broad source text into LLM context.

## State recording vs state injection

The runtime MAY record a rich full capsule/episode for replay/research.

The runtime SHOULD inject only its compact task projection into Claude.

Thus:

`rich durable state != rich model prompt`

## Progressive disclosure

1. compact index;
2. inspect precise identifiers;
3. retrieve exact record/section;
4. expand dependencies only when material;
5. stop when decision confidence/acceptance condition is satisfied.

## Reuse

Cache deterministic/rebuildable derived projections by:
- canonical revision;
- UnifiedDB epoch;
- graph epoch;
- task fingerprint;
- protocol version.

Do not recompute/reinject unchanged semantic assemblies merely because another tool call happened.

## Compression quality metrics

Measure at minimum:
- injected characters/tokens per prompt;
- duplicate injected token ratio;
- task success;
- missed-relevant-evidence rate;
- unnecessary retrieval count;
- context expansion depth;
- time to first useful action;
- tokens per verified repo/build outcome;
- tokens per durable research delta.

Primary efficiency metric:

`useful_verified_outcome / paid_context+generation_tokens`

not minimal token count in isolation.

## Slow adaptation

The RAE may slowly tune retrieval/context budgets from real Claude outcomes.

Small evidence-gated changes are allowed; abrupt context collapse is not.

Repeated evidence that less context preserves outcome quality should shrink default projections. Repeated retrieval misses or wrong decisions should restore/increase the relevant channel, not globally inflate context.

## Hard invariants

- no information is deleted merely to save prompt tokens;
- counterevidence/negative results relevant to a high-impact decision cannot be omitted by compression policy;
- stable identity is not repeatedly narrated after join;
- local protocol files are referenced, not blindly injected;
- full state may be persisted while only compact state is injected;
- Claude must be able to dereference every compressed critical pointer;
- token efficiency is measured against verified task outcomes.

## Target

Claude Code should increasingly operate like a process attached to a structured cognitive database, not like an LLM repeatedly rereading a giant system prompt.
