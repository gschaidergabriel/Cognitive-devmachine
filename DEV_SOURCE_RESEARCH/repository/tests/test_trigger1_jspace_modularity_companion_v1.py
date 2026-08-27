from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_jspace_modularity_companion_v1 as gate

HEX64 = "a" * 64


def sha_obj(value) -> str:
    return gate.canonical_json_sha(value)


def complete_candidate(rank: str = "ONE_DIMENSIONAL_SUPPORTED") -> dict:
    sentinels = sorted(gate.MANDATORY_SENTINELS)
    interventions = ["SEMANTIC_H1"] if rank != "TWO_DIMENSIONAL_REQUIRED" else ["SEMANTIC_H1", "SEMANTIC_H2"]
    cells = []
    for intervention in interventions:
        for sentinel in sentinels:
            cells.append({
                "intervention_id": intervention,
                "sentinel_id": sentinel,
                "equal_family_weighted_standardized_delta": 0.03,
                "max_abs_family_standardized_delta": 0.05,
                "family_count": 4,
                "per_family_effects_receipt_sha256": HEX64,
            })
    candidate = {
        "semantic_rank_decision": rank,
        "modularity_protocol": {
            "frozen_before_holdout": True,
            "protocol_sha256": HEX64,
            "equal_family_weighting": True,
            "family_level_signed_effects_preserved": True,
            "sentinel_endpoints": sentinels,
            "sentinel_set_sha256": sha_obj(sentinels),
            "modular_intervention_ids": interventions,
            "preregistered_max_abs_standardized_cross_effect": 0.10,
            "cross_effect_matrix": cells,
            "cross_effects_within_preregistered_bounds": True,
            "cross_effect_matrix_receipt_sha256": HEX64,
        },
        "pre_intervention_cross_effect_forecast": {
            "diagnostic_only": True,
            "used_to_adjust_holdout_thresholds": False,
            "used_to_relabel_holdout": False,
        },
    }
    if rank == "TWO_DIMENSIONAL_REQUIRED":
        candidate["rank2_composition"] = {
            "preregistered_before_holdout": True,
            "calibration_only_model_fit": True,
            "coefficient_grid_frozen_before_holdout": True,
            "coefficient_grid_sha256": HEX64,
            "fresh_scenario_family_holdout": True,
            "combinations_evaluated": 6,
            "preregistered_max_abs_standardized_residual": 0.12,
            "max_abs_standardized_residual": 0.07,
            "systematic_sign_interaction_absent": True,
            "composition_receipt_sha256": HEX64,
        }
    return candidate


class Trigger1JSpaceModularityCompanionV1Tests(unittest.TestCase):
    def test_rank1_complete_structured_cross_effects_pass(self):
        ok, failures, summary = gate._extra_modularity_evidence(complete_candidate())
        self.assertTrue(ok)
        self.assertEqual([], failures)
        self.assertFalse(summary["rank2_composition_required"])

    def test_missing_mandatory_sentinel_fails(self):
        candidate = complete_candidate()
        missing = "NONSEMANTIC_CODEBOOK_ACCURACY"
        candidate["modularity_protocol"]["sentinel_endpoints"].remove(missing)
        candidate["modularity_protocol"]["sentinel_set_sha256"] = sha_obj(candidate["modularity_protocol"]["sentinel_endpoints"])
        candidate["modularity_protocol"]["cross_effect_matrix"] = [
            c for c in candidate["modularity_protocol"]["cross_effect_matrix"] if c["sentinel_id"] != missing
        ]
        ok, failures, _ = gate._extra_modularity_evidence(candidate)
        self.assertFalse(ok)
        self.assertIn(f"MANDATORY_SENTINEL_REQUIRED:{missing}", failures)

    def test_numeric_cross_effect_bound_cannot_be_overridden_by_boolean(self):
        candidate = complete_candidate()
        candidate["modularity_protocol"]["cross_effect_matrix"][0]["max_abs_family_standardized_delta"] = 0.50
        candidate["modularity_protocol"]["cross_effects_within_preregistered_bounds"] = True
        ok, failures, _ = gate._extra_modularity_evidence(candidate)
        self.assertFalse(ok)
        self.assertTrue(any(x.startswith("CROSS_EFFECT_EXCEEDS_PREREGISTERED_BOUND:") for x in failures))

    def test_incomplete_matrix_fails_closed(self):
        candidate = complete_candidate()
        removed = candidate["modularity_protocol"]["cross_effect_matrix"].pop()
        ok, failures, _ = gate._extra_modularity_evidence(candidate)
        self.assertFalse(ok)
        expected = f"CROSS_EFFECT_CELL_MISSING:{removed['intervention_id']}:{removed['sentinel_id']}"
        self.assertIn(expected, failures)

    def test_rank2_requires_composition_evidence(self):
        candidate = complete_candidate("TWO_DIMENSIONAL_REQUIRED")
        candidate.pop("rank2_composition")
        ok, failures, summary = gate._extra_modularity_evidence(candidate)
        self.assertFalse(ok)
        self.assertTrue(summary["rank2_composition_required"])
        self.assertIn("RANK2_COMPOSITION_EVIDENCE_REQUIRED", failures)

    def test_rank2_complete_composition_passes(self):
        ok, failures, summary = gate._extra_modularity_evidence(complete_candidate("TWO_DIMENSIONAL_REQUIRED"))
        self.assertTrue(ok)
        self.assertEqual([], failures)
        self.assertAlmostEqual(summary["rank2_observed_max_abs_standardized_residual"], 0.07)

    def test_forecast_diagnostic_cannot_tune_holdout(self):
        candidate = complete_candidate()
        candidate["pre_intervention_cross_effect_forecast"]["used_to_adjust_holdout_thresholds"] = True
        ok, failures, _ = gate._extra_modularity_evidence(candidate)
        self.assertFalse(ok)
        self.assertIn("FORECAST_MUST_NOT_ADJUST_HOLDOUT_THRESHOLDS", failures)

    def test_companion_cannot_mint_modular_candidate_when_promotion_v6_fails(self):
        candidate = complete_candidate()
        base = {
            "schema": "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v6",
            "scientifically_independent_vector_candidate": False,
            "owner_trigger1_goal_credit_candidate": False,
            "canonical_credit_minted": False,
            "whole_entityos_hcu_credit": False,
            "jspace_model_runtime_credit": False,
            "training_credit": False,
        }
        with patch.object(gate.promotion_v6, "adjudicate", return_value=base):
            verdict = gate.adjudicate(candidate)
        self.assertTrue(verdict["modularity_companion_controls_pass"])
        self.assertFalse(verdict["modular_hcu_jspace_control_candidate"])
        self.assertFalse(verdict["canonical_credit_minted"])
        self.assertFalse(verdict["jspace_model_runtime_credit"])
        self.assertFalse(verdict["training_credit"])

    def test_modularity_failure_does_not_rewrite_promotion_v6_semantic_result(self):
        candidate = complete_candidate()
        candidate["modularity_protocol"]["cross_effects_within_preregistered_bounds"] = False
        base = {
            "schema": "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v6",
            "scientifically_independent_vector_candidate": True,
            "owner_trigger1_goal_credit_candidate": True,
            "canonical_credit_minted": False,
            "whole_entityos_hcu_credit": False,
            "jspace_model_runtime_credit": False,
            "training_credit": False,
        }
        with patch.object(gate.promotion_v6, "adjudicate", return_value=base):
            verdict = gate.adjudicate(candidate)
        self.assertTrue(verdict["scientifically_independent_vector_candidate"])
        self.assertFalse(verdict["modular_hcu_jspace_control_candidate"])
        self.assertIn("CROSS_EFFECTS_WITHIN_PREREGISTERED_BOUNDS_REQUIRED", verdict["modularity_failures"])


if __name__ == "__main__":
    unittest.main()
