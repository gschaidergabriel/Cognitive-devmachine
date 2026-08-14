# UnifiedDB Segmented Pulse Maintenance S1 (SPM-S1)

Status: RESEARCH_CANDIDATE / NOT_CANONICAL / NOT_EFFECT_AUTHORITY

`SPM-S1` is the collision-free research-branch identity for the segmented copy-on-write
maintenance mechanism developed during the 2026-08-10 UnifiedDB/Database-Pulse swarm cycle.
It deliberately does **not** consume a sequential U-number, because the active U12–U16
read-plane series is being advanced concurrently by other workers.

## Purpose

SPM-S1 is a maintenance primitive **below** the model-facing possibility preprocessor. It is
not the FRANK Database Pulse cognitive cycle and it is not a second semantic truth store.

It maintains immutable, content-addressed per-seed access segments plus an atomic coherent
generation-to-segment map. For a source/graph change it may recompute only an impact-complete
set of affected segments, reuse unaffected segments, verify the generation map and atomically
publish a new head. If dependency closure is incomplete, topology expands in an unbounded or
unknown way, the affected fraction exceeds the measured threshold, or an invariant fails, it
falls back to full rebuild or retains last-known-good.

UnifiedDB/StateLedger remains semantic truth authority. ClayGraph and access segments remain
derived/rebuildable. SPM-S1 never grants truth or effect authority.

## Current stack relationship

- Database Pulse Runtime V2: endogenous evidence-gated state/cognition cycle.
- Pulse Active Field V2: salience-aware incremental candidate front before candidate-budget cut.
- U12: fail-closed evidence-bound semantic entity resolver.
- U13: cycle-pinned flat access.
- U14: adaptive cheapest-safe read-plane routing.
- U15/U15.1: typed evidence-gap-controlled deepening / surface-invariant structural plan key.
- U16: measured compile-amortization gate deciding ONLINE vs COMPILE.
- EAP: bounded topology-aware Assembly compiler when deeper dependency/possibility closure is warranted.
- SPM-S1: candidate incremental physical maintenance primitive for compiled/derived semantic fields when measured locality makes it cheaper than full regeneration.

## Audit-complete successor

The audit-complete implementation currently lives in the historical transition file
`semantic_access_pulse_v16.py`; `semantic_access_segmented_maintenance_s1.py` is the
collision-free public research alias. The implementation changes segment identity so it is
computed from exactly persisted representation: seed identity + canonical path rows +
segment-wide dependency closure. A slow deep audit reconstructs those identities and the
complete generation/head hash, allowing physical corruption to be detected without forcing
an O(N) scan into every local update hot path.

## Measured local engineering evidence

A locality-friendly deterministic fixture used 1,200 seeds, 60 clusters, 20 paths/seed,
12 local update events and 500 matched read probes.

Latest local iteration before remote exact-commit verification:

- exact segmented/full snapshot equality after every local event: 1.0;
- segmented local-update p50: 23.942 ms;
- full-generation local-update p50: 109.093 ms;
- median local-update ratio: 4.534x in favor of segmented maintenance;
- segmented bootstrap: 314.721 ms;
- full-generation bootstrap: 110.248 ms (full generation materially faster at bootstrap);
- after 14 generations: full-copy path rows 336,000 vs segmented path rows 28,800 plus 16,800 generation-map rows;
- unknown topology addition: FULL_FALLBACK;
- injected failure: last-known-good preserved.

These are synthetic mechanism measurements. They do not establish universal database
superiority, target-host acceptance or downstream cognition quality.

## Negative results preserved

1. The first prototype accidentally destroyed locality with a global per-pulse safety hash
   plus N-query verification; it was slower than full-copy maintenance. Those O(N) hot-path
   checks were removed and moved into slower audits.
2. The first content identity included per-path dependency sets but persistence retained only
   their union; exact deep reconstruction was impossible. The audit-complete successor hashes
   exactly the physically retained representation.
3. Bootstrap remains slower than full-copy in the measured local fixture. SPM-S1 therefore
   requires a measured amortization gate rather than unconditional use.

## Promotion gates

1. Exact-commit Hostinger Ubuntu execution of audit-complete tests and differential benchmark.
2. Real Frank/Clay reverse-dependency fan-out and read/write/invalidation lifetime traces.
3. Integrate with U16 compile economics: choose SPM-S1 only when expected lifetime amortizes
   its maintenance/build cost without reducing quality.
4. Matched exact-key SQLite/B-tree, FTS/hybrid, online recursive SQL, EAP and full-generation baselines.
5. Peak RSS, storage/write amplification, segment GC, rollback retention and cold recovery.
6. Concurrent-writer, crash/restart, stale-head and deliberate corruption recovery tests.
7. Downstream ActiveAssembly/GWT/model/task quality and token/context impact.
8. Andreas Ubuntu target-system acceptance.

No canonical promotion is made here.
