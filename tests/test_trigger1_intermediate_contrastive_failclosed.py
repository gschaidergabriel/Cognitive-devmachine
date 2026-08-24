#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "tools/trigger1_intermediate_contrastive_protocol.py"


def load():
    spec = importlib.util.spec_from_file_location("trigger1_intermediate_contrastive_protocol", MOD)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class IntermediateFailClosedTests(unittest.TestCase):
    def setUp(self):
        self.m = load()

    def rows(self, *, wrong_layer: bool = True, lesion_rescue: bool = True, nuisance: float = 0.1):
        scores = {
            "BASELINE": 0.0,
            "+VECTOR": 2.0,
            "SIGN_FLIP": -2.0,
            "NULL_VECTOR": 0.0,
            "ORTHOGONAL_SAME_NORM": nuisance,
            "PERMUTED_SAME_NORM": 0.0,
        }
        rows = []
        for label_map in ("A_POS", "B_POS"):
            for control in self.m.REQUIRED_CONTROLS:
                row = {
                    "split": "holdout",
                    "layer": 8,
                    "gain": 2.0,
                    "case_id": "h1",
                    "label_map_id": label_map,
                    "control": control,
                    "target_score": scores[control],
                }
                if wrong_layer:
                    row["wrong_layer_delta"] = -0.1
                if lesion_rescue:
                    row["lesion_delta"] = -0.2
                    row["rescue_delta"] = 0.5
                rows.append(row)
        return rows

    def adjudicate(self, rows):
        return self.m.adjudicate_holdout(rows, selected_layer=8, selected_gain=2.0)

    def test_missing_wrong_layer_evidence_fails_closed(self):
        out = self.adjudicate(self.rows(wrong_layer=False))
        self.assertFalse(out["pass"])
        self.assertEqual("WRONG_LAYER_EVIDENCE_REQUIRED", out["classification"])

    def test_missing_lesion_rescue_evidence_fails_closed(self):
        out = self.adjudicate(self.rows(lesion_rescue=False))
        self.assertFalse(out["pass"])
        self.assertEqual("LESION_RESCUE_EVIDENCE_REQUIRED", out["classification"])

    def test_one_sided_lesion_rescue_evidence_fails_closed(self):
        rows = self.rows(lesion_rescue=False)
        rows[0]["lesion_delta"] = -0.2
        out = self.adjudicate(rows)
        self.assertFalse(out["pass"])
        self.assertEqual("LESION_RESCUE_EVIDENCE_REQUIRED", out["classification"])

    def test_large_negative_nuisance_effect_is_penalized_by_magnitude(self):
        out = self.adjudicate(self.rows(nuisance=-5.0))
        self.assertFalse(out["pass"])
        self.assertEqual("INTERMEDIATE_REPRESENTATION_NOT_ESTABLISHED", out["classification"])
        self.assertLess(out["worst_directional_specificity_margin"], 0.0)

    def test_duplicate_matched_control_fails_closed(self):
        rows = self.rows()
        rows.append(dict(rows[0]))
        out = self.adjudicate(rows)
        self.assertFalse(out["pass"])
        self.assertEqual("DUPLICATE_MATCHED_CONTROL", out["classification"])


if __name__ == "__main__":
    unittest.main()
