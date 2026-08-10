# FRANK VPS Telemetry Database Directive

**Status:** PROJECT-OWNER FIXED OPERATION LAW
**Owner instruction date:** 2026-08-10
**Scope:** persistent Frank VPS runtime, all Frank modules, Clay/Research Entity analysis, MCP, build-history and recovery

## Purpose

The VPS must maintain one bounded, queryable telemetry database that collects the important operational and cognitive-state events of Frank and its modules with enough metadata to reconstruct and analyze how states evolve over time.

The database exists for surgical debugging/research, longitudinal state analysis, causal episode reconstruction, regression discovery and runtime health. It is not an unbounded raw-log dump.

## Default location and hard storage budget

Default directory:

`/srv/frank-telemetry`

Default SQLite database:

`/srv/frank-telemetry/frank_telemetry.sqlite3`

Total telemetry storage budget is **10 GiB maximum** for the database, WAL/journal and telemetry-owned auxiliary state together. The implementation must stay below that budget by design rather than relying on manual cleanup.

Recommended default allocation:

- main SQLite DB hard page limit: <= 9 GiB;
- WAL/journal target: <= 256 MiB;
- remaining headroom for SQLite metadata, temporary maintenance and service state;
- pressure cleanup begins well before the absolute limit.

## Event schema requirements

Important events must be classified with at least:

- event id and event timestamp;
- ingest timestamp;
- module/component;
- category/event type;
- severity/priority;
- message/summary;
- structured JSON payload;
- correlation/request id;
- episode/GWT episode id where relevant;
- session/conversation id where relevant;
- build/deployment id;
- model/model-hash/mmproj identity where relevant;
- source/provenance class;
- state key/entity id where relevant;
- previous and next state hashes/values or a structured state delta;
- parent/causal predecessor event where known;
- tags;
- retention class;
- schema version.

## Important categories

At minimum support filterable categories for:

- `STATE_DELTA`;
- `GWT` selection/ignition/broadcast/reconstruction/uptake/causal-use/outcome/re-entry;
- `RETINA` / visual evidence/familiarity/open-set/change detection;
- `NEEDLE` routing/classification;
- `MEMORY` read/write/retrieval/correction/forget/recovery;
- `WORLD_MODEL`;
- `SELF_MODEL`;
- `GOAL`;
- `TOOL` / effect proposal/execution/result;
- `API` request/response/error/latency;
- `MODEL` inference/model load/context/quantization;
- `BUILD` / deployment / version transition;
- `RECOVERY` / restart / crash / rollback;
- `SECURITY` / authority rejection / stale evidence / token-auth failure without storing tokens;
- `PERFORMANCE` / latency/resource samples;
- `ERROR` / warning / exception;
- `RESEARCH_RECEIPT` / benchmark/test linkage.

## Search/query requirements

Clay/Research Entity must be able to retrieve surgically by combinations of:

- time window;
- module;
- category;
- severity;
- correlation/session/episode/build id;
- state key/entity id;
- tags;
- free-text search;
- JSON payload fields;
- before/after state hash;
- causal parent/predecessor;
- latency/resource threshold;
- retained priority.

Provide dedicated state-timeline queries that reconstruct ordered deltas for one state/entity/episode without loading unrelated logs.

## Retention and bounded-growth law

The telemetry DB is priority-aware and bounded.

Default retention preference from highest to lowest:

1. P0/P1 errors, security/authority failures, crash/recovery and rollback;
2. state transitions causally used in GWT/action/memory/world/self/goal changes;
3. build/deployment/model-identity transitions and benchmark receipts;
4. user/API request-response metadata and important tool outcomes;
5. warnings and sampled performance traces;
6. repetitive debug/info traces.

When storage pressure rises, compact/delete oldest low-retention events first. Repetitive high-frequency telemetry should be sampled/aggregated before ingestion when possible. Important retained events may outlive ordinary events, but the total database still may not exceed the fixed budget.

No retention mechanism may silently delete P0/P1 or retained causal-state evidence merely to preserve debug noise. If the database cannot preserve higher-priority evidence inside the hard budget, emit a storage-pressure error and increase aggregation/drop of lower classes.

## Privacy/secret law

Never store raw API tokens, passwords, private keys, cookies or secret environment values. Redact common authorization fields before persistence. Large binary/image/model payloads are referenced by content hash/path/receipt rather than embedded in SQLite.

## Build-history relation

Telemetry events carry `build_id` / deployment identity and the `/srv/clay-history` Git ledger records schema/config/build transitions. The history ledger provides immutable build chronology; the telemetry DB provides bounded high-volume operational/state evidence.

## Acceptance

The feature is complete only when live VPS receipts prove:

- modules can ingest events locally;
- indexed filters and FTS work;
- state timeline queries reconstruct ordered changes;
- JSON-field filtering works;
- retention pressure removes low-priority data before high-priority evidence;
- DB+WAL remains within configured 10 GiB budget under stress;
- secrets are redacted;
- restart/recovery preserves queryability;
- MCP can query the telemetry surgically.

## Compact invariant

`IMPORTANT_FRANK_EVENT -> TYPED_METADATA -> BOUNDED_SQLITE -> SURGICAL_QUERY`

and

`TELEMETRY_TOTAL_BYTES <= 10 GiB`
