import copy
import unittest

from entry_fabric_v1 import EntryAdmissionError, admit_entry


def base_event():
    return {
        "schema": "XENO_ENTRY_PACKET/v1",
        "ingress_id": "ing-001",
        "causal_id": "causal-001",
        "entity_generation": 7,
        "source_kind": "HUMAN_PROMPT",
        "modality": "TEXT",
        "observed_at": "2026-08-23T16:00:00Z",
        "received_at": "2026-08-23T16:00:01Z",
        "provenance_ref": "user:canonical-owner",
        "permission_scope": ["read:state"],
        "compute_budget": {
            "max_wall_ms": 5000,
            "max_model_tokens": 2048,
            "max_logical_cells": 10,
        },
        "payload_ref": "staging://prompt/ing-001",
        "payload_sha256": "0" * 64,
        "payload_size": 128,
        "mode_hint": "XENO_GRID10",
    }


class EntryFabricTests(unittest.TestCase):
    def test_valid_packet_binds_current_generation(self):
        packet = admit_entry(base_event(), current_generation=7)
        self.assertEqual(packet.schema, "XENO_ENTRY_PACKET/v1")
        self.assertEqual(packet.entity_generation, 7)
        self.assertEqual(packet.mode_hint, "XENO_GRID10")
        self.assertEqual(len(packet.packet_sha256), 64)

    def test_stale_generation_fails_closed(self):
        with self.assertRaisesRegex(EntryAdmissionError, "STALE_ENTITY_GENERATION"):
            admit_entry(base_event(), current_generation=8)

    def test_unknown_control_field_fails_closed(self):
        event = base_event()
        event["raw_payload"] = "must-not-enter-control-packet"
        with self.assertRaisesRegex(EntryAdmissionError, "ENTRY_UNKNOWN_FIELDS"):
            admit_entry(event, current_generation=7)

    def test_unsupported_source_kind_fails_closed(self):
        event = base_event()
        event["source_kind"] = "UNBOUNDED_MAGIC_SOURCE"
        with self.assertRaisesRegex(EntryAdmissionError, "SOURCE_KIND_UNSUPPORTED"):
            admit_entry(event, current_generation=7)

    def test_unknown_mode_fails_closed(self):
        event = base_event()
        event["mode_hint"] = "XENO_UNMEASURED_600_FULL_DECODES"
        with self.assertRaisesRegex(EntryAdmissionError, "MODE_HINT_UNSUPPORTED"):
            admit_entry(event, current_generation=7)

    def test_invalid_payload_digest_fails_closed(self):
        event = base_event()
        event["payload_sha256"] = "not-a-digest"
        with self.assertRaisesRegex(EntryAdmissionError, "PAYLOAD_SHA256_INVALID"):
            admit_entry(event, current_generation=7)

    def test_invalid_budget_fails_closed(self):
        event = base_event()
        event["compute_budget"]["max_logical_cells"] = 0
        with self.assertRaisesRegex(EntryAdmissionError, "max_logical_cells:OUT_OF_RANGE"):
            admit_entry(event, current_generation=7)

    def test_permission_order_does_not_change_identity(self):
        a = base_event()
        a["permission_scope"] = ["read:state", "read:graph"]
        b = copy.deepcopy(a)
        b["permission_scope"] = ["read:graph", "read:state", "read:graph"]
        pa = admit_entry(a, current_generation=7)
        pb = admit_entry(b, current_generation=7)
        self.assertEqual(pa.packet_sha256, pb.packet_sha256)

    def test_exact_replay_is_deterministic(self):
        event = base_event()
        a = admit_entry(event, current_generation=7)
        b = admit_entry(copy.deepcopy(event), current_generation=7)
        self.assertEqual(a, b)

    def test_causal_entry_alias_falsifier(self):
        """Unusual discriminator: materially different payload identity must not alias."""
        a = base_event()
        b = copy.deepcopy(a)
        b["payload_sha256"] = "1" * 64
        pa = admit_entry(a, current_generation=7)
        pb = admit_entry(b, current_generation=7)
        self.assertNotEqual(pa.packet_sha256, pb.packet_sha256)


if __name__ == "__main__":
    unittest.main()
