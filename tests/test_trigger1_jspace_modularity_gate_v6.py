from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_jspace_modularity_gate_v6 as gate

HEX64 = "b" * 64


def modularity_candidate(rank: int = 1) -> dict:
    candidate = {
        "modularity_evidence": {
            "sentinel_behaviors": sorted(gate.REQUIRED_SENTINELS),
            "cross_effect_matrix_receipt_sha256": HEX64,
            "equal_family_weighting": True,
            "per_family_signed_cross_effects_preserved": True,
            "fresh_holdout_family_count": 3,
            "cross_effect_thresholds_selected_on_calibration_only": True,
            "cross_effect_threshold_rule_sha256": HEX64,
            "max_abs_standardized_drift_within_preregistered_bounds": True,
            "no_structured_nuisance_reproduces_target_matrix": True,
            "target_selectivity_preserved_across_families": True,
            "representation_rank": rank,
            "pre_intervention_forecast": {
                "performed": True,
                "diagnostic_only": True,
                "used_to_adapt_holdout_thresholds": False,
                "better_than_preregistered_null": True,
                "receipt_sha256": HEX64,
            },
        }
    }
    if rank == 2:
        candidate["modularity_evidence"]["rank2_composition"] = {
            "composition_model_fit_on_calibration_only": True,
            "coefficient_grid_frozen_before_holdout": True,
            "same_residual_norm_relative_dose": True,
            "composition_model_receipt_sha256": HEX64,
            "combined_intervention_receipt_sha256": HEX64,
            "compositional_residual_metric_sha256": HEX64,
            "residual_tolerance_selected_on_calibration_only": True,
            "heldout_residuals_within_frozen_tolerance": True,
            "no_systematic_sign_interaction_missed": True,
            "family_consistency_pass": True,
        }
    return candidate


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
        "v5_specificity_failures": [],
    }


class Trigger1JSpaceModularityGateV6Tests(unittest.TestCase):
    def test_rank1_bounded_cross_effects_can_form_modular_candidate(self):
        with patch.object(gate.v5, "adjudicate", return_value=v5_pass()):
            verdict = gate.adjudicate(modularity_candidate(rank=1))
        self.assertTrue(verdict["cross_effect_modularity_controls_pass"])
        self.assertFalse(verdict["rank2_composition_applicable"])
        self.assertTrue(verdict["rank2_composition_controls_pass"])
        self.assertTrue(verdict["modular_hcu_jspace_control_candidate"])
        self.assertFalse(verdict["linear_rank2_coefficient_abi_candidate"])
        self.assertFalse(verdict["canonical_credit_minted"])

    def test_large_cross_effect_blocks_modularity_even_when_forecast_succeeds(self):
        candidate = modularity_candidate(rank=1)
        candidate["modularity_evidence"]["max_abs_standardized_drift_within_preregistered_bounds"] = False
        with patch.object(gate.v5, "adjudicate", return_value=v5_pass()):
            verdict = gate.adjudicate(candidate)
        self.assertFalse(verdict["modular_hcu_jspace_control_candidate"])
        self.assertTrue(verdict["pre_intervention_cross_effect_forecast_utility_candidate"])
        self.assertIn("SENTINEL_CROSS_EFFECT_BOUND_EXCEEDED", verdict["modularity_failures"])

    def test_rank2_requires_composition_evidence(self):
        candidate = modularity_candidate(rank=2)
        candidate["modularity_evidence"].pop("rank2_composition")
        with patch.object(gate.v5, "adjudicate", return_value=v5_pass()):
            verdict = gate.adjudicate(candidate)
        self.assertTrue(verdict["rank2_composition_applicable"])
        self.assertFalse(verdict["rank2_composition_controls_pass"])
        self.assertFalse(verdict["modular_hcu_jspace_control_candidate"])
        self.assertIn("RANK2_COMPOSITION_EVIDENCE_REQUIRED", verdict["modularity_failures"])

    def test_rank2_heldout_composition_pass_can_form_linear_abi_candidate(self):
        with patch.object(gate.v5, "adjudicate", return_value=v5_pass()):
            verdict = gate.adjudicate(modularity_candidate(rank=2))
        self.assertTrue(verdict["modular_hcu_jspace_control_candidate"])
        self.assertTrue(verdict["linear_rank2_coefficient_abi_candidate"])

    def test_nonlinear_rank2_residual_blocks_linear_abi(self):
        candidate = modularity_candidate(rank=2)
        candidate["modularity_evidence"]["rank2_composition"]["heldout_residuals_within_frozen_tolerance"] = False
        with patch.object(gate.v5, "adjudicate", return_value=v5_pass()):
            verdict = gate.adjudicate(candidate)
        self.assertFalse(verdict["modular_hcu_jspace_control_candidate"])
        self.assertFalse(verdict["linear_rank2_coefficient_abi_candidate"])
        self.assertIn("RANK2_HELDOUT_COMPOSITION_RESIDUAL_EXCEEDS_TOLERANCE", verdict["modularity_failures"])

    def test_v5_failure_cannot_be_repaired_by_perfect_modularity_fields(self):
        base = v5_pass()
        base["scientifically_independent_vector_candidate"] = False
        base["owner_trigger1_goal_credit_candidate"] = False
        with patch.object(gate.v5, "adjudicate", return_value=base):
            verdict = gate.adjudicate(modularity_candidate(rank=2))
        self.assertTrue(verdict["cross_effect_modularity_controls_pass"])
        self.assertTrue(verdict["rank2_composition_controls_pass"])
        self.assertFalse(verdict["modular_hcu_jspace_control_candidate"])
        self.assertFalse(verdict["linear_rank2_coefficient_abi_candidate"])
        self.assertFalse(verdict["jspace_model_runtime_credit"])
        self.assertFalse(verdict["training_credit"])


if __name__ == "__main__":
    unittest.main()
