# PROMPT CAPTURE POLICY — COMPLETE PROJECT TRACE

`capture_all_project_prompts = true`

Every project prompt receives a durable Prompt Run record.

## If the prompt produces substantive research/system work

Capture full Research Event Stream, source/evidence set, intermediate reasoning summaries, hypotheses, tests/results, claim transitions, artifacts, topic-packet updates and final response summary.

## If the prompt is trivial or produces no durable research/system knowledge

Create a minimal run record:
- prompt/run id;
- timestamp;
- task class;
- result summary;
- `research_delta = NONE`;
- `canonical_promotion = NO`;
- status `NO_RESEARCH_DELTA`.

This preserves complete project lineage without polluting the evidence graph.

## Privacy/safety

Prompt text may be stored exactly only when it does not contain credentials, secrets or unrelated sensitive personal data. Otherwise store a redacted digest + safe semantic summary + source chat reference.

## Intermediate analysis

Store reproducible analysis summaries and decision traces, not private hidden chain-of-thought.

## Atomic decomposition

Any durable new concept is immediately linked to one or more Topic Packets. A result must not remain only inside the final response or Prompt Run record.
