# UnifiedDB + ClayGraph semantic-safety benchmark — 2026-08-10 07:18 +07:00

## Scope

This benchmark answers the owner's `accurater for Clay` direction with an operational metric rather than a universal DBMS claim.

Compared systems:

1. `SIMPLE_ROWSTORE_BASELINE`: admits every CURRENT state row and accepts every supplied graph/context bundle without epoch/verification/hash/ambiguity gates.
2. `CLAY_TYPED_ASSEMBLY_CANDIDATE`: default UnifiedDB KNOWN-only selection plus the epoch-bound UnifiedDB↔ClayGraph assembly gate from commit `f69f05be0f4f3f2a82dd5cc90c9804fdbcc4a3b5`, with falsifier tests in `ad59500a704609adcb02033a200dea4355933a24`.

This is a deliberately simpler baseline required for causal discrimination. It is NOT a claim that PostgreSQL, SQLite, Neo4j, DuckDB or any other DBMS cannot implement equivalent constraints.

## State-context admissibility fixture

120 CURRENT rows:

- 60 `KNOWN` — ground-truth admissible under default Clay assembly policy;
- 30 `UNKNOWN` — not default-admissible;
- 30 `CONFLICT` — must remain labelled and not default-admitted.

Results:

| system | TP | FP | FN | precision | recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| SIMPLE_ROWSTORE_BASELINE | 60 | 60 | 0 | 0.500 | 1.000 | 0.667 |
| CLAY_TYPED_ASSEMBLY_CANDIDATE | 60 | 0 | 0 | 1.000 | 1.000 | 1.000 |

Interpretation: the gain comes from an explicit epistemic admission contract, not from a storage engine magically knowing truth.

## Mixed UDB↔ClayGraph assembly fault matrix

600 deterministic cases, 100 each:

- SAFE: state basis epoch == graph source epoch; graph verified; ambiguity=0; rows hash/count match;
- LAG: graph source epoch behind state basis;
- FUTURE: graph source epoch ahead of state basis;
- AMBIGUOUS: projection reports same-head ambiguity;
- UNVERIFIED: graph projection not differentially verified;
- TAMPERED: supplied graph rows do not match receipt hash/count.

Ground truth: only SAFE may be admitted.

Results:

| system | TP | TN | FP | FN | accuracy | precision | recall | false-accept-rate on unsafe |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| SIMPLE_ROWSTORE_BASELINE | 100 | 0 | 500 | 0 | 0.167 | 0.167 | 1.000 | 1.000 |
| CLAY_TYPED_ASSEMBLY_CANDIDATE | 100 | 500 | 0 | 0 | 1.000 | 1.000 | 1.000 | 0.000 |

The committed unit tests independently pin each failure class: stale state receipt, graph lag, graph future epoch, ambiguity, unverified projection, row-hash tampering and row-count tampering.

## Accuracy claim admitted

Supported for this controlled fault model:

> Clay's typed semantic assembly contract detects and rejects all injected stale/ambiguous/unverified/tampered UDB↔ClayGraph contexts while the deliberately simple row-store baseline accepts them. Default epistemic selection also removes UNKNOWN/CONFLICT false admissions without losing KNOWN recall in the fixture.

Not supported:

> Clay is more accurate than every normal database.

Database engines execute declared semantics; semantic safety depends on the schema/contracts/queries built on them. A fair cross-engine benchmark must implement comparable safety semantics in every competitor and compare correctness, latency, storage, recovery and complexity on identical inputs.

## Next discriminating benchmark

Build matched implementations of the same safety contract in:

- raw SQLite SQL/triggers without Clay receipt types;
- PostgreSQL where available;
- a graph engine only if current project tooling/cost justifies it;
- Clay UnifiedDB + ClayGraph.

Score the same fault suite plus stale snapshot, replay, crash/restart, concurrent writer, checkpoint pressure and provenance corruption. The target is not to manufacture a win; it is to identify which Clay-specific semantics have measurable value beyond what a simpler conventional design already provides.
