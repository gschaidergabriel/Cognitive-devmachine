# UnifiedDB — Authoritative Projection Outbox V1

Run: `unifieddb-20260811T2335p0700-chatgpt-secondary-projection-outbox-v1`

Status: **CANDIDATE BUILT / TARGET EXECUTION QUEUED / NO PROMOTION YET**

## Why this cycle exists

The preceding UnifiedDB cycle closed a real PROCESS_CRASH slice for independently V4-admitted SQLite 3.53.4 WAL writers, but it did not solve cross-store semantic continuity between authoritative UnifiedDB and derived ClayGraph.

Current target code already says cross-file atomicity is not claimed and the existing ClayGraph Clay contract already says `source_of_truth UnifiedDB`, `rebuildable_from_UnifiedDB`, and `activation != truth`. What was missing is a durable executable bridge that preserves these semantics through cross-store crash windows.

SQLite primary documentation also means separate WAL database files must not be treated as one power-loss-atomic transaction. The preferred design therefore does not try to make ClayGraph co-own truth.

## Selected candidate

`C_AUTHORITATIVE_TRANSACTIONAL_OUTBOX`:

1. authoritative semantic mutation and stable ProjectionEvent are committed in one UnifiedDB transaction;
2. the event has stable identity, source epoch, semantic-record identity and payload hash;
3. ClayGraph applies the event in its own transaction and records exact applied-event identity/hash;
4. the later UnifiedDB `delivery_state=APPLIED` marker is advisory only;
5. consequential graph use requires exact authoritative/destination event-set/root equivalence plus current relation-query equivalence;
6. stale, missing, extra or hash-divergent graph state fails closed;
7. ClayGraph can be deleted and deterministically rebuilt from retained authoritative event history.

Direct dual writes and pretending separate WAL files are one atomic durability domain are rejected candidates. Physical graph colocation remains a later measured comparison candidate rather than a premise.

## Target implementation

Target PR: `gschaidergabriel/Dr.-Unterweger#386`

Head: `2f86298b8d1e2196d199ea6d69965d62d54bd1bd`

Workflow: `Frank UnifiedDB projection outbox V1 VPS`

Run: `31512653656`

State at report write: `QUEUED`.

Candidate changes are deliberately not in production migration lists. Canonical Frank state is never opened by the gate.

## Falsification matrix

Three real process-exit windows are exercised behind the exact V4/private SQLite 3.53.4 path:

- A: after authoritative UnifiedDB COMMIT, before any ClayGraph write or graceful close;
- B: inside the ClayGraph projection transaction;
- C: after ClayGraph COMMIT, before advisory UnifiedDB delivery ACK.

Additional falsifiers:

- repeated relation supersession + query equivalence;
- explicit projection lag -> consequential graph gate must refuse;
- derived applied-event payload-hash tamper -> must refuse;
- full derived graph deletion -> rebuild must reproduce exact projection root and current relation set;
- post-run `integrity_check` on both databases;
- p50/p95/p99/max latency shadow for authoritative commit+outbox and projection drain;
- physical file-size shadow.

## Promotion rule

No result is promoted while the target run is queued. If target PASS occurs, promotion is limited to this candidate projection continuity mechanism on disposable current-schema state. Production migration, projector scheduling/backpressure, selected-lineage canonical recovery, OS/power-loss durability and whole Frank v0.1 remain separate gates.

No external effect, training action, canonical state mutation or Frank self-Harness authority is introduced.
