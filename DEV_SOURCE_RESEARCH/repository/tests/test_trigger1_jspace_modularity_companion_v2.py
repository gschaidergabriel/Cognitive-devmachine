from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_jspace_modularity_companion_v2 as gate

HEX64 = "a" * 64
SENTINELS = [
    "GENERIC_INSTRUCTION_CODE_COMPLIANCE",
    "LEXICALLY_MATCHED_UNRELATED_CLASSIFICATION",
    "NONSEMANTIC_CODEBOOK_ACCURACY",
    "RESPONSE_CONFIDENCE_DECISIVENESS",
]
FAMILIES = ["F1", "F2", "F3", "F4"]


def candidate(rank: str = "ONE_DIMENSIONAL_SUPPORTED") -> dict:
    interventions = ["H1"] if rank == "ONE_DIMENSIONAL_SUPPORTED" else ["H1", "H2"]
    cells = []
    for ii, intervention in enumerate(interventions):
        for ss, sentinel in enumerate(SENTINELS):
            family_rows = []
            values = []
            for ff, family in enumerate(FAMILIES):
                value = 0.01 * (1 + ii + ss) + 0.002 * ff
                values.append(value)
                family_rows.append({
                    "scenario_family_id": family,
                    "standardized_delta": value,
                    "evidence_receipt_sha256": HEX64,
                })
            cells.append({
                "intervention_id": intervention,
                "sentinel_id": sentinel,
                "equal_family_weighted_standardized_delta": sum(values) / len(values),
                "max_abs_family_standardized_delta": max(abs(x) for x in values),
                "family_count": len(values),
                "per_family_effects_receipt_sha256": HEX64,
                "per_family_standardized_deltas": family_rows,
            })
    protocol = {
        "frozen_before_holdout": True,
        "equal_family_weighting": True,
        "family_level_signed_effects_preserved": True,
        "sentinel_endpoints": list(SENTINELS),
        "sentinel_set_sha256": gate.canonical_json_sha(sorted(SENTINELS)),
        "modular_intervention_ids": interventions,
        "preregistered_max_abs_standardized_cross_effect": 0.20,
        "cross_effect_matrix": cells,
        "cross_effects_within_preregistered_bounds": True,
        "scenario_family_universe_sha256": gate.canonical_json_sha(sorted(FAMILIES)),
    }
    normalized_matrix = []
    for cell in cells:
        normalized_matrix.append({
            "intervention_id": cell["intervention_id"],
            "sentinel_id": cell["sentinel_id"],
            "per_family_standardized_deltas": sorted(cell["per_family_standardized_deltas"], key=lambda row: row["scenario_family_id"]),
        })
    normalized_matrix.sort(key=lambda row: (row["intervention_id"], row["sentinel_id"]))
    protocol["cross_effect_matrix_receipt_sha256"] = gate.canonical_json_sha(normalized_matrix)
    result = {"semantic_rank_decision": rank, "modularity_protocol": protocol}
    protocol["protocol_sha256"] = gate.canonical_json_sha(gate._protocol_contract(result, protocol))

    if rank == "TWO_DIMENSIONAL_REQUIRED":
        rows = []
        for ci in range(4):
            for fi, family in enumerate(FAMILIES):
                rows.append({
                    "combination_id": f"C{ci}",
                    "scenario_family_id": family,
                    "standardized_residual": 0.02 + 0.002 * ci + 0.001 * fi,
                    "evidence_receipt_sha256": HEX64,
                })
        normalized = sorted(rows, key=lambda row: (row["combination_id"], row["scenario_family_id"]))
        result["rank2_composition"] = {
            "preregistered_before_holdout": True,
            "calibration_only_model_fit": True,
            "coefficient_grid_frozen_before_holdout": True,
            "coefficient_grid_sha256": HEX64,
            "fresh_scenario_family_holdout": True,
            "combinations_evaluated": 4,
            "preregistered_max_abs_standardized_residual": 0.10,
            "max_abs_standardized_residual": max(abs(row["standardized_residual"]) for row in rows),
            "systematic_sign_interaction_absent": True,
            "combination_residuals": rows,
            "composition_receipt_sha256": gate.canonical_json_sha(normalized),
        }
    return result


class ModularityCompanionV2Tests(unittest.TestCase):
    def test_rank1_evidence_object_recomputes_and_binds(self):
        ok, failures, details = gate._evidence_binding(candidate())
        self.assertTrue(ok)
        self.assertEqual([], failures)
        self.assertEqual(4, details["scenario_family_count"])

    def test_fake_summary_digest_cannot_pass(self):
        c = candidate()
        c["modularity_protocol"]["cross_effect_matrix_receipt_sha256"] = HEX64
        ok, failures, _ = gate._evidence_binding(c)
        self.assertFalse(ok)
        self.assertIn("CROSS_EFFECT_MATRIX_DIGEST_MISMATCH", failures)

    def test_pooled_mean_is_recomputed_from_family_rows(self):
        c = candidate()
        c["modularity_protocol"]["cross_effect_matrix"][0]["equal_family_weighted_standardized_delta"] += 0.1
        ok, failures, _ = gate._evidence_binding(c)
        self.assertFalse(ok)
        self.assertTrue(any(x.startswith("CROSS_EFFECT_POOLED_MEAN_RECOMPUTE_MISMATCH:") for x in failures))

    def test_family_universe_must_match_across_cells(self):
        c = candidate()
        c["modularity_protocol"]["cross_effect_matrix"][0]["per_family_standardized_deltas"][0]["scenario_family_id"] = "OTHER"
        ok, failures, _ = gate._evidence_binding(c)
        self.assertFalse(ok)
        self.assertTrue(any(x.startswith("CROSS_EFFECT_FAMILY_UNIVERSE_MISMATCH:") for x in failures))

    def test_protocol_contract_digest_is_recomputed(self):
        c = candidate()
        c["modularity_protocol"]["preregistered_max_abs_standardized_cross_effect"] = 0.3
        ok, failures, _ = gate._evidence_binding(c)
        self.assertFalse(ok)
        self.assertIn("MODULARITY_PROTOCOL_DIGEST_MISMATCH", failures)

    def test_rank2_residuals_recompute_and_bind(self):
        ok, failures, details = gate._evidence_binding(candidate("TWO_DIMENSIONAL_REQUIRED"))
        self.assertTrue(ok)
        self.assertEqual([], failures)
        self.assertIsNotNone(details["rank2_composition_sha256"])

    def test_rank2_max_summary_cannot_disagree_with_bound_rows(self):
        c = candidate("TWO_DIMENSIONAL_REQUIRED")
        c["rank2_composition"]["max_abs_standardized_residual"] = 0.001
        ok, failures, _ = gate._evidence_binding(c)
        self.assertFalse(ok)
        self.assertIn("RANK2_COMPOSITION_MAX_RESIDUAL_RECOMPUTE_MISMATCH", failures)

    def test_v2_cannot_rescue_failed_v1_modularity(self):
        c = candidate()
        with patch.object(gate.v1, "adjudicate", return_value={"modular_hcu_jspace_control_candidate": False}):
            verdict = gate.adjudicate(c)
        self.assertTrue(verdict["modularity_evidence_bound_candidate"])
        self.assertFalse(verdict["modular_hcu_jspace_control_candidate"])
        self.assertFalse(verdict["canonical_credit_minted"])
        self.assertFalse(verdict["jspace_model_runtime_credit"])
        self.assertFalse(verdict["training_credit"])


if __name__ == "__main__":
    unittest.main()
