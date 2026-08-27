# UnifiedDB — Lease-Fenced Projection Worker V1

Run: `unifieddb-20260811-chatgpt-secondary-projection-worker-v1`

Status: **TARGET SUPPORTED / CANDIDATE+REGRESSION PATH MERGED / PRODUCTION SCHEMA+SERVICE ACTIVATION HELD**

## Why this cycle exists

The previous UnifiedDB cycles established two durable layers:

1. V4/private-SQLite `PROCESS_CRASH` evidence for authoritative WAL persistence;
2. a target-supported transactional ProjectionEvent/outbox candidate that lets derived ClayGraph recover exactly across cross-store process-exit windows.

This cycle addressed the next production-shaped mechanism: who drains the projection queue, how concurrent workers are fenced, how backlog is measured, and what happens when that worker crashes while a lease is live.

## Architecture choice

Four scheduler shapes were compared:

- synchronous graph projection on every authoritative write — rejected because it couples truth availability/latency to a derived store;
- optimistic multiworker projection with idempotency only — held because it adds avoidable race/lock pressure without a scheduling ownership receipt;
- **single-active lease-fenced bounded worker** — target-supported current candidate for the single-host Frank v0.1 target;
- external durable broker — retained as a future comparison, not selected before the simpler worker is falsified under sustained load.

Clay/ClayCode declares the scheduler/backpressure semantics. SQLite stores the lease/receipts physically and Python implements the contract.

## Target result

Target repo: `gschaidergabriel/Dr.-Unterweger`

PR: #391

Tested head: `6fe47f9672a997f784ac168314f8bc0c65afcd65`

Fresh base/main: `72029f838176fff5189b8c3cfd4ef5d957de6ba2`

Workflow: `Frank UnifiedDB projection worker V1 VPS`

Run: `31515873771`

Job: `93860745062`

Runner/machine: `clay` / `digital-retina`

Result: **25/25 PASS**.

## What was falsified

Initial backlog:

- 96 pending ProjectionEvents;
- pressure `HARD`;
- authoritative UnifiedDB writes remained allowed;
- consequential ClayGraph use remained closed.

Worker crash:

- worker crossed V4/private-SQLite admission;
- acquired durable lease generation 1;
- hard-exited after exactly 7 applied events;
- 89 events remained pending;
- live lease remained durable.

Lease collision/takeover:

- immediate independently V4-admitted contender was refused with `LEASE_HELD`;
- after lease expiry, recovery acquired a newer generation;
- remaining backlog drained idempotently;
- the stale crashed generation was fenced.

Second backlog/backpressure path:

- 80 pending events entered `HARD` pressure;
- bounded batches of 13, 55 and 12 events produced the expected path `HARD -> HARD -> SOFT -> NONE/HEALTHY`;
- final source/applied epoch was `176/176`;
- pending `0`, lag `0`, missing `0`, extra `0`, hash conflicts `0`;
- projection exact-current became true;
- authoritative writes remained allowed;
- consequential graph use reopened only after exact-current state.

Both SQLite integrity checks returned `ok`.

Measured batch throughput on this target workload:

- 13-event batch: `248.69 events/s`;
- 55-event batch: `344.99 events/s`;
- 12-event batch: `304.26 events/s`.

Artifact: `9111199960`, SHA-256 `4fe49d40f8acc1540d5a66d81b96bbcbc6b9f10087e9ff47e0bad24ff0fb51ee`.

## Integration result

PR #391 was squash-merged to target main as `7b458a2e779f2dd8756e3bf9df03ff96d4e3f5e5`.

Merged candidate/regression surfaces:

- Clay-native projection-worker semantic contract;
- candidate-only worker lease/telemetry schema;
- lease-fenced bounded worker physical implementation;
- process-crash/backpressure/takeover target gate;
- self-hosted target regression workflow.

Still **not activated**:

- candidate worker/outbox SQL is not in production `apply_current_schema` migration lists;
- no systemd/service worker is installed;
- no canonical Frank state was migrated;
- no multi-host lease/clock-skew claim is made;
- no OS-crash or power-loss durability claim is made.

## Current architecture law

- UnifiedDB truth remains available under derived projection backlog.
- ClayGraph remains derived/rebuildable.
- Consequential graph use is closed whenever exact-current projection admission fails.
- Worker health/pressure is observability and scheduling evidence, never truth authority.
- On the current single-host candidate lane, one durable lease generation is active at a time; expiry enables a newer generation and fences the stale one.
- Every batch remains bounded and writes a durable before/after receipt.

## Next gates

`F-V01-04-UNIFIEDDB-STATE-CONTINUITY` remains OPEN. Highest-value remaining work:

1. sustained shadow-load/backpressure operating-window evidence;
2. reversible production-schema integration for outbox+worker only after the shadow gate;
3. `DEPLOYMENT_BOOT` systemd/service V4 non-bypass proof;
4. selected-lineage `LOGICAL_ROLLBACK` recovery on the repaired runtime;
5. canonical migration + last-known-good owner gate;
6. direct `OS_CRASH` / `POWER_LOSS` evidence if required by final acceptance;
7. large-corpus graph/vector/FTS quality and resource shadows;
8. whole-product Frank v0.1 accepted-target composition.

No canonical Frank state, external effect, training action or Frank self-Harness authority was introduced by this run.
