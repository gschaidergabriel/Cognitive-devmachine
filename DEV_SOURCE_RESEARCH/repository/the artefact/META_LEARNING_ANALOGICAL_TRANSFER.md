# ClayVerse Meta-Learning / Analogical Transfer Memory Contract

Status: REQUIRED PRODUCT ARCHITECTURE CONTRACT
Authority: owner direction, 2026-08-17
Product scope: ClayVerse single-container / `the artefact/`

## 1. Principle

ClayVerse must preserve not only *what* solved a problem, but also the abstract *how*: reusable problem-solving frameworks, heuristics, counterpatterns and failure lessons that can transfer to structurally similar but factually novel problems.

This is a system-level meta-learning layer around Claude Code. It must not convert analogy into factual truth. It proposes methods, search routes, hypothesis structures and action plans; factual claims still require admitted evidence/provenance.

## 2. Canonical authority

All durable meta-learning material is stored in UnifiedDB. MicroClay is the adaptive retrieval/entry-point organ only.

MicroClay MAY learn which abstract methods are useful entry points for which structural cues.
MicroClay MUST NOT mint truth, rewrite provenance, silently promote candidate methods, grant rights, change EffectGate policy, or turn an analogy into a fact.

ClayGraph remains a rebuildable projection over canonical UnifiedDB records.

## 3. Required durable memory classes

The current `durable_memory.kind` field is unconstrained text. The product contract reserves these semantic classes and requires validation/admission logic before ACTIVE use:

- `framework_candidate`: newly abstracted reusable solution framework; not yet promoted.
- `framework`: promoted reusable problem-solving framework with evidence and counterevidence.
- `heuristic_candidate`: newly extracted bounded rule-of-thumb; not yet promoted.
- `heuristic`: promoted bounded heuristic.
- `failure_pattern`: recurring mechanism or strategy that failed, including conditions under which it failed.
- `counterexample`: evidence that limits or falsifies a framework/heuristic.
- `method_receipt`: provenance/evaluation receipt for abstraction, promotion, demotion or use.

Existing factual/task/preference/decision memory classes remain separate. Method memory is not a substitute for factual memory.

## 4. Required method record envelope

A promoted framework/heuristic must be reconstructable from canonical fields equivalent to:

- `memory_id`
- `kind`
- `name` / subject
- `problem_signature`: abstract structural features of problems to which the method may apply
- `preconditions`
- `goal_shape`
- `method_steps`
- `invariants`
- `expected_observations`
- `falsifiers`
- `failure_modes`
- `scope_limits`
- `source_episode_ids`
- `supporting_memory_ids`
- `counterexample_memory_ids`
- `provenance`
- `abstraction_version`
- `support_count`
- `success_count`
- `failure_count`
- `calibration`
- `last_validated_at`
- `status`: CANDIDATE | PROMOTED | DEMOTED | RETIRED

These fields may initially be represented inside the existing `value` + `provenance` envelope, but final ACTIVE promotion requires explicit schema/validation contracts so malformed or under-specified method records fail closed.

## 5. Two-stage retrieval law

ClayVerse retrieval must distinguish factual/evidential retrieval from analogical/method retrieval.

### Stage A — evidence retrieval

1. current cue enters MicroClay;
2. exact/structured temporal/FTS/vector/ClayGraph candidates are gathered under provenance, privacy, valid-time and conflict bounds;
3. admitted factual/task/state memories are selected;
4. retrieval returns PRESENT, UNDERCOVERED or UNKNOWN with a receipt.

### Stage B — analogical transfer

Stage B is entered only when at least one bounded trigger is present, for example:

- Stage A is UNKNOWN;
- Stage A coverage is below an explicit threshold;
- the problem is novel/out-of-distribution relative to available evidence;
- conflicting evidence leaves the solution method unresolved;
- the task explicitly asks for a strategy, plan, diagnosis or hypothesis-generation method.

Stage B searches `framework`, `heuristic`, `failure_pattern` and `counterexample` memory by structural/problem signature, not merely lexical overlap.

The output is a bounded `method_context`, never a factual answer. It may contain:

- candidate framework(s);
- why the structural match may hold;
- preconditions that must be checked;
- strongest counterexample/failure pattern;
- proposed discriminating tests/searches/actions;
- confidence/calibration and provenance.

## 6. UNKNOWN law

`UNKNOWN` must not mean “invent a likely answer”.

When evidence retrieval is UNKNOWN, ClayVerse may retrieve a method framework to decide *how to investigate*, *which hypotheses to generate*, *what to test* and *where to search*. It must preserve the factual unknown until evidence resolves it.

Therefore:

`FACT_UNKNOWN + METHOD_PRESENT != FACT_PRESENT`

This invariant is mandatory.

## 7. Framework creation / abstraction

A framework candidate may be generated after a solved or failed episode by abstracting away instance-specific names/values while preserving causal structure.

Candidate creation should capture:

- problem structure;
- competing hypotheses;
- chosen interventions/tests;
- decisive evidence;
- solution path;
- counterhypothesis;
- observed failure modes;
- what would have made the method inappropriate.

A single successful episode is insufficient to treat a general method as universally valid. Candidate frameworks remain CANDIDATE until promotion criteria are met.

## 8. Promotion, demotion and calibration

Promotion to `framework`/`heuristic` requires bounded evidence, including where practical:

- provenance-complete source episodes;
- at least one explicit falsifier/counterexample search;
- evidence that success is not merely memorization of one instance;
- replay/held-out or cross-instance transfer evidence;
- no increase in contamination, stale-state use, privacy leakage or authority leakage;
- recorded failures as negative evidence rather than deletion.

Frameworks must be demotable/retirable when new counterevidence accumulates.

MicroClay learns accessibility priors from causally bound downstream utility. It does not perform promotion itself.

## 9. MicroClay entry-point policy

MicroClay must maintain separate learnable route priors for evidence retrieval and method retrieval.

Minimum future entry keys include bounded representations equivalent to:

- cue hashes;
- memory kind;
- subject/domain;
- problem-signature facets;
- goal shape;
- uncertainty/UNKNOWN state;
- conflict state;
- successful/failed framework route identifiers.

Learning signals should include verified task outcomes, explicit user corrections, retrieval misses, unnecessary personalization, stale-memory use and method-transfer success/failure.

Normal Claude completion is not reward.

Learned method routing starts in SHADOW and requires held-out/replay evidence before ACTIVE service.

## 10. Anti-self-reinforcement / anti-hallucination gates

The architecture must prevent these failure modes:

- a generated analogy becoming durable truth because Claude stated it;
- retrieval score being treated as truth confidence;
- a framework reinforcing itself because it caused its own selection;
- one successful anecdote becoming a universal heuristic;
- abstract method retrieval overriding direct contradictory evidence;
- method memory broadening cross-user/session access boundaries;
- hidden raw transcript becoming an undeclared competing memory authority.

Every method use must remain receipt-bound to the causal turn/episode/generation and selected method IDs.

## 11. Context assembly contract

The Claude-facing context must keep evidence and method context visibly distinct:

- `evidence_context`: admitted facts/state/tasks/decisions with provenance;
- `method_context`: transferable frameworks/heuristics/failure patterns;
- `unknowns`: unresolved factual gaps;
- `counterevidence`: direct conflicts and method counterexamples;
- `retrieval_receipt`: query/episode/generation/policy identity.

Claude must be able to use a method while still seeing that the underlying fact is UNKNOWN.

## 12. Acceptance tests

Final acceptance requires isolated exact-artifact tests for at least:

1. fact-known query prefers evidence and does not need analogical fallback;
2. fact-UNKNOWN query may return method context while fact status remains UNKNOWN;
3. structurally similar but lexically dissimilar problem retrieves the correct framework;
4. lexically similar but structurally different problem rejects the misleading framework;
5. counterexample/failure pattern lowers or blocks inappropriate framework use;
6. direct contradictory evidence outranks analogical method context;
7. a single successful episode cannot auto-promote a framework;
8. negative causal outcome can reduce MicroClay route capital without deleting truth/evidence;
9. stale-generation/replay/malformed method receipt fails closed;
10. user/session privacy boundaries are unchanged by method retrieval;
11. SHADOW policy cannot alter served context before promotion;
12. held-out transfer benchmark measures relevance, miss rate, contamination, stale-state use, unnecessary personalization, latency and causal task utility.

## 13. Current implementation gap at binding time

At the time this contract was added, current main already contains:

- UnifiedDB durable memory;
- MicroClay persistent SHADOW adaptive entry-point policy;
- query-sensitive factual retrieval;
- PRESENT/UNKNOWN receipts;
- causal outcome credit;
- accessibility/truth-authority separation.

But current main does NOT yet provide a dedicated validated framework/heuristic memory layer, structural problem-signature retrieval, UNDERCOVERED/OOD-triggered Stage-B method retrieval, or promotion/demotion machinery for generalized methods.

Those are required product work, not optional future polish.

## 14. Product invariant

ClayVerse should get better at solving novel problems by accumulating validated reusable *methods* as well as facts, while preserving a strict boundary:

**experience can improve how ClayVerse searches, reasons, tests and learns; experience cannot silently manufacture truth.**
