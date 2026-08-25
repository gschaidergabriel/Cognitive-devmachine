#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "trigger1_semantic_simplex_rank.py"
SPEC = importlib.util.spec_from_file_location("trigger1_semantic_simplex_rank", MODULE_PATH)
assert SPEC and SPEC.loader
rank = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rank)


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def family(fid: str, affirmative: list[float], negative: list[float], neutral: list[float]) -> dict:
    return {
        "family_id": fid,
        "label_free_basis": True,
        "family_receipt_sha256": sha(fid),
        "class_centroids": {
            "AFFIRMATIVE": affirmative,
            "NEGATIVE": negative,
            "NEUTRAL": neutral,
        },
    }


def candidate(families: list[dict]) -> dict:
    return {
        "schema": rank.INPUT_SCHEMA,
        "phase": "CALIBRATION_ONLY",
        "fresh_holdout_opened": False,
        "model_facing_pole_labels_absent": True,
        "lexically_disjoint_families": True,
        "activation_site": "layer20.residual",
        "checkpoint_sha256": sha("checkpoint"),
        "tokenizer_sha256": sha("tokenizer"),
        "runtime_build_sha256": sha("runtime"),
        "config": {
            "min_families": 4,
            "one_dim_max_second_energy_fraction": 0.02,
            "two_dim_min_second_energy_fraction": 0.12,
            "min_primary_axis_cosine": 0.95,
            "min_secondary_axis_cosine": 0.90,
            "permutation_alpha": 0.05,
            "max_exact_permutations": 10000,
            "null_samples": 4096,
        },
        "families": families,
    }


class SemanticSimplexRankTests(unittest.TestCase):
    def test_stable_collinear_geometry_supports_one_dimension(self) -> None:
        c = candidate([
            family("f1", [2.0, 0.0, 0.0], [-2.0, 0.0, 0.0], [0.0, 0.0, 0.0]),
            family("f2", [2.1, 0.01, 0.0], [-2.1, -0.01, 0.0], [0.0, 0.0, 0.0]),
            family("f3", [1.9, -0.01, 0.0], [-1.9, 0.01, 0.0], [0.0, 0.0, 0.0]),
            family("f4", [2.05, 0.005, 0.0], [-2.05, -0.005, 0.0], [0.0, 0.0, 0.0]),
        ])
        verdict = rank.adjudicate(c)
        self.assertEqual(verdict["decision"], rank.DECISION_ONE)
        self.assertEqual(verdict["failures"], [])
        self.assertLessEqual(
            verdict["observed"]["global_second_energy_fraction"],
            c["config"]["one_dim_max_second_energy_fraction"],
        )
        self.assertFalse(verdict["canonical_credit_minted"])

    def test_stable_triangle_requires_two_dimensions(self) -> None:
        c = candidate([
            family("f1", [2.0, 0.0, 0.0], [-1.0, 1.8, 0.0], [-1.0, -1.8, 0.0]),
            family("f2", [2.05, 0.02, 0.0], [-1.02, 1.82, 0.0], [-1.03, -1.84, 0.0]),
            family("f3", [1.98, -0.02, 0.0], [-0.98, 1.78, 0.0], [-1.00, -1.76, 0.0]),
            family("f4", [2.02, 0.01, 0.0], [-1.01, 1.81, 0.0], [-1.01, -1.82, 0.0]),
        ])
        verdict = rank.adjudicate(c)
        self.assertEqual(verdict["decision"], rank.DECISION_TWO)
        self.assertTrue(verdict["observed"]["primary_axis_stable"])
        self.assertTrue(verdict["observed"]["secondary_axis_stable"])
        self.assertLessEqual(
            verdict["permutation_null"]["p_value_ge_observed"],
            c["config"]["permutation_alpha"],
        )
        self.assertFalse(verdict["jspace_model_runtime_credit"])

    def test_cross_family_cancellation_is_unresolved_not_one_dimensional(self) -> None:
        c = candidate([
            family("f1", [2.0, 0.0], [-1.0, 1.8], [-1.0, -1.8]),
            family("f2", [2.0, 0.0], [-1.0, 1.8], [-1.0, -1.8]),
            family("f3", [2.0, 0.0], [-1.0, -1.8], [-1.0, 1.8]),
            family("f4", [2.0, 0.0], [-1.0, -1.8], [-1.0, 1.8]),
        ])
        verdict = rank.adjudicate(c)
        self.assertEqual(verdict["decision"], rank.DECISION_UNRESOLVED)
        self.assertIn("FAMILY_LEVEL_ONE_DIMENSIONALITY_NOT_STABLE", verdict["unresolved_reasons"])

    def test_holdout_opening_fails_closed(self) -> None:
        c = candidate([
            family("f1", [2.0, 0.0], [-2.0, 0.0], [0.0, 0.0]),
            family("f2", [2.0, 0.0], [-2.0, 0.0], [0.0, 0.0]),
            family("f3", [2.0, 0.0], [-2.0, 0.0], [0.0, 0.0]),
            family("f4", [2.0, 0.0], [-2.0, 0.0], [0.0, 0.0]),
        ])
        c["fresh_holdout_opened"] = True
        verdict = rank.adjudicate(c)
        self.assertEqual(verdict["decision"], rank.DECISION_UNRESOLVED)
        self.assertIn("FRESH_HOLDOUT_MUST_REMAIN_CLOSED", verdict["failures"])

    def test_missing_label_free_receipt_fails_closed(self) -> None:
        rows = [
            family("f1", [2.0, 0.0], [-2.0, 0.0], [0.0, 0.0]),
            family("f2", [2.0, 0.0], [-2.0, 0.0], [0.0, 0.0]),
            family("f3", [2.0, 0.0], [-2.0, 0.0], [0.0, 0.0]),
            family("f4", [2.0, 0.0], [-2.0, 0.0], [0.0, 0.0]),
        ]
        rows[0]["label_free_basis"] = False
        c = candidate(rows)
        verdict = rank.adjudicate(c)
        self.assertEqual(verdict["decision"], rank.DECISION_UNRESOLVED)
        self.assertIn("LABEL_FREE_BASIS_REQUIRED:f1", verdict["failures"])


if __name__ == "__main__":
    unittest.main()
