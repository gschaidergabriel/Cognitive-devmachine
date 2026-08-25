from __future__ import annotations

import hashlib
import math
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_semantic_simplex_blocked_rank_v1 as ranker


def h(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def code_map(i: int) -> dict[str, str]:
    rotations = [
        {"AFFIRMATIVE": "A", "NEGATIVE": "B", "NEUTRAL": "C"},
        {"AFFIRMATIVE": "B", "NEGATIVE": "C", "NEUTRAL": "A"},
        {"AFFIRMATIVE": "C", "NEGATIVE": "A", "NEUTRAL": "B"},
    ]
    return rotations[i % 3]


def packet(mode: str, families: int = 9) -> dict:
    if mode not in {"rank1", "rank2", "grey"}:
        raise ValueError(mode)
    second = {"rank1": 0.0, "rank2": 1.0, "grey": 0.15}[mode]
    rows = []
    for i in range(families):
        nuisance = np.array([50.0 + 3.0 * i, -20.0 + i, 5.0 * math.sin(i), 0.0])
        e1 = np.array([1.0, 0.0, 0.0, 0.0])
        e2 = np.array([0.0, 1.0, 0.0, 0.0])
        jitter = 0.01 * np.array([0.0, 0.0, math.cos(i), math.sin(i)])
        a = nuisance + 1.2 * e1 + jitter
        n = nuisance - 0.6 * e1 + second * e2 - jitter
        u = nuisance - 0.6 * e1 - second * e2 + jitter
        rows.append({
            "family_id": f"f{i}",
            "split": "CALIBRATION",
            "code_map": code_map(i),
            "prompt_sha256": {
                "AFFIRMATIVE": h(f"f{i}:a"),
                "NEGATIVE": h(f"f{i}:n"),
                "NEUTRAL": h(f"f{i}:u"),
            },
            "source_receipt_sha256": h(f"receipt:f{i}"),
            "activations": {"AFFIRMATIVE": a.tolist(), "NEGATIVE": n.tolist(), "NEUTRAL": u.tolist()},
        })
    return {
        "schema": ranker.SCHEMA_IN,
        "embedding_dim": 4,
        "source_identity": {
            "repo_head": "1" * 40,
            "runtime_build_sha256": h("runtime"),
            "checkpoint_sha256": h("checkpoint"),
            "tokenizer_sha256": h("tokenizer"),
            "model_or_route": "Qwen/Qwen3-0.6B@test",
            "activation_site": "model.model.layers[20]:output:last_token",
            "token_scope": "LAST_TOKEN_ONLY",
            "layer": 20,
            "embedding_dim": 4,
        },
        "design_attestation": {
            "calibration_only": True,
            "fresh_holdout_opened": False,
            "model_facing_label_free": True,
            "lexically_disjoint_families": True,
            "matched_scenario_triplets": True,
            "output_code_independent": True,
        },
        "preregistration": {
            "permutations": 256,
            "alpha": 0.05,
            "coherence_min": 0.4,
            "rank1_max_sigma2_over_sigma1": 0.05,
            "rank2_min_sigma2_over_sigma1": 0.20,
            "rank1_min_loo_fraction": 0.8,
            "rank2_min_loo_fraction": 0.8,
        },
        "families": rows,
    }


class BlockedRankTests(unittest.TestCase):
    def test_rank1_requires_equivalence_and_is_not_inflated_by_family_offsets(self):
        result = ranker.analyze(packet("rank1"))
        self.assertEqual("ONE_DIMENSIONAL_SUPPORTED", result["decision"])
        self.assertEqual(1, result["selected_basis_dimension"])
        self.assertLessEqual(result["observed"]["sigma2_over_sigma1"], 0.05)
        self.assertGreaterEqual(result["observed"]["rank1_loo_fraction"], 0.8)

    def test_rank2_matched_geometry_promotes_second_dimension_measurement_only(self):
        result = ranker.analyze(packet("rank2"))
        self.assertEqual("TWO_DIMENSIONAL_REQUIRED", result["decision"])
        self.assertEqual(2, result["selected_basis_dimension"])
        self.assertLessEqual(result["observed"]["sigma2_empirical_p"], 0.05)
        self.assertGreaterEqual(result["observed"]["rank2_loo_fraction"], 0.8)
        self.assertFalse(result["promotion_candidate"])
        self.assertEqual(0, result["jspace_model_runtime_credit"])

    def test_intermediate_secondary_effect_is_unresolved_not_forced_rank1(self):
        result = ranker.analyze(packet("grey"))
        self.assertEqual("UNRESOLVED", result["decision"])
        self.assertEqual(0, result["selected_basis_dimension"])
        self.assertGreater(result["observed"]["sigma2_over_sigma1"], 0.05)
        self.assertLess(result["observed"]["sigma2_over_sigma1"], 0.20)

    def test_holdout_input_is_rejected(self):
        value = packet("rank1")
        value["families"][0]["split"] = "HOLDOUT"
        with self.assertRaisesRegex(ValueError, "FRESH_HOLDOUT_MUST_NOT_BE_OPENED"):
            ranker.analyze(value)

    def test_code_mapping_must_be_counterbalanced_across_families(self):
        value = packet("rank1")
        fixed = {"AFFIRMATIVE": "A", "NEGATIVE": "B", "NEUTRAL": "C"}
        for fam in value["families"]:
            fam["code_map"] = fixed
        with self.assertRaisesRegex(ValueError, "OUTPUT_CODE_MAPPING_NOT_COUNTERBALANCED"):
            ranker.analyze(value)

    def test_exact_source_provenance_is_required(self):
        value = packet("rank1")
        value["source_identity"]["checkpoint_sha256"] = "bad"
        with self.assertRaisesRegex(ValueError, "SOURCE_CHECKPOINT_SHA256_REQUIRED"):
            ranker.analyze(value)

    def test_prompt_identity_cannot_be_reused_across_semantic_rows(self):
        value = packet("rank1")
        duplicate = value["families"][0]["prompt_sha256"]["AFFIRMATIVE"]
        value["families"][1]["prompt_sha256"]["NEGATIVE"] = duplicate
        with self.assertRaisesRegex(ValueError, "PROMPT_HASH_REUSE_FORBIDDEN"):
            ranker.analyze(value)

    def test_same_input_is_deterministic(self):
        value = packet("rank2")
        a = ranker.analyze(value)
        b = ranker.analyze(value)
        self.assertEqual(a["result_sha256"], b["result_sha256"])
        self.assertEqual(a["blocked_permutation"], b["blocked_permutation"])


if __name__ == "__main__":
    unittest.main()
