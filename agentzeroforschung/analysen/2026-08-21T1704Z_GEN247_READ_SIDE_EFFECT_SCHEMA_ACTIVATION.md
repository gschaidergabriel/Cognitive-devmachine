# Gen247: Read-side schema mutation and latent capability activation

Status: SOURCE_CONFIRMED + SNAPSHOT_OBSERVED. Research-only; no AgentZero product bytes changed.

## Why this is new

Generation 246 export `f56913ac50e5b3539d6279ab3ee9ee482f024d75` rebuilt 131 live UnifiedDB tables. The first Generation 247 export `0035fb4cce1d2104b61aa37cea3e8a966a33ca44` rebuilt 132. The added live schema object is `eos_bug_hypothesen` plus its two indexes.

This is not a code-introduction event. `agentZero/code/produkt/bug_meldung.py` has the identical blob `854c1794bd225c98903a2a85a76b07b048ee5d07` in Gen246 and Gen247. `terminal_gateway.py` likewise stays blob-identical at `29afc2e7755a0fc6bffc7a3f48680e90ec601e59`; the `/api/bug` surface already existed before the table appeared.

Therefore the observed 131 -> 132 transition is a runtime materialization of an already-present latent capability, not source rollout.

## Source mechanism

`bug_meldung.sicherstellen(db)` executes `CREATE TABLE IF NOT EXISTS eos_bug_hypothesen(...)` and two `CREATE INDEX IF NOT EXISTS ...` statements.

Crucially, every operation calls `sicherstellen()`, including the read methods:

- `lesen_fuer_nutzer()` -> `sicherstellen()` -> SELECT
- `lesen_eins()` -> `sicherstellen()` -> SELECT
- `offene_fuer_architekt()` -> `sicherstellen()` -> SELECT

`terminal_gateway` exposes `GET /api/bug` and `GET /api/bug/{bug_id}` through those read methods. Thus a semantically read-only HTTP request can perform durable DDL against canonical UnifiedDB before it reads.

The same design pattern exists independently in `bewertung.py`: `lesen_fuer_sitzung()` invokes `sicherstellen()` before its SELECT, and `sicherstellen()` creates `eos_bewertungen` and its index if missing.

## External standards cross-check

RFC 9110 section 9.2.1 defines GET as a safe method whose requested semantics are essentially read-only. It allows incidental implementation side effects, but the client is not requesting a state transition.

SQLite's transaction documentation classifies CREATE as a write statement; if no transaction is active, the statement starts a transaction and the implicit transaction is committed when the statement finishes.

Therefore the EntityOS pattern is accurately described as:

`READ_REQUEST -> LAZY_SCHEMA_ENSURE -> WRITE_TRANSACTION -> READ`

not as a pure read.

## What is proven and what is not

PROVEN / OBSERVED:

1. Gen246 live schema did not contain `eos_bug_hypothesen`; Gen247 did.
2. Bug-channel source and HTTP surface were already present and blob-identical across that boundary.
3. Read methods are capable of creating the schema.
4. The same lazy-schema-on-read pattern exists in the rating subsystem.
5. Gen246 -> Gen247 kept chat/causal/workspace/retrieval counts stable, so the schema materialization need not correspond to a normal cognitive turn.

NOT PROVEN:

- Which concrete caller first materialized `eos_bug_hypothesen` between the two exports.
- Whether it was a human GET, a human POST, architect polling, status work, a test, or another direct host-side caller.
- Whether the first materialization caused measurable lock contention.
- Whether other modules repeat this pattern until a repository-wide scan is run.

This missing caller identity is itself the measurement gap.

## New hypothesis class

### H-RSM1: Observer activation
A read/poll of an uninitialized capability can change canonical state merely by observing it.

### H-RSM2: Schema-snapshot confounding
A later export can make a capability look newly introduced even though only its lazy runtime schema was first touched.

### H-RSM3: Read-path lock interference
Rare first reads can unexpectedly become SQLite write transactions and contend with normal writers.

### H-RSM4: Hidden activation provenance
Because lazy CREATE has no activation event receipt, `schema appeared` cannot be joined to the actor/request/reason that caused it.

Counterhypothesis: this is harmless one-time initialization. That remains plausible for operational impact, but it does not remove the provenance ambiguity or the fact that a read path is write-capable.

## Instrument: READ_SIDE_EFFECT_RECEIPT/v1

For every externally or internally classified READ path record:

- request_id / caller_type / user_id if applicable
- route or function
- generation
- db identity
- schema hash before
- `PRAGMA data_version` / schema_version before and after where useful
- ordered SQL statement classes: SELECT | DDL | DML | PRAGMA | UNKNOWN
- write transaction opened: yes/no
- tables/indexes created or changed
- row delta
- lock wait / SQLITE_BUSY result
- causal_id if a cognitive turn exists, otherwise explicit `OUT_OF_TURN`
- reason: MIGRATION | STARTUP | LAZY_ENSURE | USER_WRITE | UNKNOWN

Invariant:

`CLASSIFIED_READ -> no unreceipted durable semantic/schema mutation`

A stricter implementation option is to run read-only endpoint DB access behind a read-only/query-only connection so accidental DDL fails closed.

## Architectural recommendation

Move schema creation out of per-operation read/write helpers and into one explicit, versioned migration/startup boundary. Keep read APIs read-only after admission. If lazy initialization is retained for compatibility, emit an immutable `SCHEMA_ACTIVATION` receipt binding caller, generation, old/new schema hash and created objects.

Also distinguish four capability states in measurements:

1. `CODE_PRESENT`
2. `SCHEMA_MATERIALIZED`
3. `DATA_OBSERVED`
4. `BEHAVIOR_OBSERVED`

Do not infer one from another.

## Fusion with existing AgentZero research

This is the same general provenance problem already seen in F94 read-reactivity hypotheses, feedback current-state loss and evidence-spine lineage gaps: observation, projection and source state must be separated.

New general rule:

`OBSERVATION_PATH != MUTATION_AUTHORITY`

and

`CAPABILITY_CODE_PRESENT != CAPABILITY_RUNTIME_ACTIVATED`.
