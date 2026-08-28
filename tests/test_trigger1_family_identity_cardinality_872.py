#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import copy
import sys
import unittest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_intermediate_contrastive_protocol as protocol

SCORES = {
    "BASELINE": 0.0,
    "+VECTOR": 3.0,
    "SIGN_FLIP": -3.0,
    "NULL_VECTOR": 0.0,
    "ORTHOGONAL_SAME_NORM": 0.1,
    "PERMUTED_SAME_NORM": 0.2,
}


def calibration() -> list[dict]:
    return [
        {
            "split": "calibration",
            "layer": 12,
            "gain": 4.0,
            "case_id": "cal",
            "prompt_sha256": "a" * 64,
            "seed": 1701,
            "positive_label": "A",
            "negative_label": "B",
            "control": control,
            "target_score": SCORES[control],
        }
        for control in protocol.REQUIRED_CONTROLS
    ]


def holdout() -> list[dict]:
    rows: list[dict] = []
    for map_id, pos, neg, prompt_digit in (
        ("MAP_AB", "A", "B", "b"),
        ("MAP_BA", "B", "A", "c"),
    ):
        for control in protocol.REQUIRED_CONTROLS:
            row = {
                "split": "holdout",
                "layer": 12,
                "gain": 4.0,
                "case_id": "hold",
                "prompt_sha256": prompt_digit * 64,
                "seed": 2718,
                "positive_label": pos,
                "negative_label": neg,
                "label_map_id": map_id,
                "control": control,
                "target_score": SCORES[control],
            }
            if control == "+VECTOR":
                row.update(
                    {
                        "wrong_layer": 6,
                        "wrong_layer_vector_source_layer": 12,
                        "wrong_layer_same_selected_vector": True,
                        "wrong_layer_delta": -0.1,
                        "wrong_layer_receipt_sha256": "d" * 64,
                        "lesion_delta": -0.2,
                        "rescue_delta": 0.5,
                    }
                )
            rows.append(row)
    return rows


class FamilyIdentityCardinalityTests(unittest.TestCase):
    def test_bound_positive_path_passes(self) -> None:
        self.assertTrue(protocol.select_layer_gain(calibration())["selected"])
        self.assertTrue(protocol.adjudicate_holdout(holdout(), selected_layer=12, selected_gain=4.0)["pass"])

    def test_duplicate_calibration_control_fails_closed(self) -> None:
        rows = calibration()
        bad = copy.deepcopy(next(r for r in rows if r["control"] == "+VECTOR"))
        bad["target_score"] = -5.0
        rows.insert(0, bad)
        out = protocol.select_layer_gain(rows)
        self.assertFalse(out["selected"])
        self.assertEqual("DUPLICATE_CALIBRATION_CONTROL", out["reason"])

    def test_split_calibration_prompt_cannot_assemble_family(self) -> None:
        rows = calibration()
        next(r for r in rows if r["control"] == "+VECTOR")["prompt_sha256"] = "f" * 64
        self.assertFalse(protocol.select_layer_gain(rows)["selected"])

    def test_split_calibration_seed_cannot_assemble_family(self) -> None:
        rows = calibration()
        next(r for r in rows if r["control"] == "+VECTOR")["seed"] = 9999
        self.assertFalse(protocol.select_layer_gain(rows)["selected"])

    def test_split_calibration_labels_cannot_assemble_family(self) -> None:
        rows = calibration()
        next(r for r in rows if r["control"] == "+VECTOR")["positive_label"] = "C"
        self.assertFalse(protocol.select_layer_gain(rows)["selected"])

    def test_duplicate_holdout_control_fails_closed_even_if_identical(self) -> None:
        rows = holdout()
        rows.append(copy.deepcopy(next(r for r in rows if r["label_map_id"] == "MAP_AB" and r["control"] == "+VECTOR")))
        out = protocol.adjudicate_holdout(rows, selected_layer=12, selected_gain=4.0)
        self.assertFalse(out["pass"])
        self.assertEqual("DUPLICATE_MATCHED_CONTROL_ROW", out["classification"])

    def test_split_holdout_prompt_does_not_merge(self) -> None:
        rows = holdout()
        next(r for r in rows if r["label_map_id"] == "MAP_AB" and r["control"] == "SIGN_FLIP")["prompt_sha256"] = "e" * 64
        out = protocol.adjudicate_holdout(rows, selected_layer=12, selected_gain=4.0)
        self.assertFalse(out["pass"])
        self.assertEqual("INCOMPLETE_MATCHED_CONTROL_FAMILY", out["classification"])

    def test_split_holdout_seed_does_not_merge(self) -> None:
        rows = holdout()
        next(r for r in rows if r["label_map_id"] == "MAP_AB" and r["control"] == "NULL_VECTOR")["seed"] = 9999
        out = protocol.adjudicate_holdout(rows, selected_layer=12, selected_gain=4.0)
        self.assertFalse(out["pass"])
        self.assertEqual("INCOMPLETE_MATCHED_CONTROL_FAMILY", out["classification"])

    def test_split_holdout_labels_does_not_merge(self) -> None:
        rows = holdout()
        row = next(r for r in rows if r["label_map_id"] == "MAP_AB" and r["control"] == "PERMUTED_SAME_NORM")
        row["positive_label"], row["negative_label"] = "C", "D"
        out = protocol.adjudicate_holdout(rows, selected_layer=12, selected_gain=4.0)
        self.assertFalse(out["pass"])
        self.assertEqual("INCOMPLETE_MATCHED_CONTROL_FAMILY", out["classification"])

    def test_partial_lesion_rescue_pair_fails_closed(self) -> None:
        rows = holdout()
        plus = next(r for r in rows if r["label_map_id"] == "MAP_AB" and r["control"] == "+VECTOR")
        plus.pop("rescue_delta")
        out = protocol.adjudicate_holdout(rows, selected_layer=12, selected_gain=4.0)
        self.assertFalse(out["pass"])
        self.assertEqual("LESION_RESCUE_PAIR_REQUIRED", out["classification"])

    def test_auxiliary_evidence_on_baseline_does_not_satisfy_plus_vector_gate(self) -> None:
        rows = holdout()
        for map_id in ("MAP_AB", "MAP_BA"):
            plus = next(r for r in rows if r["label_map_id"] == map_id and r["control"] == "+VECTOR")
            base = next(r for r in rows if r["label_map_id"] == map_id and r["control"] == "BASELINE")
            for field in (
                "wrong_layer", "wrong_layer_vector_source_layer", "wrong_layer_same_selected_vector",
                "wrong_layer_delta", "wrong_layer_receipt_sha256", "lesion_delta", "rescue_delta",
            ):
                base[field] = plus.pop(field)
        out = protocol.adjudicate_holdout(rows, selected_layer=12, selected_gain=4.0)
        self.assertFalse(out["pass"])
        self.assertEqual("AUXILIARY_CAUSAL_EVIDENCE_MUST_BIND_PLUS_VECTOR_ROW", out["classification"])


if __name__ == "__main__":
    unittest.main()
