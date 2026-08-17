# Live Fusion + Hypofusion + Worker Re-entry Directive

**Status:** CURRENT OWNER OPERATIONAL DIRECTIVE  
**Owner instruction:** 2026-08-17 17:25 +07:00  
**Product boundary:** ClayVerse single-container; this directive does not replace `CLAYVERSE_SINGLE_CONTAINER_PRODUCT_DIRECTIVE.md`.

## Owner intent

Fusion and hypofusion are not only manual end-of-run reports. Material new evidence, contradictions, counterevidence, blockers, architecture changes and worker results must be fused back into the live research state and returned to the affected research lanes and active workers while work is still in progress.

## Core law

`OBSERVATION -> LIVE_FUSION -> LIVE_HYPOFUSION_WHEN_MATERIAL -> RESEARCH_REENTRY -> TARGETED_WORKER_REENTRY -> ACK/REVALIDATE -> NEXT WORK`

The loop is bidirectional and recursive. Worker outcomes become new observations and re-enter the same loop.

### Live Fusion

For every **material** delta:

1. refresh current canonical GitHub/research state and current work revision;
2. classify novelty: `NEW | REFINES | CONFIRMS | CONTRADICTS | SUPERSEDES | NO_CHANGE | DUPLICATE`;
3. preserve provenance, evidence class, ancestry and negative evidence;
4. fuse the delta into the supported research/coordination state;
5. identify affected claims, hypotheses, tests, architecture paths, work items, branches and active workers;
6. route a compact targeted feedback envelope to those receivers;
7. require receivers to revalidate their plan before the next material effect when the delta is relevant.

### Live Hypofusion

Hypofusion becomes an **automatic adversarial second lane** when any of these are true:

- a high-impact claim or architecture choice is proposed;
- evidence contradicts current assumptions;
- a promotion/merge/acceptance decision is near;
- stale/shared-ancestry evidence risks pseudo-replication;
- a blocker persists through repeated same-mechanism attempts;
- a result is surprising, OOD, safety/security relevant, or could invalidate active work;
- two or more active workers/PRs appear to implement competing or duplicate semantic paths.

The live hypofusion lane must record at least:

- strongest plausible counterhypothesis;
- evidence that supports or weakens it;
- shared-ancestry/independence assessment;
- cheapest discriminating falsifier;
- consequences for current work if the counterhypothesis is true.

It must not manufacture facts. `FACT_UNKNOWN + METHOD_PRESENT != FACT_PRESENT` remains invariant.

## Return to research and workers

A material fused result is incomplete until it is addressable by affected research lanes/workers.

Use the existing OmniSource/Swarm semantics rather than inventing another bus or state authority:

- publish/reuse a durable `ResearchReentryReceipt` or bounded equivalent;
- route `MATERIAL_DELTA`, `COUNTER_CHALLENGE`, `KNOWLEDGE_NEED` or `ANTI_ENTROPY_REPAIR` by semantic/work relevance;
- affected active workers ingest at the next safe checkpoint;
- high-impact invalidation interrupts before the worker's next material effect;
- track the distinction `delivered -> reconstructed -> plan_revalidated -> used -> local_effect -> causal_credit_supported`;
- delivery alone never counts as use or causal credit;
- worker feedback itself becomes a new observation and may trigger another fusion/hypofusion pass.

## Scope / efficiency

This is **live**, not indiscriminate broadcast:

- trivial/nonmaterial deltas may close with lightweight `NO_CHANGE`/duplicate receipts;
- ordinary local deltas use targeted digest/full-ref or pull-on-demand;
- dense fanout is reserved for broad invalidations/dependency-spanning changes;
- raw full conversations and private chain-of-thought are never required as shared research state;
- external web research is invoked when a material hypothesis needs current/independent evidence, not for every low-value event.

## Relationship to exact triggers

The exact short commands `fusion` and `hypofusion` remain available as **full-depth explicit macro-runs** with their existing completion contracts. This directive adds a continuous material-delta layer beneath them; it does not weaken their required branch coverage, external triangulation, artifacts or falsification requirements.

## ClayVerse safety boundary

Live research re-entry must never create:

- a second canonical state authority beside UnifiedDB;
- a second effect path beside EffectGate;
- a second identity/entity;
- automatic truth promotion from worker consensus;
- automatic product acceptance from source/component evidence;
- blind replay of uncertain effects;
- unrestricted cross-user/private context broadcast.

ClayGraph remains rebuildable projection; Fusion/Hypofusion alter research accessibility, hypotheses, work and test obligations, not truth by vote.

## Mandatory worker behavior

Before material work and after each material outcome, workers must refresh relevant shared state. When a routed live-fusion/hypofusion delta affects their work, they must either:

- `ADOPT` — revise plan/work against the new evidence;
- `CHALLENGE` — publish a bounded counterargument/falsifier;
- `DEFER` — explain why it is not currently actionable;
- `NO_CHANGE` — record why current plan remains valid.

Silent ignoring of a relevant high-impact routed delta is coordination failure.

## Current activation receipt

Activation and first live re-entry are recorded under:

`research_entity/mesh_feedback/20260817T1725p0700-live-fusion-hypofusion-reentry/`

This directive is research/coordination law. It makes **no ClayVerse runtime or whole-product PASS claim**.