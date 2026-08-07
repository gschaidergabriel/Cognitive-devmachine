# Mandatory RAE Visible Status Footer

Every substantive response by a project Research-Entity worker must end with a clearly separated status block. Trigger runs must always include it. Non-substantive social replies may omit it.

## Required format

```text
╔════════════════════ RAE STATUS ════════════════════╗
│ Entity: JOINED | DEGRADED_UNJOINED | LOCAL_ONLY    │
│ GitHub backend: VERIFIED_RW | VERIFIED_RO | UNVERIFIED | FAILED
│ Canonical: r<revision> · <short state hash>         │
│ Actor: <actor_id>                                   │
│ Active trigger: <trigger|none>                      │
│ Research write: COMMITTED | NO_RESEARCH_DELTA | SYNC_PENDING | NOT_ATTEMPTED
│ Trigger words: dump · clay · gwt · frank · emergenz · claycode · hyperposition
╚══════════════════════════════════════════════════════╝

┌──────── LAST-PROMPT COMPLETION ────────┐
│ <0-100>%                               │
│ Done: <short concrete statement>       │
│ Open: <short concrete statement|none>  │
└────────────────────────────────────────┘
```

## Verification semantics

`GitHub backend: VERIFIED_RW` may be shown only when this session actually read the expected repository/canonical and has a verified write-capable connection or verified a write/reread in the current operational context.

`VERIFIED_RO` means the backend was read successfully but write capability was not verified.

`UNVERIFIED` is mandatory if the worker is relying only on project files, chat memory or stale local snapshots.

Never print a green/success-like status merely because GitHub worked in an earlier session.

## Completion percentage

The completion percentage estimates completion of the user's **immediately preceding prompt**, not the whole project.

Compute it from explicit deliverables and material dependencies. A useful default weighting is:
- 40% core requested implementation/research;
- 20% requested data/artifact production;
- 15% repository persistence/cataloguing;
- 10% validation/tests/reread;
- 10% requested reporting/status output;
- 5% cleanup/archive/final consistency.

Adjust weights when the prompt clearly emphasizes another distribution.

Rules:
- 100% requires every material requested deliverable completed or explicitly impossible for an external reason that the user did not ask to solve, plus no falsely claimed writes/tests.
- If a large requested research cycle was only specified but not executed, completion cannot be 100%.
- If GitHub writes were requested but not verified, reserve at least the repository-persistence portion as incomplete.
- If files were meant to be moved/archived but cannot be moved, state that in `Open`.
- The percentage is an honest operational estimate, not an epistemic confidence score.

## Trigger run additions

For trigger runs, `Done` should mention the run report/packetization status. `Open` should mention missing sources, failed experiments, missing live readers or sync issues when applicable.
