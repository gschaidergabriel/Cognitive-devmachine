# UnifiedDB real-contract retrieval iteration — 2026-08-10

Status: TESTING / RESEARCH DELTA
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol
Entity boundary: temporary Clay research worker; not Frank.
Authority: context/research/build/test only. UnifiedDB/StateLedger stays canonical semantic truth; ClayGraph/compiled fields remain derived and rebuildable.

## Goal

Test whether UnifiedDB + ClayGraph can be measurably better for actual Clay/Frank governing-contract retrieval than a strong ordinary SQLite FTS5 path, while preserving explicit provenance and refusing a universal database-superiority claim.

## Frozen real-contract suite

A 32-query English/German suite was frozen before the first result. It covers eight current governing contracts and includes exact rules, negative rules and cross-contract reference questions. Ranking code is not given `expected_path` or `expected_heading_contains`.

Baseline: SQLite FTS5 `unicode61 remove_diacritics 2`, weighted BM25 over Markdown sections.

The exact PR merge-tree gate remains the promotion authority. A local reconstruction was also executed because the self-hosted runner was queued; six documents were exact current copies and two long documents were reconstructed from current GitHub excerpts. Therefore local numbers below are mechanism/dev evidence, not a replacement for exact-runner evidence.

## Iteration R0 — flat FTS5

Local reconstructed-current-contract probe:

- Top-1 path accuracy: `0.6875`
- Recall@3 path: `0.875`
- Recall@5 path: `0.90625`
- MRR path: `0.75390625`
- Section Top-1: `0.6551724138`
- p50: `~85.7–91.0 us` across repeated local probe variants

This is the strong ordinary embedded-DB baseline.

## Iteration R1 — online semantic expansion + bounded reference deepening

Candidate semantics:

- same FTS5 engine;
- project-ontology bilingual normalization;
- normative-section cue;
- explicit directed reference graph parsed from contract links;
- bounded one-hop graph deepening;
- no expected-answer mapping.

First frozen-suite run:

- Top-1: `0.90625`
- Recall@3: `1.0`
- Recall@5: `1.0`
- MRR: `0.953125`
- Section Top-1: `0.7241379310`
- p50: `~2.55 ms`

Result: large real-contract retrieval-quality gain, but online work is unnecessarily expensive.

## Iteration R2 — pretokenized online deepening

Move section tokenization/overlap structures to build time; retain the same general semantic mechanism. Error analysis also added generic missing bilingual concepts, not file/query-specific expected-answer rules.

Measured:

- Top-1: `0.9375`
- Recall@3: `1.0`
- Recall@5: `1.0`
- MRR: `0.96875`
- Section Top-1: `0.7586206897`
- p50: `~597.7 us`

Two Top-1 misses remained. Do not continue tuning the same 32-query suite for promotion; this is now a development set after post-hoc iteration.

## Iteration R3 — compiled semantic FTS projection

Shift bilingual aliases and explicit contract-reference labels into a rebuildable build-time FTS projection. Query-time uses a single raw-token FTS lookup rather than Python online expansion.

Build:

- sections: `169`
- compiled semantic-field build: `~2.94 ms`

Query result:

- Top-1: `0.84375`
- Recall@3: `0.9375`
- Recall@5: `0.9375`
- MRR: `0.8864583333`
- Section Top-1: `0.6551724138`
- p50: `~41.4 us`

This is about `2.2x` faster than the local flat FTS5 p50 while also improving Top-1 by `15.625 percentage points`, but it does not match the more accurate deep path.

Pure latency build-cost break-even versus local flat FTS5 is approximately `60 reads` at this corpus size. This is a local workload estimate, not a universal constant.

## Iteration R4 — adaptive compiled-consensus + typed disagreement deepening

Architecture:

1. query cheap raw FTS and cheap compiled semantic FTS;
2. if both top document identities agree, accept the compiled fast path;
3. if they disagree, declare an explicit retrieval sufficiency/conflict gap and invoke the bounded R2 deep path;
4. preserve context-only authority and source identity.

Measured:

- Top-1: `0.9375`
- Recall@3: `1.0`
- Recall@5: `1.0`
- MRR: `0.96875`
- p50: `~181.7 us`
- p95: `~979.7 us`
- deepening rate: `0.34375`

Thus R4 preserves R2 quality while cutting p50 by about `3.3x`. The compiled-field build cost amortizes against always-deep R2 after roughly `7 reads` at these local timings.

R4 is still about `2x` slower than flat FTS5 p50, but the comparison is not quality-equivalent: Top-1 is `0.9375` vs `0.6875` and Recall@3/5 is `1.0` vs `0.875/0.90625`.

## Important negative result — score-margin confidence

A single compiled ranking score/margin is not a reliable correctness detector. Some wrong flat/compiled results can have apparently strong ranking gaps. Therefore do **not** promote a magic score-threshold router from this suite.

Current safe direction is fail-conservative evidence:

- exact indexed reads when structurally exact;
- compiled semantic fields for stable/repeated families;
- independently observable disagreement/sufficiency gaps;
- bounded graph/semantic deepening only on those gaps;
- conventional online SQL/FTS when churn economics or simple exact reads dominate.

## ClayGraph high-degree relation accuracy experiment

Separate adversarial mechanism run:

- 800 roots;
- 8 relation classes;
- 32 edges/class;
- 204,800 edges total;
- out-degree 256;
- fixed total retrieval budget 32.

Observed:

- global Top-weight Recall@32: `0.35`;
- previous counter-only reserve Recall@32: `0.5625`;
- query-conditioned relation reserve Recall@32: `1.0`;
- requested-relation precision: about `0.127 -> 0.302`;
- p50: about `12.13 us -> 19.19 us`.

False-intent control: deliberately wrong relation intent regressed Recall@32 slightly below global (`~0.3275` vs `0.35`). Therefore relation-conditioned reserve must be confidence-gated and fall back exactly to global bounded access below the calibrated threshold. Draft V6 implements this fail-conservative rule and receipts proposed/admitted relation separately.

This is synthetic adversarial evidence only. Promotion needs real/OOD relation-intent calibration.

## Concurrency / recovery mechanism evidence

Independent local SQLite two-connection WAL mechanism falsifier, 25 rounds:

- foreign writer `BEGIN IMMEDIATE` -> retryable failure rate `1.0`;
- contended failure p50 `~40.60 ms` with 40 ms busy timeout;
- false index commit rate `0`;
- false durable receipt rate `0`;
- semantic/trace root drift `0`;
- after lock release, fresh-plan DDL+receipt recovery success `25/25`;
- recovery p50 `~1.165 ms`, p95 `~2.245 ms`.

This supports the underlying SQLite transaction assumption. Exact repository V5 two-connection tests remain a separate self-hosted gate.

## Current fused architecture

`EXACT_INDEX`
→ cheapest exact key/index path when query is structurally exact.

`COMPILED_SEMANTIC_FIELD`
→ stable/repeated semantic families with verified basis + favorable read horizon.

`EXACT_TOPK_FRONTIER`
→ mathematically exact early stop only where monotone bound proof/equivalence holds.

`TYPED_GAP_DEEPENING`
→ bounded ClayGraph/semantic expansion only after explicit sufficiency/conflict gap.

`RELATION_CONDITIONED_BOUNDED_GRAPH`
→ only when a calibrated typed relation intent is admitted; otherwise exact fallback to global bounded graph access.

`HARDENED_LEXICAL_GRAPH_FALLBACK`
→ OOD/uncompiled retrieval with explicit UnifiedDB↔ClayGraph binding, stale rejection and bounded graph work.

`CONVENTIONAL_ONLINE_SQL`
→ valid winner for high-churn families or simple reads when projection/build amortization does not pay.

## Promotion boundary

Supported by current evidence:

- UnifiedDB/ClayGraph can materially improve real Clay contract evidence retrieval over flat FTS5 on the current frozen local-reconstructed suite;
- build-time semantic projections can also beat flat FTS5 latency on the same local corpus;
- adaptive routing preserves higher-quality deep retrieval at substantially lower p50 than always-deep;
- no single physical read mechanism dominates every query type.

Not supported:

- universal superiority over every database;
- final PostgreSQL/pgvector/graph-database dominance;
- live Frank answer-quality superiority;
- independently held-out relation-intent calibration;
- final Andreas Ubuntu release evidence.

Next falsifiers:

1. exact self-hosted execution of frozen 32-query suite on PR merge tree;
2. new independently adjudicated held-out real-contract suite after R4 freeze;
3. PostgreSQL 18 matched semantic-read adversary;
4. concurrency/read-write interference + build invalidation;
5. relation-intent calibration/OOD false-positive curve;
6. larger 10k/100k/1m semantic-history and graph scale sweeps;
7. crash/restart/rebuild equivalence and last-known-good rollback;
8. final target-host validation.
