# UnifiedDB — Authoritative Projection Outbox V1

Run: `unifieddb-20260811T2335p0700-chatgpt-secondary-projection-outbox-v1`

Status: **FRESH-MAIN CANDIDATE BUILT / TARGET EXECUTION PENDING / NO PROMOTION YET**

## Why this cycle exists

The preceding UnifiedDB cycle closed a real `PROCESS_CRASH` slice for independently V4-admitted SQLite 3.53.4 WAL writers, but it did not solve cross-store semantic continuity between authoritative UnifiedDB and derived ClayGraph.

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

## Freshness repair

The first PR #386 head was based on target `main@9085f0b...`. During the run, target main advanced to `5ec9955775d9bf142e327166990a2228d543c071` through an unrelated ClayCode/WP03 integration.

Rather than accept stale evidence, the UnifiedDB candidate was rebuilt through the Git database as **one commit on fresh main plus exactly the six original candidate blobs**:

- fresh base: `5ec9955775d9bf142e327166990a2228d543c071`;
- fresh candidate: `6201556c8f47f1226ed8c2bc3792851ed3912294`;
- PR #386 now contains 1 commit / 6 files and remains mergeable;
- old target run `31512653656` is superseded before execution;
- current target run is `31513961274`.

## Target implementation

Target PR: `gschaidergabriel/Dr.-Unterweger#386`

Fresh head: `6201556c8f47f1226ed8c2bc3792851ed3912294`

Workflow: `Frank UnifiedDB projection outbox V1 VPS`

Fresh target run: `31513961274`

State at report write: `PENDING` behind the same PR concurrency/self-hosted execution lane.

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

## Supplemental pre-falsifier result

A separate GitHub-hosted precheck (`31513246399`) ended before any workflow step executed and produced zero artifacts. It is therefore recorded as `INFRA_FAILURE_PRESTART`, not as candidate counterevidence. No candidate semantic change was made from that failure and the diagnostic PR was closed.

## Promotion rule

No result is promoted while the fresh target run has not executed. If target PASS occurs, promotion is limited to this candidate projection continuity mechanism on disposable current-schema state. Production migration, projector scheduling/backpressure, selected-lineage canonical recovery, OS/power-loss durability and whole Frank v0.1 remain separate gates.

No external effect, training action, canonical state mutation or Frank self-Harness authority is introduced.
