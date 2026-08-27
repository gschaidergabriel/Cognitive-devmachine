# UnifiedDB — State Continuity + SQLite WAL Safety

Run: `unifieddb-20260811T0417p0700-chatgpt-secondary-state-continuity`

Status: **CANDIDATE BUILT / LOCAL FALSIFIERS PASS / TARGET-VPS PROMOTION HOLD**

## Fresh-state correction

The current Frank v0.1 workspace advanced during boot. The exact effect execution-generation fence is now PASS and must not be rebuilt by this branch. The remaining high-value UnifiedDB/recovery problem is narrower:

1. exactly one provenance-bound semantic state lineage must be admitted current;
2. state writes must bind to the exact current execution generation;
3. whole-DB snapshot rewind needs a rollback-domain-independent monotonic floor;
4. the accepted target currently reports SQLite 3.45.1 with WAL, while upstream SQLite documents the WAL-reset corruption bug through 3.51.2 unless fixed/backported or its trigger topology is proven unreachable.

## Candidate architecture

`UnifiedDB` remains the logical/canonical semantic state plane. `ClayGraph`, vector/FTS indexes and other projections remain rebuildable/derived. Large model/tensor backing remains physically isolated when warranted. The external monotonic recovery floor is deliberately **KEEP_ISOLATED** because placing it only inside the same UnifiedDB rollback domain cannot detect a rewind of that domain.

The candidate adds:

- one `ADMITTED_CURRENT` semantic lineage;
- lineage generation + head epoch/root hash + parent hash;
- immutable transaction binding to lease epoch/execution/session/client/lineage;
- continuity commits that advance the lineage head only from the exact prior head;
- snapshot-to-lineage bindings;
- SHADOW-first enforcement;
- a separate SQLite/WAL storage safety gate.

## Local falsifiers

Environment: Python 3.13.5, SQLite 3.46.1, Linux 6.18.35. Evidence class is local/synthetic mechanism evidence only.

PASS:

- valid current-generation commit;
- stale execution binding rejected;
- execution-id change without a higher lease epoch rejected;
- second simultaneous current sibling lineage rejected;
- higher generation valid commit;
- restored old DB snapshot rejected when external monotonic floor is newer;
- current DB accepted against matching external floor;
- WAL safety gate rejects target-like `3.45.1 + WAL` without verified backport/topology proof;
- WAL safety gate accepts upstream fixed 3.51.3 and named fixed backport 3.50.7;
- non-WAL mode correctly marks this specific bug class not applicable.

Latency proxy, N=1500, in-memory SQLite:

- baseline p50/p95/p99: 7.29 / 11.19 / 16.39 µs;
- continuity candidate: 40.32 / 77.59 / 146.99 µs;
- increment: +33.03 / +66.40 / +130.60 µs.

These are not target-VPS durability or end-to-end Frank latency measurements.

## Strongest negative result

A monotonic generation stored only inside UnifiedDB is insufficient against a snapshot rollback of UnifiedDB itself. The recovery floor must have an independently verified failure domain or recovery remains fail-closed.

## Storage safety finding

Primary SQLite documentation states that the WAL-reset corruption bug affects SQLite versions from 3.7.0 through 3.51.2 and is fixed in 3.51.3, with named backports including 3.44.6 and 3.50.7. The bug requires WAL mode with multiple connections where writing/checkpointing races occur. Therefore the current target observation `SQLite 3.45.1 + WAL` cannot be declared safe from the version string alone. A distro backport/source-id receipt, a fixed runtime upgrade, or a machine-checked topology proof is required before authoritative WAL writes can pass the release gate.

Primary sources:

- https://sqlite.org/lang_transaction.html
- https://sqlite.org/isolation.html
- https://sqlite.org/wal.html
- https://www.sqlite.org/pragma.html
- https://www2.sqlite.org/releaselog/3_51_3.html

## Promotion decision

**HOLD.** Do not promote V10 into the canonical runtime yet.

Next discriminating target work:

1. capture exact target `sqlite3_libversion`, `sqlite_source_id`, package/changelog provenance, WAL/synchronous/checkpoint settings and all connection/checkpoint callers;
2. determine fixed/backported build vs vulnerable/unknown build;
3. apply V10 in SHADOW only;
4. run same-source sibling, equal-epoch divergent-root, stale/transplanted snapshot, missing/rolled-back external-floor tests;
5. run crash/restart/checkpoint/WAL replay matrix on accepted target VPS;
6. only then enable enforcement and measure p50/p95/p99, WAL growth, checkpoint time, write amplification, RSS/CPU/storage I/O and replay equivalence.

## Re-entry

Material feedback is emitted to Frank, ClayCode, ClayGraph, Hyperposition, GWT, Emergenz, Harness and UnifiedDB. The run intentionally does not duplicate the already-PASS effect execution-generation provider fence.
