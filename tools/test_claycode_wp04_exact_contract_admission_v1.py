#!/usr/bin/env python3
from __future__ import annotations

import copy
import json

from claycode_wp04_exact_contract_admission_v1 import (
    ContractAdmissionError,
    admit_exact_contract,
    validate_runtime_binding,
)

SHA_A = "a" * 64
SHA_B = "b" * 64


def must_fail(fn, needle: str) -> None:
    try:
        fn()
    except ContractAdmissionError as exc:
        if needle not in str(exc):
            raise AssertionError(f"wrong failure {exc!r}, expected {needle!r}") from exc
    else:
        raise AssertionError(f"expected fail-closed error containing {needle!r}")


def synthetic_obligation() -> dict:
    return {"identity": {"target": "synthetic.anchor", "arity": 2}}


def explicit_evidence() -> dict:
    return {
        "kind": "EXPLICIT_TYPED_CALLABLE_DECLARATION",
        "target": "synthetic.anchor",
        "arity": 2,
        "params": [
            {"name": "left", "type_name": "InputRef"},
            {"name": "right", "type_name": "ContextRef"},
        ],
        "returns": "DecisionRef",
        "effect_class": "PURE",
        "evidence_ref": "fixture:explicit-typed-declaration",
        "source_sha256": SHA_A,
    }


def valid_binding() -> dict:
    return {
        "runtime_component_hash": SHA_A,
        "current_work_revision": "WORK-TEST-r1",
        "target_binary_build_hash": SHA_B,
        "state_lineage_epoch": 7,
        "instance_lease_ref": "lease:test-current",
        "instance_lease_epoch": 3,
        "sealed": False,
        "authority_scope_ref": None,
        "rollback_ref": None,
    }


def main() -> int:
    obligation = synthetic_obligation()
    evidence = explicit_evidence()
    admitted = admit_exact_contract(obligation, evidence)
    assert admitted["status"] == "DECLARED_SIGNATURE_EXACT_NONEXECUTABLE_UNTIL_BINDING"
    assert admitted["execution_admitted"] is False
    assert admitted["effect_authority"] == "NONE_FROM_CONTRACT"
    assert admitted["inference_used"] is False

    # Evidence/provenance does not contaminate semantic call identity.
    evidence2 = copy.deepcopy(evidence)
    evidence2["evidence_ref"] = "fixture:same-explicit-signature-other-provenance"
    evidence2["source_sha256"] = SHA_B
    admitted2 = admit_exact_contract(obligation, evidence2)
    assert admitted2["contract_semantic_hash"] == admitted["contract_semantic_hash"]

    bound = validate_runtime_binding(admitted, valid_binding())
    assert bound["status"] == "BOUND_CURRENT_RUNTIME_NONEXECUTABLE_UNTIL_WP05"
    assert bound["execution_admitted"] is False
    assert bound["effect_authority"] == "NONE"

    # Signature changes alter semantic identity.
    ret_changed = copy.deepcopy(evidence)
    ret_changed["returns"] = "OtherDecisionRef"
    assert admit_exact_contract(obligation, ret_changed)["contract_semantic_hash"] != admitted["contract_semantic_hash"]

    # Explicitly exercise the currently forbidden inference classes.
    for kind in [
        "CALLER_CONSTRAINTS",
        "TARGET_NAME_SIMILARITY",
        "BASENAME_OR_SUFFIX_MATCH",
        "TYPE_NAME_RESEMBLANCE",
        "HISTORICAL_ROLE_SIMILARITY",
        "MODEL_OUTPUT",
        "CLAYGRAPH_SALIENCE",
    ]:
        bad = copy.deepcopy(evidence)
        bad["kind"] = kind
        must_fail(lambda bad=bad: admit_exact_contract(obligation, bad), "non-authoritative signature evidence")

    wrong_target = copy.deepcopy(evidence)
    wrong_target["target"] = "Synthetic.anchor"
    must_fail(lambda: admit_exact_contract(obligation, wrong_target), "exact target mismatch")

    wrong_arity = copy.deepcopy(evidence)
    wrong_arity["arity"] = 1
    must_fail(lambda: admit_exact_contract(obligation, wrong_arity), "exact arity mismatch")

    for escape in ["Any", "Unknown", "Dynamic", "OpaqueParam"]:
        bad = copy.deepcopy(evidence)
        bad["returns"] = escape
        must_fail(lambda bad=bad: admit_exact_contract(obligation, bad), "forbidden dynamic escape type")

    stale_like = valid_binding()
    stale_like["runtime_component_hash"] = "not-a-hash"
    must_fail(lambda: validate_runtime_binding(admitted, stale_like), "runtime_component_hash")

    # External effects are a separately sealed broker path.
    external = copy.deepcopy(evidence)
    external["effect_class"] = "EXTERNAL_EFFECT"
    effect_contract = admit_exact_contract(obligation, external)
    unsealed = valid_binding()
    must_fail(lambda: validate_runtime_binding(effect_contract, unsealed), "must be sealed")
    sealed_no_scope = valid_binding()
    sealed_no_scope["sealed"] = True
    must_fail(lambda: validate_runtime_binding(effect_contract, sealed_no_scope), "authority_scope_ref")
    sealed_no_rollback = valid_binding()
    sealed_no_rollback.update(sealed=True, authority_scope_ref="scope:test")
    must_fail(lambda: validate_runtime_binding(effect_contract, sealed_no_rollback), "rollback_ref")
    effect_binding = valid_binding()
    effect_binding.update(sealed=True, authority_scope_ref="scope:test", rollback_ref="rollback:test")
    effect_bound = validate_runtime_binding(effect_contract, effect_binding)
    assert effect_bound["execution_admitted"] is False
    assert effect_bound["effect_authority"] == "RUNTIME_BROKER_ONLY_IF_SEPARATELY_AUTHORIZED"

    result = {
        "status": "PASS",
        "scope": "WP04_EXACT_CALL_CONTRACT_ADMISSION_V1",
        "positive_exact_signature": "PASS_NONEXECUTABLE",
        "semantic_identity_provenance_independence": "PASS",
        "signature_mutation_discrimination": "PASS",
        "rejected_inference_classes": 7,
        "fuzzy_target_rejected": True,
        "wrong_arity_rejected": True,
        "dynamic_escape_types_rejected": 4,
        "runtime_component_identity_required": True,
        "external_effect_requires_sealed_scope_rollback": True,
        "execution_admitted_calls": 0,
        "truth_authority": "NONE",
        "effect_authority": "NONE_FROM_CONTRACT",
        "promotion": "NONE",
    }
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
