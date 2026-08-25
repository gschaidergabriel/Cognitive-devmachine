from __future__ import annotations

from copy import deepcopy
import hashlib
import unittest
from unittest import mock

from tools import trigger1_abstract_state_protocol_v1 as protocol
from tools import trigger1_jspace_promotion_gate_v12 as gate


def h(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def v11_positive() -> dict:
    return {
        "schema": "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v11",
        "abstract_native_semantic_jspace_candidate": True,
        "abstract_state_deconfound_pass": True,
        "direct_native_scope_evidence_pass": True,
        "cross_scope_causal_effect_equivalence_candidate": False,
        "strict_micro_mechanistic_identity_candidate": False,
        "v11_failures": [],
        "canonical_credit_minted": False,
    }


def candidate() -> dict:
    att = protocol.validate_design()
    plans = protocol.expected_case_plans()
    projected = h("projected-basis")
    basis_rows = protocol.basis_rows()
    return {
        "abstract_state_exact_protocol": att,
        "preregistration_evidence": {"case_plans": plans},
        "abstract_state_basis_capture_binding": {
            "schema": gate.BASIS_BINDING_SCHEMA,
            "basis_design_sha256": att["basis_design_sha256"],
            "captured_prompt_sha256": [row["prompt_sha256"] for row in basis_rows],
            "family_count": 6,
            "capture_frozen_before_holdout": True,
            "basis_capture_receipt_sha256": h("basis-capture"),
            "projected_basis_receipt_sha256": projected,
        },
        "abstract_state_deconfound": {
            "basis_holdout_lexically_disjoint": True,
            "semantic_synonym_lexicon_disjoint": True,
            "projected_basis_receipt_sha256": projected,
        },
    }


class PromotionV12Test(unittest.TestCase):
    def test_positive_v11_plus_exact_source_audit_can_nominate_candidate(self):
        with mock.patch.object(gate.v11, "adjudicate", return_value=v11_positive()):
            result = gate.adjudicate(candidate())
        self.assertTrue(result["exact_abstract_source_audit_pass"], result["v12_failures"])
        self.assertTrue(result["abstract_native_semantic_jspace_candidate"], result["v12_failures"])
        self.assertTrue(result["abstract_state_control_candidate"])
        self.assertFalse(result["canonical_credit_minted"])
        self.assertFalse(result["strict_micro_mechanistic_identity_candidate"])

    def test_missing_exact_protocol_blocks_even_when_v11_is_positive(self):
        value = candidate()
        value.pop("abstract_state_exact_protocol")
        with mock.patch.object(gate.v11, "adjudicate", return_value=v11_positive()):
            result = gate.adjudicate(value)
        self.assertFalse(result["abstract_native_semantic_jspace_candidate"])
        self.assertIn("ABSTRACT_STATE_EXACT_PROTOCOL_ATTESTATION_REQUIRED", result["v12_failures"])

    def test_holdout_prompt_drift_blocks_exact_source_audit(self):
        value = candidate()
        value["preregistration_evidence"]["case_plans"]["HOLDOUT"] = deepcopy(
            value["preregistration_evidence"]["case_plans"]["HOLDOUT"]
        )
        value["preregistration_evidence"]["case_plans"]["HOLDOUT"]["cases"][0]["prompt"] += " drift"
        with mock.patch.object(gate.v11, "adjudicate", return_value=v11_positive()):
            result = gate.adjudicate(value)
        self.assertFalse(result["exact_abstract_source_audit_pass"])
        self.assertIn("EXACT_AUDIT_HOLDOUT_PLAN_OBJECT_MISMATCH", result["v12_failures"])

    def test_basis_prompt_universe_drift_blocks(self):
        value = candidate()
        value["abstract_state_basis_capture_binding"]["captured_prompt_sha256"][0] = h("wrong")
        with mock.patch.object(gate.v11, "adjudicate", return_value=v11_positive()):
            result = gate.adjudicate(value)
        self.assertFalse(result["abstract_native_semantic_jspace_candidate"])
        self.assertIn("ABSTRACT_STATE_BASIS_CAPTURE_PROMPT_UNIVERSE_MISMATCH", result["v12_failures"])

    def test_projected_basis_receipt_must_cross_bind_v11_deconfound(self):
        value = candidate()
        value["abstract_state_deconfound"]["projected_basis_receipt_sha256"] = h("different")
        with mock.patch.object(gate.v11, "adjudicate", return_value=v11_positive()):
            result = gate.adjudicate(value)
        self.assertFalse(result["abstract_native_semantic_jspace_candidate"])
        self.assertIn("ABSTRACT_STATE_PROJECTED_BASIS_RECEIPT_CROSS_BINDING_MISMATCH", result["v12_failures"])

    def test_negative_v11_cannot_be_overridden(self):
        base = v11_positive()
        base["abstract_native_semantic_jspace_candidate"] = False
        base["v11_failures"] = ["V11_STILL_BLOCKED"]
        with mock.patch.object(gate.v11, "adjudicate", return_value=base):
            result = gate.adjudicate(candidate())
        self.assertFalse(result["abstract_native_semantic_jspace_candidate"])
        self.assertIn("V11_STILL_BLOCKED", result["v12_failures"])


if __name__ == "__main__":
    unittest.main()
