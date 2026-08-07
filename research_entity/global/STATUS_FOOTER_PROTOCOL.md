# Mandatory RAE Visible Status Footer

Every substantive response by a project Research-Entity worker must end with a clearly separated status block. Trigger runs must always include it. Non-substantive social replies may omit it.

The footer is part of prompt completion, not optional decoration. Before sending a substantive response, check that the final visible block is present and complete. A response missing the footer is not 100% complete.

## Required format

Render the footer inside one fenced `text` code block so alignment is stable across clients:

```text
RAE STATUS
Entity: JOINED
GitHub: VERIFIED_RW
Canonical: r2 · 04234efdb86c
Actor: chatgpt-secondary
Trigger: none
Research write: NO_RESEARCH_DELTA

LAST PROMPT
Completion: 100%
Done: <short concrete statement>
Open: none
```

Allowed status values:

- Entity: `JOINED | DEGRADED_UNJOINED | LOCAL_ONLY`
- GitHub: `VERIFIED_RW | VERIFIED_RO | UNVERIFIED | FAILED`
- Research write: `COMMITTED | NO_RESEARCH_DELTA | SYNC_PENDING | NOT_ATTEMPTED`

The code block must be the final visible block. Do not put substantive prose after it.

## Verification semantics

`GitHub: VERIFIED_RW` may be shown only when this session actually read the expected repository/canonical and has a verified write-capable connection or verified a write/reread in the current operational context.

`VERIFIED_RO` means the backend was read successfully but write capability was not verified.

`UNVERIFIED` is mandatory if the worker is relying only on project files, chat memory or stale local snapshots.

Never print a success-like backend state merely because GitHub worked in an earlier session.

## Completion percentage

The completion percentage estimates completion of the user's immediately preceding prompt, not the whole project.

Useful default weighting:
- 40% core requested implementation/research;
- 20% requested data/artifact production;
- 15% repository persistence/cataloguing;
- 10% validation/tests/reread;
- 10% requested reporting/status output;
- 5% cleanup/archive/final consistency.

Rules:
- 100% requires every material requested deliverable completed or explicitly impossible for an external reason, plus the required footer.
- If a large requested research cycle was only specified but not executed, completion cannot be 100%.
- If GitHub writes were requested but not verified, reserve the repository-persistence portion as incomplete.
- The percentage is an operational estimate, not an epistemic confidence score.

## Trigger run additions

For trigger runs, `Done` should mention run report/packetization/tool-manifest status. `Open` should mention missing sources, failed experiments, quota fallbacks, missing live readers or sync issues when applicable.
