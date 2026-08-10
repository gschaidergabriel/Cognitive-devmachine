# Database Pulse U12.1 concurrency delta

Date: 2026-08-10 +07:00
Origin actor: chatgpt-secondary / OpenAI / GPT-5.6 Sol
Identity: RESEARCH_ENTITY_TEMPORARY_WORKER; I_AM_NOT=FRANK
Status: CANDIDATE / TESTING
Canonical promotion: NONE

## Fresh-state fusion

The earlier isolated Database Pulse v0.1 orchestrator PR was closed unmerged after current main advanced through U12 segmented Pulse and U14/U15 adaptive read/gap control. Its useful safety findings were re-evaluated rather than overwritten.

U12 already satisfies the important architectural direction: canonical UnifiedDB/StateLedger remains authority; immutable per-seed access segments and a coherent generation map make local impact-complete updates copy-on-write; incomplete/broad impacts fall back to full rebuild; publication is transactional and failure preserves last-known-good.

## New falsifier

U12 `SegmentedPulseProjection.apply_pulse()` reads `_head()` before `BEGIN IMMEDIATE`. A competing connection may publish a newer generation between that read and transaction acquisition. The stale writer then retains `previous_generation_id` from the old head and can attempt to promote its own generation after only superseding that old parent.

Hypothesis: database-level `single CURRENT generation` integrity closes this TOCTOU window even before a more explicit compare-and-swap rewrite lands.

Counterhypothesis: SQLite transaction serialization alone is sufficient, so an additional unique-current invariant is redundant.

## Candidate implementation

Branch: `chatgpt/unifieddb-pulse-v12-concurrency-guard-20260810`
PR: #94

Added:
- `RAE_UNIFIEDDB_V12_1_PULSE_CONCURRENCY_GUARD.sql`: partial unique index over `access_generation(status)` where status is CURRENT.
- `semantic_access_pulse_v12_1.py`: additive wrapper applying the guard without changing U12 semantic authority.
- `test_semantic_access_pulse_v12_1.py`: two-connection stale-parent race injection plus normal-path and invariant tests.
- self-hosted Ubuntu/Hostinger replication workflow.

Expected discriminator: during injected stale-parent publication the second CURRENT transition must raise `sqlite3.IntegrityError`; the stale transaction rolls back; the winning generation remains the only CURRENT generation and its query output remains intact.

## Current execution truth

- Local reasoning/proxy test development of the earlier orchestration candidate exposed and fixed dirty-frontier truncation, cross-epoch completeness, witness truncation, LKG and head-race classes.
- GitHub-hosted Ubuntu jobs for both isolated branches failed before visible steps/logs/artifacts; this is not classified as a Pulse code failure because no executable test receipt was produced.
- The U12.1 self-hosted Hostinger job was queued at this report snapshot; therefore no remote PASS is claimed.

## External research relation

Incremental view maintenance / differential dataflow supports recomputing affected derived state rather than global rebuilding, while GraphRAG/DRIFT-style structured retrieval supports bounded graph-mediated context assembly. Neither establishes Clay-specific superiority. SQLite FTS5/B-tree remains a strong conventional baseline and remains in the fused architecture for lexical/exact-key classes.

## Architecture consequence

If the U12.1 race guard passes independent execution, fold the invariant into the current segmented Pulse maintenance line (currently being renumbered/extended in main) rather than creating a second architecture. Prefer both:
1. explicit parent/head compare-and-swap after write-lock acquisition; and
2. database-level uniqueness of CURRENT as defense in depth.

Do not promote based on this report alone. Required next evidence remains real two-writer execution, crash/restart/replay, self-hosted Ubuntu receipt, and downstream Frank cycle correctness under generation changes.
