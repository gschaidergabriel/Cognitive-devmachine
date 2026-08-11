# UnifiedDB — V4 Fixed-SQLite Process-Crash Composition

Run: `unifieddb-20260811T2302p0700-chatgpt-secondary-v4-process-crash-composition`

Status: **ARCHITECTURE DELTA BUILT / TARGET EXPERIMENT QUEUED / PROMOTION HOLD**

## Fresh-state correction

The UnifiedDB branch has advanced beyond the earlier `SQLite 3.45.1 + WAL` diagnostic stage. Current target evidence already contains a private fixed SQLite 3.53.4 runtime, V4 `python -I -S` admission, V17 composition and a disposable current UnifiedDB+ClayGraph migrate/reopen smoke pass. Rebuilding that lane would be duplicate work.

The remaining useful question selected for this run is narrower: does process-crash recovery still hold when **every concurrent WAL writer independently crosses the actual V4 product admission boundary** before touching state?

## Architecture adjudication

Preferred current architecture is **logically unified, physically layered**:

- UnifiedDB remains authoritative typed semantic state;
- pinned SQLite 3.53.4 behind V4 is the current physical engine candidate, not semantic authority;
- ClayGraph remains a derived/rebuildable topology projection;
- retrieval/vector/FTS structures remain candidate-producing sidecars whose ids must resolve through UnifiedDB;
- the monotonic RecoveryFloor remains `KEEP_ISOLATED` from the UnifiedDB rollback domain;
- physical consolidation remains a candidate only if measurements dominate this layered design.

Four required architecture classes were retained/evaluated in `UNIFIED_DATABASE_ARCHITECTURE.claycode.json`; `C_SHARED_CANONICAL_PLUS_SIDECARS` is preferred.

## New recovery evidence law

A generic `RECOVERY PASS` is too lossy. This run splits recovery into non-substitutable evidence classes:

1. `PROCESS_CRASH` — application/process termination such as SIGKILL;
2. `OS_CRASH` — kernel/system crash or hard reboot;
3. `POWER_LOSS` — stable-power/storage flush failure boundary;
4. `LOGICAL_ROLLBACK` — stale snapshot/lineage rewind;
5. `PROJECTION_REBUILD` — derived ClayGraph/index loss or staleness;
6. `DEPLOYMENT_BOOT` — installed service must begin at the trusted V4 boundary.

Evidence may not be promoted from one class into a stronger class without a direct discriminator.

Fresh SQLite primary documentation supports this split: WAL `synchronous=FULL` adds a WAL sync on each commit, while application/process crash and power/OS failure have materially different durability semantics; checkpointing is also a distinct persistence boundary.

## Target candidate built

Target repo: `gschaidergabriel/Dr.-Unterweger`

- stacked parent: PR #359, fresh-main V4 storage candidate;
- new PR: #371;
- head: `c4cf3747ee8e57c10c754b7a8898264181744777`;
- workflow: `Frank UnifiedDB V4 process crash composition VPS`;
- run: `31510023573`;
- state at report write: `QUEUED`.

The new oracle:

- launches the orchestrator itself only after V4 admission;
- strips inherited internal V4 child markers before every nested writer launch, preventing accidental admission-state transfer;
- launches every writer through `frank_v0_1_sqlite_v4_launcher.sh`;
- requires each writer to receipt SQLite 3.53.4, exact source-id and `python -I -S` state before READY;
- uses one disposable WAL database;
- logs+fsyncs a transaction id only after COMMIT returns;
- terminates all active writer processes at randomized points;
- after every cycle compares durable rows to acknowledged ids, bounds the committed-but-not-yet-logged window to at most one per writer, requires zero excess phantoms, `integrity_check=ok`, and a successful recovery write;
- exercises 4 writers × 4 NORMAL cycles + 4 FULL cycles by default.

## Hypothesis / counterhypothesis

Hypothesis: the repaired V4/private-3.53.4 runtime preserves all application-acknowledged commits and remains integral+writable across the tested process-crash matrix.

Strongest counterhypothesis: prior crash evidence does not transfer to the repaired runtime/topology, or nested process launches inherit internal admission state and create false composition evidence.

The second counterhypothesis is explicitly instrumented: inherited internal child markers are removed before every nested product launch.

## Promotion decision

**HOLD.** The new workflow is queued, not yet evidence of PASS.

Even a target PASS will close only the `PROCESS_CRASH` slice. UnifiedDB/Frank v0.1 still requires:

- selected-lineage logical rollback/recovery on the repaired runtime;
- installed service/systemd boot non-bypassability;
- canonical migration + last-known-good rollback under owner gate;
- distinct OS-crash/power-loss evidence if required by final acceptance;
- whole-product composition and final Frank v0.1 acceptance.

No canonical Frank state was opened or mutated by the new experiment. No host SQLite package replacement, external Frank effect, training action, or Frank self-Harness authority change occurred.
