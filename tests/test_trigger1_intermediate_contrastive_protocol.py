from __future__ import annotations

import unittest

from tools.trigger1_intermediate_contrastive_protocol import adjudicate_holdout


class Trigger1IntermediateContrastiveProtocolTests(unittest.TestCase):
    def rows(self):
        scores = {
            "BASELINE": 0.0,
            "+VECTOR": 2.0,
            "SIGN_FLIP": -2.0,
            "NULL_VECTOR": 0.0,
            "ORTHOGONAL_SAME_NORM": 0.1,
            "PERMUTED_SAME_NORM": 0.05,
        }
        out = []
        for label_map in ("map-a", "map-b"):
            for control, score in scores.items():
                row = {
                    "split": "holdout",
                    "layer": 12,
                    "gain": 2.0,
                    "case_id": "semantic-case",
                    "label_map_id": label_map,
                    "control": control,
                    "target_score": score,
                }
                if control == "BASELINE":
                    row.update(
                        wrong_layer_delta=-0.25,
                        lesion_delta=-0.5,
                        rescue_delta=0.75,
                    )
                out.append(row)
        return out

    def adjudicate(self, rows):
        return adjudicate_holdout(rows, selected_layer=12, selected_gain=2.0)

    def test_complete_matched_family_with_required_causal_evidence_passes(self):
        result = self.adjudicate(self.rows())
        self.assertTrue(result["pass"])
        self.assertEqual(result["classification"], "INTERMEDIATE_REPRESENTATION_CAUSAL_CANDIDATE")
        self.assertTrue(result["wrong_layer_evidence_complete"])
        self.assertTrue(result["lesion_rescue_evidence_complete"])

    def test_missing_wrong_layer_evidence_fails_closed(self):
        rows = self.rows()
        for row in rows:
            row.pop("wrong_layer_delta", None)
        result = self.adjudicate(rows)
        self.assertFalse(result["pass"])
        self.assertEqual(result["classification"], "WRONG_LAYER_EVIDENCE_REQUIRED")

    def test_missing_lesion_rescue_evidence_fails_closed(self):
        rows = self.rows()
        for row in rows:
            row.pop("lesion_delta", None)
            row.pop("rescue_delta", None)
        result = self.adjudicate(rows)
        self.assertFalse(result["pass"])
        self.assertEqual(result["classification"], "LESION_RESCUE_EVIDENCE_REQUIRED")

    def test_partial_lesion_rescue_pair_fails_closed(self):
        rows = self.rows()
        for row in rows:
            row.pop("rescue_delta", None)
        result = self.adjudicate(rows)
        self.assertFalse(result["pass"])
        self.assertEqual(result["classification"], "INCOMPLETE_LESION_RESCUE_EVIDENCE")

    def test_wrong_layer_positive_effect_prevents_causal_candidate(self):
        rows = self.rows()
        for row in rows:
            if row.get("wrong_layer_delta") is not None:
                row["wrong_layer_delta"] = 0.25
        result = self.adjudicate(rows)
        self.assertFalse(result["pass"])
        self.assertEqual(result["classification"], "INTERMEDIATE_REPRESENTATION_NOT_ESTABLISHED")
        self.assertFalse(result["wrong_layer_ok"])


if __name__ == "__main__":
    unittest.main()
