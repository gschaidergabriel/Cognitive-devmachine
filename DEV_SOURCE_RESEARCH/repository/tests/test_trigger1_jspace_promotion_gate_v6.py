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

HEX64 = "a" * 64


def complete_v6_candidate() -> dict:
    return {
        "runtime_intervention_class": "LOCAL_LLAMA_CPP_CVEC_APPLIED",
        "semantic_basis_design": {
            "matched_scenario_triplets": True,
            "within_family_centered": True,
            "equal_family_weighting": True,
            "restricted_within_family_permutation": True,
            "basis_calibration_holdout_disjoint": True,
            "blocked_basis_receipt_sha256": HEX64,
            "matched_family_count": 6,
        },
        "semantic_simplex_rank": {
            "decision": "TWO_DIMENSIONAL_REQUIRED",
            "design_adequately_powered": True,
            "analysis_receipt_sha256": HEX64,
            "representation_rank": 2,
        },
        "downstream_semantic_transport": {
            "endpoint": "model.layers.24.residual_stream",
            "independent_of_intervention_vector": True,
            "independent_of_output_token_identities": True,
            "target_specific_sign_sensitive_displacement": True,
            "controls_fail_to_reproduce": True,
            "transport_receipt_sha256": HEX64,
            "transport_rank": 2,
        },
        "context_valid_dual_readout": {
            "exact_prompt_boundary_tokenization_attested": True,
            "tokenizer_boundary_receipt_sha256": HEX64,
            "context_valid_codebook_family_count": 2,
            "semantic_target_x_code_identity_counterbalanced": True,
            "likelihood_margin_receipt_sha256": HEX64,
            "emitted_decision_receipt_sha256": HEX64,
            "dual_readout_agrees": True,
        },
        "class_selective_causal_matrix": {
            "diagonal_advantage": True,
            "sign_flip_reverses_selectivity": True,
            "null_vector_baseline_like": True,
            "nuisance_controls_fail_to_reproduce": True,
            "equal_family_weighting": True,
            "matrix_receipt_sha256": HEX64,
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
            "geometry_receipt_sha256": HEX64,
        },
    }


def v5_pass() -> dict:
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


class Trigger1JSpacePromotionGateV6Tests(unittest.TestCase):
    def test_complete_second_order_and_native_geometry_passes_research_candidate(self):
        candidate = complete_v6_candidate()
        with patch.object(gate.v5, "adjudicate", return_value=v5_pass()):
            verdict = gate.adjudicate(candidate)
        self.assertTrue(verdict["v6_second_order_controls_pass"])
        self.assertTrue(verdict["v6_native_carrier_geometry_pass"])
        self.assertTrue(verdict["scientifically_independent_vector_candidate"])
        self.assertTrue(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertTrue(verdict["full_native_jspace_vector_control_candidate"])
        self.assertFalse(verdict["canonical_credit_minted"])
        self.assertFalse(verdict["jspace_model_runtime_credit"])
        self.assertFalse(verdict["training_credit"])

    def test_scenario_aliasing_fails_even_when_v5_passes(self):
        candidate = complete_v6_candidate()
        candidate["semantic_basis_design"]["matched_scenario_triplets"] = False
        candidate["semantic_basis_design"]["within_family_centered"] = False
        with patch.object(gate.v5, "adjudicate", return_value=v5_pass()):
            verdict = gate.adjudicate(candidate)
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertIn("MATCHED_SCENARIO_TRIPLETS_REQUIRED", verdict["v6_second_order_failures"])
        self.assertIn("WITHIN_FAMILY_CENTERING_REQUIRED", verdict["v6_second_order_failures"])

    def test_logit_effect_without_emitted_decision_agreement_fails(self):
        candidate = complete_v6_candidate()
        candidate["context_valid_dual_readout"]["dual_readout_agrees"] = False
        with patch.object(gate.v5, "adjudicate", return_value=v5_pass()):
            verdict = gate.adjudicate(candidate)
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertIn("LIKELIHOOD_AND_EMITTED_DECISION_MUST_AGREE", verdict["v6_second_order_failures"])

    def test_output_change_without_independent_downstream_transport_fails(self):
        candidate = complete_v6_candidate()
        candidate.pop("downstream_semantic_transport")
        with patch.object(gate.v5, "adjudicate", return_value=v5_pass()):
            verdict = gate.adjudicate(candidate)
        self.assertFalse(verdict["scientifically_independent_vector_candidate"])
        self.assertIn("DOWNSTREAM_SEMANTIC_TRANSPORT_REQUIRED", verdict["v6_second_order_failures"])

    def test_rank_disagreement_fails_closed(self):
        candidate = complete_v6_candidate()
        candidate["downstream_semantic_transport"]["transport_rank"] = 1
        with patch.object(gate.v5, "adjudicate", return_value=v5_pass()):
            verdict = gate.adjudicate(candidate)
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertFalse(verdict["rank_consistency"]["rank_compatible"])
        self.assertIn("REPRESENTATION_TRANSPORT_BEHAVIORAL_RANKS_MUST_AGREE", verdict["v6_second_order_failures"])

    def test_imported_actuator_without_native_geometry_never_gets_full_native_candidate(self):
        candidate = complete_v6_candidate()
        candidate["native_carrier_geometry"]["target_runtime_basis_reconstructed_independently"] = False
        with patch.object(gate.v5, "adjudicate", return_value=v5_pass()):
            verdict = gate.adjudicate(candidate)
        self.assertTrue(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertFalse(verdict["full_native_jspace_vector_control_candidate"])
        self.assertIn("TARGET_RUNTIME_BASIS_MUST_BE_RECONSTRUCTED_INDEPENDENTLY", verdict["v6_native_carrier_failures"])

    def test_v5_failure_cannot_be_overridden_by_v6_evidence(self):
        candidate = complete_v6_candidate()
        base = v5_pass()
        base["scientifically_independent_vector_candidate"] = False
        base["owner_trigger1_goal_credit_candidate"] = False
        base["owner_trigger1_direct_free_api_model_credit_candidate"] = False
        base["owner_target_failures"] = ["V5_BLOCK"]
        with patch.object(gate.v5, "adjudicate", return_value=base):
            verdict = gate.adjudicate(candidate)
        self.assertTrue(verdict["v6_second_order_controls_pass"])
        self.assertFalse(verdict["scientifically_independent_vector_candidate"])
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertFalse(verdict["full_native_jspace_vector_control_candidate"])
        self.assertIn("V5_BLOCK", verdict["owner_target_failures"])


if __name__ == "__main__":
    unittest.main()
