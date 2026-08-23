import copy
import pathlib
import sys
import unittest

RUNTIME = pathlib.Path(__file__).resolve().parents[1] / "runtime"
sys.path.insert(0, str(RUNTIME))

from entry_fabric_v1 import EntryAdmissionError, admit_entry
from grid10_v1 import Grid10Error, build_grid10_schedule


def base_request():
    return {
        "schema": "XENO_ENTRY_REQUEST/v1",
        "event_kind": "human_prompt",
        "entity_generation": 7,
        "causal_id": "causal:test:001",
        "source_id": "user:andreas",
        "source_type": "authenticated_human",
        "provenance": {"channel": "test", "authenticated": True},
        "modality": "text",
        "observed_at_ns": 100,
        "received_at_ns": 110,
        "permission_scope": ["read_state", "retrieve", "cognition", "simulation"],
        "parent_packet_ids": [],
        "budget": {
            "max_cells": 10,
            "max_model_calls": 8,
            "max_wall_ms": 10000,
            "max_output_bytes": 65536,
        },
        "payload": {"text": "compare two hypotheses"},
    }


class EntryFabricTests(unittest.TestCase):
    def test_same_event_replay_is_deterministic(self):
        a = admit_entry(base_request(), current_generation=7)
        b = admit_entry(base_request(), current_generation=7)
        self.assertEqual(a, b)

    def test_stale_generation_fails_closed(self):
        with self.assertRaisesRegex(EntryAdmissionError, "STALE_ENTITY_GENERATION"):
            admit_entry(base_request(), current_generation=8)

    def test_unknown_authority_field_fails_closed(self):
        request = base_request()
        request["canonical_truth"] = True
        with self.assertRaisesRegex(EntryAdmissionError, "REQUEST_UNKNOWN_FIELD"):
            admit_entry(request, current_generation=7)

    def test_reference_modality_requires_bound_digest(self):
        request = base_request()
        request.pop("payload")
        request["modality"] = "binary_ref"
        request["payload_ref"] = "blob:abc"
        with self.assertRaisesRegex(EntryAdmissionError, "REFERENCE_AND_SHA256_REQUIRED"):
            admit_entry(request, current_generation=7)

    def test_permission_scope_is_positive_allowlist(self):
        request = base_request()
        request["permission_scope"] = ["cognition", "execute_host"]
        with self.assertRaisesRegex(EntryAdmissionError, "UNSUPPORTED_ITEM"):
            admit_entry(request, current_generation=7)

    def test_causal_alias_falsifier_materially_different_events_do_not_alias(self):
        # The single unusual discriminator for this GO macrocycle:
        # keep scheduler controls/topology identical and change only material event content.
        request_a = base_request()
        request_b = copy.deepcopy(request_a)
        request_b["payload"] = {"text": "compare two different hypotheses"}

        entry_a = admit_entry(request_a, current_generation=7)
        entry_b = admit_entry(request_b, current_generation=7)
        self.assertNotEqual(entry_a.payload_sha256, entry_b.payload_sha256)
        self.assertNotEqual(entry_a.packet_id, entry_b.packet_id)

        functions = ("hypothesis", "counterhypothesis", "critic")
        schedule_a = build_grid10_schedule(
            entry_a,
            current_generation=7,
            mode="XENO_COGSIM10",
            functions=functions,
        )
        schedule_b = build_grid10_schedule(
            entry_b,
            current_generation=7,
            mode="XENO_COGSIM10",
            functions=functions,
        )
        self.assertEqual(schedule_a.active_cells, schedule_b.active_cells)
        self.assertNotEqual(schedule_a.schedule_id, schedule_b.schedule_id)


class Grid10Tests(unittest.TestCase):
    def test_schedule_is_deterministic_and_binds_entry_ancestry(self):
        entry = admit_entry(base_request(), current_generation=7)
        functions = ("retrieve", "hypothesis", "counterhypothesis", "critic", "calibrate")
        a = build_grid10_schedule(entry, current_generation=7, functions=functions)
        b = build_grid10_schedule(entry, current_generation=7, functions=functions)
        self.assertEqual(a, b)
        self.assertTrue(a.work_packets)
        for packet in a.work_packets:
            self.assertEqual(packet.entry_packet_id, entry.packet_id)
            self.assertEqual(packet.schedule_id, a.schedule_id)
            self.assertEqual(packet.causal_id, entry.causal_id)
            self.assertEqual(packet.entity_generation, entry.entity_generation)

    def test_logical_grid_does_not_claim_physical_decode_concurrency(self):
        entry = admit_entry(base_request(), current_generation=7)
        schedule = build_grid10_schedule(entry, current_generation=7, functions=("retrieve",))
        self.assertEqual(schedule.logical_capacity, 10)
        self.assertIsNone(schedule.physical_decode_concurrency_claimed)

    def test_cell_budget_fails_closed(self):
        request = base_request()
        request["budget"]["max_cells"] = 2
        entry = admit_entry(request, current_generation=7)
        with self.assertRaisesRegex(Grid10Error, "CELL_BUDGET_EXCEEDED"):
            build_grid10_schedule(
                entry,
                current_generation=7,
                functions=("retrieve", "hypothesis", "critic"),
            )

    def test_model_call_budget_fails_closed(self):
        request = base_request()
        request["budget"]["max_model_calls"] = 1
        entry = admit_entry(request, current_generation=7)
        with self.assertRaisesRegex(Grid10Error, "MODEL_CALL_BUDGET_EXCEEDED"):
            build_grid10_schedule(
                entry,
                current_generation=7,
                functions=("hypothesis", "counterhypothesis"),
            )

    def test_stale_schedule_generation_fails_closed(self):
        entry = admit_entry(base_request(), current_generation=7)
        with self.assertRaisesRegex(Grid10Error, "STALE_ENTITY_GENERATION"):
            build_grid10_schedule(entry, current_generation=8, functions=("retrieve",))


if __name__ == "__main__":
    unittest.main()
