# Authority drift note — 2026-08-27

Evidence class: `NEGATIVE_RESULT` + `CURRENT_SOURCE`.

## Observation

At canonical main `854f6bc87780f4a5242489a6c807d186b16a8c3d`:

- `research_entity/claycode/autonomous/SUPERVISOR_INBOX.json` reports schema `9.13`, `9.13O_NON_AUTHORITY`, and current provider state HARD_OFF / all provider routes false / Together forbidden / no paid fallback.
- `research_entity/rooms/PROGRAM_STATE.json` still reports schema `8.78`, points to `SUPERVISOR_STEERING_8_78.json`, and contains older owner-authorized free-contingent/VPS language.

The two surfaces therefore describe different authority epochs.

## Resolution rule

Do **not** average them.

The current inbox-selected supervisor state is newer and more specific for provider/runtime authority. `PROGRAM_STATE.json` is a stale current-facing surface until synchronized. Its older execution-policy text must not be used to re-enable provider/VPS/Together behavior forbidden by the newer 9.13 authority.

This is an instance of the project’s known failure class:

```text
SELF_CONSISTENT_STALE_ISLAND
```

A validator could pass against its own old constants while canonical authority has already advanced.

## Consequence for Frankenstein

The post-9.13 Frankenstein Bauleiter/Bugfixer scripts on current main cannot derive execution authority from stale 8.78 provider language in `PROGRAM_STATE.json`. The newer 9.13 HARD_OFF boundary controls.

## Required repair

A future authority-sync change should update current-facing surfaces from one successor-dynamic source of truth rather than hard-coding another version number.

Acceptance condition:

1. current-facing program state resolves the same provider authority epoch as the current supervisor inbox;
2. tests derive expected authority from the current canonical pointer/inbox, not from the validator under test;
3. stale provider/Together/VPS allowances cannot survive as executable authority;
4. historical 8.78 text remains available as provenance rather than being rewritten as if it never existed.

No runtime credit is granted by this note.
