# RESEARCH EVENT CAPTURE PROTOCOL — RAE-8.8

## Goal

Every substantive result produced during project research becomes durable research state, not disposable chat text. The protocol must preserve scientific continuity **without turning every small task into a bureaucratic full audit**.

This includes intermediate findings, failed attempts, corrections, hypotheses, tests, source discoveries, architecture alternatives, contradictions, artifacts and final answers.

## Important boundary

Private model chain-of-thought / hidden scratch reasoning is **not** stored or required.

Instead each preserved research step emits a reproducible **Reasoning Summary / Decision Trace** containing the evidence used, alternatives considered, test or inference performed, result, uncertainty, falsifier and downstream consequence.

The scientific objective is reproducibility and provenance, not verbatim hidden cognition.

## Capture levels

Every prompt/run is classified before work:

### L0 — NO_RESEARCH_DELTA
Use for ordinary Q&A, formatting, trivial edits or operational actions that create no durable research knowledge.

Persist at most:
- prompt/run identity;
- task classification;
- `NO_RESEARCH_DELTA` / final summary if a durable runner is active.

Do not create claims, hypotheses or canonical revisions.

### L1 — ENGINEERING_DELTA
Use for implementation/configuration changes whose mechanism is already understood and which do not constitute a new scientific claim.

Minimum durable events:
- `PROMPT_RECEIVED`;
- important `SOURCE_READ`/configuration refs;
- `ARCHITECTURE_DECISION` or `ARTIFACT_CREATED` where relevant;
- verification/test result;
- `FINAL_RESPONSE_SUMMARY`.

### L2 — RESEARCH
Use when evidence, hypothesis set, mechanism confidence, experimental result, negative result or architecture frontier changes.

Capture all scientifically meaningful events required to reconstruct the inference/test chain.

### L3 — AUDIT / LINEAGE / RECOVERY
Use for canonical-state repair, contradiction resolution, historical audits, promotion disputes, source-integrity investigations and recovery.

Capture the full source/canonical lineage, validation decisions, concurrent-head handling and reconciliation events.

A worker may escalate level during a run. It must not silently downgrade after discovering a research-relevant contradiction or result.

## Mandatory event types

Research-capable runs may emit these event types:

- `PROMPT_RECEIVED`
- `TASK_CLASSIFIED`
- `SESSION_JOIN`
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
- `NO_RESEARCH_DELTA`
- `SESSION_LEAVE`
- `SYNC_EVENT`

## Event schema

Every durable event gets, where applicable:

```json
{
  "event_id": "uuid-or-content-address",
  "timestamp": "ISO-8601",
  "session_id": "when available",
  "prompt_id": "stable hash/id",
  "capture_level": "L0|L1|L2|L3",
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
  "context_receipt": {"packet_ids":[],"source_refs":[]},
  "provenance": {"actor":"...","tool":"...","commit":"..."}
}
```

## Prompt result capture

For L1-L3 substantive prompts, create a prompt-run record containing:

- exact user request or a privacy-safe exact reference to it;
- resolved task interpretation;
- capture level;
- system-layer/domain classification;
- source set actually used;
- context receipt (which packet summaries/evidence detail were loaded);
- intermediate Research Events appropriate to the capture level;
- outputs/artifacts produced;
- claims created/changed;
- hypotheses/tests/results when present;
- final answer summary;
- topic packets touched;
- canonical promotion decision;
- Git commit/ledger references.

A research result is not considered fully archived until its required event stream and topic-packet updates are committed or explicitly marked `SYNC_PENDING`.

## Intermediate capture granularity

For L2/L3, capture an intermediate event whenever one of these changes materially:

- evidence basis;
- hypothesis set;
- favored mechanism;
- confidence;
- an alternative is eliminated;
- a test produces data;
- a contradiction appears;
- a tool or implementation changes the feasible design space;
- a new cross-domain pattern is discovered.

Do not emit meaningless token-by-token logs or duplicate every tool call.

## Append-only rule

Event history is append-only. A correction does not rewrite the old event. Instead create a new event with `supersedes_event_id` or `refutes_claim_id`.

Current views are materializations over the event log.

## Autonomous behavior during active sessions

During every active substantive project session the Research Entity performs the capture level automatically without asking the user to manually curate it.

This does not imply background activity when no session/automation is running.
