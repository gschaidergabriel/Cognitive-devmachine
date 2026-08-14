# UnifiedDB — Authoritative Projection Outbox V1

Run: `unifieddb-20260811T2335p0700-chatgpt-secondary-projection-outbox-v1`

Status: **FRESH-MAIN TARGET SUPPORTED / CANDIDATE+REGRESSION PATH MERGED / PRODUCTION ACTIVATION HELD**

## Research delta

The preceding UnifiedDB cycle closed a real `PROCESS_CRASH` slice for independently V4-admitted SQLite 3.53.4 WAL writers. This cycle closed the next narrower gap: cross-store semantic continuity from authoritative UnifiedDB to derived/rebuildable ClayGraph without pretending separate WAL database files share one cross-file durability transaction.

The existing ClayGraph contract already declared UnifiedDB source-of-truth and graph rebuildability. The missing executable bridge is now represented by `C_AUTHORITATIVE_TRANSACTIONAL_OUTBOX`:

1. authoritative semantic mutation and stable `ProjectionEvent` commit in the same UnifiedDB transaction;
2. stable event identity binds unified epoch, semantic-record identity and payload hash;
3. ClayGraph applies each event in its own idempotent transaction and durably records exact applied-event identity/hash;
4. later UnifiedDB `delivery_state=APPLIED` is advisory only and is not treated as cross-file atomicity proof;
5. consequential graph use requires exact authoritative/destination event-set/root equivalence plus current relation-query equivalence;
6. missing/extra/hash-divergent or lagging graph state fails closed;
7. derived graph state can be removed and deterministically rebuilt from retained authoritative projection history.

Direct dual-write and cross-file WAL atomicity assumptions remain rejected candidates. Physical graph colocation remains a measured comparison candidate, not a premise.

## Freshness discipline

The first target head passed its mechanism gate but target `main` advanced through unrelated ClayCode work. That old PASS was deliberately not promoted. The candidate was rebuilt through Git objects from fresh target `main@5ec9955775d9bf142e327166990a2228d543c071` plus exactly the six UnifiedDB candidate blobs.

A second CI-only scheduler commit changed PR concurrency from `cancel-in-progress: false` to `true` so stale PR-head runs could not indefinitely block the newest evidence. Candidate semantics and test matrix were otherwise unchanged.

Final tested head: `b8858f949d4ad855bff5d682994de69bfd10b7c9`.

## Fresh-main accepted-target result

Target repo: `gschaidergabriel/Dr.-Unterweger`

PR: #386

Workflow run: `31514757454`

Job: `93857015099`

Runner/machine: `clay` / `digital-retina`

Result: **23/23 PASS**.

Observed runtime:

- kernel `6.8.0-117-generic`;
- Python `3.12.3`;
- host `libsqlite3-0` remained `3.45.1-1ubuntu2.7`;
- exact V4-admitted private SQLite `3.53.4` with expected source-id.

Three hard process-exit windows:

- after authoritative UnifiedDB COMMIT, before graph write/close -> authoritative event survived, graph gate refused lag, replay recovered exactly;
- inside ClayGraph transaction -> partial graph mutation rolled back, replay recovered exactly;
- after ClayGraph COMMIT, before advisory UnifiedDB ACK -> graph commit survived and replay produced no duplicate.

Selection/recovery falsifiers:

- explicit graph lag: detected and fail-closed;
- derived applied-event payload-hash tamper: detected and fail-closed;
- complete derived graph wipe: rebuilt exact event root and exact current relation set;
- both database `integrity_check` results: `ok`.

Exact recovered projection:

- authoritative events: `76`;
- applied events: `76`;
- projection root: `be0090b4bfbe176862fccc736d0f6abdc16a752d16769a7fe7f254005b368316`;
- current relation count: `16`;
- event-root equivalence: true;
- relation-query equivalence: true.

Latency shadow on this small disposable target workload:

- authoritative commit + outbox: p50 `1.035 ms`, p95 `2.359 ms`, p99 `3.514 ms`, max `4.039 ms`;
- projection drain: p50 `2.107 ms`, p95 `4.598 ms`, p99 `5.383 ms`, max `7.930 ms`.

Storage shadow:

- UnifiedDB: `1,269,760` bytes;
- ClayGraph: `413,696` bytes.

Evidence artifact: ID `9110606930`, SHA-256 `9ce0640a2e65b0967e01c6956bc92e211250306d17f3350eb979f51d311ff06a`.

## Integration result

PR #386 was squash-merged to target main as `72029f838176fff5189b8c3cfd4ef5d957de6ba2`.

What is merged:

- typed Clay projection contract;
- candidate-only UnifiedDB and ClayGraph SQL extensions;
- executable projection candidate;
- crash/replay/lag/tamper/rebuild gate;
- self-hosted target regression workflow.

What is **not** activated:

- candidate SQL is still absent from production `apply_current_schema` migration lists;
- no canonical Frank state migration occurred;
- no production projector daemon/scheduler/backpressure path is claimed;
- no OS-crash or power-loss durability claim is made;
- no whole Frank v0.1 acceptance is made.

## Next gates

`F-V01-04-UNIFIEDDB-STATE-CONTINUITY` remains OPEN. Highest-value remaining gates are:

1. production projector scheduling/backpressure/lag telemetry and deterministic recovery;
2. only then consider candidate schema promotion into current migration lists;
3. selected-lineage `LOGICAL_ROLLBACK` recovery on the repaired runtime;
4. `DEPLOYMENT_BOOT` service/systemd non-bypass proof;
5. canonical migration + last-known-good owner gate;
6. direct `OS_CRASH` / `POWER_LOSS` evidence if required by final acceptance;
7. large-corpus graph/vector/FTS quality and resource shadows;
8. whole-product Frank v0.1 accepted-target composition.

No external Frank effect, training action, canonical-state mutation or Frank self-Harness authority was introduced by this run.
