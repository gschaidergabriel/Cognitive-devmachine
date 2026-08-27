# Authority drift note — 2026-08-27

Evidence class: `CURRENT_SOURCE` + `NEGATIVE_RESULT`.

Observed against canonical `main` `05c66f47495b22b5366e1471d842e77e5ca174ba`.

## Current-facing stale island

Two current-facing continuity surfaces remain at schema `8.78`:

- `research_entity/continuity/BOOTSTRAP_MINIMAL.json`
- `research_entity/rooms/PROGRAM_STATE.json`

while:

- `research_entity/claycode/autonomous/SUPERVISOR_INBOX.json` is schema `9.13` and selects 9.13O steering;
- current 9.13 provider authority is HARD_OFF: provider routes not admitted, Together forbidden, no paid fallback, Free-Swarm emergency stop active.

The older 8.78 surfaces contain execution/provider language that is incompatible with the newer 9.13 boundary. They therefore form a `SELF_CONSISTENT_STALE_ISLAND` for current execution decisions.

## Resolution

Do not average the surfaces.

`BOOTSTRAP_MINIMAL.json` itself records the relevant resolution order: newest explicit owner authority, then `SUPERVISOR_INBOX`-selected steering, then bootstrap/program state, then executable evidence. Under that rule, the newer 9.13 inbox/steering state outranks the stale 8.78 current-facing files.

Consequences:

- stale 8.78 provider/VPS/free-contingent text cannot re-enable execution forbidden by 9.13;
- historical Together allowance cannot mint a paid run;
- current runtime credit remains scoped by the current inbox/steering and exact admitted evidence.

## Post-HARD_OFF caller evidence

Triggerword-3 source work on `main` added a stdlib-first gate around the canonical Frankenstein Bauleiter/Bugfix entrypoints and quarantined their original provider-backed bodies as donor provenance. The associated commit reports 10/10 focused local tests, source/local-unit scope only.

That is useful closure at the **Frankenstein entrypoint** boundary, but it is not whole-provider-path closure: canonical `main` subsequently advanced to commit `05c66f47495b22b5366e1471d842e77e5ca174ba`, a fresh `harness(freepool-fallback)` Mistral provenance commit. This is consistent with the current supervisor finding that the outer `stern.py -> harness_aider.py -> last-resort/llm.py` caller remains P0 open.

Therefore:

```text
Frankenstein canonical entrypoint pre-provider gate: SOURCE/LOCAL-UNIT CLOSURE
external FreePool caller chain: OPEN / POST-HARD_OFF EXECUTION EVIDENCE EXISTS
provider-path runtime PASS: false
```

## Repair acceptance

A successor authority-sync/caller-boundary change should be accepted only when:

1. current-facing continuity surfaces resolve the same provider authority epoch as `SUPERVISOR_INBOX`;
2. expected authority is derived from a successor-dynamic canonical pointer rather than a validator's own stale constant;
3. under HARD_OFF, the real external caller path proves `provider_calls=0` and `secret_lookups=0` before provider import/network/Aider/fallback dispatch;
4. historical 8.78 text remains available as provenance rather than being rewritten as if it never existed;
5. no component/source test is promoted to whole-provider or whole-EntityOS runtime credit.

No runtime credit is granted by this note.
