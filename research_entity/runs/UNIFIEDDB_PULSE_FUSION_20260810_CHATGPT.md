# UnifiedDB / Database Pulse fusion — 2026-08-10 — chatgpt-secondary

Status: RESEARCH HANDOFF / NO ARCHITECTURE PROMOTION

## Scope

This handoff fuses the historical Database Pulse evidence with the live 2026-08-10 UnifiedDB/EAP/SPM work, current external primary sources, adversarial dependency-provenance work, and simpler SQLite counterbaselines.

It does **not** claim that UnifiedDB/Pulse is universally superior to a normal database. It does not grant effect authority to retrieval/activation. It does not constitute Andreas-target acceptance.

## 1. Historical Pulse evidence that remains valid

Project evidence from `PULSE_EVIDENCE_2026-08-09.md` established a sandbox-executed database/graph cognition pulse with:

- 120/120 autonomous ticks;
- 120 distinct graph hashes;
- median tick latency 45.34 ms, p95 83.96 ms;
- 960 hypotheses, 485 semantic relations, 120 idle thoughts;
- 240 bounded state-influence receipts;
- no per-tick model-weight updates;
- subsequent normal full-cycle retrieval of Pulse-created `semantic_graph` knowledge;
- 74-organ accounting per tick, 8880 receipts total;
- UnifiedDB/ClayGraph integrity and FK checks passing.

Interpretation retained: UnifiedDB is durable authority/replay state; ClayGraph/Pulse products are derived, rebuildable cognitive structure. Historical evidence supports causal reuse of derived memory in the sandbox, not universal retrieval superiority.

## 2. Live swarm frontier joined during this run

`main` advanced materially while this worker was active. Relevant current lanes include:

- U12 fail-closed resolver / segmented Pulse work;
- U15 sufficiency-gap-controlled deepening;
- EAP `EmergentAssemblyPreprocessor` with negative-space propagation guard;
- salience-aware incremental Active Field / SPM maintenance;
- V3 authoritative SQLite rank-index counterbaseline;
- maintenance-economics routing gates;
- horizon-regret experiments that explicitly preserve NO_PROMOTION when a policy does not dominate simpler strategies.

The worker intentionally did not overwrite or duplicate those lanes.

## 3. External evidence refresh

Primary/current sources used:

1. MemORAI, Findings of ACL 2026, DOI `10.18653/v1/2026.findings-acl.1408`.
   - Identifies absent provenance tracking and uniform retrieval as graph-memory weaknesses.
   - Uses provenance-enriched multi-relational graph memory plus query-adaptive retrieval.
2. SQLite official Partial Index documentation: `https://www.sqlite.org/partialindex.html`.
   - Partial indexes can reduce index size and improve query/write performance when only a subset of rows matters.
3. SQLite official Expression Index documentation: `https://www.sqlite.org/expridx.html`.
   - Expression indexes are supported, but planner matching depends on syntactic expression matching; reusing the exact expression is therefore material.
4. MAGMA, ACL 2026, DOI `10.18653/v1/2026.acl-long.1709`.
   - Separates semantic/temporal/causal/entity relational views and uses query-adaptive graph traversal.
5. Zep/Graphiti, arXiv `2501.13956`.
   - Temporal graph memory provides another current counterexample to static document-only retrieval.

Inference, not source fact: these sources support keeping provenance, temporal/currentness and query-adaptive relational retrieval explicit, while SQLite's native physical indexing remains the simpler baseline for scalar/ordered filtering.

## 4. Main counterhypothesis: Pulse should not become a second database

Current stronger architecture hypothesis:

1. `StateLedger / UnifiedDB` remains the canonical semantic/event authority.
2. Native SQLite indexes should handle everything that can be expressed as cheap authoritative filtering/ranking.
3. `Pulse / EAP / ClayGraph` should exist only for relation-aware reconstruction, bounded multi-hop assembly, temporal/co-dependency structure, adaptive evidence-gap closure, and query-conditioned context that a flat index does not express well.
4. Derived graph activation is never proof/truth/authority.
5. Graph dependency propagation must itself be provenance-gated; CURRENT+KNOWN on a dependency row is insufficient when its latest writer event is untrusted, missing provenance or expired.

This makes the Pulse a cognitive preprocessor over authoritative state, not an alternate truth database.

## 5. U16 dependency-provenance falsifier

Research branch / PR:

- branch: `research/unifieddb-eap-edge-provenance-20260810`
- PR: `#100`
- current guard class after fixes: `EAP-PROVENANCE-GUARD-16.3`

Mechanism:

- derive latest-write receipts from append-only `StateLedger.export_events()`;
- decide whether each dependency row may relay activation using its event provenance;
- fail closed on missing receipt/provenance/evidence class, untrusted class, future/invalid/expired validity epochs, and optionally missing source receipt;
- filter only compiled EAP adjacency; never mutate UnifiedDB;
- preserve audit/blocked dependency refs;
- hash the complete edge-decision manifest once per source epoch;
- bind the cached manifest hash into per-query receipts.

Trusted evidence classes are currently a test policy (`VERIFIED`, `VALIDATED`, `MEASURED`, `AUTHORITATIVE`, `CANONICAL`) and require real project migration/admission study before any canonical promotion.

## 6. Adversarial result, negative result, repair

Synthetic adversarial workload:

- 300 valid dependencies;
- 60 high-weight `MODEL_INFERRED` poison dependencies (20% poisoned families);
- 1500 one-hop queries.

Real Hostinger v16.2 mechanism-snapshot execution (`Dr.-Unterweger`, runner `clay`, host `digital-retina`, Ubuntu/Linux 6.8, Python 3.12.3) established the safety effect but also exposed an unacceptable hot-path implementation cost:

- baseline target recall: 0.80;
- provenance-guard target recall: 1.00;
- baseline poison-query errors: 300;
- guard poison-query errors: 0;
- guard audit: 300 admitted / 60 rejected / 60 untrusted evidence-class rejections;
- v16.2 receipt hot p50 was ~8.41 ms in the first receipt and ~9.49 ms in the later matched v16.3 process comparison.

Two implementation/test bugs were found rather than hidden:

1. Audit bug: admitted edges were initially double-counted because `reason=ADMITTED` and the admitted-status counter used the same key. Fixed by counting status once and only adding reason counters for rejected edges.
2. v16.2 reserialized/rehashed the entire decision manifest on every query. The self-contained probe also recomputed a whole-Python-state hash per query, unlike real `StateLedger` which stores its semantic-state hash in SQLite metadata.

### U16.3 real Hostinger mechanism result

U16.3 moved full decision-manifest hashing to epoch/rebuild time and kept only its cached manifest hash in per-query receipts. A second real self-hosted Hostinger run (`github run 31345102652`) passed all falsifiers and preserved the safety benefit while removing the dominant receipt cost:

- baseline target recall: **0.80**;
- U16.3 target recall: **1.00**;
- baseline poison-query errors: **300**;
- U16.3 poison-query errors: **0**;
- baseline hot p50: **6.99 us**;
- U16.3 hot p50: **12.14 us**;
- baseline hot p95: **18.18 us**;
- U16.3 hot p95: **28.03 us**;
- baseline cold compile: **8.179 ms**;
- U16.3 cold compile: **12.599 ms**;
- old v16.2 receipt path in the same v16.3 process shape: **9.487 ms p50**;
- audit: **300 admitted / 60 rejected / 60 `EVIDENCE_CLASS_UNTRUSTED`**;
- provenance-sensitive receipt binding, expired/missing/source-receipt fail-closed checks: PASS.

Interpretation: U16.3 is now a strong **mechanism-level Ubuntu PASS** for this synthetic poisoning class. It is still not source-tree execution against latest Clay `main`, not real-corpus evidence, not a real provenance migration result, and not Andreas-target acceptance.

## 7. Simpler SQLite counterbaseline must remain first-class

Current `database_pulse_rank_index_v3.py` builds a **partial expression index directly on canonical `state`** for CURRENT+KNOWN salience ordering and deliberately reuses the exact `SCORE_EXPR` in CREATE INDEX and SELECT/ORDER BY.

This aligns with SQLite's documented planner requirements for expression indexes and with the write/query-economics rationale for partial indexes.

Promotion law from this fusion:

> If the authoritative rank index preserves the needed semantics and wins total workload cost, the custom Active Field must not be promoted merely because it is more Clay-specific.

Active Field/SPM remains justified only for semantics or amortized locality that the direct authoritative index cannot provide at equivalent quality.

## 8. Maintenance/economics consequence

The current `semantic_maintenance_economics_s1.py` is the right decision shape: ONLINE, full-generation and local SPM maintenance compete on measured total work subject to equal-or-better quality; unknown locality fails conservatively.

U16 provenance maintenance should be plugged into the same economics contract rather than becoming an always-on independent service. The relevant cost terms are:

- event/provenance scan or incremental provenance-index maintenance;
- dependency-edge invalidation locality;
- reads before next dependency/provenance invalidation;
- hot-query savings/cost versus direct online provenance lookup;
- quality delta under poisoning/staleness;
- memory/RSS amplification.

The U16.3 Hostinger receipt makes this tradeoff concrete for its synthetic workload: approximately +4.42 ms one-time cold compilation versus +5.15 us median hot-query cost relative to the minimal baseline, before any real-project provenance-index optimization. Those values are workload/implementation specific and must not be generalized.

## 9. Required next discriminating experiments

1. **U16.3 exact source-tree test** on latest `main`, not only a snapshot mechanism probe.
2. **Real provenance census**: count current dependency rows by latest event evidence class, missing provenance, source receipt, writer/event type, and age. No schema/policy migration before this census.
3. **Matched authoritative SQL baseline**: test whether provenance eligibility can be materialized/query-filtered natively in SQLite without EAP-specific bookkeeping.
4. **Real/held-out retrieval episodes**: compare direct SQL/FTS/rank-index, EAP, EAP+U15, EAP+U16, and EAP+U15+U16 on recall/nDCG/top1/abstention/calibration plus tokens/context.
5. **Write-heavy and bursty traces**: measure rebuild/incremental provenance-maintenance economics under realistic Pulse update patterns.
6. **OOD/paraphrase resolver tests**: exact seed refs are too optimistic.
7. **Resource shadows**: RSS/PSS, CPU, I/O, DB query count, state/artifact amplification.
8. **Crash/restart/replay**: guard manifest must reconstruct identically from the event ledger.
9. **Hostinger exact-SHA** after Clay Actions admission is proven; final Andreas Ubuntu target later.

## 10. Architecture delta classification

`CANDIDATE / TESTING`

Proposed bounded delta:

- canonical: StateLedger/UnifiedDB event + materialized state;
- native physical acceleration: SQLite partial/expression indexes where sufficient;
- derived relational processor: EAP/Pulse/ClayGraph;
- adaptive depth: U15 evidence-gap controller;
- propagation safety: U16 dependency provenance guard;
- maintenance routing: measured economics controller;
- authority: context/projection only until external effect boundary.

Strongest counterhypothesis:

> A simpler authoritative SQLite design (including expression/partial indexes and recursive CTEs) can match all useful Pulse/EAP outcomes at lower total lifecycle cost; graph/Pulse machinery adds complexity without enough downstream quality gain.

This counterhypothesis remains active and must be tested, not rhetorically dismissed.

## 11. Handoff

Affected workers should reuse this delta rather than rerun the same poisoning/provenance experiment. Independent replication is useful only when explicitly marked as such.

Current owner gate: no merge/promotion of PR #100 until current-main source-tree tests, real provenance census/migration analysis, matched simpler baselines, and remote receipts are available.
