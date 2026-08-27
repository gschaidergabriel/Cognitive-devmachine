from __future__ import annotations

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


def code_map(i: int) -> dict[str, str]:
    rotations = [
        {"AFFIRMATIVE": "A", "NEGATIVE": "B", "NEUTRAL": "C"},
        {"AFFIRMATIVE": "B", "NEGATIVE": "C", "NEUTRAL": "A"},
        {"AFFIRMATIVE": "C", "NEGATIVE": "A", "NEUTRAL": "B"},
    ]
    return rotations[i % 3]


def packet(rank2: bool, families: int = 9) -> dict:
    rows = []
    for i in range(families):
        nuisance = np.array([50.0 + 3.0 * i, -20.0 + i, 5.0 * math.sin(i), 0.0])
        e1 = np.array([1.0, 0.0, 0.0, 0.0])
        e2 = np.array([0.0, 1.0, 0.0, 0.0])
        jitter = 0.01 * np.array([0.0, 0.0, math.cos(i), math.sin(i)])
        if rank2:
            a = nuisance + 1.2 * e1 + jitter
            n = nuisance - 0.6 * e1 + 1.0 * e2 - jitter
            u = nuisance - 0.6 * e1 - 1.0 * e2 + jitter
        else:
            a = nuisance + 1.2 * e1 + jitter
            n = nuisance - 0.6 * e1 - jitter
            u = nuisance - 0.6 * e1 + jitter
        rows.append({
            "family_id": f"f{i}",
            "split": "CALIBRATION",
            "code_map": code_map(i),
            "activations": {"AFFIRMATIVE": a.tolist(), "NEGATIVE": n.tolist(), "NEUTRAL": u.tolist()},
        })
    return {"schema": ranker.SCHEMA_IN, "embedding_dim": 4, "families": rows}


class BlockedRankTests(unittest.TestCase):
    def test_rank1_matched_geometry_is_not_inflated_by_family_offsets(self):
        result = ranker.analyze(packet(False), permutations=256, alpha=0.05, coherence_min=0.4)
        self.assertEqual("ONE_DIMENSIONAL_SUPPORTED", result["decision"])
        self.assertLess(result["observed"]["sigma1_empirical_p"], 0.05)
        self.assertGreater(result["observed"]["sigma2_empirical_p"], 0.05)

    def test_rank2_matched_geometry_promotes_second_dimension_measurement_only(self):
        result = ranker.analyze(packet(True), permutations=256, alpha=0.05, coherence_min=0.4)
        self.assertEqual("TWO_DIMENSIONAL_REQUIRED", result["decision"])
        self.assertLess(result["observed"]["sigma1_empirical_p"], 0.05)
        self.assertLess(result["observed"]["sigma2_empirical_p"], 0.05)
        self.assertFalse(result["promotion_candidate"])
        self.assertEqual(0, result["jspace_model_runtime_credit"])

    def test_holdout_input_is_rejected(self):
        value = packet(False)
        value["families"][0]["split"] = "HOLDOUT"
        with self.assertRaisesRegex(ValueError, "FRESH_HOLDOUT_MUST_NOT_BE_OPENED"):
            ranker.analyze(value, permutations=64)

    def test_code_mapping_must_be_counterbalanced_across_families(self):
        value = packet(False)
        fixed = {"AFFIRMATIVE": "A", "NEGATIVE": "B", "NEUTRAL": "C"}
        for fam in value["families"]:
            fam["code_map"] = fixed
        with self.assertRaisesRegex(ValueError, "OUTPUT_CODE_MAPPING_NOT_COUNTERBALANCED"):
            ranker.analyze(value, permutations=64)

    def test_same_input_is_deterministic(self):
        value = packet(True)
        a = ranker.analyze(value, permutations=128, alpha=0.05, coherence_min=0.4)
        b = ranker.analyze(value, permutations=128, alpha=0.05, coherence_min=0.4)
        self.assertEqual(a["result_sha256"], b["result_sha256"])
        self.assertEqual(a["blocked_permutation"], b["blocked_permutation"])


if __name__ == "__main__":
    unittest.main()
