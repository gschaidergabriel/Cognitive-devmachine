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
- `tools/program_progress.py`

The stage list is data-driven. Do NOT hardcode `BASE`, `H1`, `H2`, etc. into footer logic. If the owner changes the research narrative/stage order, the status footer must automatically follow the new `PROGRAM_STATE.json`.

Only the **first unpassed stage in `stage_order`** is shown. Completed future/history stages are not listed in the footer.

## Progress semantics

Progress is based on the current stage's declared `progress_source`.

Default work-package rule:

`progress = completed_weight / total_weight`

A package does not earn percentage merely because it is `CLAIMED`, `ACTIVE` or `IN_PROGRESS`. It contributes only when its completion status is machine-verifiably complete, unless it defines explicit weighted subchecks.

The progress bar is generated from the same percentage.

## ETA semantics

ETA is a range, never a deadline.

User work cadence for the current program:

`10 active owner-collaboration hours/day`

ETA preference order:

1. measured completed work-weight per 10h owner day;
2. measured work-weight per token/output throughput where canonical telemetry exists;
3. measured stage velocity;
4. explicit bootstrap stage priors.

The existing Project-Frankenstein history includes per-call `tokens_in`, `tokens_out`, cost and latency tracing plus session aggregation, but until a canonical current 24h token-total receipt is materialized for this RAE program, the footer must not invent a token total. It must show the lower-confidence bootstrap/measured-work basis honestly.

Parallel workers reduce wall-clock ETA only when completed receipts demonstrate actual independent parallel progress. Do not multiply throughput by worker count naively.

Failed/falsified work remains part of throughput calibration.

## Required format

```text
RAE STATUS
Entity: JOINED
GitHub: VERIFIED_RW
Canonical: <branch/revision or canonical ref>
Actor: chatgpt-secondary
Trigger: <none|registered trigger>
Research write: <COMMITTED|NO_RESEARCH_DELTA|SYNC_PENDING|NOT_ATTEMPTED>
Short commands: go · q12 · dump · fusion · hypofusion · clay · gwt · frank · emergenz · claycode · hyperposition · claygraph · unifieddb · harness

NEXT MILESTONE
Stage: <dynamic label from PROGRAM_STATE.json>
Progress: [#####...............] 25%
ETA @ 10h/day: <low> - <high>
ETA confidence: <confidence> (<basis>)
```

`Short commands` is mandatory and must list the currently registered commands from `PROJECT_COMMAND_REGISTRY.json`. If the registry changes, this line changes dynamically.

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

This is important: `gwt`, `hyperposition`, `claycode`, `harness`, `q12`, etc. remain specialist modes while the footer shows what the **whole research organism must reach next**.

## Q12 behavior

`q12` includes the same dynamic milestone and ETA in its executive briefing. It may explain the ETA basis, but it must not alter the computed percentage to make progress look better.

## Pre-send invariant

Before every substantive response verify:

1. one final fenced `text` block exists;
2. opener is exactly ` ```text `;
3. required RAE metadata fields are present;
4. all registered short commands are present;
5. `NEXT MILESTONE`, `Stage`, `Progress`, `ETA @ 10h/day`, and `ETA confidence` are present;
6. progress bar and percentage agree with `tools/program_progress.py` / current canonical inputs;
7. no forbidden Unicode frame characters occur;
8. no prompt-completion percentage is shown;
9. closing fence is final visible content.

Any violation is a formatting/governance bug and must be corrected before sending.
