#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys
import unittest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_intermediate_contrastive_protocol as protocol


def rows(
    *,
    wrong_layer_delta: float = -0.1,
    wrong_layer: int = 6,
    vector_source_layer: int = 12,
    same_selected_vector: bool = True,
    receipt_sha: str = "b" * 64,
) -> list[dict]:
    scores = {
        "BASELINE": 0.0,
        "+VECTOR": 3.0,
        "SIGN_FLIP": -3.0,
        "NULL_VECTOR": 0.0,
        "ORTHOGONAL_SAME_NORM": 0.1,
        "PERMUTED_SAME_NORM": 0.2,
    }
    out: list[dict] = []
    for map_index, (map_id, positive, negative) in enumerate((("MAP_AB", "A", "B"), ("MAP_BA", "B", "A"))):
        for case_index, case_id in enumerate(("h1", "h2")):
            prompt_sha = (("a" if case_index == 0 else "b") if map_index == 0 else ("c" if case_index == 0 else "d")) * 64
            for control in protocol.REQUIRED_CONTROLS:
                row = {
                    "split": "holdout",
                    "layer": 12,
                    "gain": 4.0,
                    "case_id": case_id,
                    "prompt_sha256": prompt_sha,
                    "seed": 2700 + case_index,
                    "label_map_id": map_id,
                    "positive_label": positive,
                    "negative_label": negative,
                    "control": control,
                    "target_score": scores[control],
                }
                if control == "+VECTOR":
                    row.update(
                        {
                            "wrong_layer": wrong_layer,
                            "wrong_layer_vector_source_layer": vector_source_layer,
                            "wrong_layer_same_selected_vector": same_selected_vector,
                            "wrong_layer_delta": wrong_layer_delta,
                            "wrong_layer_receipt_sha256": receipt_sha,
                            "lesion_delta": -0.2,
                            "rescue_delta": 0.5,
                        }
                    )
                out.append(row)
    return out


class WrongLayerProvenanceAndLocalityTests(unittest.TestCase):
    def adjudicate(self, xs: list[dict]) -> dict:
        return protocol.adjudicate_holdout(xs, selected_layer=12, selected_gain=4.0)

    def test_strictly_weaker_same_selected_vector_at_different_layer_can_pass(self) -> None:
        verdict = self.adjudicate(rows())
        self.assertTrue(verdict["pass"])
        self.assertTrue(verdict["wrong_layer_selected_vector_provenance"])
        self.assertTrue(verdict["wrong_layer_ok"])

    def test_wrong_layer_must_differ_from_selected_layer(self) -> None:
        verdict = self.adjudicate(rows(wrong_layer=12))
        self.assertFalse(verdict["pass"])
        self.assertEqual("WRONG_LAYER_SELECTED_VECTOR_PROVENANCE_REQUIRED", verdict["classification"])

    def test_wrong_layer_must_reuse_selected_vector_source_layer(self) -> None:
        verdict = self.adjudicate(rows(vector_source_layer=6))
        self.assertFalse(verdict["pass"])
        self.assertEqual("WRONG_LAYER_SELECTED_VECTOR_PROVENANCE_REQUIRED", verdict["classification"])

    def test_same_selected_vector_attestation_is_required(self) -> None:
        verdict = self.adjudicate(rows(same_selected_vector=False))
        self.assertFalse(verdict["pass"])
        self.assertEqual("WRONG_LAYER_SELECTED_VECTOR_PROVENANCE_REQUIRED", verdict["classification"])

    def test_wrong_layer_runtime_receipt_sha_is_required(self) -> None:
        verdict = self.adjudicate(rows(receipt_sha="invalid"))
        self.assertFalse(verdict["pass"])
        self.assertEqual("WRONG_LAYER_SELECTED_VECTOR_PROVENANCE_REQUIRED", verdict["classification"])

    def test_equal_wrong_layer_effect_is_not_localization(self) -> None:
        verdict = self.adjudicate(rows(wrong_layer_delta=0.0))
        self.assertFalse(verdict["pass"])
        self.assertFalse(verdict["wrong_layer_ok"])
        self.assertEqual("INTERMEDIATE_REPRESENTATION_NOT_ESTABLISHED", verdict["classification"])

    def test_stronger_wrong_layer_effect_is_not_localization(self) -> None:
        verdict = self.adjudicate(rows(wrong_layer_delta=0.1))
        self.assertFalse(verdict["pass"])
        self.assertFalse(verdict["wrong_layer_ok"])


if __name__ == "__main__":
    unittest.main()
