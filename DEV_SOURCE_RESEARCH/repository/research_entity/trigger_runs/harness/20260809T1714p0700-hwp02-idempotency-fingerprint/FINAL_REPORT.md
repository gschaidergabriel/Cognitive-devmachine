# Harness run — H-WP-02 semantic idempotency fingerprint

Run: `20260809T1714p0700-hwp02-idempotency-fingerprint`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Trigger: `harness`

## Scope

This worker continued the existing `H-WP-02-STATE-LEDGER` claim as a falsification/review worker. It did not create a competing StateLedger lineage.

The current program stage remains `BASE_CLAYCODE_RELEASE`; H1 remains blocked on BASE. This run therefore builds/tests a component-level Harness counterexample and does not claim H1 PASS or live-FRANK validation.

## Mesh grounding

The run used the latest whole-mesh live-fusion closure as compact coverage of all registered peer branches, then reread:

- current `HARNESS_WORKSPACE.json`;
- current `reference_state_ledger.py`;
- the immediately preceding H-WP-02 idempotency-race run;
- recent post-fusion Harness/ClayCode commits including semantic identity, provenance, resource lifetime and effect-authority refinements.

See `INTERCONNECT_MANIFEST.json`.

## New finding

The visible replay decision in the current H1 reference `StateLedger.commit()` checks an existing row by `idempotency_key`; when found, it compares only `existing.event_id` with the retry `event_id`. If those identifiers match, it returns `IDEMPOTENT_REPLAY`.

The replay decision does not visibly compare the retry's changed:

- `event_type`;
- normalized mutations;
- provenance.

Therefore a caller can reuse the same idempotency key and event ID with a semantically changed request and receive replay success instead of a deterministic conflict.

This is distinct from the previously preserved pre-lock concurrency race. The previous race concerns *when* duplicate identity is checked; this finding concerns *what identity is checked*.

## Executed mechanism probe

A deterministic local SQLite mechanism probe modeled the visible reference decision and a guarded fingerprint decision.

Case:

1. first request: `event_id=e1`, `key=k1`, payload `{x:1}`;
2. retry: `event_id=e1`, `key=k1`, payload `{x:2}`.

Observed vulnerable ordering model:

- first request -> `COMMITTED`;
- changed retry -> `IDEMPOTENT_REPLAY`;
- stored payload remained `{x:1}`.

Observed guarded model:

- first request -> `COMMITTED`;
- changed retry -> `IDEMPOTENCY_CONFLICT`;
- stored payload remained `{x:1}`.

Evidence class: `LOCAL_DETERMINISTIC_SYNTHETIC_MECHANISM_PROBE_PLUS_CURRENT_CODE_REVIEW`.

This is not Ubuntu project-host execution of the actual H1 module.

## New executable red probe

Committed:

`research_entity/harness/probes/hwp02_idempotency_payload_fingerprint_probe.py`

The probe imports the actual H1 reference StateLedger. It should fail against the vulnerable implementation and pass only when a same-key/same-event-ID but semantically changed retry is rejected while the original committed state and epoch remain intact.

## Negative result

Preserved as:

`NR-HARNESS-HWP02-IDEMPOTENCY-FINGERPRINT-20260809`

The result does **not** invalidate earlier H-WP-02 successes inside their tested scope, including deterministic root behavior, stale-epoch rejection, explicit epistemic-state preservation, snapshot/restore and tamper checks.

It also does not replace the separate concurrency-race negative result.

## Repair constraint

An idempotent replay must prove semantic request equivalence, not merely identifier reuse.

At minimum, the implementation should bind an equivalent canonical semantic fingerprint over:

- event ID;
- event type;
- normalized mutations;
- provenance.

Execution-local retry metadata such as writer/timestamp should remain separate from semantic identity unless the adjudicated state contract explicitly declares them semantic.

The fingerprint check must also be correctly placed inside the transaction boundary to close the already-known concurrent pre-lock race.

## Local execution handoff

Created dynamic work:

`HWP02-IDEMPOTENCY-FINGERPRINT-LOCAL-FIX`

It is explicitly coalescible with the already queued:

`HWP02-IDEMPOTENCY-RACE-LOCAL-FIX`

The new task auto-invalidates if the race fix already adds equivalent semantic fingerprint validation and passes both the new red probe and full H-WP-02 regression suite.

Required Ubuntu completion evidence:

- actual latest implementation diff;
- identical retry still returns deterministic replay without epoch/state mutation;
- same key/event ID with changed semantic request is rejected;
- committed state/root/epoch remain unchanged after conflict;
- concurrent same-key race passes;
- existing H-WP-02 regression/stress/crash/snapshot/tamper suites pass;
- exact local command/output/commit receipt.

## Mesh feedback

Material constraints were routed to:

- clayresearch;
- frank;
- claycode;
- unifieddb;
- harness.

GWT, Emergenz, Hyperposition and ClayGraph received explicit `NO_CHANGE` receipts for this finding.

See `BRANCH_FEEDBACK_MANIFEST.json`.

## Claim-state consequence

- new negative result: semantic equivalence of idempotent retry is **not established** by the current visible H1 reference replay decision;
- H-WP-02 remains incomplete;
- H1 remains blocked on BASE;
- no canonical scientific promotion;
- no live-FRANK evidence claim;
- no paid training authorization or execution.

## Next discriminating test

Run the committed red probe against the actual current H1 StateLedger on the Ubuntu project host after coalescing the race and fingerprint repairs. Require both semantic-conflict correctness and concurrent idempotency correctness, then rerun the complete H-WP-02 test surface before any completion claim.
