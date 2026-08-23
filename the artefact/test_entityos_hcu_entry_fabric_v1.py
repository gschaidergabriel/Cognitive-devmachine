import unittest

from entityos_hcu_entry_fabric_v1 import EntryAdmissionError, admit_event


def base_event():
    return {
        "schema": "ENTITYOS_ENTRY_EVENT/v1",
        "causal_id": "causal:test:1",
        "entity_generation": 7,
        "source": "human_prompt",
        "provenance": {"origin": "test", "receipt": "r1"},
        "modality": "text",
        "observed_at": "2026-08-23T15:00:00Z",
        "received_at": "2026-08-23T15:00:01Z",
        "permissions": ["read_state"],
        "capability_scope": [],
        "parent_or_stream_id": None,
        "resource_budget": {
            "max_logical_cells": 10,
            "max_inference_calls": 10,
            "max_wall_ms": 30000,
            "max_payload_bytes": 4096,
        },
        "payload": {"text": "hello"},
    }


class EntityOSEntryFabricTests(unittest.TestCase):
    def test_exact_replay_is_deterministic(self):
        event = base_event()
        a = admit_event(event, current_generation=7)
        b = admit_event(event, current_generation=7)
        self.assertEqual(a, b)
        self.assertTrue(a.ingress_id.startswith("ingress:"))
        self.assertEqual(a.authority_status, "CARRIED_NOT_GRANTED")

    def test_stale_generation_fails_closed(self):
        with self.assertRaisesRegex(EntryAdmissionError, "STALE_ENTITY_GENERATION"):
            admit_event(base_event(), current_generation=8)

    def test_unknown_semantic_field_fails_closed(self):
        event = base_event()
        event["silent_authority"] = "grant"
        with self.assertRaisesRegex(EntryAdmissionError, "UNKNOWN_INGRESS_FIELD"):
            admit_event(event, current_generation=7)

    def test_source_and_modality_use_positive_admission_sets(self):
        event = base_event()
        event["source"] = "mystery_source"
        with self.assertRaisesRegex(EntryAdmissionError, "SOURCE_NOT_ADMITTED"):
            admit_event(event, current_generation=7)
        event = base_event()
        event["modality"] = "telepathy"
        with self.assertRaisesRegex(EntryAdmissionError, "MODALITY_NOT_ADMITTED"):
            admit_event(event, current_generation=7)

    def test_grid10_budget_fails_closed_above_ten_cells(self):
        event = base_event()
        event["resource_budget"]["max_logical_cells"] = 11
        with self.assertRaisesRegex(EntryAdmissionError, "GRID10_LIMIT"):
            admit_event(event, current_generation=7)

    def test_payload_cannot_exceed_bound_budget(self):
        event = base_event()
        event["resource_budget"]["max_payload_bytes"] = 2
        with self.assertRaisesRegex(EntryAdmissionError, "PAYLOAD_EXCEEDS_BOUND_BUDGET"):
            admit_event(event, current_generation=7)

    def test_claim_order_and_duplicates_do_not_change_admission_identity(self):
        a = base_event()
        a["permissions"] = ["read_state", "candidate", "read_state"]
        b = base_event()
        b["permissions"] = ["candidate", "read_state"]
        self.assertEqual(admit_event(a, current_generation=7), admit_event(b, current_generation=7))

    def test_budget_change_keeps_event_identity_but_changes_ingress_identity(self):
        a = base_event()
        b = base_event()
        b["resource_budget"]["max_wall_ms"] = 10000
        pa = admit_event(a, current_generation=7)
        pb = admit_event(b, current_generation=7)
        self.assertEqual(pa.event_sha256, pb.event_sha256)
        self.assertNotEqual(pa.ingress_id, pb.ingress_id)

    def test_semantic_alias_causal_collision_discriminator(self):
        """GO unusual experiment spec: route-equivalent events must not alias causally."""
        a = base_event()
        b = base_event()
        a["payload"] = {"novelty": 0.80, "zero_relevance": 0.80}
        b["payload"] = {"novelty": 0.90, "zero_relevance": 0.80}
        pa = admit_event(a, current_generation=7)
        pb = admit_event(b, current_generation=7)
        self.assertNotEqual(pa.event_sha256, pb.event_sha256)
        self.assertNotEqual(pa.ingress_id, pb.ingress_id)


if __name__ == "__main__":
    unittest.main()
