# Emergent Model-Input Preprocessor Contract V3

Status: **CANDIDATE / TESTING — NOT CANONICAL ARCHITECTURE PROMOTION**

Purpose: turn the UnifiedDB/ClayGraph line into the smallest sufficient, provenance-bound model-input compiler rather than a second monolithic database.

## 1. Architectural split

### Authoritative state plane

UnifiedDB / StateLedger remains authoritative for:

- semantic/logical state;
- epochs and coherent generations;
- provenance and claim status;
- transactions/replay/recovery;
- raw benchmark rows and receipts;
- worker/capability/work state.

A conventional physical database/index is allowed and preferred whenever it is the Pareto-best primitive. Exact-key evidence already shows SQLite B-tree can beat the custom flat path. There is no requirement to replace B-trees, FTS, SQL, or physical storage engines.

### Derived model-input plane

ClayGraph, compiled semantic fields, evidence coalitions, QCEP projections and possibility frontiers are **derived / disposable / rebuildable**. They may change accessibility, grouping and rank only. They do not mint truth, proof eligibility or effect authority.

The model-facing object is not `rows`. It is a bounded **Evidence/Possibility Coalition** with explicit missing facets, alternatives, negative space and provenance.

## 2. Candidate query path

```text
verified source/read generation
-> Database Pulse / route selection
-> exact-key primitive if sufficient
-> compiled lexical/semantic field
-> Evidence Coalition compiler
-> typed sufficiency test (U15)
-> if sufficient: STOP
-> if explicit gaps remain: query/focus-conditioned ClayGraph deepening (QCEP candidate)
-> exact monotone Top-K stop
-> re-run sufficiency
-> if still insufficient: stronger conventional/dense/graph/tool retrieval or ABSTAIN
-> emit smallest sufficient provenance-bound context capsule
```

No stage is allowed to pad context merely to fill `k`.

## 3. Evidence Coalition invariant

Global row ranking is not the primary abstraction for multi-facet evidence questions.

If a query explicitly requests distinct epistemic facets such as:

- CURRENT + REFUTED;
- SUPERSEDED + OPEN;
- claim + counterclaim;
- support + blocker;

then those facets compete for **coalition slots**, not against one another in one undifferentiated rank.

A facet marker may open a navigation slot, but only authoritative claim/status data may satisfy it.

Residual item budget may be filled from ordinary topology rank after required slots are attempted.

## 4. Topology rules learned from falsifiers

1. **No self-seed reinforcement.** A seed cannot gain topic/domain evidence from its own membership. Topology means relations to other evidence.
2. **Missing relation semantics are UNKNOWN, not negative evidence.** If no admissible local query signal exists, query conditioning falls back to static edge weighting.
3. **Structural schema keys are not semantic evidence.** Tokens such as `source`, `target`, `strength`, field names or container keys cannot create query relevance.
4. **Only explicit evidence-bearing values may contribute semantic edge signal.**
5. **Inadmissible/CONFLICT/REVOKED nodes may be visible as negative space but cannot relay activation or close a sufficiency gap.**
6. **Typed gap focus outranks query-length normalization.** A long query cannot dilute an explicitly missing evidence facet. Focus affects navigation only; provenance-valid EvidenceItems close gaps.
7. **Exact Top-K stopping is allowed only under a proved monotone score bound.** QCEP's candidate transition multipliers remain <= 1, so descendant score cannot exceed frontier ancestor; ties are not prematurely stopped.

## 5. Physical execution fairness

A speed claim is invalid unless semantic output equality is established first.

For the real-claim experiments:

- SQLite matched topology and compiled topology must return the identical ordered Top-K;
- SQLite is allowed indexed, set-based joins;
- SQLite is also allowed a materialized neighbor relation;
- repeated per-candidate scalar SQL queries are explicitly rejected as an unfair speed adversary;
- compiled maps may claim only hot-path execution savings after preparation cost is reported.

Future PostgreSQL competitor must be allowed native best practices, including indexed generated/search-vector state where appropriate, GIN/GiST full-text indexing, recursive/set-based relational traversal, prepared statements and fair caching.

Future pgvector competitor must be allowed exact nearest-neighbor search and, when the workload warrants approximation, its native HNSW/IVFFlat paths with matched recall/latency reporting.

## 6. Current evidence state

### Supported, bounded

- Real Clay 17-claim ledger: semantic topic/domain/status preprocessing can improve complete evidence-set retrieval over a flat FTS-only path on the current correlated query set.
- Giving SQLite the same semantics can reproduce the same ordered results; therefore the accuracy gain belongs to the semantic compiler, not to storage-engine mystique.
- Local V1.1 execution showed compiled topology was materially faster than an initial semantically matched indexed-SQL implementation, but that first SQL speed adversary was later judged too weak.
- V2 Evidence Coalition passed its local predefined semantic-equivalence/holdout/stress gates.
- V2.1 replaced the weak speed opponent with set-based SQLite joins and a materialized-neighbor SQLite path; local pre-execution still passed semantic equality and compiled-p50-better-than-both gates.
- QCEP's local structural program has found and repaired multiple OOD/scoring errors before promotion; it remains a deepening candidate, not canonical architecture.

### Explicitly NOT proven

- universal superiority over SQLite/PostgreSQL/pgvector/graph-native systems;
- independent natural-language generalization;
- broad real Clay/Frank corpus dominance;
- downstream Frank answer/action improvement;
- Hostinger replication for the current V2.1/QCEP heads;
- Andreas target-system evidence;
- optimal physical storage backend.

## 7. Promotion rule

The model-input preprocessor may be called **dominant for a declared workload** only when:

1. authoritative semantics/provenance are preserved;
2. matched conventional competitors receive the same semantic information;
3. quality/safety does not regress on any declared class;
4. at least one material model-facing class strictly improves completeness, context efficiency, decision utility or total latency;
5. build/update/invalidation costs are included;
6. held-out/OOD/ambiguity/stale/conflict controls pass;
7. output remains reproducible on Ubuntu runtime lanes;
8. negative results remain active and can force fallback to a conventional route.

Composite dominance is valid even when the winning route for a class is SQLite/PostgreSQL itself. The goal is the best **model-input decision surface**, not ideological replacement of databases.

## 8. Next discriminators

1. Execute exact V2.1 script on clean hosted Ubuntu and Hostinger self-hosted Ubuntu; persist complete per-query receipts.
2. Independent worker authors a real-claim query/evidence-facet set without seeing V2 scores/outputs.
3. Increase the real claims/evidence/topic corpus substantially and preserve complete evidence-set ground truth.
4. Add fair PostgreSQL full-text/set-recursion baseline and pgvector exact/HNSW baseline under equal context budget.
5. Add graph-native baseline with the same typed nodes/edges and provenance constraints.
6. Measure downstream model answer/candidate-selection quality at equal token/context budget.
7. Integrate QCEP only behind a failed U15 sufficiency check; lesion it against static ExactTopK and against no-deepening.
8. Recompute preparation break-even under real mutation/churn before any materialized field is kept hot.

## 9. Research references fused into this candidate

Current external research used as mechanism inspiration, not as proof of Clay:

- CatRAG (ACL 2026): query-conditioned graph traversal and evidence-chain recovery under hub drift.
- Query-Aware Spreading Activation (2026): query-conditioned gating can improve retrieval while reducing unnecessary propagation.
- MEGRAG (2026): identify missing information and perform focused follow-up retrieval rather than unconditional expansion.
- Sufficient Context (ICLR 2025): distinguish context sufficiency from model answerability and support selective abstention.
- PostgreSQL current documentation: native full-text search/indexing and recursive/set-based SQL remain mandatory fair competitors.
- pgvector current project documentation: exact and approximate vector search must be treated as first-class conventional baselines.
- SQLite FTS5 documentation: FTS5/BM25 remains a legitimate native lexical baseline, not a strawman.

This contract is a research delta. It must not silently become canonical architecture without the remaining falsifiers.
