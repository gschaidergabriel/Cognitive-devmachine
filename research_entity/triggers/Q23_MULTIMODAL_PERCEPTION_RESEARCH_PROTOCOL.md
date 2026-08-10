# Q23 — Interconnective Multimodal Perception Research Protocol

**Status:** PROJECT-OWNER FIXED EXACT TRIGGER  
**Exact trigger:** `q23`  
**Matching:** complete trimmed message, case-insensitive  
**Field:** `research_entity/global/Q23_MULTIMODAL_PERCEPTION_RESEARCH_FIELD.clay`

## Purpose

`q23` starts the persistent interconnective research field for Frank's multimodal perception architecture. It researches how a natively multimodal <=4B Frank model, currently Qwen3.5-4B-class, should fuse with the historical Digital Retina lineage, adaptive user-specific visual learning, temporal GUI perception, visual memory and the one-module H3 architecture.

It is not a one-shot answer and not a generic model-news search. Every invocation must perform useful work immediately and feed the resulting evidence back into Clay's shared research system.

## Mandatory per-invocation cycle

Every exact `q23` invocation MUST:

1. refresh current canonical repo state, program stage, active workers/work, receipts, hypotheses, counterhypotheses, negative results and previous q23 packages;
2. form at least one current falsifiable hypothesis tied to the target architecture;
3. form the strongest useful counterhypothesis/null/failure explanation;
4. perform fresh online research during this invocation — cached prior web results alone do not satisfy q23;
5. prioritize current official model/runtime repositories, official documentation/model cards and primary papers/datasets;
6. search both supporting evidence and competing mechanisms/counterevidence;
7. identify external findings that could materially improve, simplify, falsify or de-risk the target architecture;
8. convert each such finding into a provenance-bound Q23 Research Package with source, source date/version where available, retrieval time/query, finding, relevance, internal fusion result, uncertainty and falsifier;
9. fuse the new packages with current internal research, historical Retina evidence, current Frank architecture, runtime receipts and negative results;
10. revise/create hypotheses and counterhypotheses from the fusion;
11. create versioned Architecture Delta candidates when a concrete architecture implication exists; every delta requires strongest counterhypothesis, discriminating test, metrics and rollback;
12. map findings/deltas to current dynamic work and create/revise nonduplicate test obligations/work where warranted;
13. route the packages and architecture deltas back to the semantically affected subset of the swarm, including `frank`, `harness`, `gwt`, `claycode`, `claygraph`, `unifieddb`, `hyperposition`, `emergenz`, `clayresearch` as actually relevant;
14. require normal OmniSource ResearchReentryReceipt semantics for material deltas;
15. refresh again and continue recursively while expected marginal information/architecture value exceeds cost/risk and invocation budget remains.

## Required run artifacts

Each material q23 run should create under:

`research_entity/trigger_runs/q23/<run_id>/`

at minimum:

- `RUN_MANIFEST.json`
- `HYPOTHESES.json`
- `COUNTERHYPOTHESES.json`
- `ONLINE_RESEARCH_MANIFEST.json`
- `packages/<package_id>.json|md` for each architecturally interesting external finding
- `ARCHITECTURE_DELTAS.json`
- `TEST_OBLIGATIONS.json`
- `BRANCH_FEEDBACK_MANIFEST.json`
- `FINAL_SYNTHESIS.md`

A run with no material external finding still records searched source classes/queries and an evidence-backed `NO_MATERIAL_CHANGE` package/receipt.

## Research package minimum contract

Every package contains or references:

- package/run ID;
- observed/retrieved time;
- topic/title;
- direct source references;
- publication/update/model/runtime version date when available;
- retrieval query or discovery path;
- source/evidence class;
- concise finding;
- why it may matter for Frank's target architecture;
- current internal evidence compared against;
- fusion result: SUPPORTS / REFINES / CONTRADICTS / SUPERSEDES / ALTERNATIVE / NO_CHANGE;
- hypothesis/counterhypothesis effect;
- candidate architecture delta, if any;
- cheapest discriminating experiment/test;
- affected components/work/branches;
- confidence and unresolved uncertainty;
- content/provenance identity.

Interesting does not mean true. Packaging never promotes architecture by itself.

## Current research attractor

The initial high-information-gain question is:

> Can Qwen's already-required multimodal vision/mmproj encoding become the single deep visual feature backbone for Frank — reused by the tiny familiarity/open-set learner and by semantic decode on escalation — so the target does not duplicate a second heavy Retina visual encoder?

Mandatory competing possibility:

> Raw generative-VLM visual features may be poorly calibrated for instance/layout familiarity and open-set recognition, so a separate *lightweight* embedding encoder may remain Pareto-superior even though a second heavy semantic vision stack is unnecessary.

Neither is presumed true.

## Swarm semantics

q23 is fully interconnected with the current Clay research mesh.

- Before research: read current swarm blackboard and avoid duplicate work.
- During research: consume relevant worker/runtime/repo deltas as evidence.
- After research: package and route new results by semantic/dependency relevance.
- High-impact claims create/reuse an adversarial/counterhypothesis lane when capacity permits.
- Shared ancestry is never counted as independent replication.
- A result invalidating active work interrupts that work at its next safe point.
- Low-relevance package payload stays indexed/pullable rather than broadcast into every worker context.

## Architecture feedback law

q23 MUST NOT end at a literature summary.

Every material result yields at least one of:

- architecture delta candidate;
- test obligation;
- work revision/new work;
- hypothesis/counterhypothesis revision;
- negative result;
- explicit NO_CHANGE with evidence.

Architecture deltas remain `CANDIDATE` or `TESTING` until normal evidence gates promote/refute them.

## Authority and safety

- Clay Research Entity researches/builds/tests Frank; it is not Frank.
- Frank self-Harness authority remains proposal-only.
- Model or visual prediction never mints effect authority.
- Familiarity/confidence never becomes sensor truth.
- Abliterated model preference does not bypass deterministic effect/authority gates.
- No paid/final training starts automatically.

## Primary field contract

The exact operational semantics live in:

`research_entity/global/Q23_MULTIMODAL_PERCEPTION_RESEARCH_FIELD.clay`
