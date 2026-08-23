import unittest

from xeno_entry_fabric_v1 import (
    EntryFabricError,
    admit_entry,
    to_hcu_reactive_event,
)


CAPABILITY_BINDING_SHA256 = "b" * 64
ADMITTED_CAPABILITIES = ("memory.read", "hcu.route")


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
        "capability_binding_sha256": CAPABILITY_BINDING_SHA256,
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


def admit(entry, *, current_generation=7, binding=CAPABILITY_BINDING_SHA256, capabilities=ADMITTED_CAPABILITIES):
    return admit_entry(
        entry,
        current_generation=current_generation,
        expected_capability_binding_sha256=binding,
        admitted_capabilities=capabilities,
    )


class EntryFabricTests(unittest.TestCase):
    def test_entry_admission_is_deterministic_and_canonical(self):
        a = admit(base_entry())
        reversed_entry = dict(reversed(list(base_entry().items())))
        reversed_entry["capabilities"] = list(reversed(reversed_entry["capabilities"]))
        b = admit(reversed_entry)
        self.assertEqual(a, b)
        self.assertEqual(len(a.admission_sha256), 64)

    def test_stale_generation_fails_closed(self):
        with self.assertRaisesRegex(EntryFabricError, "STALE_ENTITY_GENERATION"):
            admit(base_entry(), current_generation=8)

    def test_current_generation_authority_must_be_real_nonnegative_integer(self):
        e = base_entry()
        e["entity_generation"] = 1
        with self.assertRaisesRegex(EntryFabricError, "current_generation:NONNEGATIVE_INTEGER_REQUIRED"):
            admit(e, current_generation=True)

        e = base_entry()
        e["entity_generation"] = 0
        with self.assertRaisesRegex(EntryFabricError, "current_generation:NONNEGATIVE_INTEGER_REQUIRED"):
            admit(e, current_generation=False)

        with self.assertRaisesRegex(EntryFabricError, "current_generation:NONNEGATIVE_INTEGER_REQUIRED"):
            admit(base_entry(), current_generation=-1)

    def test_unknown_field_cannot_smuggle_effect_or_truth_authority(self):
        e = base_entry()
        e["effect_request"] = {"capability": "host.exec"}
        with self.assertRaisesRegex(EntryFabricError, "ENTRY_UNKNOWN_FIELDS:effect_request"):
            admit(e)

    def test_provenance_and_payload_hashes_are_mandatory(self):
        e = base_entry()
        e["provenance_sha256"] = "bad"
        with self.assertRaisesRegex(EntryFabricError, "provenance_sha256"):
            admit(e)

        e = base_entry()
        e["payload_sha256"] = None
        with self.assertRaisesRegex(EntryFabricError, "payload_sha256"):
            admit(e)

    def test_capability_binding_must_match_external_authority(self):
        e = base_entry()
        e["capability_binding_sha256"] = "d" * 64
        with self.assertRaisesRegex(EntryFabricError, "CAPABILITY_BINDING_MISMATCH"):
            admit(e)

    def test_entry_cannot_self_grant_capability(self):
        e = base_entry()
        e["capabilities"].append("effect.request")
        with self.assertRaisesRegex(EntryFabricError, "CAPABILITY_NOT_ADMITTED:effect.request"):
            admit(e)

    def test_entry_may_narrow_authorized_capabilities(self):
        e = base_entry()
        e["capabilities"] = ["hcu.route"]
        packet = admit(e)
        self.assertEqual(packet.capabilities, ("hcu.route",))

    def test_capability_lists_and_bindings_are_typed(self):
        e = base_entry()
        e["capabilities"] = ["hcu.route", "hcu.route"]
        with self.assertRaisesRegex(EntryFabricError, "DUPLICATE_FORBIDDEN"):
            admit(e)

        e = base_entry()
        e["capability_binding_sha256"] = "not-a-digest"
        with self.assertRaisesRegex(EntryFabricError, "capability_binding_sha256"):
            admit(e)

        with self.assertRaisesRegex(EntryFabricError, "expected_capability_binding_sha256"):
            admit(base_entry(), binding="not-a-digest")

    def test_budget_is_complete_bounded_and_typed(self):
        e = base_entry()
        e["budget"]["max_model_calls"] = -1
        with self.assertRaisesRegex(EntryFabricError, "NONNEGATIVE_INTEGER_REQUIRED"):
            admit(e)

        e = base_entry()
        del e["budget"]["max_tokens"]
        with self.assertRaisesRegex(EntryFabricError, "ALL_FIELDS_REQUIRED"):
            admit(e)

    def test_hcu_projection_preserves_causal_entry_identity(self):
        packet = admit(base_entry())
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
        packet = admit(base_entry())
        with self.assertRaisesRegex(EntryFabricError, "UNIT_INTERVAL_REQUIRED"):
            to_hcu_reactive_event(packet, novelty=1.1)

    def test_payload_change_changes_admission_identity(self):
        a = admit(base_entry())
        e = base_entry()
        e["payload_sha256"] = "d" * 64
        b = admit(e)
        self.assertNotEqual(a.admission_sha256, b.admission_sha256)


if __name__ == "__main__":
    unittest.main()
