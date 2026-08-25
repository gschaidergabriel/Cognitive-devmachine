from __future__ import annotations

import hashlib
import unittest

from tools import trigger1_semantic_simplex_rank_gate as gate


def h(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def payload(families: dict[str, dict[str, list[float]]], *, rank1=0.05, rank2=0.25):
    rows = []
    for family_id in sorted(families):
        for semantic in gate.CLASSES:
            rows.append(
                {
                    "family_id": family_id,
                    "semantic_class": semantic,
                    "prompt_sha256": h(f"{family_id}:{semantic}"),
                    "label_free": True,
                    "output_code_free": True,
                    "vector": families[family_id][semantic],
                }
            )
    return {
        "schema": gate.INPUT_SCHEMA,
        "source_identity": {
            "model_checkpoint_sha256": "1" * 64,
            "tokenizer_sha256": "2" * 64,
            "runtime_build_sha256": "3" * 64,
            "activation_site": "model.model.layers[20]:output:last_token",
            "token_scope": "LAST_TOKEN_ONLY",
            "layer": 20,
        },
        "design_attestation": {
            "calibration_only": True,
            "fresh_holdout_opened": False,
            "label_free_model_facing_prompts": True,
            "lexically_disjoint_families": True,
            "output_code_independent": True,
        },
        "preregistration": {
            "min_families": 3,
            "null_percentile": 0.95,
            "null_max_exact": 50000,
            "null_sample_count": 4096,
            "null_seed": 1701,
            "rank2_min_sigma2_over_sigma1": rank2,
            "rank2_min_null_excess": 0.05,
            "rank2_min_loo_fraction": 1.0,
            "rank1_max_sigma2_over_sigma1": rank1,
            "rank1_min_loo_fraction": 1.0,
        },
        "rows": rows,
    }


class SemanticSimplexRankGateTests(unittest.TestCase):
    def test_rank1_requires_small_secondary_component(self):
        families = {}
        for i in range(4):
            offset = [0.0, i * 0.2, -i * 0.1]
            families[f"f{i}"] = {
                "AFFIRMATIVE": [1.0 + offset[0], offset[1], offset[2]],
                "NEGATIVE": [-1.0 + offset[0], offset[1], offset[2]],
                "NEUTRAL": [0.0 + offset[0], offset[1], offset[2]],
            }
        result = gate.analyze(payload(families))
        self.assertEqual(result["decision"], "ONE_DIMENSIONAL_SUPPORTED")
        self.assertEqual(result["permutation_null"]["mode"], "EXACT")
        self.assertTrue(result["gate_checks"]["rank1_equivalence_effect"])
        self.assertTrue(result["gate_checks"]["rank1_loo_stable"])

    def test_rank2_triangle_exceeds_permutation_null(self):
        families = {}
        triangle = {
            "AFFIRMATIVE": [1.0, 0.0, 0.0],
            "NEGATIVE": [-0.5, 0.866025403784, 0.0],
            "NEUTRAL": [-0.5, -0.866025403784, 0.0],
        }
        for i in range(4):
            common = [i * 0.1, -i * 0.07, i * 0.03]
            families[f"f{i}"] = {
                c: [v[j] + common[j] for j in range(3)]
                for c, v in triangle.items()
            }
        result = gate.analyze(payload(families))
        self.assertEqual(result["decision"], "TWO_DIMENSIONAL_REQUIRED")
        self.assertGreater(result["global_geometry"]["sigma2_over_sigma1"], 0.9)
        self.assertTrue(result["gate_checks"]["rank2_null_excess"])
        self.assertEqual(result["gate_checks"]["rank2_loo_fraction"], 1.0)

    def test_intermediate_effect_is_unresolved_not_forced_rank1(self):
        families = {}
        for i in range(4):
            common = [0.0, i * 0.1, 0.0]
            families[f"f{i}"] = {
                "AFFIRMATIVE": [1.0, common[1], 0.0],
                "NEGATIVE": [-0.5, common[1] + 0.18, 0.0],
                "NEUTRAL": [-0.5, common[1] - 0.18, 0.0],
            }
        result = gate.analyze(payload(families, rank1=0.05, rank2=0.5))
        self.assertEqual(result["decision"], "UNRESOLVED")

    def test_missing_label_free_attestation_fails_closed(self):
        families = {
            f"f{i}": {
                "AFFIRMATIVE": [1.0, 0.0],
                "NEGATIVE": [-1.0, 0.0],
                "NEUTRAL": [0.0, 0.0],
            }
            for i in range(3)
        }
        p = payload(families)
        p["rows"][0]["label_free"] = False
        with self.assertRaisesRegex(gate.GateError, "LABEL_FREE"):
            gate.analyze(p)

    def test_holdout_opened_fails_closed(self):
        families = {
            f"f{i}": {
                "AFFIRMATIVE": [1.0, 0.0],
                "NEGATIVE": [-1.0, 0.0],
                "NEUTRAL": [0.0, 0.0],
            }
            for i in range(3)
        }
        p = payload(families)
        p["design_attestation"]["fresh_holdout_opened"] = True
        with self.assertRaisesRegex(gate.GateError, "HOLDOUT"):
            gate.analyze(p)

    def test_result_is_deterministic(self):
        families = {}
        triangle = {
            "AFFIRMATIVE": [1.0, 0.0],
            "NEGATIVE": [-0.5, 0.8],
            "NEUTRAL": [-0.5, -0.8],
        }
        for i in range(8):
            families[f"f{i}"] = triangle
        p = payload(families)
        p["preregistration"]["null_max_exact"] = 100
        p["preregistration"]["null_sample_count"] = 250
        one = gate.analyze(p)
        two = gate.analyze(p)
        self.assertEqual(one["permutation_null"]["mode"], "DETERMINISTIC_SAMPLED")
        self.assertEqual(one["result_sha256"], two["result_sha256"])
        self.assertEqual(one["permutation_null"]["null_values_sha256"], two["permutation_null"]["null_values_sha256"])


if __name__ == "__main__":
    unittest.main()
