# UnifiedDB / Database Pulse — Adaptive Preprocessor + Maintenance Fusion

Date: 2026-08-10 +07:00  
Origin actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Identity: `RESEARCH_ENTITY_TEMPORARY_WORKER`  
Status: `MEASURED_CANDIDATES / TESTING / NO_CANONICAL_PROMOTION`

## Atomic synthesis

Current evidence supports neither a novel monolithic physical database nor a permanently
active graph traversal loop. The strongest current architecture is a **provenance-bound,
epoch-coherent possibility preprocessor whose own access and maintenance strategies are
adaptive**.

UnifiedDB/StateLedger remains semantic truth/persistence authority. ClayGraph, semantic
fields, active fields, rank indexes and segmented access materializations remain derived or
implementation-level acceleration surfaces. No retrieval/preprocessing output gains truth or
effect authority merely because it is salient, highly ranked or repeatedly activated.

The model-facing goal is increasingly:

`state change -> Pulse -> coherent possibility field -> bounded ActiveAssembly/PossibilityCapsule -> cognition`

rather than:

`prompt -> generic database search -> top-k -> stuff prompt`.

## Current fused control stack

```text
authoritative UnifiedDB / StateLedger transaction + provenance
  -> Database Pulse Runtime V2 endogenous bounded cycle
       candidate-generation implementation under active falsification:
         A) PulseActiveFieldV2 (known repair for lexical pre-limit bug)
         B) simpler authoritative RankIndexV3 counterhypothesis
  -> source/graph epoch changes + completed Pulse telemetry
  -> cycle-coherent semantic access generation
  -> U12 fail-closed semantic entity resolution
  -> U13 one-cycle/one-generation pin
  -> U14 cheapest validated read primitive
       exact resolved key -> ordinary indexed/B-tree lookup
       verified sufficient compiled field -> return + STOP
       compositional route -> precomputed Pareto possibility frontier
       unresolved mention -> evidence-bound resolver
       unsupported/stale -> conventional fallback / ABSTAIN
  -> U15 typed evidence-gap controller
       deepen only while explicit unresolved evidence remains
       no novelty / sufficient evidence -> STOP
       bounded query-aware EAP/ClayGraph expansion
  -> U16 compile economics
       ONLINE vs COMPILE from measured build/query quality/cost
       Pulse-informed lifetime estimate remains a testable predictor, not truth
  -> when COMPILE is selected, maintenance economics S1
       FULL_GENERATION vs SPM-S1 from measured bootstrap/update cost + locality
  -> SPM-S1 candidate
       immutable per-seed segments + coherent generation map
       impact-complete local update -> copy-on-write segment refresh
       incomplete/broad/unknown impact -> FULL_FALLBACK
       failure -> last-known-good preserved
       slower deep audit -> content/hash/corruption verification
  -> provenance-bearing ActiveAssembly / PossibilityCapsule
  -> GWT/model cognition
  -> verified outcome / causal credit / re-entry
  -> Pulse telemetry updates read horizon + update/locality history
  -> next adaptive access/maintenance decision
```

This makes Pulse not a timer but a measured feedback control surface around the state plane.

## What was actually built in this cycle

### SPM-S1 — segmented Pulse maintenance

A new collision-free branch identity was created:

`UNIFIEDDB_SEGMENTED_PULSE_MAINTENANCE_S1`

Lineage:

- provisional segmented-generation schema and runtime were first developed under a transient
  V12 label;
- that collided with the established U12 semantic resolver;
- a temporary V16 renumber then collided with the concurrently established U16 compile
  amortization controller;
- the mechanism was therefore moved to the orthogonal research identity `SPM-S1` rather than
  continuing a race over sequential U-numbers.

This naming correction is itself a coordination result: concurrent workers are allowed to
advance different branches without silently redefining one another's architecture.

SPM-S1 keeps immutable content-addressed seed segments. A coherent generation contains a
small seed->segment map. Local pulses can create only changed segments and reuse unchanged
ones. Publication remains atomic and epoch-bound.

### Deep-audit repair

Two self-discovered negative results materially changed the implementation:

1. The first local prototype was slower than full-copy maintenance because it recomputed a
   global safety hash and performed N verification queries after every pulse. Those O(N)
   checks destroyed locality and were removed from the hot path.
2. The first segment content identity hashed per-path dependency sets, but persistence retained
   only their segment-wide union. Exact reconstruction was therefore impossible. The
   audit-complete successor hashes exactly the persisted representation: seed identity +
   canonical path rows + segment dependency closure. A slow deep audit can then recompute
   segment hashes/IDs and the complete generation/head hash and detect physical tampering.

The hot-path law is now: immutable content identity + atomic map verification. Deep O(N)
integrity scanning is a recovery/release audit, not mandatory local-update work.

### Maintenance economics S1

`semantic_maintenance_economics_s1.py` adds a separate performance controller with three
possible outcomes:

- `ONLINE`
- `FULL_GENERATION`
- `SPM_S1`

SPM is disqualified when locality is unknown, quality regresses, per-update savings vanish,
or total guarded work does not amortize its additional bookkeeping. This complements U16:
U16 decides whether a derived field should be compiled at all; Maintenance Economics S1
decides how an equivalent-quality compiled field should be maintained.

### Pulse-derived maintenance horizon S1

`semantic_maintenance_horizon_estimator_s1.py` estimates from completed lifetimes:

- conservative reads before invalidation;
- conservative updates before invalidation;
- one-sided Wilson lower bound for impact-complete/local update probability;
- recent-locality collapse bound;
- read-horizon churn-shock propagation.

Sparse history or no completed update trials disables SPM rather than guessing. Fault/recovery
boundaries remain real samples rather than being discarded as inconvenient outliers.

This estimator is a hypothesis. Unit correctness does not imply good policy regret.

## Local SPM mechanism measurements

Local deterministic synthetic fixture:

- 1,200 seeds;
- 60 clusters;
- 20 paths/seed;
- 24,000 current access paths;
- 12 local update events;
- 500 matched read probes.

Latest local iteration:

- exact snapshot equality with full-generation baseline after every local event: `1.0`;
- SPM local-update p50: `23.942 ms`;
- full-generation local-update p50: `109.093 ms`;
- median update ratio: `4.534x` in favor of SPM for this locality-friendly fixture;
- SPM bootstrap: `314.721 ms`;
- full-generation bootstrap: `110.248 ms` — full generation wins bootstrap materially;
- 14 generations: full-copy path rows `336,000`; segmented path rows `28,800` plus
  generation-map rows `16,800`;
- unknown topology addition: `FULL_FALLBACK`;
- injected failure: last-known-good preserved.

A simple matched break-even calculation for these same local maintenance numbers gives about
`2.4013` fully local updates before SPM's extra bootstrap cost is amortized versus full-copy
maintenance. This number is fixture-specific and is not a universal threshold.

No universal database superiority claim follows. Already-resolved exact keys retain ordinary
indexed SQLite/B-tree as the latency floor. The relevant SPM claim is narrower: when a derived
semantic field has already been justified and updates are sufficiently local, copy-on-write
maintenance may reduce rebuild/write amplification while preserving an equivalent snapshot.

## Database Pulse V1 -> V2 result

The adversarial V1 test exposed a correctness defect: `max_candidates` could be applied to
lexicographically ordered state rows before salience scoring, hiding a late-sorted but highly
salient state such as `memory:zzzz-critical`.

`PulseActiveFieldV2` repaired this by materializing salience before the budget cut, while
remaining rebuildable/non-authoritative and preserving replay/root invariants. `DatabasePulseRuntimeV2`
fused the V1 owner contract with this candidate path.

A further receipt bug was also repaired: candidate-budget truncation must remain truthfully
observable in the Pulse receipt even when the candidate implementation changes.

However, ActiveFieldV2 is not promoted. A concurrent simpler counterhypothesis is now testing
an authoritative SQLite expression/rank index directly on StateLedger. If it preserves the
same correctness/replay/fail-closed semantics with lower total cost and less duplicated state,
it should replace the extra ActiveField projection.

## Current U16 insight: compile only when lifetime amortizes it

The measured U16 compile gate uses build/query/quality measurements and an explicit safety
factor. Existing fixture-derived guarded break-even read counts are about `1536` reads for
one no-alias case and `1327` for the alias case. These are not constants; they depend on
hardware, workload, build cost and invalidation lifetime.

A Pulse-history predictor was added to estimate reads-before-invalidation conservatively, but
its synthetic regret hypothesis is already being treated adversarially. The CI path was
corrected so a predictor that loses to simple always-online or always-compile policies is
recorded as a negative result rather than hidden by a failed workflow or falsely promoted.

Maintenance-horizon S1 inherits the same requirement: policy regret/total work against simple
baselines is the next discriminator, not unit-test success.

## External primary-research fusion

The architecture is consistent with, but not proven by, current database/retrieval research:

- DBSP formalizes general incremental view maintenance for rich query languages.
- Enzyme (Databricks, 2026) shows an industrial IVM design where refresh planning is explicitly
  cost-based rather than universally incremental; large-scale production validation motivates
  choosing refresh strategies from measured economics.
- SQLite FTS5 explicitly separates ongoing index synchronization, integrity-check and full
  rebuild semantics; derived indexes require consistency discipline with their source.
- Current graph/RAG work continues to support bounded/adaptive traversal and evidence
  sufficiency rather than unconditional graph expansion.

Clay consequence: incremental maintenance is a selectable mechanism under measured workload
and quality constraints, never an identity or truth claim.

## Strongest counterhypotheses

1. A simpler authoritative SQLite rank/expression index may dominate PulseActiveFieldV2.
2. SPM-S1 may lose on real Frank workloads if dependency fan-out is broad, write churn is high,
   locality closure is expensive/uncertain, or segment bookkeeping/GC/RSS dominates savings.
3. Pulse-history predictors may have higher regret than simple fixed policies under regime
   changes; conservative estimators are not automatically good forecasters.
4. The apparent semantic-field wins may be materialization/cache effects reproducible by a
   conventional DB/search/graph stack implementing the same provenance/sufficiency contracts.
5. Downstream cognition may not improve even when retrieval/model-input assembly metrics do.
6. Exact-key and simple lexical workloads should continue bypassing expensive Clay topology.

## Current promotion status

Supported candidates:

- conventional storage + Clay semantic possibility preprocessor;
- cycle-pinned coherent access;
- sufficiency-stop;
- typed evidence-gap-controlled deepening;
- adaptive cheapest-safe primitive selection;
- cost-gated materialization;
- SPM-S1 as an incremental maintenance candidate only under proven locality/economics.

Not promoted / refuted:

- UnifiedDB as a universal novel physical DB replacement: `REFUTED`;
- always graph-expand: `REFUTED`;
- always fill top-k: `REFUTED WHEN FIELD IS SUFFICIENT`;
- exact key always through Clay: `REFUTED`;
- unconditional materialization: `REFUTED`;
- unconditional segmented maintenance: `REFUTED BY BOOTSTRAP/LOCALITY TRADEOFF`;
- ActiveFieldV2 as final implementation: `UNDER SIMPLER-BASELINE FALSIFICATION`;
- Pulse horizon predictor as promoted optimizer: `NOT PROMOTED / REGRET TEST ACTIVE`.

## Immediate next falsifiers

1. Hostinger exact-commit execution receipts for SPM-S1, maintenance economics S1 and
   maintenance horizon S1.
2. Hostinger authoritative RankIndexV3 vs ActiveFieldV2 matched benchmark and randomized
   differential test.
3. Real Frank/Clay Pulse telemetry: reads/epoch, updates/epoch, impact-set fraction,
   structural/nonstructural write mix, invalidation causes, recovery boundaries.
4. Maintenance policy regret benchmark against `ALWAYS_ONLINE`, `ALWAYS_FULL`, `ALWAYS_SPM`
   and oracle on regime shifts, not only stationary synthetic histories.
5. Peak RSS, WAL/storage/write amplification, segment GC, recovery time and rollback retention.
6. Concurrent writer + crash/restart + deliberate corruption on SPM-S1.
7. Same-semantics conventional baselines and downstream answer/tool-route/calibration/token
   effects.
8. Final Andreas Ubuntu target-system acceptance.

No canonical promotion or effect-authority change is authorized by this fusion.
