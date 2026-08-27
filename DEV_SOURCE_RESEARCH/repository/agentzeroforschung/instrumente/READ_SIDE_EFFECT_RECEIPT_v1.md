# READ_SIDE_EFFECT_RECEIPT/v1

Purpose: detect and classify durable DB/schema mutations reachable from operations that are presented as reads, observations, GETs, probes, status checks or measurements.

## Trigger

Emit one receipt for every classified READ operation when any of these occur:

- SQL statement class is not SELECT/read-only PRAGMA;
- transaction upgrades to write;
- schema hash changes;
- row count changes outside explicitly allowed telemetry/logging;
- SQLite reports write-lock contention from a read-classified caller.

A no-side-effect READ may be sampled rather than fully logged once the instrument itself is validated.

## Receipt fields

- `receipt_version`: `READ_SIDE_EFFECT_RECEIPT/v1`
- `request_id`
- `caller_type`: HUMAN_HTTP | HUMAN_CHAT | AUTONOMY | ARCHITECT | EXPORTER | TEST | INTERNAL_TIMER | UNKNOWN
- `caller_id`: route/function/job identifier
- `http_method`: nullable
- `user_id`: nullable
- `session_id`: nullable
- `turn_id`: nullable
- `causal_id`: nullable; if none, explicit `OUT_OF_TURN`
- `entity_generation`
- `db_identity`
- `schema_hash_before`
- `schema_hash_after`
- `schema_version_before`
- `schema_version_after`
- `sql_classes`: ordered list from SELECT | PRAGMA_READ | DDL | DML | TX_CONTROL | UNKNOWN
- `write_transaction_opened`: boolean
- `objects_created`
- `objects_changed`
- `rows_changed`
- `lock_wait_ms`
- `sqlite_result`
- `mutation_reason`: MIGRATION | STARTUP | LAZY_ENSURE | USER_WRITE | TELEMETRY | UNKNOWN
- `declared_operation_class`: READ | WRITE | MIXED | UNKNOWN
- `observed_operation_class`: READ | WRITE | MIXED | UNKNOWN
- `classification_match`: boolean
- `ts`

## Core invariants

`CLASSIFIED_READ -> no unreceipted durable semantic/schema mutation`

`GET/OBSERVE/PROBE -> mutation authority is never inferred from the route name`

`CODE_PRESENT != SCHEMA_MATERIALIZED != DATA_OBSERVED != BEHAVIOR_OBSERVED`

## Gen247 motivating case

Source-confirmed:

- `bug_meldung.lesen_fuer_nutzer`, `lesen_eins` and `offene_fuer_architekt` call `sicherstellen()` before SELECT.
- `sicherstellen()` can execute CREATE TABLE + CREATE INDEX against canonical UnifiedDB.
- `terminal_gateway` exposes GET paths through these methods.
- `bewertung.lesen_fuer_sitzung()` repeats the same pattern.

Snapshot-observed:

- Gen246 (`f56913ac...`) schema rebuild: 131 tables.
- first Gen247 (`0035fb4c...`) schema rebuild: 132 tables.
- newly materialized table: `eos_bug_hypothesen` (+ indexes).
- `bug_meldung.py` blob is identical across the boundary (`854c1794...`).
- `terminal_gateway.py` blob is identical across the boundary (`29afc2e7...`).

Therefore schema appearance is runtime activation of pre-existing code, not code rollout.

Unknown: which caller caused first materialization. This instrument exists to make that unknowable transition joinable next time.

## Paired discriminator

Use two GET/read paths against the same frozen disposable DB identity:

A. `GET /readyz` / `_runtime_ready()` as the negative control. Current Gen247 source labels `_runtime_ready()` read-only and its UnifiedDB path consists of SELECTs; it should leave schema/data identity unchanged.

B. `GET /api/bug` on a database where `eos_bug_hypothesen` has deliberately not been materialized. Current source reaches `lesen_fuer_nutzer() -> sicherstellen() -> CREATE TABLE/INDEX -> SELECT`.

Record before/after schema hash, statement classes, SQLite write-transaction presence, lock wait and row delta.

Expected discriminator if H-RSM1 is correct:

- A: `declared=READ`, `observed=READ`, no schema delta.
- B: `declared=READ`, `observed=MIXED/WRITE`, schema delta on first access only.

Repeat B once after materialization. The second call should become observationally read-only if lazy initialization is the sole cause. This separates first-touch activation from a permanently mutating GET path.

## Preferred architecture

Best: run explicit versioned migrations/startup schema creation before serving traffic, then use read-only/query-only connections for read surfaces.

Fallback: if lazy initialization remains, treat first schema creation as a typed `SCHEMA_ACTIVATION` event and bind caller, generation, before/after schema identity and created objects.
