# FRANK Memory — Titan -> LCME -> Hippocampus / MemoryHub deep evolution lineage

Run: `fusion-20260809T1538p0700-frank-architecture-lineage`
Status: archaeology + current target synthesis; no canonical promotion

## M-0 — multi-store memory was present before unification

By the 2026-02 public architecture, FRANK already had multiple persistence layers rather than one memory:
- chat/session memory;
- Titan episodic/semantic graph;
- E-PQ personality history;
- consciousness/reflection state;
- world experience;
- pattern/derived state.

The 2026-02-20 documentation commit `2b4f0e8...` explicitly documented six layers. Later versions added more specialized stores.

Core historical lesson:
`number of DB files != number of semantic memory organs` and `semantic unity != one physical store`.

## M-1 — Titan epistemic design

Frozen-head LCME core still preserves the original Titan leitmotif:
> Context is not text. Context is a time-weighted, uncertain graph structure observed through text.

Historical principles encoded in current source:
- claims, not unconditional facts;
- confidence and time weighting;
- counter-hypotheses for inferences;
- controlled forgetting;
- SQLite + vector + knowledge-graph tri-hybrid storage;
- ingestion, retrieval and maintenance separated;
- source/origin carried into ingestion.

This is a direct conceptual precursor of current ClayGraph + UnifiedDB epistemic roles.

## M-2 — catastrophic graph corruption exposed missing storage invariants

Commit `2d64017...` reports Titan graph corruption:
- 6,675 orphaned edges;
- 0 nodes.

Repair:
- `PRAGMA foreign_keys=ON`;
- `ON DELETE CASCADE`;
- 24h protection against pruning newly created nodes in the same lifecycle;
- 30 days chat reingested, reported 2,014 nodes / 3,233 edges.

Current law:
- derived relation topology cannot outlive source identity without an explicit dangling/retracted semantics;
- publication/retraction closure is a first-class invariant;
- crash/replay/maintenance must preserve referential integrity.

## M-3 — semantic chat retrieval and hybrid search

Same memory upgrade added:
- MiniLM-L6-v2 384D embeddings;
- FTS5 + vector cosine retrieval;
- reciprocal-rank fusion (`k=60`);
- crash-safe embedding backfill state;
- source-specific context budget allocation;
- session compression and preference memory.

Reported engineering measurement:
- 642/642 historical messages embedded;
- ~20 ms inline embedding per new message in that environment.

Evidence class: `REPORTED_MEASURED`, not current H1 acceptance threshold.

## M-4 — MemoryHub: logical unification over heterogeneous stores

`2d64017...` created a single MemoryHub query path over:
1. chat hybrid search;
2. Titan;
3. consciousness retrieval;
4. world experience;
5. user preferences.

Fusion used RRF plus greedy budget packing and recency penalty, with source attribution.

Historical strength:
- query semantics were unified without deleting specialized source stores.

Historical weakness identified by later FRANK research:
- readers were queried sequentially, so latency could become the sum of independent sources;
- current target therefore retains logical unity while allowing concurrent deadlines and specialized physical placement.

## M-5 — memory layer wiring failures were common

Examples:
- `c93873c...`: entity sessions were stored in their own DBs/transcripts but never ingested into Titan/chat memory, so FRANK could not recall them globally;
- `14b5071...`: world-experience bridge existed structurally but world tables had 0 entities/0 causal links until explicit injection paths were added;
- `6d680d3...`: FRANK said it had no persistent profile because no active memory-recall tool exposed the long-term store despite ~2,106 Titan nodes;
- autonomous research and agentic memory endpoints later returned 404 until changed to direct handlers (`07f8e26...`).

Current law:
`persisted != retrievable != selected != model-visible != causally usable`.

Harness must exercise each transition.

## M-6 — permanent archive vs working-set eviction

Commit `cae8751...` found destructive forgetting in consciousness ring buffers; permanent archives were added.

Memory fusion generalizes this into lifecycle classes:
- authoritative event/history;
- stable semantic profile;
- temporal event relations;
- derived associative indexes;
- hot salience/activation;
- active Assembly.

Evicting L4/L5 state must not erase L0/L1/L2 history.

## M-7 — Titan Neural Cortex / learned memory fast paths

Commit `ccebdc78...` added six small Titan neural networks (~77K parameters reported) for "living memory".

SFT Stabilizer `e7ac4bc...` later added:
- weight anchoring;
- decay;
- gradient clipping;
- drift monitoring/checkpoint behavior.

A later audit `1d44389...` found synthetic warmup inflating step counts for untrained neural modules.

The LCME rename/fix commit `290d5e2...` subsequently added a cold-start kill-switch so neural Cortex weights are used only at 300+ steps.

Current rule:
- learned accelerators begin in shadow/fallback mode;
- maturity cannot be fabricated by synthetic counters;
- learned retrieval never replaces exact provenance/authority.

## M-8 — Hippocampus neural retrieval

Frozen LCME core tries Hippocampus first only when:
- module is ready;
- `is_mature` is true;
- otherwise traditional retrieval remains the fallback.

This was strengthened by `290d5e2...` cold-start gating.

Current use:
- retain learned retrieval as an optional derived route;
- exact/source-grounded fallback is mandatory;
- retrieval utility requires matched quality/cost evaluation, not existence of a neural pathway.

## M-9 — room/entity and category migrations affected memory semantics

Entity sessions were later replaced by Rooms. That migration affected:
- session memory source names;
- NAc reward categories;
- spatial state;
- thought/reflection categories;
- neural state masks.

Memory schemas must preserve aliases/history while current semantic roles are versioned.

Current ClayGraph relation identity therefore includes roles and provenance rather than relying on string/category position.

## M-10 — room-ambient feedback contamination

Commit `1b86158...` is a major memory negative result:
- decorative room text entered generated thoughts;
- generated thoughts were stored;
- stored thoughts were reinjected;
- ThoughtSeedVAE trained on them;
- room-description style amplified into a recurrent attractor.

Fixes included removing room ambience from hot projection, filtering contaminated content and forcing VAE retraining.

Current law:
- model output persisted into memory retains `MODEL_GENERATED` epistemic role;
- repeated ancestry does not become independent evidence;
- retrieved self-generated text cannot silently promote into world truth or trusted training truth.

## M-11 — experiment/research results entered memory through lossy summaries

`809f0d6...` extracted one-sentence findings from experiment results into Titan.
`3277107...` injected discoveries into later thought.

Useful architecture:
`experiment -> durable result -> interpreted claim -> retrievable memory -> later cognition`.

Correction:
- experimental data/result and LLM summary are separate typed objects;
- summary cannot overwrite primary evidence;
- contradictory experimental results remain representable.

## M-12 — long-term conversational memory expansion

`f1ea0b47...` added:
- proper multi-turn message array through pipeline;
- long-term sentence-transformer embeddings;
- 180-day retention;
- GPU-generated session summaries;
- Titan episodic ingest;
- semantic/session context injection;
- larger recent-message/context budgets.

This shows memory quality depends both on persistence and reader/context assembly.

## M-13 — Titan -> LCME rename and retrieval correction

Commit `290d5e2b8640d55eb2a0aa38b99338c8070a0009` (2026-03-25) renamed Titan to **L.C.M.E. (Local Cognitive Memory Engine)** across 42 files while preserving DB filenames/tool names for compatibility.

Reported retrieval fixes:
- P@5 0.40 -> 1.00 in the commit's test;
- removed 7,213 entity vectors that polluted retrieval;
- EN+DE stop-word filtering;
- score redesign: 99.2% relevance / 0.8% tiebreaker;
- neural Cortex cold-start kill-switch;
- Hippocampus maturity gate;
- graph expansion disabled by default;
- HNSW activated at 500+ vectors;
- memory_recall routed through LCME rather than bypassing Hippocampus;
- automatic reconnect for closed DB connection.

Evidence class: `REPORTED_MEASURED/IMPLEMENTED`; exact benchmark must be rerun under H1.

Major architectural conclusion:
**graph expansion was not universally beneficial**. Broad association can degrade precision and create frequent-attractor contamination. This maps directly into current CASAR `BYPASS|SUPPLEMENT|ESCALATE|QUARANTINE` and bounded propagation.

## M-14 — frozen-head LCME current mechanics

Frozen `tools/lcme/lcme_core.py`:
- SQLiteStore + VectorStore + KnowledgeGraph;
- ingestion through Architect;
- retrieval through Retriever;
- hourly maintenance thread;
- controlled forget/protect/unprotect;
- counter-hypothesis API;
- invalidate retrieval cache immediately after writes;
- hot buffer for recent non-chat entries;
- chat-origin entries deliberately excluded from hot buffer because Q&A flooding harmed fact retrieval;
- Hippocampus neural fast path only if mature;
- fallback to traditional retrieval;
- compatibility aliases preserve old `Titan` API names.

This is a rich reusable historical substrate but remains a monolithic host implementation rather than the target Clay/UnifiedDB semantics.

## M-15 — C4-C9 abstraction

C4:
- memory fabric is provenance/freshness aware;
- exact state is separate from retrieved context.

C5:
- immutable semantic memory epochs + non-authoritative activation + bounded Active Assembly;
- Assembly pins exact anchors and relation instances.

C6:
- explicit epistemic roles (`OBSERVATION`, `INFERENCE`, `HYPOTHESIS`, etc.);
- persistent symbolic memory distinct from weight memory and transient activation;
- graph activation cannot create truth/authority.

C7:
- UnifiedDB logical query fabric and ClayGraph memory become explicit organs;
- record provenance and selection provenance are distinct;
- approximate route cannot satisfy exact obligation without validation.

C8:
- L0..L5 memory lifecycle formalized;
- Salience Governor can adapt gain/decay/inhibition but never canonical truth;
- Cognitive Resource Governor builds bounded active slices.

C9:
- presence/authenticity is distinct from admissibility;
- CASAR route is orthogonal to epistemic use;
- authentic but context-invalid memory can be quarantined;
- utility credit is scoped (`ITEM|PATH|ASSEMBLY|UNKNOWN`) to avoid reinforcing every surfaced memory.

## M-16 — Unified Memory <-> Retina extension

Current target integrates historical memory with visual learning:
- stable entity/alias identity;
- episodic encounters;
- visual evidence/features/views;
- context/spatial relations;
- lookalikes/confusions;
- prototype/readout/calibration state;
- current feature-backbone compatibility;
- trusted corrections and rollback lineage.

Memory priors feed perception recurrently but remain distinguishable from current sensor evidence.

Two gates remain separate:
1. **RecognitionValidity** — can learned memory support the fast recognition path now?
2. **AdaptiveStatePromotion** — is candidate learned state trustworthy enough to become durable/current?

## M-17 — current fused target

### Canonical / durable
Append/replay source events, effects, outcomes, owner contracts and trusted corrections.

### Stable semantic profile
Evidence-gated derived self/world/entity memory.

### Temporal relational memory
Valid-time + transaction-time events/relations.

### Associative derived memory
ClayGraph/vector/FTS/HNSW/materialized views, versioned and rebuildable.

### Salience / familiarity
Fast non-authoritative accessibility and calibration state.

### Active Assembly
Small operation-conditioned evidence slice supplied to GWT/model.

Logical query semantics unify these layers through UnifiedDB; physical stores remain evidence-driven until the post-H3 UDB stage.

## Mandatory regressions

- M-REG-01 orphan edges after node prune/crash;
- M-REG-02 store succeeds but immediate retrieval remains stale;
- M-REG-03 persisted session not reachable through global memory;
- M-REG-04 memory exists but no active retrieval route;
- M-REG-05 graph expansion degrades exact retrieval;
- M-REG-06 vector/entity flood dominates relevant claims;
- M-REG-07 cold-start learned retriever activated prematurely;
- M-REG-08 synthetic training/maturity counters promote untrained module;
- M-REG-09 hot-buffer/working-set eviction erases durable history;
- M-REG-10 self-generated content recursively becomes training/world truth;
- M-REG-11 rename/migration loses alias/source identity;
- M-REG-12 derived edge remains CURRENT after source retraction;
- M-REG-13 crash during semantic epoch publication exposes mixed CURRENT state;
- M-REG-14 misleading prior/near-confuser overrides Retina sensor evidence;
- M-REG-15 H1/H2/H3 query/result/admissibility/Assembly equivalence.

## Fusion decision

`TITAN/LCME: REUSE_EPISTEMIC_AND_RETRIEVAL_LINEAGE + ADAPT_TO_CLAYGRAPH_UNIFIEDDB + RETEST_ALGORITHMS`.
`MemoryHub: REUSE_LOGICAL_UNIFICATION_IDEA; replace serial hot-path fanout with typed planner/deadlines/Assembly`.
`Hippocampus/Titan Cortex: RETEST_AS_DERIVED_ACCELERATORS_WITH_MATURITY_AND_EXACT_FALLBACK`.
