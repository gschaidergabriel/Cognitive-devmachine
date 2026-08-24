# HCU J-SPACE ACTIVATION LEASE RUNTIME FENCE v1

Status: SOURCE / EXECUTION-INGRESS CONTRACT ONLY — NO MODEL-RUNTIME CREDIT
Authority epoch at creation: 8.68
Program: ENTITYOS_HCU
Product: EntityOS
Architecture: HCU
Mode: FREE_ONLY

## Problem

`tools/hcu_jspace_local_activation_probe.py` validates that a supplied unusual-experiment claim exists and has the expected core fields, but the current probe does not itself enforce the full post-claim migration/race fence required by `research_entity/continuity/GO_EXPERIMENT_ATOMIC_LEASE_PROTOCOL.md`.

The atomic lease protocol requires two separate properties before an unusual intervention starts:

1. the caller owns the one canonical create-only claim path for the exact user-triggered `go`;
2. after that claim exists, the claims directory contains no legacy/noncanonical semantic duplicate encoding the same immutable request identity or the same exact timestamp plus payload digest.

A valid-looking claim file alone is therefore insufficient execution authority. Historical repository evidence contains noncanonical claim-key spellings from earlier race incidents, so this is a reachable coordination boundary rather than a theoretical format concern.

## Selected fence

`tools/hcu_jspace_guarded_activation_probe.py` is the canonical execution ingress for the unusual local activation intervention while this contract is active.

Before launching the underlying model probe it must:

- require `clay-go-experiment-claim/v1`, `trigger=go`, `status=CLAIMED`;
- require the claim path to be inside `research_entity/continuity/go_experiment_claims/`;
- require a canonical trigger key in exactly one current protocol form:
  - `rid_<64-lowercase-hex>`; or
  - `ts_<YYYYMMDDTHHMMSSffffffZ>__p_<64-lowercase-hex>`;
- reject a pre-existing `<trigger_key>.result.json`;
- scan sibling claim records before intervention;
- normalize recognized historical timestamp-key forms to UTC;
- treat historical shortened payload hashes as prefixes only for semantic-race detection, never as canonical identity;
- reject with `EXPERIMENT_BUDGET_RACE_VIOLATION` when a recognized legacy/noncanonical sibling encodes the same timestamp plus payload digest;
- bind the guard source hash, underlying probe source hash and exact Git HEAD into the emitted candidate receipt;
- never claim that the guard reconstructed GitHub create-only transaction history merely from the file being present.

## Raw-probe evidence boundary

Direct execution of `tools/hcu_jspace_local_activation_probe.py` remains useful mechanism/source code, but a receipt lacking the `lease_runtime_fence` record from the guarded ingress is **NOT ADMISSIBLE AS A NEW UNUSUAL-EXPERIMENT EXECUTION RECEIPT** under this v1 contract.

This does not create a second experiment authority. The canonical atomic claim protocol remains the coordination authority; the guard only enforces it at the intervention ingress.

## Current-go coordination

The 2026-08-24 18:31 +07 user trigger exposed to this ChatGPT organ has minute-level project metadata, not a shared immutable request/turn identifier or an immutable whole-second-or-better user-message timestamp available to every worker. Therefore this `go` is:

`COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT`

The new guard and its deterministic regressions are ordinary source/control-plane work. No model intervention is authorized or executed by this delta.

## Evidence / promotion law

A guard PASS establishes only that this ingress observed a canonical-form claim and found no recognized semantic duplicate at its execution boundary. It does not establish:

- that GitHub create-only semantics were historically used unless separately evidenced;
- model/checkpoint/tokenizer/runtime loader-consumption identity;
- J-Space causality;
- HCU full runtime;
- training benefit;
- whole EntityOS/HCU acceptance.

All corresponding credits remain zero until their independent exact evidence gates close.
