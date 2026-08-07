# RESEARCH EVENT CAPTURE PROTOCOL — RAE-8.8

## Goal

Every substantive result produced during project research becomes durable research state, not disposable chat text.

This includes intermediate findings, failed attempts, corrections, hypotheses, tests, source discoveries, architecture alternatives, contradictions, artifacts and final answers.

## Important boundary

Private model chain-of-thought / hidden scratch reasoning is **not** stored or required.

Instead each research step emits a reproducible **Reasoning Summary / Decision Trace** containing the evidence used, alternatives considered, test or inference performed, result, uncertainty, falsifier and downstream consequence.

The scientific objective is reproducibility and provenance, not verbatim hidden cognition.

## Mandatory event types

Every substantive prompt/run may emit zero or more events of these types:

- `PROMPT_RECEIVED`
- `TASK_CLASSIFIED`
- `SOURCE_DISCOVERED`
- `SOURCE_READ`
- `SOURCE_HASHED`
- `EVIDENCE_EXTRACTED`
- `ANALYSIS_INTERMEDIATE`
- `PATTERN_DETECTED`
- `HYPOTHESIS_CREATED`
- `COUNTER_HYPOTHESIS_CREATED`
- `PREDICTION_PREREGISTERED`
- `EXPERIMENT_DESIGNED`
- `EXPERIMENT_EXECUTED`
- `RESULT_OBSERVED`
- `NEGATIVE_RESULT`
- `CONTRADICTION_FOUND`
- `CLAIM_REFUTED`
- `CLAIM_SUPERSEDED`
- `CLAIM_PROMOTED`
- `ARCHITECTURE_CANDIDATE`
- `ARCHITECTURE_DECISION`
- `TOOL_ACQUIRED`
- `TOOL_FAILED`
- `ARTIFACT_CREATED`
- `TOPIC_PACKET_UPDATED`
- `DOMAIN_CROSS_LINK_CREATED`
- `FINAL_RESPONSE_SUMMARY`
- `SYNC_EVENT`

## Event schema

Every event gets:

```json
{
  "event_id": "uuid-or-content-address",
  "timestamp": "ISO-8601",
  "session_id": "when available",
  "prompt_id": "stable hash/id",
  "event_type": "...",
  "system_layers": ["..."],
  "domains": ["..."],
  "topic_packet_ids": ["..."],
  "source_refs": ["repo/file/hash/line-or-artifact"],
  "parent_event_ids": ["..."],
  "reasoning_summary": "reproducible summary, not private chain-of-thought",
  "claim_ids_created_or_updated": ["..."],
  "hypothesis_ids": ["..."],
  "experiment_ids": ["..."],
  "result": "...",
  "status": "CURRENT|OPEN|SUPERSEDED|REFUTED|NEGATIVE|LOCAL_ONLY",
  "confidence": "...",
  "falsifier_or_next_test": "...",
  "artifact_refs": ["..."],
  "provenance": {"actor":"...","tool":"...","commit":"..."}
}
```

## Prompt result capture

For every substantive user prompt, create a prompt-run record containing:

- exact user request or a privacy-safe exact reference to it;
- resolved task interpretation;
- system-layer/domain classification;
- source set actually used;
- intermediate Research Events;
- outputs/artifacts produced;
- claims created/changed;
- hypotheses/tests/results;
- final answer summary;
- topic packets touched;
- canonical promotion decision;
- Git commit/ledger references.

A prompt result is not considered fully archived until its event stream and topic-packet updates are committed or explicitly marked `SYNC_PENDING`.

## Intermediate capture granularity

Capture an intermediate event whenever one of these changes:

- evidence basis;
- hypothesis set;
- favored mechanism;
- confidence materially changes;
- an alternative is eliminated;
- a test produces data;
- a contradiction appears;
- a tool or implementation changes the feasible design space;
- a new cross-domain pattern is discovered.

Do not emit meaningless token-by-token thought logs.

## Append-only rule

Event history is append-only. A correction does not rewrite the old event.
Instead create a new event with `supersedes_event_id` or `refutes_claim_id`.

Current views are materializations over the event log.

## Autonomous behavior during active sessions

During every active substantive project session the Research Entity performs capture automatically without asking the user to manually curate it.

This does not imply background activity when no session/automation is running.
