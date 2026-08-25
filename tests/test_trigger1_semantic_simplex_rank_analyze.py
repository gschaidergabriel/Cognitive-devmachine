#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "trigger1_semantic_simplex_rank_analyze.py"
SPEC = importlib.util.spec_from_file_location("simplex_rank", TOOL)
assert SPEC is not None and SPEC.loader is not None
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def config(min_families: int) -> dict:
    return {
        "alpha": 0.05,
        "rank1_equivalence_max_ratio": 0.10,
        "rank2_min_ratio": 0.25,
        "rank2_min_lofo_cosine": 0.90,
        "min_matched_families": min_families,
        "max_exact_signflip_families": 16,
        "monte_carlo_signflips": 4096,
    }


def payload(kind: str, groups: int) -> dict:
    rows = []
    for i in range(groups):
        # Common family nuisance is deliberately large; matched triad contrasts cancel it.
        common = [0.0, 0.0, float(i) * 10.0, -float(i) * 7.0]
        if kind == "rank1":
            vectors = {
                "AFFIRMATIVE": [1.0, 0.0, common[2], common[3]],
                "NEGATIVE": [-1.0, 0.0, common[2], common[3]],
                "NEUTRAL": [0.0, 0.0, common[2], common[3]],
            }
        elif kind == "rank2":
            vectors = {
                "AFFIRMATIVE": [1.0, 0.0, common[2], common[3]],
                "NEGATIVE": [-0.5, 1.0, common[2], common[3]],
                "NEUTRAL": [-0.5, -1.0, common[2], common[3]],
            }
        else:
            raise AssertionError(kind)
        for semantic, activation in vectors.items():
            rows.append(
                {
                    "row_id": f"g{i}:{semantic}",
                    "family_group_id": f"g{i}",
                    "semantic_class": semantic,
                    "activation": activation,
                }
            )
    return {
        "schema": mod.INPUT_SCHEMA,
        "dimension": 4,
        "decision_config": config(groups),
        "rows": rows,
    }


class SemanticSimplexRankTests(unittest.TestCase):
    def test_rank1_supported(self):
        result = mod.analyze(payload("rank1", 6))
        self.assertEqual(result["verdict"], "ONE_DIMENSIONAL_SUPPORTED")
        self.assertAlmostEqual(result["geometry"]["h2_to_h1_ratio"], 0.0, places=12)
        self.assertEqual(result["promotion_boundary"]["new_runtime_credit"], 0)

    def test_rank2_required_with_six_matched_families(self):
        result = mod.analyze(payload("rank2", 6))
        self.assertEqual(result["verdict"], "TWO_DIMENSIONAL_REQUIRED")
        self.assertLessEqual(result["randomization"]["p_value"], 0.05)
        self.assertGreaterEqual(result["leave_one_family_out"]["min_h2_cosine_to_full"], 0.99)

    def test_three_family_rank2_design_is_underpowered_at_alpha_005(self):
        data = payload("rank2", 3)
        data["decision_config"]["min_matched_families"] = 3
        result = mod.analyze(data)
        self.assertEqual(result["verdict"], "UNRESOLVED")
        self.assertIn(
            "EXACT_SIGNFLIP_DESIGN_CANNOT_REACH_DECLARED_ALPHA_AT_THIS_FAMILY_COUNT",
            result["reasons"],
        )
        self.assertGreater(result["randomization"]["theoretical_min_p_for_mode"], 0.05)

    def test_missing_class_fails_closed(self):
        data = payload("rank1", 6)
        data["rows"] = [
            row for row in data["rows"]
            if not (row["family_group_id"] == "g0" and row["semantic_class"] == "NEUTRAL")
        ]
        with self.assertRaisesRegex(ValueError, "MISSING_CLASSES"):
            mod.analyze(data)

    def test_result_is_deterministic(self):
        data = payload("rank2", 6)
        one = mod.analyze(data)
        two = mod.analyze(data)
        self.assertEqual(one["analysis_receipt_sha256"], two["analysis_receipt_sha256"])


if __name__ == "__main__":
    unittest.main()
