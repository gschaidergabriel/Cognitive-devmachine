<!-- RAE_META
{
  "packet_id": "KMP-UNIFIEDDB-SQLITE-WAL-UBUNTU-RUNTIME-20260809",
  "title": "Ubuntu WAL probe quantifies reader checkpoint retention, one-writer contention and FULL/NORMAL latency split",
  "domains": ["unifieddb", "frank", "harness", "persistence", "recovery", "observability"],
  "topics": ["sqlite", "wal", "checkpoint", "reader_writer", "durability", "busy", "latency"],
  "epistemic_class": "MEASURED_RESULT_SUMMARY",
  "status_hint": "CURRENT",
  "origin_actor": "chatgpt-secondary",
  "provider": "OpenAI",
  "model": "GPT-5.6 Sol",
  "created_at": "2026-08-09T23:49:00+07:00",
  "source_refs": [
    "gschaidergabriel/Dr.-Unterweger@773449b8d56a1dbda5693ede497cd4c822146e85",
    "gschaidergabriel/Dr.-Unterweger@39ab05470efedd792048b0611a01fbbb67b41040:runtime/vps_integrity/sqlite_wal_probe_latest.json",
    "https://sqlite.org/wal.html",
    "https://sqlite.org/pragma.html#pragma_synchronous"
  ],
  "evidence_refs": ["FRANK_SQLITE_WAL_RUNTIME_PROBE"],
  "confidence": 0.995,
  "verification_required": "Repeat under representative FRANK state traffic and explicit crash/power-loss fault injection before durability policy promotion",
  "falsifier_or_next_test": "Representative FRANK workloads show materially different contention/checkpoint behavior, or a different persistence topology dominates under recovery, latency and correctness constraints."
}
RAE_META -->

### Atomic result
A disposable SQLite workload executed on the real Ubuntu self-hosted runner `digital-retina` using SQLite `3.45.1`. Canonical FRANK state was not mutated.

Measured results:

- `journal_mode=WAL` for all test databases;
- 120 FULL commits: mean `0.745740 ms`, p50 `0.726155 ms`, p95 `0.956806 ms`, max `1.861071 ms`;
- 120 NORMAL commits: mean `0.025938 ms`, p50 `0.021440 ms`, p95 `0.045000 ms`, max `0.088350 ms`;
- host-local mean FULL/NORMAL wall-time ratio: about `28.75x` in this micro-workload;
- with a read transaction intentionally held open, all 120 writer commits still completed;
- WAL size with the reader held: `650,992 bytes`;
- `PRAGMA wal_checkpoint(PASSIVE)` while reader held returned `[0,158,3]`: 158 log frames, only 3 checkpointed;
- after reader release, `TRUNCATE` checkpoint returned `[0,0,0]` and WAL size became `0`;
- a second concurrent `BEGIN IMMEDIATE` observed `SQLITE_BUSY` / error code `5` after about `100.861 ms`;
- after releasing the first writer, the second writer succeeded;
- all integrity checks returned `ok`.

### Interpretation boundary
The probe reproduces documented WAL mechanics: readers and a writer can overlap, only one writer exists at a time, and a sufficiently long reader can prevent checkpoint progress. The FULL/NORMAL latency difference is a host-local microbenchmark, not a universal multiplier. Normal process execution is not a power-loss test. SQLite documentation states that WAL + `synchronous=NORMAL` preserves consistency but can lose recent transactions after power/OS loss; `FULL` adds stronger durability behavior.

### UnifiedDB implication
Logical unification must not hide physical durability/locking semantics. For the Ubuntu v0.1 lane:

- reader lifetime and WAL/checkpoint progress should be observable;
- writer busy/retry time should be measurable and bounded;
- durability mode must be explicit per authority boundary, not selected only by latency;
- recovery receipts must include checkpoint/WAL state where relevant;
- multi-file atomicity must not be inferred from single-file WAL behavior.

### Next falsifier
Run the same measurements against representative FRANK state transactions and derived-materialization access patterns; then perform controlled process/host crash tests on disposable replicas under FULL and NORMAL, validating replay/recovery invariants and measuring lost-commit windows.
