# Authority drift note — 2026-08-27

Evidence class: `NEGATIVE_RESULT` + `CURRENT_SOURCE`.

## Observation

At canonical main `854f6bc87780f4a5242489a6c807d186b16a8c3d`:

- `research_entity/claycode/autonomous/SUPERVISOR_INBOX.json` reports schema `9.13`, `9.13O_NON_AUTHORITY`, and current provider state HARD_OFF / all provider routes false / Together forbidden / no paid fallback.
- `research_entity/rooms/PROGRAM_STATE.json` still reports schema `8.78`, points to `SUPERVISOR_STEERING_8_78.json`, and contains older owner-authorized free-contingent/provider language alongside the active dual-machine local/VPS sandbox authority.

The two surfaces therefore describe different authority epochs for provider execution.

## Resolution rule

Do **not** average them.

The current inbox-selected supervisor state is newer and more specific for provider/runtime authority. `PROGRAM_STATE.json` is a stale current-facing surface for provider admission until synchronized. Its older free-provider-contingent text must not be used to re-enable Groq/Mistral/NVIDIA/OpenRouter, Together, or paid fallback while the newer 9.13 HARD_OFF authority says all provider routes are false.

This does **not** mean the VPS sandbox itself is forbidden. The active owner authority still authorizes the `clay-direct-dev` sandbox, and the 9.13 inbox explicitly states that non-provider local or sandbox validation is allowed under current FREE_ONLY authority. Provider HARD_OFF and non-provider sandbox execution are separate boundaries.

This is an instance of the project’s known failure class:

```text
SELF_CONSISTENT_STALE_ISLAND
```

A validator could pass against its own old constants while canonical authority has already advanced.

## Consequence for Frankenstein

The post-9.13 Frankenstein Bauleiter/Bugfixer scripts on current main cannot derive provider execution authority from stale 8.78 free-contingent language in `PROGRAM_STATE.json`. The newer 9.13 HARD_OFF provider boundary controls. Non-provider source review, local validation, and authorized sandbox validation remain available and should be preferred for clean re-execution while provider routes are HARD_OFF.

## Required repair

A future authority-sync change should update current-facing provider-authority surfaces from one successor-dynamic source of truth rather than hard-coding another version number. It must preserve the distinct active owner boundary for non-provider local/VPS sandbox work unless a newer explicit owner authority changes that boundary.

Acceptance condition:

1. current-facing program state resolves the same provider authority epoch as the current supervisor inbox;
2. tests derive expected provider authority from the current canonical pointer/inbox, not from the validator under test;
3. stale provider/Together/paid-fallback allowances cannot survive as executable authority;
4. non-provider local/VPS sandbox authority is not accidentally disabled by provider HARD_OFF;
5. historical 8.78 text remains available as provenance rather than being rewritten as if it never existed.

No runtime credit is granted by this note.
