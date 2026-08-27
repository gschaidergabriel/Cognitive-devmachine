# Harness H-WP-10 — Effect Authority Freshness Foundation

Run: `harness-20260809T1710p0700-effect-authority-v1`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: `r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE`  
Status: `PASS_SYNTHETIC_FOUNDATION_NOT_PROMOTED`

## Goal

Build and execute a deterministic reference oracle for the final effect-commit boundary without granting authority to model output, Needle routing, GWT selection, ClayGraph activation, recurrence or emergent-state observations.

The tested candidate binds commit eligibility to the exact decision dependency closure plus capability generation/epoch, resource generation/identity, current budget, information-flow allowance, external authorization for irreversible effects and local idempotency identity.

## Mesh inputs

This run joined the current Harness mesh and avoided active H-WP-02, H-WP-04 and H-WP-11 claims. Primary fresh discriminators were:

- recurrent decision freshness / dependency-envelope research from `clayresearch`;
- ClayCode generational resource-handle ABA probe;
- fixed Clay-native authority contract and Safe-Effect geometry;
- current TurnTraceEnvelope replay foundation;
- concurrent external-effect recovery probe discovered during execution.

These inputs share repository ancestry and are not counted as independent replication.

## Executable artifact

`research_entity/harness/effect_commit_v1.py`

The oracle compares three commit strategies:

1. retained decision-time permit;
2. global epoch equality;
3. scoped dependency/capability/resource/budget validation.

It contains self-tests and exhaustive/fuzz discriminators and does not execute real effects.

## Results

Recorded local synthetic execution:

- Python compile: PASS
- self-tests: 18/18 PASS
- exhaustive state-change matrix: 32 cases
  - retained permit: 30 unsafe commits, 0 false aborts
  - global epoch: 0 unsafe commits, 1 false abort
  - scoped envelope: 0 unsafe commits, 0 false aborts
- seeded fuzz discriminator: 100,000 cases
  - retained permit: 45,008 unsafe commits, 0 false aborts
  - global epoch: 0 unsafe commits, 31,403 false aborts
  - scoped envelope: 0 unsafe commits, 0 false aborts

The initial self-test run exposed a nested-dataclass mutation bug in the test construction; it was corrected before the recorded PASS. This negative development result is preserved in `EXECUTION_RECEIPT.json`.

## Interpretation

Within the constructed state model, a retained permit is unsafe because authority/resource/critical-state conditions may change after decision formation. A global epoch avoids those unsafe commits but invalidates good work when unrelated state changes. The scoped witness preserves safety in these tests while avoiding unrelated-churn aborts.

This supports a Harness candidate rule:

`commit(effect) -> revalidate exact decision deps + capability generation/epoch + resource generation/identity + budget + information-flow + external irreversible approval + recovery/idempotency identity`

It does **not** prove that the chosen dependency closure is complete in live FRANK.

## Important negative result: external exactly-once

A concurrent ClayCode recovery probe demonstrates that local `PREPARED` state is indistinguishable between crash-before-effect and crash-after-effect worlds. Therefore the local idempotency ledger in this H-WP-10 oracle must not be interpreted as proof of exactly-once external effects.

For external effects the future Harness must require one of:

- remote idempotency/deduplication;
- transactional coupling;
- queryable/reconcilable remote effect identity;
- otherwise a typed `UNCERTAIN` recovery outcome.

This limitation blocks promotion of the current oracle to a complete effect ABI.

## Authority non-collapse

The executable tests reject `MODEL_OUTPUT` and `NEEDLE_ROUTE` as authority origins. Irreversible effects require an explicit external approval witness. GWT, ClayGraph, recurrence, Hyperposition and emergence state may enter the declared decision-dependency set where semantically relevant, but they never become authorization evidence merely by activation or selection.

## Branch feedback

Explicit receipts were returned to `frank`, `claycode`, `clayresearch`, `unifieddb`, `gwt`, `claygraph`, `hyperposition`, `emergenz` and `harness` in `BRANCH_FEEDBACK.json`.

Key implementation deltas:

- ClayCode runtime ABI: carry dependency versions and generational resource handles;
- UnifiedDB: persist authority/resource/idempotency/recovery witnesses and `UNCERTAIN` outcomes;
- Harness: add capability revoke/regrant, resource ABA, budget shrink, unrelated churn, queue delay, crash/restart and external-effect recovery lanes to H1/H2/H3 differential tests;
- Frank: preserve the existing rule that the model and Needle propose/route but never mint commit authority.

## Promotion boundary

This is `LOCAL_SYNTHETIC_EXECUTION`, not target-host evidence, not live Frank evidence, not an H1 PASS and not a scientific promotion. The repository artifact was materialized after a source-equivalent local execution but exact byte-for-byte repository-source replay was not asserted; CI/Ubuntu replay remains required.

## Next discriminating executions

1. Execute the exact repository source in CI and on Andreas' Ubuntu target.
2. After BASE permits H1 execution, adapt frozen H1 effect traces into the oracle.
3. Inject unrelated churn, critical dependency changes, capability revoke/regrant, resource ABA, budget changes and delayed queues.
4. Add crash/restart worlds for remote-idempotent, transactionally coupled and unreconcilable external effects.
5. Add generated child-code/FFI closure tests so delegated code cannot exceed the parent Clay capability/effect envelope.
6. Differentially reproduce the same suite in H2 ClayCode and later H3.

No paid training was started or authorized by this run.
