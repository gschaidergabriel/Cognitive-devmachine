import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import mini_pipeline_turn_workspace_v1 as mod


def d(ch: str) -> str:
    return hashlib.sha256(ch.encode()).hexdigest()


class PipelineTurnWorkspaceTests(unittest.TestCase):
    def base(self):
        profile = {
            "profile_id": "blogpost-v2",
            "_runtime_profile_snapshot": {"profile_id": "blogpost-v2", "profile_hash": d("profile")},
        }
        previous = {"generation": 7}
        compiled = {
            "canonical_state_hash": d("canonical"),
            "packet_hash": d("packet"),
            "allowed_evidence_refs": ["state:z", "probe:a", "event:m"],
        }
        return profile, previous, compiled

    def test_same_exact_material_is_deterministic(self):
        p, prev, comp = self.base()
        a = mod.prepare_pipeline_turn_material(profile=p, previous=prev, compiled=comp)
        b = mod.prepare_pipeline_turn_material(profile=copy.deepcopy(p), previous=dict(prev), compiled=copy.deepcopy(comp))
        self.assertEqual(a["task_text"], b["task_text"])
        self.assertEqual(a["workspace_digest"], b["workspace_digest"])
        self.assertEqual(a["selected_workspace_slots"], ["event:m", "probe:a", "state:z"])

    def test_packet_or_profile_identity_changes_task_and_workspace(self):
        p, prev, comp = self.base()
        a = mod.prepare_pipeline_turn_material(profile=p, previous=prev, compiled=comp)
        comp2 = copy.deepcopy(comp)
        comp2["packet_hash"] = d("packet-2")
        b = mod.prepare_pipeline_turn_material(profile=p, previous=prev, compiled=comp2)
        self.assertNotEqual(a["task_sha256"], b["task_sha256"])
        self.assertNotEqual(a["workspace_digest"], b["workspace_digest"])
        p2 = copy.deepcopy(p)
        p2["_runtime_profile_snapshot"]["profile_hash"] = d("profile-2")
        c = mod.prepare_pipeline_turn_material(profile=p2, previous=prev, compiled=comp)
        self.assertNotEqual(a["task_sha256"], c["task_sha256"])
        self.assertNotEqual(a["workspace_digest"], c["workspace_digest"])

    def test_workspace_is_explicit_text_only_unknown_not_measured(self):
        p, prev, comp = self.base()
        out = mod.prepare_pipeline_turn_material(profile=p, previous=prev, compiled=comp)
        ws = out["workspace"]
        self.assertEqual(ws["contradiction_state"], "UNKNOWN")
        self.assertEqual(ws["measurement_state"]["jspace"], "UNMEASURED")
        self.assertEqual(ws["measurement_state"]["gwt"], "TEXT_ONLY_BASELINE")
        self.assertFalse(ws["authority"]["direct_truth_authority"])
        self.assertFalse(ws["authority"]["direct_effect_authority"])

    def test_slot_budget_is_bounded_and_order_independent(self):
        p, prev, comp = self.base()
        comp["allowed_evidence_refs"] = [f"ref:{i:02d}" for i in range(30, -1, -1)]
        out = mod.prepare_pipeline_turn_material(profile=p, previous=prev, compiled=comp, max_slots=4)
        self.assertEqual(out["selected_workspace_slots"], ["ref:00", "ref:01", "ref:02", "ref:03"])
        comp2 = copy.deepcopy(comp)
        comp2["allowed_evidence_refs"].reverse()
        out2 = mod.prepare_pipeline_turn_material(profile=p, previous=prev, compiled=comp2, max_slots=4)
        self.assertEqual(out["workspace_digest"], out2["workspace_digest"])

    def test_bad_or_placeholder_identity_fails_closed(self):
        p, prev, comp = self.base()
        comp["packet_hash"] = "0" * 64
        with self.assertRaisesRegex(mod.PipelineTurnWorkspaceError, "PLACEHOLDER_REJECTED"):
            mod.prepare_pipeline_turn_material(profile=p, previous=prev, compiled=comp)
        p, prev, comp = self.base()
        prev["generation"] = True
        with self.assertRaisesRegex(mod.PipelineTurnWorkspaceError, "GENERATION_INVALID"):
            mod.prepare_pipeline_turn_material(profile=p, previous=prev, compiled=comp)

    def test_duplicate_evidence_ref_fails_closed(self):
        p, prev, comp = self.base()
        comp["allowed_evidence_refs"] = ["a", "a"]
        with self.assertRaisesRegex(mod.PipelineTurnWorkspaceError, "DUPLICATE"):
            mod.prepare_pipeline_turn_material(profile=p, previous=prev, compiled=comp)

    def test_profile_snapshot_mismatch_fails_closed(self):
        p, prev, comp = self.base()
        p["_runtime_profile_snapshot"]["profile_id"] = "other"
        with self.assertRaisesRegex(mod.PipelineTurnWorkspaceError, "PROFILE_SNAPSHOT_ID_MISMATCH"):
            mod.prepare_pipeline_turn_material(profile=p, previous=prev, compiled=comp)

    def test_task_text_is_structured_operation_not_prompt_prose(self):
        p, prev, comp = self.base()
        out = mod.prepare_pipeline_turn_material(profile=p, previous=prev, compiled=comp)
        task = json.loads(out["task_text"])
        self.assertEqual(task["schema"], mod.TASK_SCHEMA)
        self.assertEqual(task["entity_generation"], 7)
        self.assertNotIn("system", task)
        self.assertNotIn("user", task)
        self.assertFalse(task["authority"]["semantic_truth_authority"])


if __name__ == "__main__":
    unittest.main()
