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
FAMILIES = ["family-1", "family-2", "family-3"]
SENTINELS = [
    "GENERIC_COMPLIANCE",
    "DECISIVENESS_PROXY",
    "NONSEMANTIC_CODEBOOK",
    "UNRELATED_LEXICAL_CLASSIFICATION",
]


def v5_pass_verdict(scientific: bool = True) -> dict:
    return {
        "schema": "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v5",
        "mechanism_runtime_vector_credit_candidate": True,
        "scientifically_independent_vector_candidate": scientific,
        "owner_trigger1_goal_credit_candidate": scientific,
        "owner_trigger1_direct_free_api_model_credit_candidate": scientific,
        "canonical_credit_minted": False,
        "whole_entityos_hcu_credit": False,
        "jspace_model_runtime_credit": False,
        "training_credit": False,
        "v5_specificity_controls_pass": scientific,
        "owner_target_failures": [],
    }


def modular_candidate(*, rank2: bool = False) -> dict:
    interventions = ["H1_POS"] if not rank2 else ["H1_POS", "H2_POS"]
    cross_rows = []
    for intervention in interventions:
        for sentinel in SENTINELS:
            for family in FAMILIES:
                cross_rows.append({
                    "intervention_id": intervention,
                    "sentinel_id": sentinel,
                    "family_id": family,
                    "standardized_delta": 0.05,
                    "runtime_receipt_sha256": HEX64,
                })

    evidence = {
        "schema": gate.EVIDENCE_SCHEMA,
        "frozen_before_holdout": True,
        "protocol_sha256": HEX64,
        "target_selectivity_preserved": True,
        "structured_nuisance_control_not_reproduced": True,
        "rank_selection": {
            "decision": "TWO_DIMENSIONAL_REQUIRED" if rank2 else "ONE_DIMENSIONAL_SUPPORTED",
            "receipt_sha256": HEX64,
            "holdout_opened_during_rank_selection": False,
        },
        "intervention_ids": interventions,
        "family_ids": list(FAMILIES),
        "sentinels": [
            {
                "sentinel_id": sentinel,
                "threshold_abs_standardized": 0.20,
                "threshold_frozen_before_holdout": True,
            }
            for sentinel in SENTINELS
        ],
        "cross_effect_matrix_receipt_sha256": HEX64,
        "cross_effect_rows": cross_rows,
    }

    if rank2:
        endpoint_ids = ["SEMANTIC_TARGET", *SENTINELS]
        combinations = ["H1_PLUS_H2", "H1_MINUS_H2"]
        rows = []
        for combination in combinations:
            for endpoint in endpoint_ids:
                for family in FAMILIES:
                    rows.append({
                        "combination_id": combination,
                        "endpoint_id": endpoint,
                        "family_id": family,
                        "predicted_delta": 0.10,
                        "observed_delta": 0.12,
                        "runtime_receipt_sha256": HEX64,
                    })
        evidence["composition"] = {
            "model_frozen_on_calibration_only": True,
            "coefficient_grid_frozen_before_holdout": True,
            "no_systematic_sign_interaction_missed": True,
            "composition_receipt_sha256": HEX64,
            "tolerance_abs_standardized_residual": 0.05,
            "combination_ids": combinations,
            "endpoint_ids": endpoint_ids,
            "target_endpoint_id": "SEMANTIC_TARGET",
            "rows": rows,
        }

    return {"control_modularity": evidence}


class Trigger1JSpaceModularityGateV1Tests(unittest.TestCase):
    def test_rank1_complete_cross_effect_matrix_passes_modularity_companion(self):
        candidate = modular_candidate(rank2=False)
        with patch.object(gate.v5, "adjudicate", return_value=v5_pass_verdict(True)):
            verdict = gate.adjudicate(candidate)
        self.assertTrue(verdict["structured_cross_effect_controls_pass"])
        self.assertTrue(verdict["rank2_composition_controls_pass"])
        self.assertTrue(verdict["modular_jspace_control_candidate"])
        self.assertFalse(verdict["canonical_credit_minted"])
        self.assertFalse(verdict["jspace_model_runtime_credit"])

    def test_v5_semantic_failure_blocks_modular_promotion(self):
        candidate = modular_candidate(rank2=False)
        with patch.object(gate.v5, "adjudicate", return_value=v5_pass_verdict(False)):
            verdict = gate.adjudicate(candidate)
        self.assertTrue(verdict["structured_cross_effect_controls_pass"])
        self.assertFalse(verdict["modular_jspace_control_candidate"])
        self.assertFalse(verdict["semantic_scientific_candidate_preserved_from_v5"])

    def test_incomplete_cross_effect_matrix_fails_closed_but_preserves_v5_semantics(self):
        candidate = modular_candidate(rank2=False)
        candidate["control_modularity"]["cross_effect_rows"].pop()
        with patch.object(gate.v5, "adjudicate", return_value=v5_pass_verdict(True)):
            verdict = gate.adjudicate(candidate)
        self.assertTrue(verdict["semantic_scientific_candidate_preserved_from_v5"])
        self.assertFalse(verdict["structured_cross_effect_controls_pass"])
        self.assertFalse(verdict["modular_jspace_control_candidate"])
        self.assertTrue(any(item.startswith("CROSS_EFFECT_MATRIX_INCOMPLETE:") for item in verdict["modularity_failures"]))

    def test_single_family_sentinel_bound_exceedance_blocks_modularity(self):
        candidate = modular_candidate(rank2=False)
        candidate["control_modularity"]["cross_effect_rows"][0]["standardized_delta"] = 0.21
        with patch.object(gate.v5, "adjudicate", return_value=v5_pass_verdict(True)):
            verdict = gate.adjudicate(candidate)
        self.assertFalse(verdict["modular_jspace_control_candidate"])
        self.assertIn("SENTINEL_BOUND_EXCEEDED:GENERIC_COMPLIANCE", verdict["modularity_failures"])

    def test_rank2_without_composition_evidence_fails_closed(self):
        candidate = modular_candidate(rank2=True)
        del candidate["control_modularity"]["composition"]
        with patch.object(gate.v5, "adjudicate", return_value=v5_pass_verdict(True)):
            verdict = gate.adjudicate(candidate)
        self.assertTrue(verdict["structured_cross_effect_controls_pass"])
        self.assertFalse(verdict["rank2_composition_controls_pass"])
        self.assertFalse(verdict["modular_jspace_control_candidate"])
        self.assertIn("RANK2_COMPOSITION_EVIDENCE_REQUIRED", verdict["modularity_failures"])

    def test_rank2_complete_cross_effect_and_composition_matrices_pass(self):
        candidate = modular_candidate(rank2=True)
        with patch.object(gate.v5, "adjudicate", return_value=v5_pass_verdict(True)):
            verdict = gate.adjudicate(candidate)
        self.assertTrue(verdict["structured_cross_effect_controls_pass"])
        self.assertTrue(verdict["rank2_composition_controls_pass"])
        self.assertTrue(verdict["modular_hcu_control_primitive_candidate"])
        self.assertLessEqual(
            verdict["composition_summary"]["max_abs_standardized_residual"],
            verdict["composition_summary"]["tolerance_abs_standardized_residual"],
        )

    def test_rank2_composition_residual_exceedance_blocks_only_modular_claim(self):
        candidate = modular_candidate(rank2=True)
        candidate["control_modularity"]["composition"]["rows"][0]["observed_delta"] = 0.30
        with patch.object(gate.v5, "adjudicate", return_value=v5_pass_verdict(True)):
            verdict = gate.adjudicate(candidate)
        self.assertTrue(verdict["semantic_scientific_candidate_preserved_from_v5"])
        self.assertFalse(verdict["rank2_composition_controls_pass"])
        self.assertFalse(verdict["modular_jspace_control_candidate"])
        self.assertTrue(any(item.startswith("COMPOSITION_RESIDUAL_BOUND_EXCEEDED:") for item in verdict["modularity_failures"]))


if __name__ == "__main__":
    unittest.main()
