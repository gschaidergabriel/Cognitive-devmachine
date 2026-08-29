# DURABLE WORK REENTRY PROTOCOL V1

Status: CURRENT PROTOCOL CANDIDATE
Scope: long-running Clay / EntityOS / HCU / Frankenstein research, build, benchmark and reconciliation runs
Authority: this protocol grants no new execution/effect/provider authority. It defines durability and re-entry semantics only.

## 0. Problem

A correct execution route is not enough if useful work can disappear when a chat response, tool call, runner, transport, or worker process is interrupted. The final assistant message MUST NOT be the sole carrier of run progress.

Canonical distinction:

```text
WORK_COMPLETED
!= FINAL_CHAT_MESSAGE_DELIVERED

PROCESS_INTERRUPTED
!= COMPLETED_WORK_LOST

RETRY
!= RESTART_FROM_ZERO
```

## 1. Mandatory checkpoint rule

Any run expected to cross multiple material tool calls, external fetches, repository writes, model downloads, benchmarks, or long analysis phases MUST have a stable `run_id` and durable cursor.

Persist a checkpoint after each material node whose result would be expensive, slow, externally observed, or unsafe to repeat blindly. At minimum checkpoint after:

- authority / execution-surface resolution;
- source or model revision pinning;
- model/artifact download and hash verification;
- successful repository write / merge / dispatch;
- hardware or runtime inventory;
- benchmark completion;
- evidence classification;
- any state-changing operation;
- any phase boundary before a high-latency or failure-prone operation.

## 2. Node model

Each material step has a stable `node_id` and one state:

- `PENDING`
- `RUNNING_UNCONFIRMED`
- `COMPLETED`
- `FAILED_RETRYABLE`
- `FAILED_TERMINAL`
- `BLOCKED_EXTERNAL`
- `SUPERSEDED`

Only evidence-backed terminal output may move a node to `COMPLETED`.

A worker interruption while a node is `RUNNING_UNCONFIRMED` MUST re-enter by checking the external effect/result first. It MUST NOT blindly repeat the operation.

## 3. Cursor schema

A durable cursor is a JSON object with at least:

```json
{
  "schema": "DURABLE_WORK_CURSOR/v1",
  "run_id": "...",
  "objective": "...",
  "authority_generation": "...",
  "source_generation": "...",
  "updated_at": "...",
  "nodes": [],
  "next_node_id": "...",
  "resume_rule": "VERIFY_THEN_CONTINUE",
  "final_message_delivered": false
}
```

Each node records stable identity, status, attempt count, idempotency key when relevant, input/source identity, output/evidence references, and next discriminator.

## 4. Re-entry algorithm

On every continuation after an interruption:

1. locate the newest durable cursor for the same stable run/objective identity;
2. revalidate current owner authority and execution-surface generation;
3. revalidate source/model identities required by the next node;
4. preserve all `COMPLETED` nodes unless explicit evidence proves them invalid/superseded;
5. for `RUNNING_UNCONFIRMED`, inspect the external system/repository/runner/result before retrying;
6. retry only `FAILED_RETRYABLE` or confirmed-unperformed nodes using the same idempotency identity where applicable;
7. continue from `next_node_id`, not from the beginning;
8. write the updated cursor before relying on the final visible response.

## 5. Idempotency and duplicate-effect law

Any operation capable of creating duplicate effects MUST use a stable idempotency identity or equivalent create-only/compare-before-write guard.

Examples:

- repository writes: exact path/blob/ref plus compare-before-update;
- PR/issue/workflow ownership: create-only claim or stable external identity;
- downloads: immutable revision + target path + content hash;
- benchmarks: run_id + source/model/hardware configuration identity;
- effects: canonical EffectGate/EffectJournal identity and existing project effect law.

A retry must first answer: `DID_THE_PRIOR_ATTEMPT_ALREADY_COMMIT?`

## 6. Pending-write preservation

If independent nodes run in parallel and one fails, successful outputs are durable completed evidence. They MUST NOT be discarded merely because the aggregate phase did not finish.

The cursor records completed node outputs separately from the aggregate phase state.

## 7. Negative and transient outcomes

Transport timeout, queued runner, rate limit, response-delivery failure, model-download interruption, or worker termination remain scoped observations. They may mark a node retryable or externally blocked; they do not invalidate earlier completed nodes.

## 8. Final-message semantics

`final_message_delivered` is presentation metadata only. It never determines whether work is complete.

A run may contain durable completed nodes while `final_message_delivered == false`. The next invocation must report and reuse those nodes rather than claiming invisible background work or restarting them.

## 9. Stop semantics

A run may conclude only when one of these is true:

- objective terminally completed with evidence;
- explicit current authority denial;
- terminal external impossibility backed by current exhaustive execution-surface resolution;
- user explicitly stops the run.

A transient tool/transport failure alone is not terminal.

## 10. Integration with execution-surface resolution

Before selecting/retrying a material node, apply `governance/EXECUTION_SURFACE_RESOLUTION_PROTOCOL_V1.md` when execution capability is relevant.

The two protocols solve different axes:

```text
EXECUTION_SURFACE_RESOLUTION = WHERE/HOW CAN THIS NODE RUN NOW?
DURABLE_WORK_REENTRY        = WHAT HAS ALREADY COMMITTED, AND WHERE DO WE RESUME?
```

Both are required for robust long-horizon execution.

## 11. Acceptance tests

A conforming implementation MUST satisfy:

1. completed A/B + interrupted C -> resume at C, not A;
2. `RUNNING_UNCONFIRMED` effect -> verify external result before retry;
3. successful parallel node + failed sibling -> successful output remains completed;
4. authority generation changes -> revalidate route before next execution without erasing prior evidence;
5. source identity changes -> affected future node is re-planned; unrelated completed nodes remain intact;
6. final response not delivered -> durable node progress remains recoverable;
7. duplicate retry with same idempotency key -> no second logical effect;
8. retryable transport failure -> run remains resumable, not terminally blocked.

## 12. Permanent anti-recurrence invariants

```text
THE FINAL CHAT MESSAGE IS NEVER THE CHECKPOINT.

COMPLETED MATERIAL WORK MUST BE DURABLE BEFORE THE NEXT FAILURE-PRONE STEP.

AFTER INTERRUPTION: VERIFY -> RECONCILE -> RESUME; NEVER ASSUME -> REPEAT.
```
