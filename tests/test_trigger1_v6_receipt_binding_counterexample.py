from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_jspace_promotion_gate_v6 as gate

FAKE_HEX64 = "a" * 64


def self_attested_v6_candidate() -> dict:
    """No underlying evidence objects: only true booleans plus syntactic digest strings."""
    return {
        "runtime_intervention_class": "LOCAL_LLAMA_CPP_CVEC_APPLIED",
        "semantic_basis_design": {
            "matched_scenario_triplets": True,
            "within_family_centered": True,
            "equal_family_weighting": True,
            "restricted_within_family_permutation": True,
            "basis_calibration_holdout_disjoint": True,
            "blocked_basis_receipt_sha256": FAKE_HEX64,
            "matched_family_count": 6,
        },
        "semantic_simplex_rank": {
            "decision": "TWO_DIMENSIONAL_REQUIRED",
            "design_adequately_powered": True,
            "analysis_receipt_sha256": FAKE_HEX64,
            "representation_rank": 2,
        },
        "downstream_semantic_transport": {
            "endpoint": "model.layers.24.residual_stream",
            "independent_of_intervention_vector": True,
            "independent_of_output_token_identities": True,
            "target_specific_sign_sensitive_displacement": True,
            "controls_fail_to_reproduce": True,
            "transport_receipt_sha256": FAKE_HEX64,
            "transport_rank": 2,
        },
        "context_valid_dual_readout": {
            "exact_prompt_boundary_tokenization_attested": True,
            "tokenizer_boundary_receipt_sha256": FAKE_HEX64,
            "context_valid_codebook_family_count": 2,
            "semantic_target_x_code_identity_counterbalanced": True,
            "likelihood_margin_receipt_sha256": FAKE_HEX64,
            "emitted_decision_receipt_sha256": FAKE_HEX64,
            "dual_readout_agrees": True,
        },
        "class_selective_causal_matrix": {
            "diagonal_advantage": True,
            "sign_flip_reverses_selectivity": True,
            "null_vector_baseline_like": True,
            "nuisance_controls_fail_to_reproduce": True,
            "equal_family_weighting": True,
            "matrix_receipt_sha256": FAKE_HEX64,
            "behavioral_rank": 2,
        },
        "native_carrier_geometry": {
            "target_runtime_basis_reconstructed_independently": True,
            "imported_source_basis_excluded_from_parity_decision": True,
            "carrier_local_norm_calibration": True,
            "principal_angle_or_equivalent_subspace_test": True,
            "leave_one_family_out_stability": True,
            "permutation_null_passed": True,
            "within_carrier_causal_matrix_passed": True,
            "geometry_receipt_sha256": FAKE_HEX64,
        },
    }


def v5_pass_stub() -> dict:
    return {
        "schema": "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v5",
        "mechanism_runtime_vector_credit_candidate": True,
        "scientifically_independent_vector_candidate": True,
        "owner_trigger1_goal_credit_candidate": True,
        "owner_trigger1_direct_free_api_model_credit_candidate": True,
        "canonical_credit_minted": False,
        "whole_entityos_hcu_credit": False,
        "jspace_model_runtime_credit": False,
        "training_credit": False,
        "owner_target_failures": [],
    }


class Trigger1V6ReceiptBindingCounterexample(unittest.TestCase):
    @unittest.expectedFailure
    def test_unbound_fake_receipts_must_not_be_promotable(self):
        candidate = self_attested_v6_candidate()
        with patch.object(gate.v5, "adjudicate", return_value=v5_pass_stub()):
            verdict = gate.adjudicate(candidate)

        # Desired fail-closed invariant: syntax-valid digest strings and self-declared
        # booleans cannot substitute for recomputable evidence packets. This currently
        # fails against v6 and therefore remains a strict executable counterexample.
        self.assertFalse(verdict["v6_second_order_controls_pass"])
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertFalse(verdict["full_native_jspace_vector_control_candidate"])


if __name__ == "__main__":
    unittest.main()
