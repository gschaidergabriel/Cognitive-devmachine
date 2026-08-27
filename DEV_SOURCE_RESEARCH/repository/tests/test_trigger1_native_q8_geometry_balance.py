from __future__ import annotations

import math
import unittest

import numpy as np

from tools import trigger1_native_q8_geometry_balance as geometry


def triad(family: str, h1: np.ndarray, d2: np.ndarray) -> list[dict]:
    # Construct a zero-grand-mean triad with exactly the requested contrasts:
    # h1 = A - .5*(N+U), d2 = N-U.
    a = (2.0 / 3.0) * h1
    n = -(1.0 / 3.0) * h1 + 0.5 * d2
    u = -(1.0 / 3.0) * h1 - 0.5 * d2
    return [
        {"row_id": f"{family}:a", "family_group_id": family, "semantic_class": "AFFIRMATIVE", "activation": a.tolist()},
        {"row_id": f"{family}:n", "family_group_id": family, "semantic_class": "NEGATIVE", "activation": n.tolist()},
        {"row_id": f"{family}:u", "family_group_id": family, "semantic_class": "NEUTRAL", "activation": u.tolist()},
    ]


def payload(rows: list[dict]) -> dict:
    return {
        "schema": geometry.INPUT_SCHEMA,
        "dimension": 4,
        "rows": rows,
    }


def rank_result(verdict: str = "TWO_DIMENSIONAL_REQUIRED") -> dict:
    return {"verdict": verdict, "analysis_receipt_sha256": "a" * 64}


class NativeQ8GeometryBalanceTests(unittest.TestCase):
    def test_equal_energy_families_leave_axes_unchanged(self):
        rows = []
        h1 = np.array([1.0, 0.0, 0.0, 0.0])
        d2 = np.array([0.0, 1.0, 0.0, 0.0])
        for index in range(6):
            rows.extend(triad(f"f{index}", h1, d2))
        result = geometry.finalize(payload(rows), rank_result())
        self.assertAlmostEqual(result["raw_vs_balanced_diagnostic"]["axis_h1_cosine"], 1.0, places=12)
        self.assertAlmostEqual(result["raw_vs_balanced_diagnostic"]["axis_h2_cosine"], 1.0, places=12)
        self.assertAlmostEqual(result["raw_vs_balanced_diagnostic"]["energy_dynamic_range"], 1.0, places=12)
        self.assertLess(result["zero_sum_target_vector_residual_l2"], 1e-12)

    def test_one_huge_family_cannot_dominate_balanced_controller_direction(self):
        rows = []
        common_h1 = np.array([1.0, 0.0, 0.0, 0.0])
        common_d2 = np.array([0.0, 1.0, 0.0, 0.0])
        for index in range(6):
            rows.extend(triad(f"common{index}", common_h1, common_d2))
        # Rank remains two-dimensional, but this family is 1000x larger and lives in
        # an orthogonal semantic plane. Raw averaging is almost entirely controlled by it.
        rows.extend(triad(
            "huge",
            np.array([0.0, 0.0, 1000.0, 0.0]),
            np.array([0.0, 0.0, 0.0, 1000.0]),
        ))
        result = geometry.finalize(payload(rows), rank_result())
        diagnostic = result["raw_vs_balanced_diagnostic"]
        self.assertGreater(diagnostic["energy_dynamic_range"], 999.0)
        self.assertLess(abs(diagnostic["axis_h1_cosine"]), 0.25)
        self.assertLess(abs(diagnostic["axis_h2_cosine"]), 0.25)
        self.assertEqual(result["family_weighting"], "INVERSE_WITHIN_FAMILY_CONTRAST_PAIR_ENERGY")
        self.assertLess(result["zero_sum_target_vector_residual_l2"], 1e-12)

    def test_rank1_omits_second_axis(self):
        rows = []
        h1 = np.array([1.0, 0.0, 0.0, 0.0])
        d2 = np.array([0.0, 0.0, 0.0, 0.0])
        for index in range(6):
            rows.extend(triad(f"f{index}", h1, d2))
        result = geometry.finalize(payload(rows), rank_result("ONE_DIMENSIONAL_SUPPORTED"))
        self.assertEqual(result["rank"], 1)
        self.assertIsNone(result["balanced_axis_h2_sha256_f64le"])

    def test_unresolved_rank_fails_closed(self):
        rows = []
        for index in range(3):
            rows.extend(triad(
                f"f{index}",
                np.array([1.0, 0.0, 0.0, 0.0]),
                np.array([0.0, 1.0, 0.0, 0.0]),
            ))
        with self.assertRaisesRegex(geometry.GeometryError, "ADMITTED_RANK_VERDICT_REQUIRED"):
            geometry.finalize(payload(rows), rank_result("UNRESOLVED"))

    def test_degenerate_family_fails_closed(self):
        rows = []
        for index in range(3):
            h1 = np.array([1.0, 0.0, 0.0, 0.0]) if index else np.zeros(4)
            d2 = np.array([0.0, 1.0, 0.0, 0.0]) if index else np.zeros(4)
            rows.extend(triad(f"f{index}", h1, d2))
        with self.assertRaisesRegex(geometry.GeometryError, "DEGENERATE_MATCHED_CONTRAST_PAIR"):
            geometry.finalize(payload(rows), rank_result())

    def test_output_is_deterministic(self):
        rows = []
        for index in range(6):
            rows.extend(triad(
                f"f{index}",
                np.array([1.0, 0.0, 0.0, 0.0]),
                np.array([0.0, 1.0, 0.0, 0.0]),
            ))
        first = geometry.finalize(payload(rows), rank_result())
        second = geometry.finalize(payload(rows), rank_result())
        self.assertEqual(first, second)
        self.assertEqual(first["geometry_receipt_sha256"], second["geometry_receipt_sha256"])


if __name__ == "__main__":
    unittest.main()
