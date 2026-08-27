import copy
import importlib.util
from pathlib import Path
import unittest

HERE = Path(__file__).resolve()
MODULE_PATH = HERE.parents[1] / "tools" / "trigger2_executable_transition_pilot_v1.py"
spec = importlib.util.spec_from_file_location("pilot", MODULE_PATH)
pilot = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(pilot)

RESULT_REQUIRED = [
    "schema","causal_event_id","admission_id","generation","work_id","process_id",
    "executor_binding","result_id","result_class","result_payload_ref","result_digest",
    "evidence_refs","unknowns","db_write_proposals","effect_request_candidates",
    "workspace_reentry","runtime_receipt",
]
ABI = {
    "schema": "COGNITIVE_PROCESS_ABI/v1",
    "packet_types": {
        "COGNITIVE_RESULT_PACKET/v1": {
            "required": RESULT_REQUIRED,
            "allowed_result_class": ["CANDIDATE","PROJECTION","MEASUREMENT","DETERMINISTIC_CONTROL_RESULT","EFFECT_RECEIPT"],
        }
    }
}
CENSUS = {
    "schema": "ZERO_ENTITYOS_COGNITIVE_PROCESS_CENSUS/v1",
    "processes": [
        {"id": pid, "implementation_class": cls}
        for pid, cls in [
            ("ZECP03","SIMULATE_ON_GRID"),("ZECP04","SIMULATE_ON_GRID"),
            ("ZECP05","SIMULATE_ON_GRID"),("ZECP06","SIMULATE_ON_GRID"),
            ("ZECP07","SIMULATE_ON_GRID"),("ZECP08","SIMULATE_ON_GRID"),
            ("ZECP09","SIMULATE_ON_GRID"),("ZECP10","SIMULATE_ON_GRID"),
            ("ZECP12","SIMULATE_ON_GRID"),("ZECP13","EXTERNAL_STRONG_MODEL_BRIDGE"),
            ("ZECP14","EXTERNAL_STRONG_MODEL_BRIDGE"),("ZECP15","SIMULATE_ON_GRID"),
            ("ZECP16","SIMULATE_ON_GRID"),("ZECP18","SIMULATE_ON_GRID"),
            ("ZECP17","DETERMINISTIC_BOUNDARY"),
        ]
    ],
}

class PilotTests(unittest.TestCase):
    def audit(self, rows):
        return pilot.audit(rows, abi=ABI, census=CENSUS)

    def test_pilot_passes_machine_adjudication_fixture(self):
        result = self.audit(pilot.rows())
        self.assertTrue(result["pass"], result["failures"])
        self.assertEqual(result["rows"], 14)
        self.assertFalse(result["training_eligible"])
        self.assertEqual(result["accepted_dataset_tokens_minted"], 0)

    def test_meta_rule_narration_is_rejected(self):
        rows = copy.deepcopy(pilot.rows())
        rows[0]["target"]["result_payload_ref"]["payload"]["rule"] = "describe instead of execute"
        rows[0]["target"]["result_digest"] = pilot.dg(rows[0]["target"]["result_payload_ref"]["payload"])
        rows[0]["transition_semantic_digest"] = pilot.dg({
            "process_id": rows[0]["process_id_evaluator_only"],
            "state_before_digest": rows[0]["state_before_digest"],
            "decisive_semantic_delta": rows[0]["decisive_semantic_delta"],
            "result_digest": rows[0]["target"]["result_digest"],
            "expected_state_after_digest": rows[0]["expected_state_after_digest"],
        })
        result = self.audit(rows)
        self.assertFalse(result["pass"])
        self.assertTrue(any(x.startswith("META_RULE_NARRATION_TARGET:") for x in result["failures"]))

    def test_result_digest_tamper_is_rejected(self):
        rows = copy.deepcopy(pilot.rows())
        rows[0]["target"]["result_digest"] = "0" * 64
        result = self.audit(rows)
        self.assertIn("RESULT_DIGEST_MISMATCH:ECT01_WORKING_STATE", result["failures"])

    def test_unknown_collapse_is_rejected(self):
        rows = copy.deepcopy(pilot.rows())
        rows[4]["target"]["unknowns"] = []
        result = self.audit(rows)
        self.assertIn("UNKNOWN_COLLAPSE:ECT05_HYPERPOSITION", result["failures"])

    def test_effect_self_mint_is_rejected(self):
        rows = copy.deepcopy(pilot.rows())
        rows[12]["target"]["effect_request_candidates"][0]["executed"] = True
        result = self.audit(rows)
        self.assertIn("EFFECT_AUTHORITY_SELF_MINT:ECT13_EFFECT_PROPOSAL", result["failures"])

    def test_state_after_tamper_is_rejected(self):
        rows = copy.deepcopy(pilot.rows())
        rows[3]["expected_state_after"]["prereq_u2"] = True
        result = self.audit(rows)
        self.assertIn("STATE_AFTER_DIGEST_MISMATCH:ECT04_REPLAN", result["failures"])

    def test_deterministic_authority_process_cannot_be_model_target(self):
        rows = copy.deepcopy(pilot.rows())
        rows[0]["process_id_evaluator_only"] = "ZECP17"
        rows[0]["implementation_class_evaluator_only"] = "DETERMINISTIC_BOUNDARY"
        rows[0]["target"]["process_id"] = "ZECP17"
        rows[0]["transition_semantic_digest"] = pilot.dg({
            "process_id": "ZECP17",
            "state_before_digest": rows[0]["state_before_digest"],
            "decisive_semantic_delta": rows[0]["decisive_semantic_delta"],
            "result_digest": rows[0]["target"]["result_digest"],
            "expected_state_after_digest": rows[0]["expected_state_after_digest"],
        })
        result = self.audit(rows)
        self.assertIn("NONMODEL_AUTHORITY_PROCESS_TARGETED:ECT01_WORKING_STATE", result["failures"])

    def test_both_trainable_implementation_classes_are_covered(self):
        result = self.audit(pilot.rows())
        self.assertEqual(
            set(result["model_implementation_classes_covered"]),
            {"SIMULATE_ON_GRID", "EXTERNAL_STRONG_MODEL_BRIDGE"},
        )

if __name__ == "__main__":
    unittest.main()
