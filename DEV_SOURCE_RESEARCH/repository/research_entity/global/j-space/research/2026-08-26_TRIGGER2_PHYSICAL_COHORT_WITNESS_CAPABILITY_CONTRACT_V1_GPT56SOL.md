# Trigger-2 Physical Cohort Witness Capability Contract v1

Status: `SOURCE_CONTRACT_CANDIDATE_ONLY`

Date: 2026-08-26

Authority context: Supervisor 8.84 · `FREE_ONLY` · EntityOS + HCU. Runtime quiescence remains actively failed. This contract authorizes no provider/model/physical-GRID10/training execution and mints zero runtime or training credit.

## Problem

The retained `FusedFabric.atomic_fused_cohort_commit(...)` currently accepts an ordinary caller-supplied `proof` dictionary. The dictionary carries booleans/markers that are intended to represent observations made by the physical cohort path, but source/API shape alone does not distinguish a genuinely observed proof from a synthetic all-true dictionary.

Current blocker: `CALLER_FORGEABLE_PHYSICAL_COHORT_PROOF_DICTIONARY`.

The strict regression `tests/test_trigger2_physical_proof_provenance_gap_v1.py` must eventually pass by rejecting synthetic/raw physical proof input before any epoch, `fused_cohort_admissions`, or `admitted_results` mutation.

## Design objective

Create one request-scoped physical witness capability bound to the retained `FusedFabric` instance and minted only by the retained physical observation path. Keep deterministic source-fixture composition explicitly nonphysical and structurally incapable of becoming a physical replay or physical runtime receipt.

This is a provenance boundary, not a new coordinator, truth store, effect path, or persistent entity.

## Threat / trust boundary

This contract defends the coordinator API against ordinary caller data, serialized/reconstructed proof objects, accidental reuse, cross-instance transplant, and source-fixture promotion.

It does **not** claim security against arbitrary code already executing with unrestricted introspection/mutation rights inside the same Python process. A Python class name or underscore convention alone is therefore not sufficient evidence of closure.

## Required evidence classes

Two evidence classes are mandatory and disjoint:

- `PHYSICAL_OBSERVED`
- `SOURCE_FIXTURE_ONLY`

The evidence class MUST enter the cohort identity derivation and persisted cohort admission record. The same envelopes admitted under different evidence classes MUST derive different cohort identities.

A `SOURCE_FIXTURE_ONLY` receipt MUST always contain explicit zero physical-runtime credit and MUST never be accepted as a physical replay.

## Physical witness object

Proposed conceptual type:

`PhysicalCohortWitness`

Required immutable fields:

- `schema = PHYSICAL_COHORT_WITNESS/v1`
- `fabric_instance_id`
- `witness_nonce`
- `proof_digest`
- `observation_source = spawn_held_cohort`
- `generation`
- `state_epoch`
- `state_digest`
- `membership_digest`
- canonical node/PID/read-receipt/barrier bindings
- `evidence_class = PHYSICAL_OBSERVED`

The proof payload itself should be immutable/frozen after minting. The witness must not be constructible from an arbitrary JSON/dict path accepted by the physical coordinator.

## Minting rule

Only the retained physical observation path may mint/register a physical witness.

At observation time the owning `FusedFabric` instance generates a high-entropy `witness_nonce`, computes the canonical proof digest, and stores a request-scoped registry entry:

`witness_nonce -> (fabric_instance_id, proof_digest, exact starting identity, exact membership identity, observation bindings, evidence_class)`

The returned `PhysicalCohortWitness` is only a capability handle to that already-registered observation. Possession of a shaped dictionary is insufficient.

The registry is noncanonical runtime provenance. It cannot override UnifiedDB/state/effect authority and cannot mint facts beyond its bounded observation claim.

## Physical commit gate

`atomic_fused_cohort_commit(...)` must fail closed **before envelope verification or mutation** unless all of the following hold:

1. input is a `PhysicalCohortWitness`, not `dict`/Mapping/serialized reconstruction;
2. `evidence_class == PHYSICAL_OBSERVED`;
3. `fabric_instance_id` matches the owning `FusedFabric` instance;
4. `witness_nonce` exists in the owning instance registry;
5. registered proof digest equals the witness proof digest;
6. registered starting generation/epoch/state digest equals the commit expectation;
7. registered membership digest equals the commit expectation;
8. node/PID/read-receipt/barrier bindings match the frozen proof;
9. the witness is not a `SOURCE_FIXTURE_ONLY` object and cannot be converted from one;
10. cohort identity is derived with `evidence_class = PHYSICAL_OBSERVED`.

Required rejection codes include:

- `PHYSICAL_COHORT_WITNESS_REQUIRED`
- `PHYSICAL_COHORT_PROVENANCE_INVALID`
- `PHYSICAL_COHORT_WITNESS_FABRIC_MISMATCH`
- `PHYSICAL_COHORT_WITNESS_DIGEST_MISMATCH`
- `PHYSICAL_COHORT_WITNESS_START_IDENTITY_MISMATCH`
- `PHYSICAL_COHORT_WITNESS_MEMBERSHIP_MISMATCH`

## Source-fixture path

Deterministic adapter persistence/replay testing must use a distinct API, conceptually:

`atomic_fused_source_fixture_commit(...)`

Requirements:

- accepts only an explicitly marked `SOURCE_FIXTURE_ONLY` proof;
- cannot call the physical public gate by pretending to possess a physical witness;
- derives cohort identity with `evidence_class = SOURCE_FIXTURE_ONLY`;
- persists the evidence class alongside the cohort admission;
- returns a receipt whose physical/model/J-Space/training/HCU/EntityOS credits are all zero;
- may test resealed envelope persistence, atomic `state_delta=1`, exact replay `state_delta=0`, tamper rejection, and transport-order invariance only at source-fixture scope.

This path reuses the sole existing deterministic cohort mutation implementation internally; it must not create a second coordinator authority.

## Replay law

Physical replay is valid only while the exact witness provenance can still be verified at the required scope.

A serialized witness or JSON copy is not sufficient to reconstruct physical authority after process restart. If request-scoped witness provenance is lost, physical outcome authority is `UNKNOWN/UNVERIFIED`, not recreated from caller data.

Source-fixture replay remains separately deterministic under `SOURCE_FIXTURE_ONLY` and can never upgrade itself to physical evidence.

## Why a class wrapper alone is insufficient

A plain dataclass/type check is cosmetic if ordinary callers can instantiate it from arbitrary booleans. Closure requires the witness to refer to an observation already registered by the retained physical observation path and bound to the owning `FusedFabric` instance.

## Why an HMAC/signature alone is insufficient

A MAC can prove that some holder of the signing key created the object, but if the public minting API signs arbitrary caller proof dictionaries then provenance is still forgeable semantically. Signing is optional defense-in-depth; issuance must remain observation-bound.

## Minimum source acceptance tests

1. `RAW_DICT_REJECTED_BEFORE_MUTATION`
   - strict V67 xfail becomes ordinary PASS;
   - expected error `PHYSICAL_COHORT_WITNESS_REQUIRED` or narrower successor;
   - epoch/cohort/result counts unchanged.

2. `SYNTHETIC_SOURCE_FIXTURE_REJECTED_BY_PHYSICAL_GATE`
   - all-true source proof cannot enter physical commit.

3. `CROSS_FABRIC_WITNESS_TRANSPLANT_REJECTED`
   - witness minted by Fabric A fails on Fabric B before mutation.

4. `WITNESS_DIGEST_TAMPER_REJECTED`
   - altered proof/binding or digest fails before mutation.

5. `START_IDENTITY_TRANSPLANT_REJECTED`
   - stale generation/epoch/state or membership identity fails before mutation.

6. `SOURCE_FIXTURE_POSITIVE_COMPOSITION`
   - resealed adapter path can produce source-fixture `state_delta=1` and exact replay `state_delta=0` with persisted resealed envelope digests.

7. `SOURCE_AND_PHYSICAL_COHORT_IDS_DISJOINT`
   - identical structural envelopes with different evidence classes cannot share cohort identity.

8. `PHYSICAL_WITNESS_POSITIVE_PATH`
   - only after current execution authority permits exact-current non-provider physical execution; witness comes from retained physical observation path, not a synthetic fixture.

9. `TRANSPORT_ORDER_INVARIANCE_WITHIN_EVIDENCE_CLASS`
   - arrival ordering does not change cohort identity for the same evidence class.

10. `SERIALIZED_WITNESS_CANNOT_REHYDRATE_AUTHORITY`
    - a JSON copy cannot recreate physical admission after registry/session loss.

## Adapter integration

`atomic_fused_two_phase_commit(...)` remains a validation/delegation adapter and must not mint physical witness authority itself.

For physical execution it receives/passes an already valid `PhysicalCohortWitness` to the retained physical coordinator. For source-fixture composition it must explicitly route through the source-fixture API. The two routes must be impossible to confuse through a common untyped `proof` dictionary.

## Acceptance / credit boundary

This document is design evidence only.

- source implementation credit: `0`
- strict-xfail closure credit: `0`
- repository CI credit: `0`
- physical GRID10 runtime credit: `0`
- model/J-Space runtime credit: `0`
- accepted dataset tokens: `0`
- training credit: `0`
- whole HCU runtime credit: `0`
- whole EntityOS runtime credit: `0`

## Next exact action

Implement the boundary in the retained FusedFabric path without creating a peer coordinator: raw/synthetic proof rejection first, observation-bound witness registration/minting second, explicit source-fixture evidence class third, cohort-ID/persistence binding fourth, then promote the V67 strict xfail only after fail-before-mutation is demonstrated on exact current source.