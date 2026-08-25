from __future__ import annotations

import hashlib
from unittest import mock

from tools import trigger1_jspace_promotion_gate_v13 as gate


def h(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


CHALLENGE = h("challenge")
BASE = {
    "schema": "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v12",
    "abstract_native_semantic_jspace_candidate": True,
    "abstract_state_challenge_sha256": CHALLENGE,
    "v12_failures": [],
    "canonical_credit_minted": False,
}
INTERNAL = {
    "internal_state_specificity_candidate": True,
    "generic_compliance_rejected_by_same_case_competition": True,
    "abstract_state_challenge_sha256": CHALLENGE,
    "internal_state_analysis_sha256": h("analysis"),
    "failures": [],
}


def run(base=None, internal=None):
    with mock.patch.object(gate.v12, "adjudicate", return_value=dict(BASE if base is None else base)), mock.patch.object(gate.internal_gate, "adjudicate", return_value=dict(INTERNAL if internal is None else internal)):
        return gate.adjudicate({})


def test_v12_plus_reconstructed_internal_state_can_form_candidate_without_minting():
    result = run()
    assert result["abstract_native_semantic_jspace_candidate"]
    assert result["v12_internal_state_challenge_binding_pass"]
    assert not result["strict_micro_mechanistic_identity_candidate"]
    assert not result["canonical_credit_minted"] and not result["jspace_model_runtime_credit"]


def test_internal_failure_blocks_v12_positive():
    result = run(internal={**INTERNAL, "internal_state_specificity_candidate": False, "failures": ["NO_INTERNAL"]})
    assert not result["abstract_native_semantic_jspace_candidate"]
    assert "INTERNAL:NO_INTERNAL" in result["v13_failures"]


def test_v12_failure_cannot_be_repaired():
    result = run(base={**BASE, "abstract_native_semantic_jspace_candidate": False, "v12_failures": ["UPSTREAM"]})
    assert not result["abstract_native_semantic_jspace_candidate"]
    assert "UPSTREAM" in result["v13_failures"]


def test_challenge_identity_mismatch_blocks_composition():
    result = run(internal={**INTERNAL, "abstract_state_challenge_sha256": h("other")})
    assert not result["v12_internal_state_challenge_binding_pass"]
    assert not result["abstract_native_semantic_jspace_candidate"]
    assert "V12_INTERNAL_STATE_CHALLENGE_BINDING_FAILED" in result["v13_failures"]


def test_generic_compliance_rejection_is_visible_in_successor():
    result = run()
    assert result["same_case_generic_compliance_rejected"]
