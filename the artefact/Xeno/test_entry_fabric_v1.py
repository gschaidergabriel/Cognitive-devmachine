import unittest

from entry_fabric_v1 import IngressAdmissionError, admit_ingress


PAYLOAD_A = "a" * 64
PAYLOAD_B = "b" * 64


def base_ingress():
    return {
        "schema": "XENO_INGRESS_PACKET/v1",
        "causal_id": "cause-7",
        "entity_generation": 7,
        "source": "intrinsic_system_event",
        "provenance": {"kind": "test", "ref": "event-1"},
        "modality": "json",
        "observed_at_ns": 100,
        "received_at_ns": 110,
        "permissions": ["state.read"],
        "capability_scope": [],
        "resource_budget": {
            "max_wall_ms": 1000,
            "max_model_calls": 4,
            "max_context_tokens": 4096,
            "max_logical_cells": 10,
        },
        "payload_ref": "unifieddb:event:1",
        "payload_sha256": PAYLOAD_A,
    }


class EntryFabricTests(unittest.TestCase):
    def test_same_exact_input_is_deterministic(self):
        a = admit_ingress(base_ingress(), current_generation=7)
        b = admit_ingress(base_ingress(), current_generation=7)
        self.assertEqual(a, b)

    def test_stale_generation_fails_closed(self):
        with self.assertRaisesRegex(IngressAdmissionError, "STALE_ENTITY_GENERATION"):
            admit_ingress(base_ingress(), current_generation=8)

    def test_unknown_source_fails_closed(self):
        raw = base_ingress(); raw["source"] = "mystery"
        with self.assertRaisesRegex(IngressAdmissionError, "SOURCE_CLASS_UNSUPPORTED"):
            admit_ingress(raw, current_generation=7)

    def test_payload_digest_is_part_of_ingress_identity(self):
        a = base_ingress()
        b = base_ingress(); b["payload_sha256"] = PAYLOAD_B
        self.assertNotEqual(
            admit_ingress(a, current_generation=7).ingress_id,
            admit_ingress(b, current_generation=7).ingress_id,
        )

    def test_supplied_ingress_id_must_match_recomputed_identity(self):
        raw = base_ingress(); raw["ingress_id"] = "0" * 64
        with self.assertRaisesRegex(IngressAdmissionError, "INGRESS_ID_MISMATCH"):
            admit_ingress(raw, current_generation=7)

    def test_unknown_top_level_field_fails_closed(self):
        raw = base_ingress(); raw["semantic_truth"] = True
        with self.assertRaisesRegex(IngressAdmissionError, "INGRESS_KEYSET_INVALID"):
            admit_ingress(raw, current_generation=7)

    def test_scale_ceiling_is_not_silently_exceeded(self):
        raw = base_ingress(); raw["resource_budget"]["max_logical_cells"] = 601
        with self.assertRaisesRegex(IngressAdmissionError, "ABOVE_CURRENT_RESEARCH_CEILING"):
            admit_ingress(raw, current_generation=7)


if __name__ == "__main__":
    unittest.main()
