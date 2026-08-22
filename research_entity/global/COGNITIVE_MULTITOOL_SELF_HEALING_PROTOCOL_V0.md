# COGNITIVE MULTITOOL SELF-HEALING PROTOCOL V0

Status: REQUIRED ARCHITECTURE CONTRACT
Date: 2026-08-22

## Goal
The Cognitive Multitool MUST recover automatically from process, backend, slot, model, capsule, database-session and invalid-state failures while remaining observable and auditable. Recovery must return the affected cognitive slot to the latest independently verified stable state without silently hiding the failure.

Self-healing is not self-certification: the neural backend may propose recovery cognition, but an external deterministic supervisor decides whether a checkpoint is valid, whether rollback is allowed, and whether effects may resume.

## Health state machine
Every slot and backend exposes exactly one health state:

`HEALTHY -> DEGRADED -> RECOVERING -> HEALTHY`

or, when recovery cannot be proven safe:

`DEGRADED/RECOVERING -> QUARANTINED`.

A crash, timeout, malformed ClayCog result, invariant violation, stale generation, DB/CAS conflict, impossible state transition, repeated backend fault or missing receipt MUST leave a durable health event. No transition back to HEALTHY may occur without a verified recovery receipt.

## Stable checkpoint
A stable checkpoint is created only after deterministic gates accept the cognitive state. It contains at minimum:

- monotonic `generation` and `episode_id`;
- `slot_id`;
- capsule hash plus system-prompt hash;
- DB binding identity/namespace plus DB generation/transaction marker;
- backend identity and immutable model/config digest where available;
- canonical cognitive-state hash (`R`, GRF, Hyperposition, workspace state);
- accepted evidence/provenance references;
- last committed effect receipt set;
- deterministic invariant/schema version;
- timestamp/sequence metadata for diagnosis, never as truth authority.

Checkpoint payloads are append-only or versioned. Recovery MUST NOT rewrite or erase the failed state/event that caused rollback.

## Failure detection
A deterministic supervisor/watchdog, outside the neural model, detects at least:

- process exit/crash;
- heartbeat or inference deadline failure;
- malformed/invalid Cognitive Multitool response;
- ClayCode/type/invariant gate rejection;
- stale generation or CAS conflict;
- DB binding disappearance/mismatch;
- capsule/slot cross-contamination signal;
- repeated identical failure loop;
- effect intent without a matching terminal receipt;
- corrupted/unverifiable checkpoint.

## Recovery algorithm
For one failed slot:

1. Mark slot `DEGRADED`, stop new external effects for that slot, and append a crash/failure event.
2. Snapshot diagnostic metadata needed to reproduce the failure: input/event id, backend, capsule/config hashes, generation, error class, relevant state hashes and receipts. Secrets remain redacted.
3. Mark slot `RECOVERING` and select the newest checkpoint that independently passes schema, hash, generation, DB-binding and invariant verification.
4. Restore capsule binding and cognitive state from that checkpoint into a fresh sequence/KV context. Never trust the crashed model's hidden/KV state as continuity authority.
5. Reconcile DB generation/CAS. If canonical DB has advanced incompatibly, do not overwrite it; rebase cognition from current canonical DB or quarantine.
6. Reconcile effects using receipts. Already committed effects are never blindly replayed. Unknown-effect state remains `UNKNOWN` until externally resolved.
7. Run a deterministic recovery probe plus a bounded cognitive self-check. The neural backend may propose diagnosis, but cannot approve itself.
8. If all gates pass, emit a durable `RECOVERY_RECEIPT`, increment recovery generation, expose the incident to telemetry/UI, and return to `HEALTHY`.
9. If the same fault repeats beyond the configured bounded retry/circuit-breaker threshold, quarantine the slot/backend and optionally route cognition to a configured alternate backend such as `mistral_dual`. Do not keep rebooting indefinitely.

## Observable recovery
A recovered system must not look as though nothing happened. At minimum persist/expose:

`incident_id`, `slot_id`, failure class, first/last failing generation, rollback checkpoint generation, backend before/after, state hashes before/after, effects reconciled, retry count, recovery result, quarantine/fallback status, and recovery receipt.

Normal user-facing behavior may stay concise, but operational telemetry MUST make every recovery visible and queryable.

## Blast-radius control
Failure of one cognitive slot MUST NOT automatically roll back unrelated slots. Shared DB rollback is forbidden unless the database itself proves a transaction-level recovery requirement. Backend-wide failure may trip a backend circuit breaker while preserving independently verified slot states.

## Backend fallback
Self-healing is compatible with backend substitution. If `local_0_5b` repeatedly fails or is disabled, the same stable checkpoint/capsule/Cognitive Multitool contract can resume on `mistral_dual` or another admitted backend. Backend substitution does not alter canonical identity or memory.

## Training requirements
The 0.5B curriculum MUST include trajectories for:

- crash after cognition but before commit;
- crash after effect intent with no terminal receipt;
- stale generation/CAS conflict;
- malformed state and invariant rejection;
- recovery from last stable checkpoint;
- current-DB-wins rebase instead of destructive rollback;
- repeated-crash circuit breaker and backend escalation;
- recovery with hot-swapped system prompt/DB capsule;
- cross-slot isolation during another slot's crash;
- explicit `UNKNOWN` when effect outcome cannot be proven;
- NOOP after successful stable recovery when no further action is warranted.

Training must teach the neural kernel to cooperate with recovery, not to claim that recovery succeeded. Only deterministic receipts can promote a recovered state.

## Promotion gates
A Cognitive Multitool implementation cannot be promoted until tests prove:

- deterministic crash detection;
- rollback to last verified stable state;
- no blind replay of external effects;
- persistent incident and recovery receipts;
- bounded retry + quarantine/circuit breaker;
- slot-local blast radius;
- safe backend substitution from the same canonical checkpoint;
- visible recovery telemetry;
- crash/recovery training cases pass for the tuned 0.5B kernel and backend-contract tests pass with the 0.5B disabled.
