#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "trigger1_semantic_simplex_primary_coherence_gate.py"
SPEC = importlib.util.spec_from_file_location("primary_coherence", TOOL)
assert SPEC is not None and SPEC.loader is not None
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


def payload(*, reverse_families: int = 0, rank2: bool = False) -> dict:
    rows = []
    for index in range(6):
        sign = -1.0 if index < reverse_families else 1.0
        if rank2:
            vectors = {
                "AFFIRMATIVE": [2.0 * sign, 0.0, 0.0],
                "NEGATIVE": [-1.0 * sign, 1.5, 0.0],
                "NEUTRAL": [-1.0 * sign, -1.5, 0.0],
            }
        else:
            vectors = {
                "AFFIRMATIVE": [2.0 * sign, 0.0, 0.0],
                "NEGATIVE": [-2.0 * sign, 0.0, 0.0],
                "NEUTRAL": [0.0, 0.0, 0.0],
            }
        for semantic, activation in vectors.items():
            rows.append(
                {
                    "row_id": f"f{index}:{semantic}",
                    "family_group_id": f"f{index}",
                    "semantic_class": semantic,
                    "activation": activation,
                }
            )
    return {
        "schema": gate.INPUT_SCHEMA,
        "dimension": 3,
        "decision_config": {"primary_axis_min_family_cosine": 0.90},
        "rows": rows,
    }


def rank_result(data: dict, verdict: str = "ONE_DIMENSIONAL_SUPPORTED") -> dict:
    return {
        "schema": gate.RANK_SCHEMA,
        "input_sha256": gate.canonical_sha(data),
        "verdict": verdict,
        "analysis_receipt_sha256": "a" * 64,
    }


class PrimaryCoherenceGateTests(unittest.TestCase):
    def test_preserves_coherent_rank1(self) -> None:
        data = payload()
        result = gate.adjudicate(data, rank_result(data))
        self.assertEqual(result["verdict"], "ONE_DIMENSIONAL_SUPPORTED")
        self.assertTrue(result["primary_axis_coherent"])
        self.assertFalse(result["promotion_boundary"]["canonical_semantics_promotion"])

    def test_preserves_coherent_rank2(self) -> None:
        data = payload(rank2=True)
        result = gate.adjudicate(data, rank_result(data, "TWO_DIMENSIONAL_REQUIRED"))
        self.assertEqual(result["verdict"], "TWO_DIMENSIONAL_REQUIRED")
        self.assertTrue(result["primary_axis_coherent"])

    def test_family_axis_reversal_forces_unresolved(self) -> None:
        data = payload(reverse_families=2)
        result = gate.adjudicate(data, rank_result(data))
        self.assertEqual(result["verdict"], "UNRESOLVED")
        self.assertIn("PRIMARY_H1_CROSS_FAMILY_DIRECTION_INCOHERENT", result["reasons"])
        self.assertLess(result["min_primary_family_cosine_to_full"], 0.0)

    def test_rank_result_input_mismatch_fails_closed(self) -> None:
        data = payload()
        prior = rank_result(data)
        prior["input_sha256"] = "0" * 64
        result = gate.adjudicate(data, prior)
        self.assertEqual(result["verdict"], "UNRESOLVED")
        self.assertIn("RANK_RESULT_INPUT_SHA_MISMATCH", result["reasons"])

    def test_base_unresolved_can_never_be_upgraded(self) -> None:
        data = payload()
        result = gate.adjudicate(data, rank_result(data, "UNRESOLVED"))
        self.assertEqual(result["verdict"], "UNRESOLVED")
        self.assertEqual(result["monotonicity"], "PRESERVE_OR_REDUCE_TO_UNRESOLVED_ONLY")


if __name__ == "__main__":
    unittest.main()
