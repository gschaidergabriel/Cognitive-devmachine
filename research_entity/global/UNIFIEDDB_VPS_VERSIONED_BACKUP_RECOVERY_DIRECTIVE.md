# UnifiedDB VPS Versioned Backup + Recovery Directive

**Status:** PROJECT-OWNER FIXED OPERATION LAW
**Owner instruction date:** 2026-08-10
**Scope:** current and future Frank UnifiedDB/canonical SQLite stores on the persistent VPS

## Core law

UnifiedDB and any authoritative SQLite store that will become part of the UnifiedDB lineage must be backed up repeatedly on the VPS using **consistent online snapshots**, versioned manifests and recovery validation.

A running SQLite database must never be backed up by naive raw file copy alone. Use SQLite's online backup API / equivalent consistent snapshot mechanism; validate the snapshot before admitting it as recovery evidence.

## Default paths

Backup root:

`/srv/unifieddb-backups`

Manifest/history metadata is also linked into the append-only `/srv/clay-history` build ledger. Large database snapshot files remain outside Git and are referenced by SHA-256, size and path.

## Snapshot triggers

Snapshots are required:

- periodically while the VPS is running (default timer: every 15 minutes);
- before schema migration or physical-store consolidation;
- before risky application/runtime upgrades that can change canonical state semantics;
- after successful migration/deployment once integrity is confirmed;
- on explicit Research-Entity request before a discriminating experiment that may materially alter canonical state.

Periodic snapshots may be skipped when the resulting consistent database content is byte-identical to the newest admitted snapshot.

## Snapshot manifest

Each admitted snapshot records at minimum:

- snapshot id;
- source logical store id and absolute source path;
- creation timestamp;
- source DB size and source file metadata;
- backup SHA-256 and size;
- SQLite `user_version`, `schema_version`, page size and journal mode where available;
- `PRAGMA quick_check` result and periodic/full `integrity_check` result where configured;
- source application/build/deployment id when known;
- previous admitted snapshot id/hash;
- reason/trigger (`PERIODIC`, `PRE_MIGRATION`, `POST_MIGRATION`, `PRE_DEPLOY`, `POST_DEPLOY`, `EXPLICIT`, `RECOVERY_TEST`);
- tool/service version and provenance;
- corresponding Clay build-history/event reference.

## Physical retention

Backups are tiered and bounded so repeated snapshots cannot consume the VPS indefinitely.

Default policy:

- preserve all explicitly pinned/release/migration/recovery snapshots;
- retain dense recent snapshots, then progressively sparser hourly/daily/weekly generations;
- retain at least multiple independently timed recovery points;
- enforce a configurable backup-storage budget (default 50 GiB) for non-pinned snapshots;
- prune only backup-owned redundant/expired physical snapshots, never the live database;
- preserve manifests/history for pruned snapshots so the chronology remains auditable.

If the configured budget cannot hold the minimum protected recovery set, stop pruning protected snapshots and emit a storage-pressure fault.

## Recovery law

Automatic backup tooling may **not silently overwrite the live UnifiedDB**.

Recovery testing creates a new recovery candidate file, validates it and records its hash/manifest. Switching a recovery candidate into the live canonical path is a separate explicit recovery/deployment effect with its own pre-switch snapshot and receipt.

## Collapse acceptance

The backup system is not considered valid until tests prove:

1. snapshot can be created while source DB is live;
2. admitted snapshot passes SQLite check;
3. snapshot can be opened/read independently;
4. recovery candidate can be materialized to a new path;
5. schema/user-version metadata is preserved;
6. restart does not lose snapshot index/history;
7. retention preserves protected recovery points;
8. corrupted snapshot is rejected rather than promoted;
9. backup manifests are linked to `/srv/clay-history`;
10. no secret values are written to snapshot manifests.

## Compact invariant

`LIVE_UNIFIEDDB -> CONSISTENT_VERSIONED_SNAPSHOT -> INTEGRITY_CHECK -> RECOVERY_CANDIDATE`

never

`LIVE_UNIFIEDDB -> BLIND_FILE_COPY -> ASSUME_RECOVERABLE`
