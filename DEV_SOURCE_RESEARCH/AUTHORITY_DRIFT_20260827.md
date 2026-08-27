# Authority drift note — 2026-08-27

Evidence class: `NEGATIVE_RESULT` + `CURRENT_SOURCE`.

## Observation

At Triggerword-3 re-entry on canonical main `ed70385760c03a30dea7b6ecf8f6b78cbbaa584a`:

- `research_entity/claycode/autonomous/SUPERVISOR_INBOX.json` reports schema `9.13`, `9.13O_NON_AUTHORITY`, and current provider state HARD_OFF / all provider routes false / Together forbidden / no paid fallback.
- `research_entity/rooms/PROGRAM_STATE.json` still reports schema `8.78`, points to `SUPERVISOR_STEERING_8_78.json`, and contains older owner-authorized free-contingent/provider language alongside the active dual-machine local/VPS sandbox authority.

The two current-facing surfaces therefore describe different authority epochs for provider execution.

## Resolution rule

Do **not** average them.

The current inbox-selected supervisor state is newer and more specific for provider/runtime authority. `PROGRAM_STATE.json` is a stale current-facing surface for provider admission until synchronized. Its older free-provider-contingent text must not be used to re-enable Groq/Mistral/NVIDIA/OpenRouter, Together, or paid fallback while the newer 9.13 HARD_OFF authority says all provider routes are false.

This does **not** mean non-provider local/sandbox validation is forbidden. The 9.13 inbox explicitly states that non-provider local or sandbox validation is allowed under current FREE_ONLY authority. Provider HARD_OFF and non-provider validation are separate boundaries.

This is an instance of the project's known failure class:

```text
SELF_CONSISTENT_STALE_ISLAND
```

A validator could pass against its own old constants while canonical authority has already advanced.

## Consequence for Frankenstein

Historical or quarantined Frankenstein Bauleiter/Bugfixer provider code cannot derive provider execution authority from stale 8.78 free-contingent language in `PROGRAM_STATE.json`. The newer 9.13 HARD_OFF provider boundary controls. Current supported entrypoints now fail closed before provider machinery, but that source/local-unit closure does not synchronize all current-facing authority files and does not create provider runtime credit.

## Required repair

A future authority-sync change should update current-facing provider-authority surfaces from one successor-dynamic source of truth rather than hard-coding another version number. It must preserve the distinct current permission for non-provider local/sandbox validation unless newer explicit authority changes it.

Acceptance condition:

1. current-facing program state resolves the same provider authority epoch as the current supervisor inbox;
2. tests derive expected provider authority from the current canonical pointer/inbox, not from the validator under test;
3. stale provider/Together/paid-fallback allowances cannot survive as executable authority;
4. non-provider local/sandbox validation is not accidentally disabled by provider HARD_OFF;
5. historical 8.78 text remains available as provenance rather than being rewritten as if it never existed.

No runtime credit is granted by this note.
