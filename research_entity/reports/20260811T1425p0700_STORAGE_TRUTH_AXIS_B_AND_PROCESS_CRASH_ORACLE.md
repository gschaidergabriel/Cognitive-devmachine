# Storage truth — FixPresenceVector axis B, and a real process-crash oracle

Date: 2026-08-11 14:25 +07:00
Origin actor: `claude-code` / Anthropic / Claude Opus 5 (1M) — external contributor session
Identity: `EXTERNAL_CONTRIBUTOR_NOT_A_BOOTED_CLAY_ORGAN`
Work package: `F-V01-13-SECURITY-RECOVERY-OBSERVABILITY`
Discriminators addressed: the program's own #2 (FixPresenceVector axis B) and #3 (crash/restart/concurrency storage oracle)
Status: `EXECUTED_ON_TARGET_VPS / PULL_REQUEST_OPEN / NO_PROMOTION_REQUESTED`
Pull request: `gschaidergabriel/Dr.-Unterweger` — branch `storage/fixpresence-axisb-and-crash-oracle`

## 1. Why this matters beyond storage

The single-instance presence PASS — 12 contenders, 1 winner, stale/ghost fencing — rests entirely
on SQLite's `BEGIN IMMEDIATE` write lock and on epoch-guarded optimistic fencing. The V17 bound
re-entry invariant rests on six schema-level `RAISE(ABORT)` triggers. Both are good engineering,
and both are only as strong as the storage engine underneath them.

While `F-V01-13` carries "exact live SQLite source/build/loader binding" and "crash/restart/
concurrency recovery oracles" as open blockers, those two component PASSes are resting on an
unverified foundation. That is the reason to close these two discriminators first.

## 2. Axis B — the identity half of the FixPresenceVector

Axis A is already resolved: `NO_WAL_CODE_BACKPORT_EVIDENCE_IN_UBUNTU_PATCHSET`. That is a
statement about a **source tree**. It is not a statement about the **object this process
executes**. Axis B supplies the missing half.

The probe reads `/proc/self/maps`, not `ldd` — `ldd` reports what a fresh link would resolve,
not what is currently mapped, and the difference is exactly where a "wrong library loaded"
failure would hide.

Measured on `clay@digital-retina`, Python 3.12.3, **6/6 checks**:

| property | value |
|---|---|
| mapped realpath | `/usr/lib/x86_64-linux-gnu/libsqlite3.so.0.8.6` |
| GNU build-id | `92f59a77085057d1b9de43e943ba6231dc7ae452` |
| SHA-256 | `f2cd05de8b6f71ea9d0495a6f9ff9cae844b15d9c45b7ef49ee0af0f81658cc7` |
| size | 1,468,440 bytes |
| owning package | `libsqlite3-0:amd64` `3.45.1-1ubuntu2.7` |
| runtime version | 3.45.1 |
| linkage | `SHARED_LIBSQLITE_MAPPED` — not statically linked into `_sqlite3` |
| WAL reachable | yes (`journal_mode=wal` accepted on a file-backed database) |

**A provenance finding worth recording.** The runtime `SQLITE_SOURCE_ID` is

```
2024-01-30 16:01:20 e876e51a0ed5c5b3126f52e532044363a014bc594cfefa87ffb5b82257ccalt1
```

The suffix is not an upstream 3.45.1 digest. **The running binary therefore cannot be mapped to
an upstream source tree by `SQLITE_SOURCE_ID` alone.** Any future fix-presence argument that
leans on source-id comparison has to account for this. `UPSTREAM_SOURCE_IDS` in the probe is
deliberately left empty: a guessed mapping would manufacture provenance, which is the failure
mode this whole vector exists to prevent.

The probe concludes **neither FIXED nor VULNERABLE**, and says so in its own output. Version
equality is not fix presence; package provenance is not object identity. What it delivers is a
uniquely identified object, so that a later behavioural discriminator can be attributed to *this*
binary rather than to "SQLite 3.45.1".

## 3. The crash oracle — what the V17 "restart" test was not

Audit finding C established that `restart_between_reentry_and_done_recovers_nonterminal_state`
is a context-manager close/reopen inside one process. This is the real thing.

Concurrent writer processes commit against one WAL database. Each writer appends the committed id
to its own append-only log and `fsync`s it **only after `COMMIT` returns**, so the log is exactly
the set of transactions the application was told had succeeded. All writers are `SIGKILL`ed at a
random instant. The database is then reopened and checked.

Measured on `clay@digital-retina`, **6/6 checks**, 10 cycles × 6 writers, at both `synchronous`
levels:

| | |
|---|---|
| acknowledged commits | **12,807** |
| lost acknowledged commits | **0** |
| phantom commits | **0** |
| `integrity_check` after every kill | `ok` |
| writable after every kill | yes |
| committed-but-unlogged in flight | 9 across 10 cycles (≤ 1 per writer, as designed) |

Throughput cost of durability, incidentally measured: `NORMAL` sustained roughly 1,500–2,800
commits per cycle, `FULL` roughly 415–743 — a ~3–4× difference on this host.

### Claim boundary, stated in the receipt itself

`SIGKILL` terminates the process but does **not** discard the OS page cache. This proves
**process-crash** durability, concurrency safety and recoverability. It does **not** prove
power-loss or kernel-panic durability, which additionally depends on `synchronous`, filesystem
barriers and the device honouring flushes. It is also **not** a targeted discriminator for the
upstream WAL-reset defect — it is a general durability oracle.

## 4. Three instrument bugs, all mine — recorded because they are the finding

Per `messgeraet-vor-glauben`: in this session two of three initial failures were defects of the
measuring instrument, not of the system under test. Recording them is more useful than hiding
them, because each is a trap the next probe author will walk into.

1. **WAL capability probed on an in-memory database.** An in-memory database legitimately refuses
   WAL and reports `memory`. A healthy build read as "WAL unavailable". Fixed by probing on a
   file-backed temporary database. *Lesson: capability probes must run on the storage class they
   make claims about.*
2. **Post-crash writability probed through pysqlite's implicit transaction management.** The
   explicit `BEGIN IMMEDIATE` collided with pysqlite's own implicit `BEGIN` and raised "cannot
   start a transaction within a transaction". This read as "database not writable after crash" in
   all 10 cycles — a spectacular false alarm about durability. Fixed with `isolation_level=None`.
   *Lesson: a storage claim measured through a driver's convenience layer measures the driver.*
3. **The phantom check was unsound.** A transaction that `COMMIT`s and is killed before its log
   write is present-but-unacknowledged **by design** — the kill lands in the window between
   `COMMIT` returning and the log `fsync`. Counting those as phantoms produced 6 false positives.
   Because each writer commits strictly sequentially, at most one such record can exist per
   writer; that window is now measured separately as `committed_but_unlogged_in_flight`, and only
   excess counts as a genuine phantom. *Lesson: an oracle must model its own observation window,
   or it will report the window as a defect.*

Had these three not been chased down, this report would have claimed a durability failure in
SQLite that does not exist.

## 5. What this closes, and what it does not

**Closed:** discriminator #2 in full (live object identity is now bound and reproducible), and
discriminator #3 for the process-crash class at both `synchronous` levels.

**Still open under `F-V01-13`:**
- power-loss / kernel-panic durability (needs device-level fault injection, not `SIGKILL`);
- a **targeted** behavioural discriminator for the upstream WAL-reset defect — axis C of the
  FixPresenceVector remains the honest gap, and neither axis A nor axis B substitutes for it;
- the selection decision on private SQLite 3.53.4, which remains `CANDIDATE_CAPABILITY_ONLY`.

**Recommended next:** run the crash oracle against the private 3.53.4 build and compare, so the
selection decision rests on differential durability evidence on this exact host rather than on a
version number and a bounded smoke test.

## 6. Scope limits

- Both probes ran in a disposable `/tmp` copy on the accepted target VPS. The runner working tree
  was not modified; no canonical database was touched; no external effect was performed.
- Results are specific to the object identified in §2 on this host and filesystem. They do not
  transfer to another build or another mount by version equality — that is the same rule the
  probes themselves enforce.
- Delivered as an open pull request. Disposition belongs to Clay and the project owner.
  `whole_frank_v0_1_acceptance: NOT_CLAIMED`.
