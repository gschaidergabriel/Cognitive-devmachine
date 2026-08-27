# HCU J-Space Vector-Control ABI Namespace Contract v1

Status: CURRENT SOURCE CONTRACT / FAIL-CLOSED NAMESPACE CONVERGENCE
Program: ENTITYOS_HCU
Product: EntityOS
Architecture: HCU
Authority epoch: supervisor 8.73 / FREE_ONLY

## Purpose

`JSPACE_VECTOR_CONTROL_ABI/v1` SHALL have one current-facing semantic role: a **full causal control packet**. One schema identifier must not name incompatible preimages or wire languages.

This contract resolves the previously observed namespace collision without rewriting historical evidence and without creating a second truth, effect, state or model authority.

## Canonical current meaning

New current-facing uses of:

`schema = JSPACE_VECTOR_CONTROL_ABI/v1`

MUST use:

`abi_role = FULL_CAUSAL_CONTROL_PACKET`

and MUST be accepted through `tools/jspace_vector_control_abi_v1.py` or an explicitly admitted successor preserving these invariants.

A full packet binds at minimum:

- exact source and target model/runtime identity;
- target activation site;
- vector/subspace identity;
- construction/derivation family and receipt;
- explicit proof that holdout was not used for derivation;
- frozen calibration identity;
- applied gain plus a predeclared allowed magnitude envelope;
- token-position policy;
- intervention operator;
- matched control runtime receipts;
- target metric definition;
- distinct off-target metric definition;
- holdout identity;
- causal intervention receipt;
- candidate-only truth/credit fences.

Missing evidence is UNKNOWN and fails closed. It is not inferred from narration, control names, source code shape, majority vote, or a previous positive result.

## Collision quarantine

Two older uses remain provenance but are not valid new packet producers under this namespace:

1. The Trigger-1 promotion bridge historically hashes a small derivation/source descriptor whose preimage contains `schema = JSPACE_VECTOR_CONTROL_ABI/v1`. That object is not a full control packet. New code SHALL NOT copy this use. Its successor namespace should be explicit, e.g. `JSPACE_VECTOR_DERIVATION_DESCRIPTOR/v1`, when the bridge is migrated.
2. Retained donor PR #1263 contains a deterministic q8 vector wire codec under the same schema identifier. It SHALL NOT be fused under `JSPACE_VECTOR_CONTROL_ABI/v1`. A donor fusion must rename/version it under an explicit wire-codec namespace, e.g. `JSPACE_VECTOR_Q8_WIRE_CODEC/v1`, or provide a tested adapter whose source and destination identities remain distinct.

Historical receipts/hashes are not rewritten. Their exact old bytes remain evidence of what existed at that time.

## Current producer gate

The existing Trigger-1 direct candidate does not yet provide all facts required by the full control ABI. In particular, current source does not prove a complete explicit envelope for:

- intervention operator;
- token-position policy;
- off-target metric definition;
- allowed magnitude/energy envelope with receipt;
- frozen calibration receipt in the full-control namespace.

Therefore `tools/jspace_vector_control_abi_v1.py` correctly returns BLOCKED for such candidates until an upstream producer emits `JSPACE_VECTOR_CONTROL_EXPLICIT_EVIDENCE/v1` from predeclared/measured evidence.

This is intentional. `FACT_UNKNOWN + METHOD_PRESENT != FACT_PRESENT`.

## Relation to JSPACE_TRACE_ABI/v1

`JSPACE_TRACE_ABI/v1` is the trace/observation envelope. `JSPACE_VECTOR_CONTROL_ABI/v1` is the full causal control packet. They are complementary and must remain distinguishable.

A future causal trace may reference a validated full control packet, but trace validity alone does not prove control causality and a control packet alone does not mint canonical truth.

## Migration order

1. Keep the new full-control builder/validator as the current namespace gate.
2. Extend the strongest current Trigger-1 producer/bridge to emit `JSPACE_VECTOR_CONTROL_EXPLICIT_EVIDENCE/v1` only from actual predeclared/measured fields.
3. Migrate the old partial descriptor to a non-colliding derivation-descriptor namespace with deterministic regression coverage; preserve old receipts unchanged.
4. Run the full-control packet validator after the direct candidate is built and before any downstream dataset/training promotion.
5. Adapt the PR #1263 q8 codec only under a distinct wire-codec schema; never overload the full-control schema.
6. Bind validated control packet identity into `JSPACE_TRACE_ABI/v1` / downstream TrainingTrace only after exact execution evidence exists.

## Evidence and credit boundary

This contract and its standard-library builder/validator are source/control-plane mechanisms only.

They grant:

- whole EntityOS/HCU runtime credit: 0;
- full HCU runtime credit: 0;
- J-Space model-runtime credit: 0;
- translation/intermodel credit: 0;
- training credit: 0;
- canonical fact credit: 0.

Real/state-changing effects remain behind deterministic EntityOS authority and `EffectGate + EffectJournal`.
