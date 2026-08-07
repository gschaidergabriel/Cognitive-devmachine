# CLAIM LIFECYCLE PROTOCOL

Raw data and historical text are never deleted because an interpretation changes.

Every atomic claim has:
- `claim_id`
- normalized proposition
- scope / target substrate / system layer
- source/evidence refs
- first_seen_at
- current_status
- confidence
- supporting evidence
- counterevidence
- supersedes / superseded_by
- refuted_by
- open_falsifiers
- last_reviewed_at

## State transitions

```text
OPEN -> CURRENT
OPEN -> REFUTED
CURRENT -> SUPERSEDED
CURRENT -> REFUTED
SUPERSEDED -> CURRENT   (only with new evidence and explicit revival event)
REFUTED -> OPEN         (only if refuting evidence is invalidated)
```

Every transition is appended to `CLAIM_STATUS_EVENTS.jsonl`.

## Scope sensitivity

Statuses are not universal unless the evidence is universal.

Example:
`causal GWT validator rejects malformed synthetic episodes`
may be CURRENT in sandbox scope while
`causal GWT improves live FRANK behavior`
remains OPEN.

## Conflict preservation

When credible evidence conflicts:
- do not average away the disagreement;
- mark `OPEN_CONTRADICTION`;
- link competing claims and evidence;
- schedule a discriminating test when useful.

## Supersession vs refutation

SUPERSEDED means a newer representation/version/model replaces an older one without proving the old claim false in its original context.

REFUTED means adequate evidence contradicts the proposition in its stated scope.

This distinction is mandatory for all source ingestion and prompt-result capture.
