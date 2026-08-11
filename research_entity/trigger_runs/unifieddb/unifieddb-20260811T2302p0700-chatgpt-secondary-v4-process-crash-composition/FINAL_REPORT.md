# UnifiedDB — V4 Fixed-SQLite Process-Crash Composition

Run: `unifieddb-20260811T2302p0700-chatgpt-secondary-v4-process-crash-composition`

Status: **PROCESS_CRASH TARGET SUPPORTED / ARCHITECTURE DELTA BUILT / WHOLE COMPONENT PROMOTION HOLD**

## Fresh-state correction

The UnifiedDB branch has advanced beyond the earlier `SQLite 3.45.1 + WAL` diagnostic stage. Current target evidence contains a private fixed SQLite 3.53.4 runtime, V4 `python -I -S` admission, V17 composition and a disposable current UnifiedDB+ClayGraph migrate/reopen smoke pass. This run did not duplicate that work.

The discriminating question was narrower: does process-crash recovery still hold when **every concurrent WAL writer independently crosses the actual V4 product admission boundary** before touching state?

Target result: **yes for the tested PROCESS_CRASH matrix**.

## Architecture adjudication

Preferred current architecture is **logically unified, physically layered**:

- UnifiedDB remains authoritative typed semantic state;
- pinned SQLite 3.53.4 behind V4 is the current physical engine candidate, not semantic authority;
- ClayGraph remains a derived/rebuildable topology projection;
- retrieval/vector/FTS structures remain candidate-producing sidecars whose ids must resolve through UnifiedDB;
- the monotonic RecoveryFloor remains `KEEP_ISOLATED` from the UnifiedDB rollback domain;
- physical consolidation remains a candidate only if measurements dominate this layered design.

Four required architecture classes were retained/evaluated in `UNIFIED_DATABASE_ARCHITECTURE.claycode.json`; `C_SHARED_CANONICAL_PLUS_SIDECARS` is preferred.

SQLite primary documentation adds a second reason not to pretend multiple physical WAL databases are one atomic store: multi-database transactions in WAL mode do not provide the rollback-journal super-journal's cross-file power-loss atomicity. Therefore authoritative UnifiedDB state and the event needed to rebuild a derived ClayGraph projection should be committed inside the authoritative transaction; ClayGraph should consume that projection event idempotently and remain rebuildable rather than co-owning truth.

## Recovery evidence law

A generic `RECOVERY PASS` is too lossy. This run splits recovery into non-substitutable evidence classes:

1. `PROCESS_CRASH` — application/process termination such as SIGKILL;
2. `OS_CRASH` — kernel/system crash or hard reboot;
3. `POWER_LOSS` — stable-power/storage flush failure boundary;
4. `LOGICAL_ROLLBACK` — stale snapshot/lineage rewind;
5. `PROJECTION_REBUILD` — derived ClayGraph/index loss or staleness;
6. `DEPLOYMENT_BOOT` — installed service must begin at the trusted V4 boundary.

Evidence may not be promoted from one class into a stronger class without a direct discriminator.

## Target execution

Target repo: `gschaidergabriel/Dr.-Unterweger`

- stacked parent: PR #359, fresh-main V4 storage candidate;
- new PR: #371;
- tested head: `c4cf3747ee8e57c10c754b7a8898264181744777`;
- workflow: `Frank UnifiedDB V4 process crash composition VPS`;
- run: `31510023573`;
- job: `93841210700`;
- runner/machine: `clay` / `digital-retina`;
- result: **SUCCESS**.

Exact target metadata observed by the workflow:

- kernel `6.8.0-117-generic`;
- Python `3.12.3`;
- host package still `libsqlite3-0:amd64 3.45.1-1ubuntu2.7`;
- admitted private SQLite `3.53.4`;
- exact source-id `2026-07-24 19:02:57 bf7c7f30031888f4e796e429ab3978879485813aaca6f641c7b33e4e09459bcc`;
- private library SHA-256 `3bc7d1bfd013ffb645e7e16414f498873b13044a26a114c5fa12e24ef18968df`;
- manifest SHA-256 `7567f708d6c02f02a1c07c03ec05d563c21b7f081001cf33b0c9752aa35b02c8`.

## Process-crash results

Matrix:

- `NORMAL`: 4 crash cycles;
- `FULL`: 4 crash cycles;
- 4 writer processes per cycle;
- 32 independently launched writer-process instances total;
- each writer crossed a fresh V4 launcher/admission path before READY;
- each transaction id was append+fsync logged only after COMMIT returned.

Measured aggregate result:

- checks: **10/10 PASS**;
- application-acknowledged commits: **4250**;
- lost acknowledged commits: **0**;
- unbounded phantom commits: **0**;
- committed-but-not-yet-logged in-flight observations: **7**, each within the predeclared bound of at most one per writer;
- every selected writer process terminated by SIGKILL;
- `integrity_check=ok` after every crash cycle;
- database writable after every crash cycle.

The artifact was preserved as ID `9109020862`, digest SHA-256 `7940c5f03d3fe865e8220386f7f0bda93c09df77da5a323e5aeac8432bd62ea3`.

## Hypothesis / counterhypothesis adjudication

Hypothesis: supported for the tested `PROCESS_CRASH` matrix.

Counterhypothesis A — prior process-crash success does not transfer to repaired V4/private-3.53.4 topology: **refuted for this matrix**.

Counterhypothesis B — nested writers can inherit internal V4 child state and create false admission evidence: the candidate explicitly strips inherited internal child markers and then requires a fresh per-writer V4 receipt plus target-side exact runtime observation. This bypass class did not reproduce in the tested run.

## Promotion decision

**Promote only the PROCESS_CRASH evidence slice. Hold F-V01-04 as OPEN.**

Remaining release-critical work includes:

- selected-lineage logical rollback/recovery on the repaired runtime;
- authoritative projection-event/outbox semantics so ClayGraph can be rebuilt without cross-file atomicity assumptions;
- installed service/systemd boot non-bypassability;
- canonical migration + last-known-good rollback under owner gate;
- distinct OS-crash/power-loss evidence if required by final acceptance;
- whole-product composition and final Frank v0.1 acceptance.

No canonical Frank state was opened or mutated by the experiment. No host SQLite package replacement, external Frank effect, training action, or Frank self-Harness authority change occurred.
