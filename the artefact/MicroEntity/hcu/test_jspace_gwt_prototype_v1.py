import hashlib
import json
import unittest

from jspace_gwt_prototype_v1 import CellSignal, JSpaceGWTError, matched_budget_lesion_rescue, run_transition


def h(s):
    return hashlib.sha256(s.encode()).hexdigest()


class PrototypeTests(unittest.TestCase):
    def setUp(self):
        self.cells = [
            CellSignal("c1", "planner", (0.9, 0.1, -0.2, 0.4), 0.9, 0.6, 0.2, 0.8, 0.15, h("ws1"), {"action": "PLAN"}),
            CellSignal("c2", "critic", (-0.3, 0.8, 0.5, -0.1), 0.8, 0.7, 0.9, 0.7, 0.20, h("ws2"), {"action": "CRITIQUE"}),
            CellSignal("c3", "provenance", (0.2, -0.4, 0.7, 0.3), 0.5, 0.4, 0.6, 0.9, 0.10, h("ws3"), {"action": "CHECK"}),
        ]
        self.kw = dict(
            generation=7,
            basis_id="B42",
            entry_event_sha256=h("event"),
            entry_admission_sha256=h("admission"),
            route_decision_sha256=h("route"),
            grid_plan_sha256=h("grid"),
            cells=self.cells,
            coalition_size=2,
            hyperposition_branch_ids=["hp:a", "hp:b"],
            resource_budget=40,
            requested_action_class="COGNITION_ONLY",
        )

    def test_deterministic_transition_and_trace_ids(self):
        a = run_transition(**self.kw)
        b = run_transition(**self.kw)
        self.assertEqual(a["transition_id"], b["transition_id"])
        self.assertEqual([t["trace_id"] for t in a["traces"]], [t["trace_id"] for t in b["traces"]])

    def test_required_training_trace_fields_exist(self):
        required = {
            "schema_version", "trace_id", "generation", "entry_event_sha256", "entry_admission_sha256",
            "route_decision_sha256", "grid_plan_sha256", "cell_id", "role", "jspace_basis_id",
            "jspace_input_vector_ref", "jspace_input_codec_version", "local_workspace_state_ref",
            "gwt_competition_set", "gwt_broadcast_gate", "global_jspace_slice_ref", "hyperposition_branch_ids",
            "provenance_evidence_class", "resource_budget", "requested_action_class",
            "expected_structured_model_output", "observed_downstream_outcome", "falsifier_lesion_condition", "credit_label",
        }
        result = run_transition(**self.kw)
        self.assertTrue(result["traces"])
        for trace in result["traces"]:
            self.assertTrue(required.issubset(trace))

    def test_competition_is_bounded_and_hyperposition_preserved(self):
        result = run_transition(**self.kw)
        self.assertLessEqual(len(result["selected_cell_ids"]), 2)
        for trace in result["traces"]:
            self.assertEqual(trace["hyperposition_branch_ids"], ["hp:a", "hp:b"])

    def test_matched_budget_empty_broadcast_lesion_and_exact_rescue(self):
        lr = matched_budget_lesion_rescue(**self.kw)
        self.assertTrue(lr["matched_resource_budget"])
        self.assertTrue(lr["lesion_changed_broadcast"])
        self.assertTrue(lr["rescue_exact"])
        self.assertTrue(lr["baseline_selected"])
        self.assertEqual(lr["lesion_selected"], [])
        self.assertIsNotNone(lr["baseline_slice"])
        self.assertIsNone(lr["lesion_slice"])
        self.assertEqual(lr["baseline_slice"], lr["rescue_slice"])

    def test_shuffled_slice_changes_global_slice_without_changing_competition(self):
        base = run_transition(**self.kw)
        shuffled = run_transition(**self.kw, lesion_condition="SHUFFLED_SLICE")
        self.assertEqual(base["selected_cell_ids"], shuffled["selected_cell_ids"])
        self.assertNotEqual(base["global_jspace_slice_ref"], shuffled["global_jspace_slice_ref"])

    def test_generation_change_changes_transition_identity(self):
        a = run_transition(**self.kw)
        b = run_transition(**{**self.kw, "generation": 8})
        self.assertNotEqual(a["transition_id"], b["transition_id"])

    def test_duplicate_cell_and_bad_digest_fail_closed(self):
        with self.assertRaises(JSpaceGWTError):
            run_transition(**{**self.kw, "cells": [self.cells[0], self.cells[0]]})
        with self.assertRaises(JSpaceGWTError):
            run_transition(**{**self.kw, "entry_event_sha256": "bad"})

    def test_trace_json_is_machine_serializable_without_private_reasoning(self):
        result = run_transition(**self.kw)
        encoded = json.dumps(result["traces"], sort_keys=True)
        self.assertIn("expected_structured_model_output", encoded)
        self.assertNotIn("chain_of_thought", encoded)


if __name__ == "__main__":
    unittest.main(verbosity=2)
