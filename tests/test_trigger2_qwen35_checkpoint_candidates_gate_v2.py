import copy
import json
import unittest
from pathlib import Path

from tools import trigger2_qwen35_checkpoint_candidates_gate_v2 as g

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "research_entity/global/j-space/research/trigger2_qwen35_08b_checkpoint_candidates_v2.json"
with MANIFEST.open(encoding="utf-8") as fh:
    BASE = json.load(fh)


class Trigger2CheckpointCandidatesGateV2Test(unittest.TestCase):
    def test_role_typed_registry_passes_but_selection_is_not_ready(self):
        result = g.adjudicate(copy.deepcopy(BASE))
        self.assertTrue(result["pass"])
        self.assertFalse(result["selection_ready"])
        self.assertIsNone(result["checkpoint_winner"])

    def test_source_registry_cannot_select_winner(self):
        x = copy.deepcopy(BASE)
        x["selected_candidate"] = "QWEN35_08B_JOSIEFIED_GABLITERATED_MEASURED"
        self.assertIn("SOURCE_REGISTRY_CANNOT_SELECT_WINNER", g.adjudicate(x)["failures"])

    def test_measured_target_cannot_be_omitted(self):
        x = copy.deepcopy(BASE)
        x["candidates"] = [c for c in x["candidates"] if c["candidate_role"] != "TARGET_MEASURED"]
        self.assertIn("MEASURED_ABLITERATED_TARGET_REQUIRED", g.adjudicate(x)["failures"])

    def test_official_control_cannot_role_collapse_into_target(self):
        x = copy.deepcopy(BASE)
        x["candidates"][0]["candidate_role"] = "TARGET_EXTERNAL_UNMEASURED"
        failures = g.adjudicate(x)["failures"]
        self.assertIn("MISSING_CONTROL:QWEN35_08B_BASE", failures)

    def test_incomplete_identity_cannot_claim_selection_eligibility(self):
        x = copy.deepcopy(BASE)
        target = next(c for c in x["candidates"] if c["candidate_role"] == "TARGET_MEASURED")
        target["selection_eligible"] = True
        self.assertIn(
            "INCOMPLETE_IDENTITY_CANNOT_BE_SELECTION_ELIGIBLE:QWEN35_08B_JOSIEFIED_GABLITERATED_MEASURED",
            g.adjudicate(x)["failures"],
        )

    def test_model_card_claim_cannot_mint_clay_selection_credit(self):
        x = copy.deepcopy(BASE)
        target = next(c for c in x["candidates"] if c["candidate_id"] == "QWEN35_08B_WANGZHANG_ABLITERATED_EXTERNAL")
        target["external_claims"]["clay_selection_credit"] = 1
        self.assertIn(
            "MODEL_CARD_CLAIM_CANNOT_MINT_SELECTION_CREDIT:QWEN35_08B_WANGZHANG_ABLITERATED_EXTERNAL",
            g.adjudicate(x)["failures"],
        )

    def test_holdout_leak_fails_closed(self):
        x = copy.deepcopy(BASE)
        x["matched_pilot_contract"]["holdout_seen_during_selection"] = True
        self.assertIn("HOLDOUT_LEAK_FORBIDDEN", g.adjudicate(x)["failures"])

    def test_source_registry_cannot_claim_matched_pilot_execution(self):
        x = copy.deepcopy(BASE)
        x["matched_pilot_contract"]["matched_pilot_executed"] = True
        self.assertIn("MATCHED_PILOT_MUST_REMAIN_UNEXECUTED_IN_SOURCE_REGISTRY", g.adjudicate(x)["failures"])


if __name__ == "__main__":
    unittest.main()
