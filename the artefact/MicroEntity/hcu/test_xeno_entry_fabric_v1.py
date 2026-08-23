import unittest

from xeno_entry_fabric_v1 import (
    EntryFabricError,
    admit_entry,
    to_hcu_reactive_event,
)


def base_entry():
    return {
        "schema": "XENO_ENTRY_PACKET/v1",
        "ingress_id": "ingress:test:1",
        "causal_id": "causal:test:1",
        "entity_generation": 7,
        "source_kind": "HUMAN_PROMPT",
        "source_id": "user:test",
        "modality": "TEXT",
        "observed_time": "2026-08-23T23:24:00+07:00",
        "received_time": "2026-08-23T23:24:01+07:00",
        "provenance_ref": "unifieddb:source:test:1",
        "provenance_sha256": "a" * 64,
        "capabilities": ["memory.read", "hcu.route"],
        "capability_binding_sha256": "b" * 64,
        "parent_id": None,
        "stream_id": "stream:test",
        "budget": {
            "max_model_calls": 2,
            "max_tokens": 2048,
            "max_wall_ms": 5000,
        },
        "payload_ref": "unifieddb:payload:test:1",
        "payload_sha256": "c" * 64,
    }


class EntryFabricTests(unittest.TestCase):
    def test_entry_admission_is_deterministic_and_canonical(self):
        a = admit_entry(base_entry(), current_generation=7)
        reversed_entry = dict(reversed(list(base_entry().items())))
        reversed_entry["capabilities"] = list(reversed(reversed_entry["capabilities"]))
        b = admit_entry(reversed_entry, current_generation=7)
        self.assertEqual(a, b)
        self.assertEqual(len(a.admission_sha256), 64)

    def test_stale_generation_fails_closed(self):
        with self.assertRaisesRegex(EntryFabricError, "STALE_ENTITY_GENERATION"):
            admit_entry(base_entry(), current_generation=8)

    def test_unknown_field_cannot_smuggle_effect_or_truth_authority(self):
        e = base_entry()
        e["effect_request"] = {"capability": "host.exec"}
        with self.assertRaisesRegex(EntryFabricError, "ENTRY_UNKNOWN_FIELDS:effect_request"):
            admit_entry(e, current_generation=7)

    def test_provenance_and_payload_hashes_are_mandatory(self):
        e = base_entry()
        e["provenance_sha256"] = "bad"
        with self.assertRaisesRegex(EntryFabricError, "provenance_sha256"):
            admit_entry(e, current_generation=7)

        e = base_entry()
        e["payload_sha256"] = None
        with self.assertRaisesRegex(EntryFabricError, "payload_sha256"):
            admit_entry(e, current_generation=7)

    def test_capability_binding_is_metadata_not_self_granted_freeform(self):
        e = base_entry()
        e["capabilities"] = ["hcu.route", "hcu.route"]
        with self.assertRaisesRegex(EntryFabricError, "DUPLICATE_FORBIDDEN"):
            admit_entry(e, current_generation=7)

        e = base_entry()
        e["capability_binding_sha256"] = "not-a-digest"
        with self.assertRaisesRegex(EntryFabricError, "capability_binding_sha256"):
            admit_entry(e, current_generation=7)

    def test_budget_is_complete_bounded_and_typed(self):
        e = base_entry()
        e["budget"]["max_model_calls"] = -1
        with self.assertRaisesRegex(EntryFabricError, "NONNEGATIVE_INTEGER_REQUIRED"):
            admit_entry(e, current_generation=7)

        e = base_entry()
        del e["budget"]["max_tokens"]
        with self.assertRaisesRegex(EntryFabricError, "ALL_FIELDS_REQUIRED"):
            admit_entry(e, current_generation=7)

    def test_hcu_projection_preserves_causal_entry_identity(self):
        packet = admit_entry(base_entry(), current_generation=7)
        event = to_hcu_reactive_event(
            packet,
            novelty=0.8,
            contradiction=0.2,
            zero_relevance=0.7,
        )
        self.assertEqual(event["schema"], "HCU_REACTIVE_EVENT/v1")
        self.assertEqual(event["ingress_id"], packet.ingress_id)
        self.assertEqual(event["causal_id"], packet.causal_id)
        self.assertEqual(event["entry_admission_sha256"], packet.admission_sha256)
        self.assertEqual(event["entity_generation"], 7)

    def test_hcu_projection_rejects_invalid_signal(self):
        packet = admit_entry(base_entry(), current_generation=7)
        with self.assertRaisesRegex(EntryFabricError, "UNIT_INTERVAL_REQUIRED"):
            to_hcu_reactive_event(packet, novelty=1.1)

    def test_payload_change_changes_admission_identity(self):
        a = admit_entry(base_entry(), current_generation=7)
        e = base_entry()
        e["payload_sha256"] = "d" * 64
        b = admit_entry(e, current_generation=7)
        self.assertNotEqual(a.admission_sha256, b.admission_sha256)


if __name__ == "__main__":
    unittest.main()
