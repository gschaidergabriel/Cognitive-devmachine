from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_jspace_modularity_gate_v1 as gate

HEX64 = "a" * 64


def upstream_pass() -> dict:
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


def rank1_candidate() -> dict:
    return {
        "semantic_subspace": {
            "rank": 1,
            "rank_decision_receipt_sha256": HEX64,
            "rank_selected_before_holdout": True,
        },
        "modularity_evidence": {
            "sentinel_set_preregistered": True,
            "sentinel_set_receipt_sha256": HEX64,
            "sentinel_behavior_count": 5,
            "heldout_scenario_family_count": 4,
            "cross_effect_matrix_test": True,
            "cross_effect_matrix_receipt_sha256": HEX64,
            "equal_family_weighting": True,
            "per_family_signed_cross_effects_recorded": True,
            "per_family_cross_effect_stability_test": True,
            "cross_effect_thresholds_selected_on_calibration_only": True,
            "cross_effect_thresholds_frozen_before_holdout": True,
            "cross_effect_threshold_receipt_sha256": HEX64,
            "max_abs_standardized_sentinel_drift": 0.20,
            "preregistered_max_abs_standardized_sentinel_drift": 0.25,
            "all_sentinel_effects_within_preregistered_bounds": True,
            "structured_nuisance_control_reproduces_target_matrix": False,
            "pre_intervention_forecast": {
                "diagnostic_only": True,
                "used_to_select_holdout_thresholds": False,
                "uses_holdout_outcomes_for_fit": False,
                "receipt_sha256": HEX64,
            },
        },
    }


def rank2_candidate() -> dict:
    candidate = rank1_candidate()
    candidate["semantic_subspace"]["rank"] = 2
    candidate["composition_evidence"] = {
        "combination_grid_frozen_before_holdout": True,
        "combination_grid_receipt_sha256": HEX64,
        "composition_model_fit_on_calibration_only": True,
        "heldout_compositional_residual_test": True,
        "target_and_sentinel_endpoints_included": True,
        "per_family_residuals_recorded": True,
        "compositional_residual_receipt_sha256": HEX64,
        "max_abs_standardized_compositional_residual": 0.12,
        "preregistered_max_abs_standardized_compositional_residual": 0.15,
        "compositional_residuals_within_preregistered_bounds": True,
        "systematic_sign_interaction_missed_by_model": False,
    }
    return candidate


class Trigger1JSpaceModularityGateV1Tests(unittest.TestCase):
    def test_rank1_candidate_can_pass_structured_cross_effect_gate(self):
        with patch.object(gate.v5, "adjudicate", return_value=upstream_pass()):
            verdict = gate.adjudicate(rank1_candidate())

        self.assertTrue(verdict["cross_effect_controls_pass"])
        self.assertTrue(verdict["composition_controls_pass"])
        self.assertTrue(verdict["modular_jspace_control_candidate"])
        self.assertEqual("BOUNDED_MODULAR_CONTROL_CANDIDATE", verdict["modularity_classification"])
        self.assertFalse(verdict["canonical_credit_minted"])

    def test_large_structured_sentinel_cross_effect_blocks_modularity(self):
        candidate = rank1_candidate()
        candidate["modularity_evidence"]["max_abs_standardized_sentinel_drift"] = 0.40
        candidate["modularity_evidence"]["all_sentinel_effects_within_preregistered_bounds"] = False

        with patch.object(gate.v5, "adjudicate", return_value=upstream_pass()):
            verdict = gate.adjudicate(candidate)

        self.assertFalse(verdict["modular_jspace_control_candidate"])
        self.assertEqual("ENTANGLED_CONTROL_WITH_STRUCTURED_CROSS_EFFECTS", verdict["modularity_classification"])
        self.assertIn("SENTINEL_CROSS_EFFECT_EXCEEDS_PREREGISTERED_BOUND", verdict["modularity_failures"])

    def test_forecast_cannot_fit_on_holdout_or_select_holdout_thresholds(self):
        candidate = rank1_candidate()
        forecast = candidate["modularity_evidence"]["pre_intervention_forecast"]
        forecast["used_to_select_holdout_thresholds"] = True
        forecast["uses_holdout_outcomes_for_fit"] = True

        ok, failures = gate._cross_effect_evidence(candidate)

        self.assertFalse(ok)
        self.assertIn("SIDE_EFFECT_FORECAST_MUST_NOT_SELECT_HOLDOUT_THRESHOLDS", failures)
        self.assertIn("SIDE_EFFECT_FORECAST_MUST_NOT_FIT_ON_HOLDOUT_OUTCOMES", failures)

    def test_rank2_requires_explicit_composition_evidence(self):
        candidate = rank1_candidate()
        candidate["semantic_subspace"]["rank"] = 2

        with patch.object(gate.v5, "adjudicate", return_value=upstream_pass()):
            verdict = gate.adjudicate(candidate)

        self.assertFalse(verdict["composition_controls_pass"])
        self.assertFalse(verdict["modular_jspace_control_candidate"])
        self.assertIn("RANK2_COMPOSITION_EVIDENCE_REQUIRED", verdict["modularity_failures"])

    def test_rank2_compositional_residual_must_stay_within_frozen_bound(self):
        candidate = rank2_candidate()
        candidate["composition_evidence"]["max_abs_standardized_compositional_residual"] = 0.30
        candidate["composition_evidence"]["compositional_residuals_within_preregistered_bounds"] = False

        with patch.object(gate.v5, "adjudicate", return_value=upstream_pass()):
            verdict = gate.adjudicate(candidate)

        self.assertFalse(verdict["modular_jspace_control_candidate"])
        self.assertEqual("RANK2_NONLINEAR_OR_COMPOSITION_UNRESOLVED", verdict["modularity_classification"])
        self.assertIn("RANK2_COMPOSITIONAL_RESIDUAL_EXCEEDS_PREREGISTERED_BOUND", verdict["modularity_failures"])

    def test_upstream_v5_failure_can_never_be_repaired_by_modularity_evidence(self):
        base = upstream_pass()
        base["scientifically_independent_vector_candidate"] = False
        base["owner_trigger1_goal_credit_candidate"] = False
        base["owner_trigger1_direct_free_api_model_credit_candidate"] = False

        with patch.object(gate.v5, "adjudicate", return_value=base):
            verdict = gate.adjudicate(rank2_candidate())

        self.assertTrue(verdict["cross_effect_controls_pass"])
        self.assertTrue(verdict["composition_controls_pass"])
        self.assertFalse(verdict["modular_jspace_control_candidate"])
        self.assertEqual("MODULARITY_UNRESOLVED_OR_UPSTREAM_BLOCKED", verdict["modularity_classification"])
        self.assertFalse(verdict["canonical_credit_minted"])
        self.assertFalse(verdict["jspace_model_runtime_credit"])
        self.assertFalse(verdict["training_credit"])


if __name__ == "__main__":
    unittest.main()
