# Adaptive semantic backend router — Hostinger exact-branch fusion — 2026-08-10

Status: SUPPORTED CANDIDATE
Origin: chatgpt-secondary / OpenAI / GPT-5.6 Sol

## Why this exists

Cross-engine research refuted the simplistic objective that one physical database engine should win every primitive operation.

The supported Frank-specific objective is stronger and more useful:

`for each semantic query class, select the cheapest verified physical executor that satisfies the current accuracy / evidence-closure / provenance / epoch / authority floor`

UnifiedDB / Clay remains semantic authority. This router only selects a physical executor and has explicit authority:

`PHYSICAL_EXECUTOR_SELECTION_ONLY_NO_EFFECT_AUTHORITY`

## Candidate implementation

Files:

- `adaptive_semantic_backend_router_v1.py`
- `test_adaptive_semantic_backend_router_v1.py`
- `benchmark_adaptive_semantic_backend_router_v1.py`

Typed query classes:

- `DIRECT_KEYED`
- `LEXICAL`
- `VECTOR_SEMANTIC`
- `RELATIONAL_MULTIHOP`
- `COUNTEREVIDENCE_CLOSURE`

Each backend candidate is evidence-bound with:

- supported query classes;
- measured epoch;
- verified flag;
- provenance validity;
- evidence class;
- measured p50 latency;
- Hit@1 / Recall@5 / complete-evidence@5 / nDCG@5;
- ANN Recall@5 versus exact oracle where applicable;
- production-embedding validation state;
- fixed no-effect authority.

## Selection law

The router does NOT minimize latency first.

It applies this ordering:

1. reject conflict or ambiguity;
2. reject stale query basis;
3. reject unverified evidence;
4. reject invalid provenance;
5. reject unsupported query class;
6. reject stale/future measurement epoch;
7. enforce query-class-specific accuracy / closure floors;
8. for production vector queries reject proxy/unvalidated embeddings;
9. for ANN require Recall@5 floor against exact search;
10. retain the maximum verified quality front;
11. only within that quality front choose minimum p50 latency.

This prevents a fast but materially incomplete FTS/vector backend from silently winning a relational evidence-closure query.

## Adversarial tests

The test suite requires:

- equal-quality direct keyed query -> faster SQL backend wins;
- materially better multi-hop closure -> graph backend wins even when slower;
- equal-quality multi-hop -> lower-latency backend wins;
- production vector query -> token-hash/proxy embedding backend rejected;
- ANN below exact-recall floor -> rejected;
- stale measurement cannot win by speed;
- shuffled/invalid provenance rejected;
- unverified backend rejected;
- backend cannot smuggle effect authority;
- conflict/ambiguity blocks all executor selection;
- stale query basis blocks selection;
- no global engine rank exists across query classes.

## Exact Hostinger execution

The runner-bound `Dr.-Unterweger` bridge clones the exact current Clay branch:

`chatgpt/udb-claygraph-colocation-20260810`

and persists the exact SHA with the benchmark receipt at:

`runtime/vps_unifieddb/exact_adaptive_router/LATEST.json`

Current exact-branch result:

- PASS = true;
- route iterations = 20,000;
- expected route accuracy = 100%;
- conflict fail-closed = true;
- production-vector proxy rejected = true;
- routing p50 < 50 us;
- routing p95 < 100 us;
- routing p99 < 200 us.

These latency bounds are for the Python research policy evaluator, not total database-query latency.

## Relation to measured backends

The router deliberately supports the evidence already gathered in this research cycle:

### Direct keyed state

Main Hostinger measurements show selective indexed SQL pushdown can be roughly two orders of magnitude faster than reconstructing a full materialized state view. Therefore direct keyed access should remain on the cheapest safe relational path when semantic receipts are equivalent.

### Lexical

FTS remains a legitimate physical executor. Graph activation is not automatically added to every lexical query.

### Vector semantic

PostgreSQL + pgvector exact / ANN / hybrid are strong candidate executors. The current cross-engine vector corpus uses deterministic token-hash proxy vectors, so production-vector routing remains blocked until a real frozen embedding model passes exact/ANN recall and OOD gates.

### Relational multi-hop / counterevidence

Controlled PostgreSQL and Neo4j experiments support topology/closure as a quality mechanism. Graph closure is selected only when it clears the evidence-completeness floor; equal-quality graph/SQL implementations compete on latency.

## Architecture consequence

The target is not:

`Clay database engine > all databases`

The target is:

`Clay semantic data plane = UnifiedDB truth + ClayGraph topology + evidence-bound adaptive physical execution`

This lets Frank use normal database engines where they are best without surrendering:

- epistemic state;
- provenance;
- epoch coherence;
- causal / graph receipts;
- replay;
- fail-closed safety;
- effect-authority separation.

## Promotion gate

Before making this router canonical:

- route inputs must be generated from the canonical Clay access-plan semantics rather than ad-hoc caller labels;
- benchmark receipts must be versioned and durable in UnifiedDB;
- capability freshness policy must be defined for reboot/runtime changes;
- backend failure/recovery and fallback must be tested;
- real production embedding lane must replace the vector proxy;
- final Andreas Ubuntu target must reproduce the accepted route decisions and resource budget.

Current status remains `SUPPORTED CANDIDATE`, not canonical promotion.
