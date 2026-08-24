# MiniUnifiedDB Cognition DB Guards v1

Status: **SOURCE HARDENING CANDIDATE / RUNTIME UNVERIFIED**

This guard layer hardens the already-canonical `tools/miniunifieddb_cognition_store_v1.py` tables. It creates **triggers only** and introduces no second database, table family, cognition store, truth authority, effect path, identity, or recovery ledger.

## Observed gaps

### 1. Generation check/write race

The canonical store checks `entity_state.generation` in Python before inserting object admissions, boot bindings, and causal-turn bindings. The database schema does not independently repeat that live-generation check at INSERT time.

A concurrency schedule can therefore be:

1. caller reads live generation `g`;
2. another canonical writer advances `entity_state.generation` to `g+1` and commits;
3. the first caller continues with an INSERT carrying generation `g`.

Application-side validation alone is insufficient to prove that step 3 cannot materialize stale cognition ancestry. The database must reject it at the write boundary.

### 2. Prior-generation admission reuse

Current canonical store source still resolves cognition-object admission with `admitted_generation <= entity_generation`. A repair PR for exact equality was closed unmerged. Prior-generation admission can therefore satisfy the Python pre-check for a new boot generation unless the database write boundary independently requires exact-current-generation admission.

### 3. Transaction-preserving bootstrap

Current canonical `install_schema()` explicitly stays inside the caller's `BEGIN IMMEDIATE` transaction and forbids `executescript()` because Python's sqlite wrapper may commit before running it. A guard installer that used `executescript()` would split the same authority boundary it is supposed to strengthen.

The v1 guard installer therefore uses individual `Connection.execute()` calls for each `CREATE TRIGGER` and never commits or rolls back the caller's transaction.

## Guard contract

`tools/miniunifieddb_cognition_db_guards_v1.py` installs 11 triggers on the existing `mini_cognition_*` tables:

- object-admission INSERT requires `NEW.admitted_generation == entity_state.generation`;
- boot-binding INSERT requires exact live generation, the canonical boot schema, and an **exact-current-generation** admission for every required boot identity;
- turn-binding INSERT requires exact live generation, the canonical turn schema, and a boot binding from that same generation;
- cognition objects, object admissions, boot bindings, and turn bindings reject direct UPDATE and DELETE after admission.

The guard module refuses installation unless the existing canonical store tables and `entity_state` already exist. `guard_status()` verifies the expected trigger set, reports `creates_tables=false`, and identifies the installer as transaction-preserving.

## Why append-only

The cognition contract describes immutable cognition-object identities, explicit generation-bound admissions, one boot binding per generation, and exact causal-turn bindings. Allowing arbitrary direct SQL UPDATE/DELETE would permit a later caller to rewrite or erase the provenance ancestry that a prior turn used. Corrections therefore belong in a new generation/new binding, not in-place mutation of admitted evidence.

Old admissions remain durable evidence but are not current-generation runtime authority.

## Regression obligations

The source tests cover four distinct classes:

1. post-check generation advance before a direct INSERT;
2. direct SQL attempt to construct a new-generation boot binding from only prior-generation admissions;
3. the current canonical `store.admit_boot_binding()` API attempting the same prior-generation reuse while guards are installed;
4. `BEGIN IMMEDIATE -> store.install_schema -> guard.install_guards` remaining one transaction, with rollback removing both newly created cognition tables and triggers.

The third case makes the guard a real final enforcement boundary even while the application helper still contains `<=`. The fourth prevents a false security improvement that silently commits the bootstrap halfway through.

## Coordination boundary

The persisted-row digest reconstruction/read-integrity repair is already merged into the canonical store and is not duplicated here. The earlier parallel exact-generation API repair was closed unmerged; this lane owns the database-level enforcement of that invariant without creating another store.

## Authority

`MiniUnifiedDB = canonical durable authority`

`DB guards = integrity constraints only`

`Cognition binding = candidate/provenance admission only`

`EffectGate = only real-effect authority`

The guards cannot promote model/J-Space/GWT/HCU output to truth and cannot perform external effects.

## Integration gate

When the canonical cognition-store schema is installed in the retained `pipeline_init`/bootstrap path, install these guards immediately afterward in the **same transaction** and same MiniUnifiedDB before any cognition object/admission/binding write is allowed.

Then execute the exact integrated source on an actually-started authorized isolated executor. Required falsifiers include a post-check generation advance before INSERT, direct stale boot/turn writes, prior-generation admission reuse through both direct SQL and canonical store API, transaction rollback, unadmitted boot-object injection, and direct UPDATE/DELETE mutation attempts.

Until that exact integration executes, this remains source hardening only and grants zero runtime/model/J-Space/GWT/Claude/HCU/whole-product credit.
