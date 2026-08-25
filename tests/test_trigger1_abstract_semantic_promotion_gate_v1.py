from __future__ import annotations

import copy
import unittest

from tools import trigger1_abstract_semantic_promotion_gate_v1 as hard
from tools import trigger1_abstract_state_counterbalance_v1 as design
from tools import trigger1_intervention_scope_equivalence_v1 as scope


def scope_payload(diverge_last: bool = False):
    rows = []
    for i in range(18):
        base = (i + 1) / 10.0
        values = {
            scope.PATHS[0]: (-base if diverge_last and i % 2 else base),
            scope.PATHS[1]: 1.01 * base,
            scope.PATHS[2]: 0.99 * base,
        }
        for path, effect in values.items():
            rows.append({"cell_id": f"cell-{i:02d}", "path": path, "semantic_effect": effect})
    return {
        "schema": scope.SCHEMA,
        "metric_identity": "normalized_semantic_causal_effect/v1",
        "normalizer_identity": "frozen_calibration_scale/v1",
        "rows": rows,
    }


def passing_payload():
    receipt = design.validate()
    return {
        "schema": hard.SCHEMA,
        "v8_verdict": {
            "scientifically_independent_vector_candidate": True,
            "preregistration_runtime_binding_pass": True,
        },
        "abstract_design": {
            "design_receipt_sha256": receipt["design_receipt_sha256"],
            "rows_sha256": receipt["rows_sha256"],
            "observed_prompt_sha256": [row["prompt_sha256"] for row in design.build_rows()],
        },
        "scope_equivalence_payload": scope_payload(),
        "nuisance_control": {
            "semantic_target_selectivity_pass": True,
            "affect_nuisance_invariance_pass": True,
            "surface_form_invariance_pass": True,
            "presentation_position_invariance_pass": True,
        },
    }


class AbstractSemanticPromotionGateTests(unittest.TestCase):
    def test_full_hard_gate_can_promote_scientific_candidate_without_minting_credit(self):
        result = hard.adjudicate(passing_payload())
        self.assertTrue(result["abstract_semantic_jspace_candidate"])
        self.assertFalse(result["causal_identity_claim_allowed"])
        self.assertFalse(result["canonical_semantics_promotion"])
        self.assertFalse(result["jspace_model_runtime_credit"])
        self.assertEqual(result["failures"], [])

    def test_scope_divergence_blocks_abstract_semantic_promotion(self):
        payload = passing_payload()
        payload["scope_equivalence_payload"] = scope_payload(diverge_last=True)
        result = hard.adjudicate(payload)
        self.assertFalse(result["abstract_semantic_jspace_candidate"])
        self.assertIn("THREE_WAY_SCOPE_INVARIANT_RESPONSE_EQUIVALENCE_REQUIRED", result["failures"])

    def test_missing_one_prompt_hash_blocks_exact_design_binding(self):
        payload = passing_payload()
        payload["abstract_design"]["observed_prompt_sha256"].pop()
        result = hard.adjudicate(payload)
        self.assertFalse(result["abstract_semantic_jspace_candidate"])
        self.assertIn("EXACT_ABSTRACT_DESIGN_AND_PROMPT_UNIVERSE_BINDING_REQUIRED", result["failures"])

    def test_nuisance_failure_blocks_promotion(self):
        payload = passing_payload()
        payload["nuisance_control"]["affect_nuisance_invariance_pass"] = False
        result = hard.adjudicate(payload)
        self.assertFalse(result["abstract_semantic_jspace_candidate"])
        self.assertIn("COUNTERBALANCED_NUISANCE_INVARIANCE_REQUIRED", result["failures"])

    def test_v8_failure_remains_blocking(self):
        payload = passing_payload()
        payload["v8_verdict"]["scientifically_independent_vector_candidate"] = False
        result = hard.adjudicate(payload)
        self.assertFalse(result["abstract_semantic_jspace_candidate"])
        self.assertIn("V8_SCIENTIFIC_AND_PREREG_BINDING_REQUIRED", result["failures"])


if __name__ == "__main__":
    unittest.main()
