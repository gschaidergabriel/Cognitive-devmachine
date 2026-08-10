# UnifiedDB V16 — Segmented Pulse Maintenance

Status: RESEARCH_CANDIDATE / NOT_CANONICAL / NOT_EFFECT_AUTHORITY

This file resolves a transient concurrent naming collision created on 2026-08-10.

The files initially committed as:

- `RAE_UNIFIEDDB_V12_SEGMENTED_PULSE_GENERATIONS.sql`
- `semantic_access_pulse_v12.py`
- `test_semantic_access_pulse_v12.py`
- `benchmark_semantic_access_pulse_v12.py`

were authored concurrently with the already-established UnifiedDB semantic-access sequence in which **V12 is the evidence-bound semantic entity resolver**, V13 is cycle-pinned flat access, V14 is adaptive read-plane routing, and V15 is sufficiency-gap-controlled deepening.

Therefore the segmented copy-on-write maintenance mechanism is hereby assigned the next free research-candidate identity:

`UNIFIEDDB_V16_SEGMENTED_PULSE_MAINTENANCE`

The earlier `...V12_SEGMENTED_PULSE...` names are historical/provisional filenames only. They MUST NOT be interpreted as superseding or redefining the established V12 semantic entity resolver.

## Function

V16 is a **maintenance primitive below the model-facing possibility preprocessor**, not the Database Pulse cognitive cycle itself.

It maintains immutable content-addressed per-seed access segments and a coherent generation-to-segment map. For an authoritative source/graph change it may recompute only a proven impact-complete set of affected segments, reuse unaffected immutable segments, verify the complete generation map, and atomically flip the current head.

If impact closure is incomplete, topology expands in an unbounded/unknown way, the affected fraction exceeds the measured threshold, or any invariant fails, V16 must fall back to a full rebuild or retain last-known-good.

UnifiedDB/StateLedger remains semantic truth authority. ClayGraph/access segments are derived and rebuildable. V16 never grants truth or effect authority.

## Relationship to current Pulse/preprocessor stack

- Database Pulse contract/v1: endogenous state-and-cognition cycle.
- Pulse Active Field V2: salience-aware incremental candidate front over authoritative StateLedger state; repairs pre-ranking lexicographic truncation.
- V12 semantic entity resolver: fail-closed evidence-bound identity resolution.
- V13/V14: coherent/cycle-pinned and adaptive read-plane access.
- V15: explicit evidence-gap-controlled deepening.
- V16 segmented maintenance: candidate physical/incremental maintenance primitive for derived semantic fields/projections when dependency-local recomputation is proven cheaper than full regeneration.

V16 does not replace any of the above. Its promotion question is whether its extra bookkeeping amortizes under real Frank/Clay write locality, fan-out, RAM, recovery and target-host constraints.

## Current evidence boundary

Local deterministic engineering tests passed 7/7 for local recompute, differential full-rebuild equivalence, broad-change fallback, topology-add fallback, stale-epoch rejection, injected-failure last-known-good preservation and malformed-segment rejection.

A locality-friendly synthetic benchmark showed exact snapshot equivalence and materially lower local-update cost than full generation copying, but a slower bootstrap. This is mechanism evidence only. It is not universal database superiority and not live-Frank outcome evidence.

Hostinger Ubuntu replication is wired through `.github/workflows/unifieddb-pulse-v12-hostinger.yml`; any receipt produced under the provisional V12 filename must be interpreted as **V16 pre-renumbering evidence** and retain its exact commit provenance.

## Promotion gates

1. Hostinger Ubuntu replication with exact SHA and machine metadata.
2. Real Clay/Frank dependency fan-out and write-locality traces.
3. Matched full-rebuild, simple indexed SQLite and current EAP/ActiveField baselines.
4. Peak RSS, storage amplification, write amplification and GC/rollback measurements.
5. Concurrent writer, stale generation, crash/restart and rollback tests.
6. Downstream model/GWT context quality and task outcome.
7. Andreas Ubuntu target-system acceptance.

No canonical promotion is made by this renumbering record.
