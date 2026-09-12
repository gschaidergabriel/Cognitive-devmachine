# TRIGGER 999 — canonical Realtime presence-policy merge receipt

Date: 2026-09-12
Organ: ChatGPT / GPT-5.6 Sol
Scope: product-source convergence + real-host verification; **not** whole human-conversation acceptance

## Result

The strongest open product gate identified by the prior 999 convergence pass (Frankenstein issue #48) is now closed on canonical `frankenstein/main`.

Current verified product head at this receipt:

- repo: `gschaidergabriel/frankenstein`
- main: `7a7b12d7f2408eb3fdd6e03aa8a53f7942961d16`
- merge: PR #55 — `999: gate canonical Realtime initiative through presence policy`
- issue #48: CLOSED by the merge

The run re-resolved authority repeatedly because `main` moved while the gate was being implemented:

1. `bdb2a74...` — explicit conversation-presence policy + tests/CI existed, but canonical `_stille_reopen_pruefen()` still used binary shadow/non-shadow realization.
2. `882f205...` — Voice convergence merge landed while work was active.
3. `938f2d0...` — PR #51 landed deterministic reactive social-floor arbitration (`RESPOND/BACKCHANNEL/HOLD`) in the canonical transcript path.
4. `7a7b12d...` — PR #55 then merged the still-missing **proactive initiative realization policy** after existing GWT selection and stale-context revalidation.

No stale base was force-merged. The first candidate PR (#54) was explicitly closed as superseded after `main` advanced; the accepted delta was rebuilt/ported and reverified against the newer product base.

## Exact behavioral closure

The canonical silence/reopen path now keeps the existing architecture:

`existing candidates -> existing GWT/voice_loop_core arbitration -> existing stale-context revalidation -> conversation_presence_policy -> existing _response_erstellen()`

There is **no** second GWT, turn loop, state DB, memory authority, watcher, or effect authority.

For an already-selected `SPEAK` candidate, the existing `conversation_presence_policy.decide_initiative()` now receives only existing/measured product values:

- `self._vl_initiative_modus`
- selected `gewinner.akt.value`
- current PresenceBridge `user_present`
- existing explicit transcript contradiction/STOP/NO helper
- `gewinner.interruption_cost`
- current chatter debt
- selected score
- configured speak threshold

Mechanical result:

- `SUPPRESS` -> no `_response_erstellen()`; exact policy reason is recorded.
- `CONFIRM` -> bounded conversational confirmation/question only; effect authority is not granted.
- `ALLOW` -> the already-selected speech act uses the existing response realization path.
- stale context still wins before policy realization.
- no real transcript => NO/STOP state is treated UNKNOWN and unsolicited initiative fails closed.
- `effect_execution_authorized` remains `false` in the policy evidence.
- existing `initiative_episode` remains the canonical evidence row; policy mode/action/reason are written into its `outcome_json` instead of creating a second store.
- production default remains `shadow`.

This is complementary to PR #51's reactive social-floor gate; it does not replace it.

## Real-host evidence

Target/receipt attribution is explicit:

- `machine_id`: `ai-core-node`
- `owner`: `gabriel`
- execution boundary: `REAL_LOCAL_HOST_AI_CORE_NODE_NOT_SANDBOXED`
- scratch checkout only; no production Voice/Avatar/VM service touched

Accepted current-base port receipt:

- Local Bridge command: `999-presence-port-5032259d66e6`
- receipt: `local_bridge/results/receipts/999-presence-port-5032259d66e6.json`
- receipt status: `PASS`
- exit code: `0`
- exact tested branch head: `2c9dd81f69e91d180178ab7f6aff074265f55852`
- exact merge base during port: `882f2053b1e9aadfa015699637efc38ff464cd5b`
- targeted policy + canonical-callsite tests: **22 passed**
- Python compile: PASS
- `git diff --check`: PASS

After PR creation, `main` advanced again through PR #51 to `938f2d0...`; GitHub recomputed PR #55 as mergeable against that newer base. The relevant PR checks on exact head `2c9dd81...` then both completed successfully:

- `conversation-presence-policy`: SUCCESS
- `speaker-handoff-regression`: SUCCESS

Only then was PR #55 merged, with expected-head protection, producing canonical main `7a7b12d...`.

## Negative / non-promotion evidence

This merge does **not** prove or activate full human-like conversation by itself.

Still not promoted:

- whole `999` human-conversation acceptance;
- unrestricted/adaptive unsolicited initiative in production (`shadow` remains default);
- true word-in-the-mouth full-duplex interruption.

The current canonical Realtime mic sender still suppresses microphone upload while assistant audio is playing plus calculated tail time to prevent self-echo. That protects correctness but means true physical full-duplex barge-in is not yet earned. The next solution needs an admitted echo-cancellation / duplex audio path (e.g. PipeWire/AEC-class approach), not a prompt trick.

## Next nonduplicate gates

1. Run a bounded **real Realtime microphone** acceptance session on current `main`, preserving default `shadow`, to verify that PR #51 reactive social-floor behavior + PR #55 initiative-policy logging/suppression coexist with current speaker/host/GRID/immune routing.
2. Re-resolve the open P3 dialogue-act work (currently PR #53) against the new main before any merge; do not assume its pre-#51 base remains current.
3. Treat any old limited-mode activation branch/PR as stale until rebuilt against current main; do not blindly merge an activation branch merely because source tests once passed.
4. Solve/test full-duplex AEC before claiming natural mid-speech interruption.

## Promotion statement

`ISSUE_48_CANONICAL_CALLSITE_CLOSED = 1`

`REAL_HOST_SOURCE_TESTED = 1`

`PR_CHECKS_GREEN = 1`

`CANONICAL_MAIN_MERGED = 1`

`PRODUCTION_DEFAULT_SHADOW = 1`

`REAL_REALTIME_MIC_ACCEPTANCE_AFTER_MERGE = 0`

`TRUE_FULL_DUPLEX_AEC_ACCEPTED = 0`

`WHOLE_999_HUMAN_CONVERSATION_ACCEPTED = 0`

The next `999` should continue from the strongest current nonduplicate live-runtime gate, not rebuild the presence policy or social-floor architecture again.
