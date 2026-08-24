#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys
import unittest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_intermediate_contrastive_protocol as protocol


def rows(wrong_layer_delta: float) -> list[dict]:
    scores = {
        "BASELINE": 0.0,
        "+VECTOR": 3.0,
        "SIGN_FLIP": -3.0,
        "NULL_VECTOR": 0.0,
        "ORTHOGONAL_SAME_NORM": 0.1,
        "PERMUTED_SAME_NORM": 0.2,
    }
    out = []
    for map_id, positive, negative in (("MAP_AB", "A", "B"), ("MAP_BA", "B", "A")):
        for case_id in ("h1", "h2"):
            for control in protocol.REQUIRED_CONTROLS:
                row = {
                    "split": "holdout",
                    "layer": 12,
                    "gain": 4.0,
                    "case_id": case_id,
                    "label_map_id": map_id,
                    "positive_label": positive,
                    "negative_label": negative,
                    "control": control,
                    "target_score": scores[control],
                }
                if control == "+VECTOR":
                    row.update({
                        "wrong_layer": 6,
                        "wrong_layer_vector_source_layer": 12,
                        "wrong_layer_same_selected_vector": True,
                        "wrong_layer_delta": wrong_layer_delta,
                        "lesion_delta": -0.2,
                        "rescue_delta": 0.5,
                    })
                out.append(row)
    return out


class WrongLayerStrictLocalityTests(unittest.TestCase):
    def test_strictly_weaker_wrong_layer_can_pass_locality_gate(self) -> None:
        verdict = protocol.adjudicate_holdout(
            rows(-0.1), selected_layer=12, selected_gain=4.0
        )
        self.assertTrue(verdict["pass"])
        self.assertTrue(verdict["wrong_layer_ok"])

    def test_equal_effect_wrong_layer_is_not_localization_evidence(self) -> None:
        verdict = protocol.adjudicate_holdout(
            rows(0.0), selected_layer=12, selected_gain=4.0
        )
        self.assertFalse(verdict["pass"])
        self.assertFalse(verdict["wrong_layer_ok"])
        self.assertEqual(
            "INTERMEDIATE_REPRESENTATION_NOT_ESTABLISHED",
            verdict["classification"],
        )

    def test_stronger_wrong_layer_is_not_localization_evidence(self) -> None:
        verdict = protocol.adjudicate_holdout(
            rows(0.1), selected_layer=12, selected_gain=4.0
        )
        self.assertFalse(verdict["pass"])
        self.assertFalse(verdict["wrong_layer_ok"])


if __name__ == "__main__":
    unittest.main()
