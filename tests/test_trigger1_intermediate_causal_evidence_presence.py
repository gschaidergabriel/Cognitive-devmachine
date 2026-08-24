from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_intermediate_contrastive_protocol as p


def rows(*, include_wrong=True, include_lesion=True, partial_pair=False):
    result=[]
    controls={
        "BASELINE":0.0,
        "+VECTOR":2.0,
        "SIGN_FLIP":-2.0,
        "NULL_VECTOR":0.0,
        "ORTHOGONAL_SAME_NORM":0.0,
        "PERMUTED_SAME_NORM":0.0,
    }
    for label_map in ("map-a","map-b"):
        for control,score in controls.items():
            r={"split":"holdout","layer":14,"gain":2.0,"case_id":"case-1","label_map_id":label_map,"control":control,"target_score":score}
            if include_wrong and control == "BASELINE":
                r["wrong_layer_delta"]=-0.2
            if include_lesion and control == "+VECTOR":
                r["lesion_delta"]=-0.5
                if not partial_pair:
                    r["rescue_delta"]=0.8
            result.append(r)
    return result


class CausalEvidencePresenceTests(unittest.TestCase):
    def test_complete_evidence_can_pass(self):
        v=p.adjudicate_holdout(rows(), selected_layer=14, selected_gain=2.0)
        self.assertTrue(v["pass"])
        self.assertGreater(v["wrong_layer_evidence_count"],0)
        self.assertGreater(v["lesion_rescue_evidence_count"],0)

    def test_missing_wrong_layer_evidence_fails_closed(self):
        v=p.adjudicate_holdout(rows(include_wrong=False), selected_layer=14, selected_gain=2.0)
        self.assertFalse(v["pass"])
        self.assertEqual(v["classification"],"WRONG_LAYER_EVIDENCE_REQUIRED")

    def test_missing_lesion_rescue_evidence_fails_closed(self):
        v=p.adjudicate_holdout(rows(include_lesion=False), selected_layer=14, selected_gain=2.0)
        self.assertFalse(v["pass"])
        self.assertEqual(v["classification"],"LESION_RESCUE_EVIDENCE_REQUIRED")

    def test_partial_lesion_rescue_pair_fails_closed(self):
        v=p.adjudicate_holdout(rows(partial_pair=True), selected_layer=14, selected_gain=2.0)
        self.assertFalse(v["pass"])
        self.assertEqual(v["classification"],"LESION_RESCUE_PAIR_REQUIRED")

    def test_present_but_wrong_signed_wrong_layer_fails(self):
        xs=rows()
        xs[0]["wrong_layer_delta"]=0.2
        v=p.adjudicate_holdout(xs, selected_layer=14, selected_gain=2.0)
        self.assertFalse(v["pass"])
        self.assertFalse(v["wrong_layer_ok"])

    def test_present_but_wrong_signed_lesion_rescue_fails(self):
        xs=rows()
        for r in xs:
            if "lesion_delta" in r:
                r["lesion_delta"]=0.1
                r["rescue_delta"]=-0.1
        v=p.adjudicate_holdout(xs, selected_layer=14, selected_gain=2.0)
        self.assertFalse(v["pass"])
        self.assertFalse(v["lesion_rescue_ok"])


if __name__ == "__main__":
    unittest.main()
