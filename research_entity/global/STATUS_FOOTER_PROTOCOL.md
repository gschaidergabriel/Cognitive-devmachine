# Mandatory RAE Visible Status Footer

Every substantive response by a project Research-Entity worker must end with a clearly separated status block. Trigger runs always include it. Non-substantive social replies may omit it.

The footer no longer reports prompt-completion percentage. It reports two separate horizons:

1. **NEXT LEVEL** — the first unpassed shared program gate and its strict machine-derived progress.
2. **DOOMSDAY / Clay 0.1** — a freshly recomputed project forecast for the first end-to-end project-hardware run of the Clay-programmed, one-module/binary FRANK with UnifiedDB and the final fully fine-tuned Clay-native model.

## Canonical rendering contract

The footer MUST be the final visible block and MUST be wrapped in one plain fenced Markdown code block. The opening fence line must be exactly ` ```text ` and the closing fence line exactly ` ``` `.

Rendering rules:

- opener exactly ` ```text ` with no attributes;
- no indentation before fences;
- no Unicode/box-drawing frame characters;
- no Markdown tables or pipe-based layout inside the footer;
- no nested code fence;
- no visible content after the closing fence;
- progress bars use ASCII only;
- `·` separators in the short-command list are allowed.

## Dynamic source of truth

NEXT LEVEL is resolved from:

- `research_entity/rooms/PROGRAM_STATE.json`;
- `research_entity/rooms/PROGRAM_THROUGHPUT.json`;
- the current stage workspace, including `research_entity/archive_assimilation/666_WORKSPACE.json` for Level 0;
- `tools/program_progress.py`.

DOOMSDAY is recomputed on every resolver run from:

- `research_entity/global/DOOMSDAY_DYNAMIC_FORECAST_PROTOCOL.md`;
- `research_entity/forecast/DOOMSDAY_FORECAST_MODEL.json`;
- `research_entity/forecast/DOOMSDAY_CAPABILITY_RULES.json`;
- `research_entity/forecast/DOOMSDAY_EVENTS.jsonl`;
- current program/stage progress;
- measured throughput;
- current/future verified capacity;
- all registered APIs/tools and every `*_RESEARCH_CAPABILITY.json` extension;
- verified API/technology benchmark impacts;
- owner training authorization state;
- `tools/doomsday_forecast.py`.

No fixed DOOMSDAY date is canonical. The date/range is always a fresh conclusion from the current critical-path table.

## NEXT LEVEL progress semantics

The first unpassed stage in `PROGRAM_STATE.stage_order` is shown.

Default work-package progress is based on completed machine-verifiable weight. Claimed/active work earns no percentage merely for being active.

Level 0 is stricter: progress comes only from frozen atomic archive-analysis obligations. Before the denominator is frozen, exact progress remains 0%.

## DOOMSDAY progress semantics

The DOOMSDAY percentage is an effort-weighted dynamic forecast-progress measure over the current Clay 0.1 critical-path table. It is not a simple stage count.

It may move backward if a newly discovered necessary dependency legitimately expands the remaining scope. Verified eliminations or technology jumps may move it forward discontinuously.

## APIs and new technology

Every currently registered API/tool and every new `*_RESEARCH_CAPABILITY.json` extension is considered automatically by `tools/doomsday_forecast.py`.

A newly available API appears immediately in the capability table, but availability alone does not make the date earlier. A time multiplier is applied only when:

- the capability is runtime verified; and
- a benchmark/receipt verifies its impact on one or more DOOMSDAY workstreams.

For one workstream, multiple provider multipliers do not blindly multiply. The strongest single verified factor is used by default unless a future joint benchmark explicitly validates a combined factor.

## ETA semantics

ETA is a range, never a promise.

Configured owner cadence defaults to 10 active collaboration hours/day unless `PROGRAM_THROUGHPUT.json` changes it.

DOOMSDAY uses a dependency/critical-path forecast, not a naive sum of all work. Independent rows may overlap when dependencies allow it. Hardware availability dates and owner authorization constraints are applied explicitly.

If final training is not yet authorized, the DOOMSDAY date must state that it is conditional on immediate owner authorization when the frozen training-data gate becomes ready. Unknown human waiting time is never guessed.

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

NEXT LEVEL
Stage: <dynamic stage label>
Progress: [#####...............] 25%
ETA @ 10h/day: <low> - <high>
ETA confidence: <confidence> (<basis>)

DOOMSDAY / Clay 0.1
Progress: [###.................] 15%
Forecast: <YYYY-MM-DD> - <YYYY-MM-DD>
Center: <YYYY-MM-DD>
Confidence: <confidence>
Conditional on immediate training authorization when data is ready: <yes|no>
Forecast basis: <N>-row dynamic critical path + live capabilities/APIs
```

## Allowed status values

- Entity: `JOINED | DEGRADED_UNJOINED | LOCAL_ONLY`
- GitHub: `VERIFIED_RW | VERIFIED_RO | UNVERIFIED | FAILED`
- Research write: `COMMITTED | NO_RESEARCH_DELTA | SYNC_PENDING | NOT_ATTEMPTED`

## Verification semantics

`GitHub: VERIFIED_RW` may be shown only when the session actually read the expected repository/canonical and verified a write-capable connection or successful write/reread in the current operational context.

`VERIFIED_RO` means the backend was read successfully but write capability was not verified.

`UNVERIFIED` is mandatory when relying only on project files/chat memory/stale local snapshots.

## Trigger behavior

Every registered trigger uses the same two-horizon footer.

Exact `666` while Level 0 is open additionally shows its detailed archive-assimilation progress before this final footer.

After Level 0 PASS, `666` becomes the stochastic emergent research-field genesis trigger, while NEXT LEVEL continues to show the current shared gate and DOOMSDAY remains the long-range Clay 0.1 forecast.

## Q12 behavior

Q12 must understand both horizons. When a major event materially moves DOOMSDAY, Q12 should be able to explain the underlying critical-path table, capability/API change, accelerator/blocker or new dependency rather than merely repeating a date.

## Pre-send invariant

Before every substantive response verify:

1. one final fenced `text` block exists;
2. required RAE metadata fields are present;
3. all registered short commands are present;
4. NEXT LEVEL lines match `tools/program_progress.py`;
5. DOOMSDAY lines match the same resolver / `tools/doomsday_forecast.py`;
6. no fixed/stale DOOMSDAY date is copied from an older response;
7. no prompt-completion percentage is shown;
8. no forbidden frame characters occur;
9. the closing fence is the final visible content.

Any violation is a formatting/governance bug and must be corrected before sending.
