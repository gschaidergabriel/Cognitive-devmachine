# Forschungsrun 2 — static-attestation authenticity confirmation

## Scope

Non-model, non-interventional confirmation of `R2_B11_CROSS_TASK_GATE_IS_NOT_RUNTIME_EVIDENCE_AUTHENTICATOR` from the main Run-2 synthesis. No new runtime/model/provider credit is created.

## Direct test-source confirmation

Current `tests/test_trigger1_cross_task_abstract_control_gate_v2.py` constructs `valid()` entirely from synthetic caller-provided data and expects:

`g.adjudicate(valid())["cross_task_abstract_native_control_pass"] == True`

The positive fixture contains:

- three toy basis directions of dimension **3**, e.g. `[1.0, 0.1, 0.0]`;
- caller-declared pinned GGUF and llama.cpp identity strings;
- caller-declared rank-consistency booleans;
- caller-declared tokenizer/runtime binding boolean;
- caller-declared geometry null thresholds;
- synthetic causal margins (`TARGET=0.5`, `NULL=0.0`, `SIGN_FLIP=-0.4`, other controls `0.0`);
- synthetic off-target margins;
- no per-row runtime receipts;
- no exact prompt-byte receipts;
- no cvec/vector byte hashes bound to the causal rows.

Therefore the repository's own positive unit test directly demonstrates that `cross_task_abstract_native_control_pass` is a **static schema/predicate pass**, not authenticated Qwen3-0.6B runtime evidence.

This is stronger than an argument from missing fields: the intended unit-test contract positively accepts synthetic three-dimensional evidence material.

## Qwen-specific dimension contrast

Official Qwen3-0.6B configuration reports hidden size `1024`. The positive gate fixture uses dimension `3`. This is valid for testing generic gate logic, but proves that the gate's current PASS cannot itself authenticate a Qwen3-0.6B hidden-state vector identity.

## Required naming/evidence boundary

Until a producer/binder is composed in front of the gate, interpret its positive verdict as:

`PASS_STATIC_ATTESTATION_CONSISTENCY_ONLY`

not:

`PASS_AUTHENTICATED_QWEN06_RUNTIME_EVIDENCE`

A future evidence capsule should require exact model/prompt/vector/runtime receipt binding before the static predicates are evaluated for promotion purposes.

## Credit delta

- new model execution: `0`
- runtime credit: `0`
- J-Space model runtime credit: `0`
- canonical semantics promotion: `false`
- research finding confidence: `SOURCE_AND_UNIT_TEST_CONTRACT_CONFIRMED`

## Result

`PASS_STATIC_AUTHENTICITY_BLOCKER_CONFIRMED_BY_POSITIVE_FIXTURE`
