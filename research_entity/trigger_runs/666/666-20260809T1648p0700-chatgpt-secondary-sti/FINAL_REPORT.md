# 666 Emergent Field Report — Semantic Transaction Isolation for Cognitive State

Run: `666-20260809T1648p0700-chatgpt-secondary-sti`
Field: `field-666-20260809T1648p0700-semantic-transaction-isolation-cd8cb4f6`
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol
Canonical parent: r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
Milestone: `BASE_CLAYCODE_RELEASE`
Seed: `14811412243250910653` (`cd8cb4f604d795bd715552f374e91d7c0df5b54b1f82a39b609519b8d760d630`)

## Spawn decision

Recent fields already covered proof-carrying adaptive state, perceptual cache coherence,
re-entry causal identifiability, memory-reconsolidation shock testing and conformal familiarity.
This run therefore selected a distinct lens combining transaction theory, event sourcing,
programming-language effects and multi-agent concurrency.

The milestone is an attractor, not a direct dispatch target. The field nevertheless has a
clear BASE relevance because current ClayCode acceptance requires async/concurrency/atomics,
runtime ABI/FFI, DB-backed service execution, deterministic semantic hashes and explicit
effect/capability boundaries.

## Research question

Can authoritative FRANK/Clay multi-field state remain replay-safe under concurrent learning,
correction, rollback and effect paths using only per-field atomics, or is snapshot/transaction
isolation required at invariant boundaries?

## External grounding

1. Berenson et al., *A Critique of ANSI SQL Isolation Levels* (MSR-TR-95-51, 1995) defines
   snapshot isolation and demonstrates that conventional isolation descriptions omit important
   concurrency anomalies.
2. PostgreSQL's Serializable isolation documentation states the operational target clearly:
   committed concurrent executions must behave like some serial execution, otherwise a
   serialization failure is raised and the transaction must be retried.

Evidence class: primary research + primary implementation documentation. These sources establish
the concurrency-control mechanism class; they do not prove the FRANK-specific hypothesis.

## Hypotheses

### H-STI-01 — invariant-level snapshot boundary
Authoritative multi-field cognitive state participating in one invariant must be observed and
committed through a snapshot-consistent or equivalent serializable boundary. Per-field atomics
alone admit fractured states.

Status after test: **SUPPORTED_WORKING_HYPOTHESIS**.

### H-STI-02 — no ClayCode syntax change yet
The needed behavior likely fits the current ClayCode direction as a typed runtime/ABI/stdlib
transaction contract. A new syntax primitive is not justified unless a real ClayCode/FRANK
counterexample proves existing semantics cannot lower it safely.

Status: **OPEN**.

### H-STI-03 — effect commit must bind state version
Consequential effect commits should bind to the authoritative state snapshot/read-set on which
the decision was made, or an equivalent guard, to prevent stale-state TOCTOU effects.

Status: **OPEN**.

## Exact synthetic experiments

### EXP-STI-01 — fractured snapshot enumeration
Initial invariant group:
`prototype_version = calibration_version = active_version = 5`.

A writer upgrades the three fields to version 6 in three ordered writes. A reader reads the same
three fields in three ordered reads. All order-preserving interleavings were exhaustively
enumerated: `C(6,3) = 20`.

Result:
- 20 legal interleavings total
- 10 coherent observations: all 5 or all 6
- 10 fractured observations mixing 5 and 6
- fractured rate: **50%**

A snapshot/atomic-group read would admit only the two coherent version states.

### EXP-STI-02 — lost update vs version-guarded commit
Two transactions each execute `read version -> write version+1` on one versioned object.
All 6 order-preserving interleavings were exhaustively enumerated.

Result:
- 2 serial interleavings: both updates survive and final version is 7
- 4 overlapping-read interleavings: naive last-write-wins reports both writes but final version
  is only 6, silently losing one update
- compare-and-swap commit detects a conflict in all 4 overlapping cases, preserving explicit
  retry/reconciliation instead of silent lineage loss

Evidence class for both: **EXACT_SYNTHETIC_MECHANISM_EXPERIMENT**, not live FRANK evidence.

## Negative results

`N-STI-01`: Per-field atomics are insufficient for the tested three-field invariant.
Exactly half of legal schedules exposed a tuple that cannot represent one committed version.

`N-STI-02`: Naive last-write-wins is not lineage-safe for concurrent versioned cognitive updates.
Four of six legal schedules silently lose one update.

## Counterhypotheses

1. **Single deterministic scheduler:** serialize all authoritative cognitive state transitions.
   This can eliminate transaction anomalies but may create latency/concurrency cost.
2. **Actor/ownership partitioning:** most state can be single-owner; only cross-owner invariant
   groups need transactions.
3. **Eventual derived state:** caches, activation and other rebuildable non-authoritative state
   may remain eventually consistent if epoch-tagged and excluded from consequential authority.

These alternatives remain OPEN and should be benchmarked rather than rejected.

## Cross-branch integration

### claycode
Route to `CC-WP-07-RUNTIME-ABI-FFI` and `CC-WP-09-CONCURRENCY-MEMORY`:
- explicit snapshot/read-set/write-set semantics;
- commit conflict and deterministic retry receipts;
- bind capability/effect intents to transaction/snapshot identity;
- no new syntax until an executable counterexample defeats ABI/stdlib lowering.

### unifieddb
Prioritize:
- invariant-group transaction/effect atomicity;
- exact snapshot/replay under concurrent updates;
- explicit serialization-conflict receipts;
- authoritative-vs-derived state classification;
- epoch/version identity for rebuildable derivatives.

### harness
Add minimized/exhaustive race tests for:
- fractured multi-field snapshots;
- lost updates;
- stale snapshot -> effect commit;
- retry after serialization conflict;
- crash between state commit and effect/outcome/re-entry.

## Minimal candidate runtime contract

`StateTxn` should carry at least:
- `txn_id`, `attempt`;
- `snapshot_epoch` and/or exact object-version read set;
- typed write set;
- invariant-group identity;
- capability/effect intents;
- commit guard;
- outcome `COMMITTED | SERIALIZATION_CONFLICT | ABORTED`;
- pre/post canonical state hashes;
- retry/replay receipt.

This is an **implementation/research candidate**, not a promoted ClayCode language primitive.

## Decision

**ROUTE_AS_RUNTIME_ABI_AND_TEST_OBLIGATION_NOT_LANGUAGE_REDESIGN.**

The field produced a concrete concurrency counterexample that matters to ClayCode BASE, UnifiedDB
and Harness. It does not justify changing ClayCode syntax today. The highest-information next test
is to implement the contract using the existing ClayCode semantic/effect basis and attempt the
DB/concurrent/FRANK application proofs. Only an executable failure should reopen language semantics.

Result:
`SUPPORTED_WORKING_HYPOTHESIS_WITH_EXACT_SYNTHETIC_COUNTEREXAMPLE_ROUTED_TO_MESH_NOT_PROMOTED`
