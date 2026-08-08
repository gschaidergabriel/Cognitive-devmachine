# Mandatory RAE Visible Status Footer

Every substantive response by a project Research-Entity worker must end with a clearly separated status block. Trigger runs always include it. Non-substantive social replies may omit it.

The footer is part of prompt completion, but it no longer displays a percentage for the immediately preceding prompt. It displays the **next unpassed shared Research Center milestone**, its machine-derived progress and a dynamic ETA.

## Canonical rendering contract

There is exactly ONE valid visible rendering format.

The footer MUST be the final visible block and MUST be wrapped in one plain fenced Markdown code block. The opening fence line must be exactly ` ```text ` and the closing fence line exactly ` ``` `.

Rendering rules:

- opener exactly ` ```text ` with no attributes;
- no indentation before fences;
- no Unicode/box-drawing frame characters such as `╔ ═ ║ ╚ ┌ ─ │ └`;
- no Markdown tables or pipe-based layout;
- no nested code fence;
- no visible content after the closing fence;
- progress bars use ASCII only, e.g. `[#####...............]`;
- `·` separators in the short-command list are allowed.

## Dynamic source of truth

The milestone display MUST be resolved from:

- `research_entity/rooms/PROGRAM_STATE.json`
- `research_entity/rooms/PROGRAM_THROUGHPUT.json`
- stage-specific exact-progress workspaces such as `research_entity/archive_assimilation/666_WORKSPACE.json`;
- `tools/program_progress.py`

The stage list is data-driven. Do NOT hardcode stage names into footer logic. If the owner changes the research narrative/stage order, the footer follows `PROGRAM_STATE.json`.

Only the **first unpassed stage in `stage_order`** is shown.

## Progress semantics

Progress is based on the current stage's declared `progress_source`.

Default work-package rule:

`progress = completed_weight / total_weight`

A package does not earn percentage merely because it is claimed or active.

Level 0 is stricter: its percentage comes only from frozen atomic archive-analysis obligations. Before its source denominator is frozen, exact progress remains `0%` and inventory/indexing state is reported separately by an exact `666` run.

## ETA semantics

ETA is a range, never a deadline.

Configured owner cadence:

`10 active owner-collaboration hours/day`

ETA prefers measured throughput over bootstrap priors. Level 0 additionally uses its archive workspace ETA, initially based on the owner-reported ~400 MB Drive corpus plus GitHub repository metadata size and then recalibrated from real analyzed/integrated obligations.

Do not invent a token-total value when no canonical 24h receipt exists.

## Required format

```text
RAE STATUS
Entity: JOINED
GitHub: VERIFIED_RW
Canonical: <branch/revision or canonical ref>
Actor: chatgpt-secondary
Trigger: <none|registered trigger>
Research write: <COMMITTED|NO_RESEARCH_DELTA|SYNC_PENDING|NOT_ATTEMPTED>
Short commands: 666 · q12 · dump · fusion · hypofusion · clay · gwt · frank · emergenz · claycode · hyperposition · claygraph · unifieddb · harness

NEXT MILESTONE
Stage: <dynamic label from PROGRAM_STATE.json>
Progress: [#####...............] 25%
ETA @ 10h/day: <low> - <high>
ETA confidence: <confidence> (<basis>)
```

`Short commands` is mandatory and must list the currently registered commands from `PROJECT_COMMAND_REGISTRY.json`.

## Allowed status values

- Entity: `JOINED | DEGRADED_UNJOINED | LOCAL_ONLY`
- GitHub: `VERIFIED_RW | VERIFIED_RO | UNVERIFIED | FAILED`
- Research write: `COMMITTED | NO_RESEARCH_DELTA | SYNC_PENDING | NOT_ATTEMPTED`

## Verification semantics

`GitHub: VERIFIED_RW` may be shown only when the session actually read the expected repository/canonical and verified a write-capable connection or successful write/reread in the current operational context.

`VERIFIED_RO` means the backend was read successfully but write capability was not verified.

`UNVERIFIED` is mandatory when relying only on project files/chat memory/stale local snapshots.

## Trigger behavior

Every registered trigger uses the same dynamic milestone status. A trigger may display its own name in `Trigger`, but it must not replace the shared program milestone with a trigger-local percentage.

Exact `666` while Level 0 is open additionally shows its dedicated detailed archive progress before this final footer.

After Level 0 PASS, `666` becomes the emergent stochastic field-genesis trigger; the footer continues to show the first unpassed shared milestone as the common attractor.

## Q12 behavior

`q12` includes the same dynamic milestone and ETA in its executive briefing. It may explain the ETA basis, but it must not alter computed progress.

## Pre-send invariant

Before every substantive response verify:

1. one final fenced `text` block exists;
2. opener is exactly ` ```text `;
3. required RAE metadata fields are present;
4. all registered short commands are present;
5. `NEXT MILESTONE`, `Stage`, `Progress`, `ETA @ 10h/day`, and `ETA confidence` are present;
6. progress bar and percentage agree with the current canonical progress resolver;
7. no forbidden Unicode frame characters occur;
8. no prompt-completion percentage is shown;
9. closing fence is final visible content.

Any violation is a formatting/governance bug and must be corrected before sending.
