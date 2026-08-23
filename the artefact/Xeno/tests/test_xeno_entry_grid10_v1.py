import copy
import sys
import unittest
from pathlib import Path

RUNTIME = Path(__file__).resolve().parents[1] / "runtime"
sys.path.insert(0, str(RUNTIME))

from entry_fabric_v1 import EntryAdmissionError, admit_entry
from grid10_v1 import Grid10SchedulingError, schedule_grid10


def base_request():
    return {
        "schema": "XENO_ENTRY_REQUEST/v1",
        "event_kind": "human_prompt",
        "entity_generation": 11,
        "causal_id": "causal-11-a",
        "source_id": "user:andreas",
        "source_type": "human",
        "provenance": {"channel": "terminal", "authenticated": True},
        "modality": "text",
        "observed_at_ns": 100,
        "received_at_ns": 101,
        "permission_scope": ["read_state", "retrieve", "cognition", "simulation"],
        "parent_packet_ids": [],
        "budget": {
            "max_cells": 10,
            "max_model_calls": 6,
            "max_wall_ms": 5000,
            "max_output_bytes": 65536,
        },
        "payload": {"text": "compare two hypotheses"},
    }


class EntryFabricTests(unittest.TestCase):
    def test_same_event_replay_is_deterministic(self):
        a = admit_entry(base_request(), current_generation=11)
        b = admit_entry(copy.deepcopy(base_request()), current_generation=11)
        self.assertEqual(a.packet_id, b.packet_id)
        self.assertEqual(a, b)

    def test_stale_generation_fails_closed(self):
        with self.assertRaisesRegex(EntryAdmissionError, "STALE_ENTITY_GENERATION"):
            admit_entry(base_request(), current_generation=12)

    def test_unknown_field_fails_closed(self):
        request = base_request()
        request["canonical_truth"] = True
        with self.assertRaisesRegex(EntryAdmissionError, "REQUEST_UNKNOWN_FIELD"):
            admit_entry(request, current_generation=11)

    def test_reference_modality_requires_bound_digest(self):
        request = base_request()
        request["modality"] = "binary_ref"
        request.pop("payload")
        request["payload_ref"] = "object://sensor/frame-1"
        request["payload_sha256"] = "a" * 64
        packet = admit_entry(request, current_generation=11)
        self.assertEqual(packet.payload_sha256, "a" * 64)
        self.assertIsNone(packet.canonical_payload_json)

    def test_permission_scope_is_positive_allowlist(self):
        request = base_request()
        request["permission_scope"] = ["read_state", "execute_host"]
        with self.assertRaisesRegex(EntryAdmissionError, "permission_scope:UNSUPPORTED_ITEM"):
            admit_entry(request, current_generation=11)

    def test_causal_alias_falsifier_materially_different_events_do_not_alias(self):
        # GO unusual experiment: preserve all route/scheduler-relevant controls while
        # changing only the causal payload. The packet identity must separate them.
        request_a = base_request()
        request_b = copy.deepcopy(request_a)
        request_b["payload"] = {"text": "compare hypothesis A"}
        a = admit_entry(request_a, current_generation=11)
        b = admit_entry(request_b, current_generation=11)
        self.assertNotEqual(a.payload_sha256, b.payload_sha256)
        self.assertNotEqual(a.packet_id, b.packet_id)

        sched_a = schedule_grid10(
            a,
            mode="XENO_COGSIM10",
            requested_functions=["retrieve", "hypothesis", "counterhypothesis", "critic", "calibrate"],
            current_generation=11,
        )
        sched_b = schedule_grid10(
            b,
            mode="XENO_COGSIM10",
            requested_functions=["retrieve", "hypothesis", "counterhypothesis", "critic", "calibrate"],
            current_generation=11,
        )
        self.assertNotEqual(sched_a.schedule_id, sched_b.schedule_id)


class Grid10Tests(unittest.TestCase):
    def test_schedule_is_deterministic_and_binds_entry_identity(self):
        entry = admit_entry(base_request(), current_generation=11)
        functions = ["retrieve", "hypothesis", "counterhypothesis", "critic", "calibrate"]
        a = schedule_grid10(entry, mode="XENO_COGSIM10", requested_functions=functions, current_generation=11)
        b = schedule_grid10(entry, mode="XENO_COGSIM10", requested_functions=functions, current_generation=11)
        self.assertEqual(a, b)
        self.assertEqual(a.entry_packet_id, entry.packet_id)
        self.assertTrue(all(w.entry_packet_id == entry.packet_id for w in a.work_packets))
        self.assertTrue(all(w.schedule_id == a.schedule_id for w in a.work_packets))
        self.assertIsNone(a.physical_decode_concurrency_claimed)

    def test_grid_has_ten_logical_slots_but_does_not_claim_physical_concurrency(self):
        entry = admit_entry(base_request(), current_generation=11)
        schedule = schedule_grid10(
            entry,
            mode="XENO_GRID10",
            requested_functions=["retrieve", "provenance", "hypothesis"],
            current_generation=11,
        )
        self.assertEqual(schedule.logical_capacity, 10)
        self.assertEqual(len(schedule.active_cells), 3)
        self.assertIsNone(schedule.physical_decode_concurrency_claimed)

    def test_cell_budget_fails_closed(self):
        request = base_request()
        request["budget"]["max_cells"] = 2
        entry = admit_entry(request, current_generation=11)
        with self.assertRaisesRegex(Grid10SchedulingError, "CELL_BUDGET_EXCEEDED"):
            schedule_grid10(
                entry,
                mode="XENO_GRID10",
                requested_functions=["retrieve", "hypothesis", "critic"],
                current_generation=11,
            )

    def test_model_call_budget_fails_closed(self):
        request = base_request()
        request["budget"]["max_model_calls"] = 1
        entry = admit_entry(request, current_generation=11)
        with self.assertRaisesRegex(Grid10SchedulingError, "MODEL_CALL_BUDGET_EXCEEDED"):
            schedule_grid10(
                entry,
                mode="XENO_COGSIM10",
                requested_functions=["hypothesis", "counterhypothesis"],
                current_generation=11,
            )

    def test_stale_schedule_generation_fails_closed(self):
        entry = admit_entry(base_request(), current_generation=11)
        with self.assertRaisesRegex(Grid10SchedulingError, "STALE_ENTITY_GENERATION"):
            schedule_grid10(
                entry,
                mode="XENO_GRID10",
                requested_functions=["retrieve"],
                current_generation=12,
            )


if __name__ == "__main__":
    unittest.main()
