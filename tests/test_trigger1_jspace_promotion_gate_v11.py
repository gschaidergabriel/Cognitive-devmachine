from __future__ import annotations

from copy import deepcopy
import hashlib
import unittest
from unittest import mock

from tools import trigger1_abstract_state_protocol_v1 as protocol
from tools import trigger1_jspace_promotion_gate_v11 as gate
from tools import trigger1_scope_matched_broadcast_witness as scope


def h(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def v10_positive_stub() -> dict:
    return {
        "schema": "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v10",
        "scientifically_independent_vector_candidate": True,
        "owner_trigger1_goal_credit_candidate": True,
        "owner_trigger1_direct_free_api_model_credit_candidate": True,
        "modular_hcu_jspace_control_candidate": True,
        "v10_failures": [],
        "canonical_credit_minted": False,
        "canonical_semantics_promotion": False,
        "whole_entityos_hcu_credit": False,
        "whole_hcu_credit": False,
        "jspace_model_runtime_credit": False,
        "training_credit": False,
    }


def candidate() -> dict:
    plans = protocol.expected_case_plans()
    att = protocol.validate_design()
    basis = h("native-q8-family-balanced-basis")
    scores = {
        "PYTORCH_ALL_TOKEN_BROADCAST": {
            "BASELINE": 0.0,
            "+VECTOR": 2.0,
            "SIGN_FLIP": -2.0,
            "NULL_VECTOR": 0.0,
            "ORTHOGONAL_SAME_NORM": 0.4,
            "PERMUTED_SAME_NORM": 0.2,
        },
        "NATIVE_LLAMA_CPP_CVEC": {
            "BASELINE": 0.0,
            "+VECTOR": 1.4,
            "SIGN_FLIP": -1.2,
            "NULL_VECTOR": 0.0,
            "ORTHOGONAL_SAME_NORM": 0.3,
            "PERMUTED_SAME_NORM": 0.1,
        },
    }
    rows = []
    for backend, control_scores in scores.items():
        expected_scope = scope.PYTORCH_SCOPE if backend.startswith("PYTORCH") else scope.NATIVE_SCOPE
        for case in plans["HOLDOUT"]["cases"]:
            for control, value in control_scores.items():
                rows.append({
                    "backend": backend,
                    "case_id": case["case_id"],
                    "prompt_sha256": case["prompt_sha256"],
                    "semantic_target": case["semantic_target"],
                    "output_code_identity": case["output_code_identity"],
                    "control": control,
                    "target_score": value,
                    "runtime_receipt_sha256": h(f"{backend}:{case['case_id']}:{control}"),
                    "basis_packet_sha256": basis,
                    "intervention_scope": "BASELINE_NO_VECTOR" if control == "BASELINE" else expected_scope,
                })
    return {
        "abstract_state_protocol": att,
        "preregistration_evidence": {"case_plans": plans},
        "scope_matched_replication": {
            "schema": gate.SCOPE_EVIDENCE_SCHEMA,
            "scope_contract_sha256": scope.scope_contract()["scope_contract_sha256"],
            "llama_cpp_commit": scope.PINNED_LLAMA_CPP_COMMIT,
            "injection_layer": scope.INJECTION_LAYER,
            "dimension": scope.N_EMBD,
            "historical_last_token_witness_used_for_promotion": False,
            "basis_packet_sha256": basis,
            "rows": rows,
        },
    }


class Trigger1PromotionGateV11Tests(unittest.TestCase):
    def test_positive_requires_abstract_protocol_and_both_scope_matched_backends(self):
        with mock.patch.object(gate.v10, "adjudicate", return_value=v10_positive_stub()):
            result = gate.adjudicate(candidate())
        self.assertTrue(result["abstract_state_protocol_pass"], result["v11_failures"])
        self.assertTrue(result["scope_matched_broadcast_native_replication_pass"], result["v11_failures"])
        self.assertTrue(result["semantic_jspace_claim_candidate"], result["v11_failures"])
        self.assertTrue(result["abstract_state_control_candidate"])
        self.assertFalse(result["canonical_credit_minted"])

    def test_last_token_witness_is_rejected(self):
        value = candidate()
        value["scope_matched_replication"]["historical_last_token_witness_used_for_promotion"] = True
        with mock.patch.object(gate.v10, "adjudicate", return_value=v10_positive_stub()):
            result = gate.adjudicate(value)
        self.assertFalse(result["semantic_jspace_claim_candidate"])
        self.assertIn("HISTORICAL_LAST_TOKEN_WITNESS_MUST_BE_EXCLUDED", result["v11_failures"])

    def test_wrong_pytorch_scope_is_rejected(self):
        value = candidate()
        for row in value["scope_matched_replication"]["rows"]:
            if row["backend"] == "PYTORCH_ALL_TOKEN_BROADCAST" and row["control"] == "+VECTOR":
                row["intervention_scope"] = scope.HISTORICAL_SCOPE
                break
        with mock.patch.object(gate.v10, "adjudicate", return_value=v10_positive_stub()):
            result = gate.adjudicate(value)
        self.assertFalse(result["scope_matched_broadcast_native_replication_pass"])
        self.assertFalse(result["semantic_jspace_claim_candidate"])
        self.assertTrue(any("INTERVENTION_SCOPE_MISMATCH" in x for x in result["v11_failures"]))

    def test_non_specific_native_control_signature_is_rejected(self):
        value = candidate()
        target_case = protocol.expected_case_plans()["HOLDOUT"]["cases"][0]["case_id"]
        for row in value["scope_matched_replication"]["rows"]:
            if row["backend"] == "NATIVE_LLAMA_CPP_CVEC" and row["case_id"] == target_case and row["control"] == "ORTHOGONAL_SAME_NORM":
                row["target_score"] = 2.0
                break
        with mock.patch.object(gate.v10, "adjudicate", return_value=v10_positive_stub()):
            result = gate.adjudicate(value)
        self.assertFalse(result["semantic_jspace_claim_candidate"])
        self.assertTrue(any("SCOPE_CAUSAL_SIGNATURE_FAIL:NATIVE_LLAMA_CPP_CVEC" in x for x in result["v11_failures"]))

    def test_drift_from_frozen_abstract_holdout_plan_is_rejected(self):
        value = candidate()
        value["preregistration_evidence"]["case_plans"]["HOLDOUT"] = deepcopy(
            value["preregistration_evidence"]["case_plans"]["HOLDOUT"]
        )
        value["preregistration_evidence"]["case_plans"]["HOLDOUT"]["cases"][0]["prompt"] += " altered"
        with mock.patch.object(gate.v10, "adjudicate", return_value=v10_positive_stub()):
            result = gate.adjudicate(value)
        self.assertFalse(result["abstract_state_protocol_pass"])
        self.assertFalse(result["semantic_jspace_claim_candidate"])
        self.assertIn("ABSTRACT_STATE_HOLDOUT_PLAN_OBJECT_MISMATCH", result["v11_failures"])

    def test_negative_v10_cannot_be_overridden_by_new_gates(self):
        base = v10_positive_stub()
        base["scientifically_independent_vector_candidate"] = False
        base["owner_trigger1_goal_credit_candidate"] = False
        base["modular_hcu_jspace_control_candidate"] = False
        base["v10_failures"] = ["OLDER_GATE_STILL_BLOCKED"]
        with mock.patch.object(gate.v10, "adjudicate", return_value=base):
            result = gate.adjudicate(candidate())
        self.assertFalse(result["semantic_jspace_claim_candidate"])
        self.assertIn("OLDER_GATE_STILL_BLOCKED", result["v11_failures"])


if __name__ == "__main__":
    unittest.main()
