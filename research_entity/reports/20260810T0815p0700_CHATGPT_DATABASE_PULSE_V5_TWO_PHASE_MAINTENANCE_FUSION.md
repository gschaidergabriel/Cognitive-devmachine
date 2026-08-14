# FRANK Database Pulse V5 — Two-Phase Maintenance Fusion and Atomic Audit

Date: 2026-08-10 +07:00  
Origin actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Identity: `RESEARCH_ENTITY_TEMPORARY_WORKER`  
Status: `BUILT / ADVERSARIAL_TESTS_COMMITTED / UBUNTU RECEIPTS PENDING / NOT PROMOTED`

## Why V5 exists

V1→V4 established a progressively stronger invariant:

1. V1 bounded lexicographic census before salience ranking can miss a later high-salience state.
2. V2 repairs correctness by materializing salience before the candidate budget, but adds a
   second candidate table and explicit refresh surface.
3. V3 shows the same deterministic scalar ordering can live directly on authoritative
   StateLedger with a partial SQLite expression index; no second semantic candidate table is
   required.
4. V4 separates semantic correctness from physical acceleration and makes a correct online
   score-before-LIMIT query available when an index has not been amortized.
5. V5 removes the final hidden cognition-side schema work: **Database Pulse never creates or
   drops the index.** Physical maintenance runs between Pulses against a newly validated current
   post-Pulse epoch.

Current strongest research shape:

```text
authoritative StateLedger event/state transaction
-> inter-Pulse physical maintenance controller (optional)
-> Database Pulse cognition/read phase (schema read-only)
-> authoritative score-before-LIMIT candidate generation
-> bounded focus / GWT context
-> optional model organ => UNKNOWN candidate only
-> Pulse receipt / verified downstream outcome / causal re-entry
-> next post-Pulse epoch
-> replan physical maintenance from fresh telemetry
```

## Critical epoch insight

A lifecycle plan computed before a Pulse cannot simply be applied after that Pulse because the
Pulse receipt itself advances the authoritative ledger epoch. Therefore the correct contract is:

```text
Pulse N reads at epoch E
-> Pulse N commits receipt at E+1
-> old maintenance plan for E is stale
-> maintenance controller replans at E+1
-> BUILD/DROP/NONE executes between Pulses
-> Pulse N+1 reads the prepared physical state without schema mutation
```

Runtime V5 explicitly records `REPLAN_REQUIRED_AT_NEW_EPOCH` for this reason.

## Runtime V5 behavior

Files:

- `research_entity/runtime/database_pulse_rank_path_v5.py`
- `research_entity/runtime/database_pulse_runtime_v5.py`
- `research_entity/runtime/test_database_pulse_rank_path_v5.py`
- `research_entity/runtime/test_database_pulse_rank_path_v5_atomic.py`
- `research_entity/runtime/test_database_pulse_runtime_v5.py`
- `research_entity/runtime/test_database_pulse_runtime_v5_adversarial.py`
- `tools/database_pulse_rank_path_v5_benchmark.py`
- `.github/workflows/database-pulse-v5-two-phase-probe.yml`

Read modes:

- `COMPILED_INDEX`: economics wants compiled and a prior maintenance phase already built it.
- `ONLINE_PENDING_COMPILE`: economics wants compiled but index is absent; cognition remains
  correct online now and requests BUILD_INDEX for a later maintenance phase.
- `ONLINE_PENDING_DECOMPILE`: economics wants online but an index remains; query forces
  `NOT INDEXED` immediately and requests DROP_INDEX later.
- `ONLINE`: no index desired/present.

Missing telemetry never mints economics. Default runtime policy remains
`UNMEASURED_FAIL_ONLINE` and creates no index.

## Semantic and authority invariants preserved

- StateLedger remains semantic/provenance authority.
- Physical index is disposable/rebuildable.
- Candidate ordering remains the deterministic authoritative score before candidate LIMIT.
- `pulse_count` is independent from `state_transition_count`.
- Pure Pulse bookkeeping has `state_transition_count=0`.
- Optional model output is stored `UNKNOWN`, never admitted semantic truth by generation alone.
- tool/effect authority remains zero for this runtime path.
- stale basis fails before policy/index side effects.
- pause does not invoke physical optimization.
- Pulse ID retries remain idempotent.
- truthful re-entry remains lesionable against NO_REENTRY.

## New V5 physical-maintenance hardening

A deep recovery audit found two physical-state defects in the first V5 maintenance candidate:

1. successful CREATE/DROP returned a Python receipt but did not durably persist the physical
   action atomically with the schema mutation;
2. a maintenance plan checked semantic epoch/root but not whether the disposable physical index
   had independently changed since planning.

The V5 rank path was hardened with:

### Semantic + physical compare-and-swap

Before maintenance:

```text
plan.basis_epoch == current ledger epoch
AND plan.semantic_state_hash == current semantic root
AND plan.actual_index_present == current physical index presence
```

Any physical mismatch raises `RankPhysicalStateStale` and requires replan.

### Atomic DDL + physical receipt

For actual BUILD/DROP:

```text
BEGIN IMMEDIATE
-> revalidate semantic CAS
-> revalidate physical CAS
-> create/verify physical maintenance-log table
-> CREATE INDEX or DROP INDEX
-> verify semantic_state_hash unchanged
-> verify trace_root_hash unchanged
-> INSERT physical maintenance receipt
-> COMMIT
```

If receipt insertion fails, SQLite rolls the DDL back in the same transaction. This removes the
crash window in which the real accelerator changes without a durable physical audit record.

Durable physical receipts are stored in:

`pulse_rank_maintenance_receipts_v5`

with receipt id, lifecycle plan hash, basis epoch, action/status, before/after physical index
presence, semantic root before/after, trace root before/after, execution timestamp and explicit
non-semantic authority class.

## Atomic maintenance falsifiers

`test_database_pulse_rank_path_v5_atomic.py` adds direct adversarial cases:

- successful BUILD is durably receipted and leaves semantic/trace roots fixed;
- replaying the same BUILD plan after the index exists is physical-CAS rejected instead of
  falsely returning another successful build;
- deliberately broken receipt-table schema causes receipt INSERT failure and must roll back
  CREATE INDEX;
- the same fault injection must roll back DROP INDEX;
- an external physical index change invalidates a plan even while semantic epoch/root match;
- successful DROP is durably receipted and roots remain fixed.

Runtime adversarial tests also cover:

- no measured policy => no index;
- idempotent Pulse retry does not reconsult policy;
- stale Pulse basis fails before policy invocation;
- maintenance BUILD/DROP keeps semantic/trace roots unchanged;
- truthful re-entry versus NO_REENTRY changes focus without effect authority.

## Remaining provenance hardening

The new atomic physical log currently persists the lifecycle plan hash and physical/semantic
before/after state, but the base log does not yet store `actor` and `policy_provenance_ref` as
first-class atomic columns. The Runtime maintenance wrapper carries those fields in its returned
wrapper receipt, so the decision is reconstructable only if that wrapper receipt is retained.

This is a real remaining audit improvement and should be resolved with a backward-compatible
physical-log migration before production promotion. It is intentionally left explicit rather
than hidden behind a claimed complete audit trail.

## Execution state

Source, tests and workflows are committed to the shared repository.

The V5 Ubuntu probe runs the same stack on:

- GitHub-hosted `ubuntu-latest` as auxiliary preflight;
- Hostinger `[self-hosted, Linux, X64]` as the project's real remote Ubuntu lane.

The Hostinger job is configured to persist:

`research_entity/benchmarks/database_pulse/rank_path_v5_vps.json`

with exact runner/Python/SQLite/hardware/filesystem metadata plus current program-progress
resolver output.

At the time of this report, **no V3/V4/V5 Hostinger benchmark receipt commit has appeared**.
Therefore remote status remains `PENDING/UNKNOWN`, not PASS. GitHub RW itself is healthy and
other evidence commits exist today, so this is treated as an execution-lane/job-specific
blocker rather than silently assuming success.

A direct local shell checkout was also attempted but failed before code execution because the
shell environment could not resolve `github.com`; this is a network/DNS limitation of that
local execution lane, not a code PASS or code FAIL.

## Current scientific position

### Supported

- Database Pulse can be modeled as an endogenous zero-model-capable cycle over authoritative
  transactional state rather than a continuous LLM loop.
- Candidate ranking must happen before bounded truncation for salience semantics to be valid.
- For the present deterministic scalar score, a conventional authoritative SQLite expression
  sort/index is a strong simpler mechanism versus a second candidate table.
- Physical compilation should be treated as an amortized optimization, not semantic truth.
- Schema maintenance should be separated from the cognition read phase.
- Physical maintenance needs semantic CAS, physical CAS, rollback and durable receipts.

### Refuted / not supported

- “UnifiedDB must be a novel physical database engine to be better.”
- “Clay-specific storage should replace ordinary indexes everywhere.”
- “Any successful Pulse implies a substantive state transition.”
- “An LLM call is required for Frank to Pulse.”
- “A high-salience state can safely be ranked after an arbitrary lexical LIMIT.”
- “A successful physical CREATE/DROP without a durable audit receipt is sufficient recovery
  evidence.”

### Still unproven

- V5 beats V3/V4 on exact Hostinger/Andreas hardware under realistic read/write churn.
- the Pulse horizon policy has lower regret than ALWAYS_ONLINE/ALWAYS_COMPILE under regime
  changes.
- improved candidate context produces better downstream Frank answer/tool-route/calibration
  quality rather than only retrieval correctness.
- the current fixed salience weighting is the best Frank controller.

## Next discriminating work

1. Obtain/consume actual V5 GitHub-hosted and Hostinger receipts; any test failure supersedes
   architectural optimism.
2. Persist `actor` + `policy_provenance_ref` atomically in the physical maintenance log via a
   backward-compatible migration.
3. Measure p50/p95/p99 read latency, cold build/drop, StateLedger write amplification, WAL/file
   bytes, CPU/RSS and lock/reader-writer behavior.
4. Run kill/crash/restart around maintenance commit boundaries and verify physical receipt/index
   equivalence after reopen.
5. Run policy-regret traces against ALWAYS_ONLINE, ALWAYS_COMPILE and oracle.
6. Run fair conventional SQLite/PostgreSQL baselines with equivalent semantic contracts.
7. Measure downstream Frank cognitive/tool outcomes and token/context savings.
8. Re-run exact accepted stack on Andreas' final Ubuntu target before any v0.1 release claim.

## Current architecture delta

```text
CANDIDATE / TESTING

Semantic Pulse path:
  authoritative StateLedger
  -> correct score-before-LIMIT candidate generation
  -> bounded focus
  -> optional UNKNOWN model organ
  -> outcome/re-entry

Physical rank path:
  cognition phase NEVER mutates schema
  -> online or prepared-index read only

Inter-Pulse maintenance path:
  fresh post-Pulse epoch
  -> conservative lifetime/economics policy
  -> semantic CAS + physical CAS
  -> transactional CREATE/DROP + physical audit receipt
  -> semantic/trace roots must remain unchanged
  -> next Pulse consumes prepared state

No promotion until Ubuntu execution receipts and matched baseline evidence exist.
```
