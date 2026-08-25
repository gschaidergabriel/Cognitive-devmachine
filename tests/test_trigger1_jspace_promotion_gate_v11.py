from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_jspace_promotion_gate_v11 as gate


def v10_result(passes: bool, full_native: bool = True) -> dict:
    return {
        "schema": "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v10",
        "scientifically_independent_vector_candidate": passes,
        "owner_trigger1_goal_credit_candidate": passes,
        "modular_hcu_jspace_control_candidate": passes,
        "full_native_jspace_vector_control_candidate": full_native,
        "v10_failures": [] if passes else ["V10_FAIL"],
        "canonical_credit_minted": False,
    }


def abstract_result(passes: bool) -> dict:
    return {
        "pass": passes,
        "failures": [] if passes else ["LEXICAL_OVERLAP"],
        "design_sha256": "d" * 64,
        "payload_lexicon_sizes": {"basis": 18, "calibration": 9, "holdout": 9},
        "payload_lexicon_overlaps": {},
    }


def scope_result(passes: bool) -> dict:
    return {
        "pass": passes,
        "failures": [] if passes else ["PREFILL_MUST_BE_UNSTEERED"],
        "native_single_token_position_scope_candidate": passes,
    }


class Trigger1PromotionGateV11Tests(unittest.TestCase):
    def test_positive_requires_all_three_layers(self):
        with patch.object(gate.v10, "adjudicate", return_value=v10_result(True)), patch.object(
            gate.abstract_gate, "validate", return_value=abstract_result(True)
        ), patch.object(gate.scope_gate, "validate", return_value=scope_result(True)):
            verdict = gate.adjudicate({})
        self.assertTrue(verdict["scientifically_independent_vector_candidate"])
        self.assertTrue(verdict["full_native_jspace_vector_control_candidate"])

    def test_abstract_failure_revokes_inherited_full_native(self):
        with patch.object(gate.v10, "adjudicate", return_value=v10_result(True)), patch.object(
            gate.abstract_gate, "validate", return_value=abstract_result(False)
        ), patch.object(gate.scope_gate, "validate", return_value=scope_result(True)):
            verdict = gate.adjudicate({})
        self.assertFalse(verdict["scientifically_independent_vector_candidate"])
        self.assertFalse(verdict["full_native_jspace_vector_control_candidate"])
        self.assertIn("FULL_NATIVE_REVOKED_BY_V11_HARDENING", verdict["v11_failures"])

    def test_scope_failure_revokes_inherited_full_native(self):
        with patch.object(gate.v10, "adjudicate", return_value=v10_result(True)), patch.object(
            gate.abstract_gate, "validate", return_value=abstract_result(True)
        ), patch.object(gate.scope_gate, "validate", return_value=scope_result(False)):
            verdict = gate.adjudicate({})
        self.assertFalse(verdict["scientifically_independent_vector_candidate"])
        self.assertFalse(verdict["full_native_jspace_vector_control_candidate"])
        self.assertFalse(verdict["legacy_multitoken_prefill_cvec_causally_identical_to_last_token_witness"])

    def test_hardening_cannot_rescue_v10_failure(self):
        with patch.object(gate.v10, "adjudicate", return_value=v10_result(False, full_native=False)), patch.object(
            gate.abstract_gate, "validate", return_value=abstract_result(True)
        ), patch.object(gate.scope_gate, "validate", return_value=scope_result(True)):
            verdict = gate.adjudicate({})
        self.assertFalse(verdict["scientifically_independent_vector_candidate"])
        self.assertFalse(verdict["full_native_jspace_vector_control_candidate"])

    def test_all_credit_fields_remain_non_minting(self):
        with patch.object(gate.v10, "adjudicate", return_value=v10_result(True)), patch.object(
            gate.abstract_gate, "validate", return_value=abstract_result(True)
        ), patch.object(gate.scope_gate, "validate", return_value=scope_result(True)):
            verdict = gate.adjudicate({})
        for key in (
            "canonical_credit_minted", "canonical_semantics_promotion",
            "whole_entityos_hcu_credit", "whole_hcu_credit",
            "jspace_model_runtime_credit", "training_credit",
        ):
            self.assertFalse(verdict[key], key)


if __name__ == "__main__":
    unittest.main()
