# UnifiedDB — Lease-Fenced Projection Worker V1

Run: `unifieddb-20260811-chatgpt-secondary-projection-worker-v1`

Status: **CANDIDATE BUILT / TARGET EXECUTION QUEUED / NO PROMOTION YET**

## Why this cycle exists

The previous UnifiedDB cycles now provide two durable layers:

1. V4/private-SQLite `PROCESS_CRASH` evidence for authoritative WAL persistence;
2. a target-supported transactional ProjectionEvent/outbox candidate that lets derived ClayGraph recover exactly across cross-store process-exit windows.

The next missing production-shaped mechanism is scheduling: who drains the projection queue, how concurrent workers are fenced, how backlog is measured, and what happens when that worker crashes while a lease is live.

## Architecture choice

Four scheduler shapes were compared:

- synchronous graph projection on every authoritative write — rejected because it couples truth availability/latency to a derived store;
- optimistic multiworker projection with idempotency only — held because it adds avoidable race/lock pressure without a scheduling ownership receipt;
- **single-active lease-fenced bounded worker** — preferred current candidate for the single-host Frank v0.1 target;
- external durable broker — retained as a future comparison, not selected before the simpler worker is falsified.

Clay/ClayCode declares the semantics. SQLite stores the lease/receipts physically and Python implements the contract.

## Candidate laws

- UnifiedDB stays authoritative even under HARD projection backlog.
- ClayGraph stays derived/rebuildable.
- Consequential graph use remains fail-closed while projection is not exact-current.
- Only one live lease generation may project at a time.
- Every worker batch is bounded.
- Lease expiry permits takeover only with a newer generation.
- A stale generation must be fenced after takeover.
- Worker receipts bind before/after pending count, lag, pressure, generation and outcome.
- HARD pressure may throttle derived-dependent producers, but never demotes or blocks authoritative truth.
- Multi-host clock-skew safety is explicitly outside this V1 claim.

## Target candidate

Repo: `gschaidergabriel/Dr.-Unterweger`

PR: #391

Head: `6fe47f9672a997f784ac168314f8bc0c65afcd65`

Workflow: `Frank UnifiedDB projection worker V1 VPS`

Run: `31515873771`

State at report write: `QUEUED`.

Candidate changes remain outside production migration lists and no service/systemd entry is installed.

## Falsification matrix

The target gate is designed to test:

- create 96 authoritative pending ProjectionEvents -> pressure must be HARD;
- authoritative writes remain allowed, but consequential graph use must be closed;
- V4-admitted worker acquires a 1200 ms durable lease and hard-exits after exactly 7 applied events;
- immediate V4-admitted contender must be refused while that lease is live;
- after expiry, a new worker generation must take over and drain the remaining 89 events;
- crashed generation must then be fenced;
- create a second 80-event backlog;
- bounded batches `13 -> 55 -> 12` must produce pressure `HARD -> HARD -> SOFT -> NONE/HEALTHY`;
- final projection must be exact-current and graph use may reopen;
- applied-event count, worker receipts and both SQLite integrity checks must remain exact;
- throughput and storage shadow are captured.

## Promotion rule

A target PASS would support only the single-host, lease-fenced, bounded projection-worker candidate on disposable current schemas. It would not yet authorize production schema migration, systemd deployment, multi-host scheduling, power-loss claims, canonical migration or whole Frank v0.1 acceptance.

No canonical Frank state, external effect, training action or Frank self-Harness authority is introduced.
