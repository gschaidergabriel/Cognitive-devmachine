# UnifiedDB + ClayGraph Cross-Engine Benchmark Contract

Status: OWNER-GO-DERIVED FAIRNESS CONTRACT / CANDIDATE
Date: 2026-08-10
Origin actor: chatgpt-secondary / OpenAI / GPT-5.6 Sol

## Purpose

Test the strong claim that UnifiedDB + ClayGraph is materially better for Clay than conventional database designs without handicapping the conventional baselines.

This contract explicitly forbids comparing a fully guarded Clay semantic system to a deliberately naive row store and then calling the result database-engine superiority.

## Claim classes

### C1 — workload-specific Clay advantage

Admissible when Clay is Pareto-superior or materially Pareto-competitive on the declared Clay workload after all systems implement equivalent required semantics.

### C2 — architecture-level semantic advantage

Admissible when Clay achieves equivalent or better correctness/safety with measurably lower implementation/maintenance/context complexity, or provides a required semantic invariant that the matched baseline does not provide without materially greater cost.

### C3 — universal database superiority

NOT ADMISSIBLE from a single engine, single host, synthetic fixture, naive baseline, or unmatched semantics. Requires broad independent engine/workload evidence. The default result is UNSUPPORTED.

## Competitor implementations

Every competitor receives the same opportunity to implement the required semantics using its native best practices.

Required initial lanes when available:

1. SQLite conventional relational implementation.
2. PostgreSQL conventional relational/MVCC implementation.
3. A graph-native engine such as Neo4j only when current project capability/cost makes a reproducible lane available.
4. Clay UnifiedDB + ClayGraph using the current canonical/candidate implementation under test.

Additional engines may be added, but no engine may be intentionally deprived of indexes, constraints, transactions, materialized projections, generated columns, views, triggers, native graph indexes, or application-side receipt verification when those are normal tools for implementing the same contract.

## Frozen semantic workload

All systems must implement the same externally observable semantics.

### Semantic state

Each state item has at minimum:

- domain;
- key;
- canonical value;
- epistemic class: KNOWN / UNKNOWN / CONFLICT / REVOKED;
- status: CURRENT / RETRACTED / SUPERSEDED / QUARANTINED;
- state/domain epoch;
- integrity/provenance identity.

Default cognitive assembly must not silently promote UNKNOWN, CONFLICT, REVOKED, RETRACTED, SUPERSEDED or QUARANTINED items as KNOWN CURRENT context.

### Graph state

Graph topology is derived from semantic/version history and must support:

- logical node/edge identity;
- version identity;
- graph epoch;
- source semantic epoch;
- CURRENT/tombstone status;
- provenance;
- rebuild from authoritative history;
- explicit detection or deterministic contract for same-logical/same-epoch ambiguity.

### Coherent assembly

A context assembly is admissible only when the implementation's declared contract proves or verifies:

- semantic read basis is current for the requested source epoch;
- graph source epoch is allowed for that same read basis;
- the graph projection is verified/rebuildable according to that system's contract;
- ambiguity policy is satisfied;
- supplied rows match the integrity identity/count used by the receipt or equivalent verification mechanism;
- the result grants context authority only, never effect authority.

Equivalent mechanisms are allowed; identical internal data structures are not required.

## Correctness and accuracy suites

### S1 — epistemic admission

Balanced fixtures containing KNOWN, UNKNOWN, CONFLICT, REVOKED and non-CURRENT rows.

Metrics:

- precision;
- recall;
- F1;
- false-admission rate by class;
- abstention rate;
- calibration where a confidence score exists.

### S2 — mixed state/graph fault matrix

Inject at minimum:

- coherent current state;
- stale semantic read receipt;
- graph lag;
- graph future epoch;
- unverified projection;
- same-head ambiguity;
- graph row tamper;
- graph row-count mismatch;
- provenance corruption;
- tombstone resurrection attempt;
- out-of-order older version arrival.

Metrics:

- true accept;
- true reject;
- false accept;
- false reject;
- false-accept rate on unsafe inputs;
- detection latency;
- recovery outcome.

### S3 — replay/rebuild

From identical authoritative history:

- cold rebuild;
- crash/restart rebuild;
- randomized insertion order where order should be irrelevant;
- deterministic replay;
- last-known-good rollback.

Metrics:

- state equivalence;
- graph equivalence;
- integrity-root equivalence where applicable;
- lost/duplicate/stale rows;
- recovery time;
- peak memory/storage I/O.

### S4 — concurrency and snapshot safety

Matched readers/writers under declared isolation settings.

Inject:

- concurrent writer during long read;
- stale snapshot reuse;
- checkpoint pressure;
- aborted transaction;
- duplicate/idempotent retry;
- writer crash before/after commit boundary.

Metrics:

- inconsistent assembly rate;
- lost-update rate;
- duplicate-effect/state rate;
- stale-read detection;
- p50/p95/p99 latency;
- writer blocking;
- checkpoint/recovery behavior.

## Performance workloads

### P1 — exact key read

A fair raw/indexed lookup floor. Clay is expected to pay receipt/semantic overhead; that overhead must be reported rather than hidden.

### P2 — bounded filtered semantic read

Typical Clay context assembly predicates with LIMIT and epistemic/status filtering.

### P3 — graph adjacency current-head read

Current logical outgoing/incoming edges from version history.

### P4 — mixed semantic + graph assembly

End-to-end bounded context construction including verification gates.

### P5 — authoritative single-key update

Includes every mandatory durability/integrity operation required by the system's declared semantics.

### P6 — projection delta refresh

Incremental rebuildable projection maintenance after one and small-batch authoritative updates.

### P7 — full recovery rebuild

Reconstruct every non-authoritative projection/integrity shadow from authoritative state/history.

## Required resource measurements

At minimum:

- wall-clock p50/p90/p95/p99/min/max;
- N and raw rows;
- CPU time/utilization where available;
- process RSS/peak Python heap where relevant;
- database pages/file bytes;
- WAL/journal bytes where available;
- read/write/query count;
- rows scanned/returned;
- index/projection size;
- rebuild I/O;
- failure/retry counts.

Do not report only averages.

## Metadata

Preserve the project-wide benchmark metadata contract including:

- exact repository commit/dirty state;
- implementation/configuration/schema versions;
- host/VM/provider;
- CPU/RAM/storage;
- OS/kernel/libc;
- DB engine/version/extensions;
- Python/runtime versions;
- durability/isolation settings;
- indexes/constraints/projections enabled;
- seeds/dataset hashes;
- warm/cold state;
- concurrency;
- run order;
- timestamps/timezone;
- logs/artifacts/receipts.

Unknown values stay UNKNOWN.

## Fairness controls

1. Match semantics before comparing speed.
2. Allow each engine its normal optimization features.
3. Do not call application receipt verification a database-engine defect if the same semantics intrinsically require application logic in another system.
4. Report raw engine latency separately from semantic-system latency.
5. Match durability/isolation guarantees; do not benchmark FULL durability against unsafe relaxed durability without labeling it.
6. Separate hot-path maintenance from full recovery/rebuild.
7. Randomize/counterbalance order when cache/thermal effects matter.
8. Preserve negative results and configurations that lose.
9. A baseline that becomes equivalent to Clay after adding the same semantic contract is a valid result; it may refute a Clay-specific mechanism claim while validating the contract itself.
10. No universal claim from synthetic data alone.

## Promotion rule

A Clay mechanism may be promoted from this benchmark only when:

- correctness/safety is non-inferior under matched semantics;
- no unresolved high-severity false-accept/recovery defect exists;
- performance/resource gain is reproducible on at least local and Ubuntu lanes when applicable;
- the simpler matched baseline does not dominate it on the declared metric vector;
- the result survives a counterhypothesis/falsification lane;
- rollback and rebuild are verified.

## Current evidence entering this contract

The existing 2026-08-10 work already establishes two useful anchors that future cross-engine runs must preserve:

- raw indexed SQLite key lookup is faster than Clay receipt-bearing lookup, so raw engine latency is not a legitimate Clay superiority claim;
- Clay's explicit epistemic/epoch/projection/tamper gates materially outperform a deliberately simple accept-current row-store baseline on controlled safety fixtures, but that does not prove superiority over a conventional database implementing equivalent gates.

Therefore the next strong experiment is not another naive-baseline win. It is matched-semantics competition.
