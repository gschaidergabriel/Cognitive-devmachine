# Trigger-2 physical witness wrapper closure audit v1

Status: `SOURCE_AUDIT_NONCANONICAL_FAIL_CLOSED`

Date: 2026-08-26

Organ: GPT-5.6 Sol / ChatGPT organ

Authority context: Supervisor 8.84 · `FREE_ONLY` · EntityOS + HCU. Runtime quiescence remains unresolved/actively blocked. This audit performs no provider/model/physical-GRID10/VPS/training execution and grants zero runtime/training credit.

## Question

Does the newly landed `tools/trigger2_physical_cohort_witness_boundary_v1.py` close the V67 blocker `CALLER_FORGEABLE_PHYSICAL_COHORT_PROOF_DICTIONARY` under the stronger contract recorded in `2026-08-26_TRIGGER2_PHYSICAL_COHORT_WITNESS_CAPABILITY_CONTRACT_V1_GPT56SOL.md`?

## Observed positive delta

The new wrapper is meaningful source progress:

- raw caller dictionaries are rejected by `PhysicalCohortWitnessBoundary.atomic_fused_physical_commit` because the boundary requires a `PhysicalCohortWitness`;
- its public observer path calls the retained `spawn_held_cohort` and refuses proofs explicitly marked `synthetic_source_fixture_only`;
- the witness binds a boundary instance, fabric instance, observer script path/hash, DB path, node set, packet digests and canonical proof payload;
- an in-process HMAC seal prevents ordinary serialized/transplanted proof reconstruction across boundary instances;
- wrapper tests exercise raw-dict rejection, synthetic mint rejection, boundary/fabric transplant rejection, witness tamper rejection, packet-set binding and single delegation.

These are source/component design properties only; no exact-current test execution receipt was observed by this audit.

## Stronger contract comparison

The wrapper does **not yet fully close** the V67/capability-contract boundary at the retained coordinator itself.

### 1. Retained physical coordinator still accepts raw `dict`

Current `FusedFabric.atomic_fused_cohort_commit(...)` still has:

`proof: dict[str, Any]`

and directly evaluates caller-provided physical booleans/markers. A caller that reaches this method can therefore still bypass the wrapper. The stronger contract explicitly requires the physical coordinator to fail closed unless a physical witness/capability is presented.

Adjudication: wrapper-only enforcement is useful, but it is not equivalent to source-enforcing the invariant at the sole mutation boundary.

### 2. Cohort identity still omits evidence class

Current `FusedFabric.derive_cohort_id(...)` hashes scope, coordinator lease, starting snapshot, starting membership digest and canonical members. It does not include `evidence_class`.

The capability contract requires at least the disjoint classes:

- `PHYSICAL_OBSERVED`
- `SOURCE_FIXTURE_ONLY`

and requires identical structural envelopes admitted under different evidence classes to derive different cohort identities.

Adjudication: `SOURCE_AND_PHYSICAL_COHORT_IDS_DISJOINT` is not source-closed by the wrapper.

### 3. Persisted admission schema still omits evidence class

Current `fused_cohort_admissions` has no `evidence_class` column. The wrapper receipt says `raw_proof_dictionary_accepted_at_physical_boundary: false`, but the sole underlying persisted cohort record does not itself encode whether admission was physical-observed or source-fixture-only.

Adjudication: evidence-class provenance is not yet persisted at the cohort authority boundary.

### 4. No distinct source-fixture commit route is present in the retained coordinator

The stronger contract calls for an explicitly nonphysical `SOURCE_FIXTURE_ONLY` route that can exercise persistence/replay semantics without being confusable with physical evidence. The current wrapper delegates to the existing raw-proof coordinator, and the current source fixture can still call that coordinator directly.

Adjudication: source-composition and physical evidence admission remain separable by convention/wrapper entry point, not yet by the retained mutation API itself.

## Counterhypothesis

`PhysicalCohortWitnessBoundary` can be treated as the only supported public physical API, while `FusedFabric.atomic_fused_cohort_commit` is an internal persistence primitive that intentionally remains untyped.

### Counterhypothesis result

This is insufficient under the currently written V67 capability contract because:

1. `atomic_fused_cohort_commit` remains directly callable and source-enforces no wrapper-only restriction;
2. the contract explicitly places witness rejection at that physical commit gate before envelope verification/mutation;
3. the contract explicitly requires evidence class in cohort identity and persisted admission;
4. source-fixture/physical disjointness cannot be established solely by an outer receipt when the persisted cohort authority is identical.

If authority is intentionally revised so `atomic_fused_cohort_commit` is reclassified as a private class-agnostic persistence primitive and **all** mutation entry paths are statically/runtime-enforced through typed evidence-class front doors, that would be a different closure design and needs an explicit successor contract plus reachability tests.

## Current blocker decomposition

`CALLER_FORGEABLE_PHYSICAL_COHORT_PROOF_DICTIONARY` is now partially reduced:

- `WRAPPER_RAW_DICT_REJECTION`: source-designed, not execution-credited here;
- `WRAPPER_SYNTHETIC_MINT_REJECTION`: source-designed, not execution-credited here;
- `RETAINED_COORDINATOR_RAW_DICT_REJECTION`: **OPEN**;
- `EVIDENCE_CLASS_IN_COHORT_ID`: **OPEN**;
- `EVIDENCE_CLASS_PERSISTED`: **OPEN**;
- `DISTINCT_SOURCE_FIXTURE_ROUTE`: **OPEN**;
- `EXACT_CURRENT_EXECUTION`: **OPEN**.

## Cheapest high-information next discriminator

Modify the retained `FusedFabric` boundary rather than adding another outer wrapper:

1. make the physical mutation entry require a registered/opaque witness handle or split the underlying mutation primitive into an explicitly private class-agnostic helper;
2. add `evidence_class` to cohort-id derivation and persisted admission;
3. add an explicit `SOURCE_FIXTURE_ONLY` front door whose receipt hard-codes zero physical credit;
4. prove identical envelopes under `PHYSICAL_OBSERVED` vs `SOURCE_FIXTURE_ONLY` yield disjoint cohort IDs;
5. prove a raw all-true dict cannot mutate via **any reachable public physical commit path**;
6. prove serialized witness reconstruction cannot regain physical authority;
7. keep the sole deterministic state mutation implementation shared internally so no second truth/effect authority is created.

## Credit boundary

- new source audit delta: `1`
- physical proof boundary fully closed: `0`
- wrapper execution credit: `0`
- repository CI credit: `0`
- physical GRID10 runtime credit: `0`
- model-call runtime credit: `0`
- J-Space model credit: `0`
- accepted dataset tokens: `0`
- training credit: `0`
- whole HCU runtime credit: `0`
- whole EntityOS runtime credit: `0`
