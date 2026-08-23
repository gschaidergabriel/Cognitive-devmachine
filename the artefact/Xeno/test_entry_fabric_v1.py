import copy
import unittest

from entry_fabric_v1 import (
    IngressAdmissionError,
    TrustedCapabilitySnapshot,
    admit_ingress,
)


PAYLOAD_A = "a" * 64
PAYLOAD_B = "b" * 64
AUTH_A = "1" * 64
AUTH_B = "2" * 64


def trusted(*, permissions=("state.read",), capabilities=(), binding=AUTH_A):
    return TrustedCapabilitySnapshot(
        permissions=tuple(permissions),
        capability_scope=tuple(capabilities),
        authority_binding_sha256=binding,
    )


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


def admit(raw=None, *, generation=7, snapshot=None):
    return admit_ingress(
        base_ingress() if raw is None else raw,
        current_generation=generation,
        trusted_capability_snapshot=trusted() if snapshot is None else snapshot,
    )


class EntryFabricTests(unittest.TestCase):
    def test_same_exact_input_is_deterministic(self):
        a = admit()
        b = admit(copy.deepcopy(base_ingress()))
        self.assertEqual(a, b)

    def test_stale_generation_fails_closed(self):
        with self.assertRaisesRegex(IngressAdmissionError, "STALE_ENTITY_GENERATION"):
            admit(generation=8)

    def test_unknown_source_fails_closed(self):
        raw = base_ingress(); raw["source"] = "mystery"
        with self.assertRaisesRegex(IngressAdmissionError, "SOURCE_CLASS_UNSUPPORTED"):
            admit(raw)

    def test_payload_digest_changes_event_and_admission_identity(self):
        a = admit()
        raw = base_ingress(); raw["payload_sha256"] = PAYLOAD_B
        b = admit(raw)
        self.assertNotEqual(a.event_sha256, b.event_sha256)
        self.assertNotEqual(a.admission_sha256, b.admission_sha256)

    def test_replay_transport_change_preserves_event_but_changes_admission(self):
        a = admit()
        raw = base_ingress()
        raw["received_at_ns"] = 999
        raw["payload_ref"] = "cache-copy:event:1"
        b = admit(raw)
        self.assertEqual(a.event_sha256, b.event_sha256)
        self.assertNotEqual(a.admission_sha256, b.admission_sha256)
        self.assertNotEqual(a.ingress_id, b.ingress_id)

    def test_budget_change_preserves_event_but_changes_admission(self):
        a = admit()
        raw = base_ingress(); raw["resource_budget"]["max_model_calls"] = 3
        b = admit(raw)
        self.assertEqual(a.event_sha256, b.event_sha256)
        self.assertNotEqual(a.admission_sha256, b.admission_sha256)

    def test_untrusted_permission_self_grant_is_rejected(self):
        raw = base_ingress(); raw["permissions"] = ["state.read", "effect.request"]
        with self.assertRaisesRegex(IngressAdmissionError, "PERMISSION_AUTHORITY_MISMATCH"):
            admit(raw)

    def test_untrusted_capability_self_grant_is_rejected(self):
        raw = base_ingress(); raw["capability_scope"] = ["entityos.exec"]
        with self.assertRaisesRegex(IngressAdmissionError, "CAPABILITY_AUTHORITY_MISMATCH"):
            admit(raw)

    def test_authority_binding_is_admission_not_event_identity(self):
        a = admit()
        b = admit(snapshot=trusted(binding=AUTH_B))
        self.assertEqual(a.event_sha256, b.event_sha256)
        self.assertNotEqual(a.admission_sha256, b.admission_sha256)

    def test_trusted_snapshot_is_required(self):
        with self.assertRaisesRegex(IngressAdmissionError, "TRUSTED_CAPABILITY_SNAPSHOT_REQUIRED"):
            admit_ingress(base_ingress(), current_generation=7, trusted_capability_snapshot=None)

    def test_supplied_event_identity_must_match(self):
        raw = base_ingress(); raw["event_sha256"] = "0" * 64
        with self.assertRaisesRegex(IngressAdmissionError, "EVENT_SHA256_MISMATCH"):
            admit(raw)

    def test_supplied_admission_identity_must_match(self):
        raw = base_ingress(); raw["admission_sha256"] = "0" * 64
        with self.assertRaisesRegex(IngressAdmissionError, "ADMISSION_SHA256_MISMATCH"):
            admit(raw)

    def test_supplied_ingress_id_is_compatibility_alias_for_admission(self):
        packet = admit()
        raw = base_ingress(); raw["ingress_id"] = packet.admission_sha256
        replay = admit(raw)
        self.assertEqual(replay.ingress_id, packet.admission_sha256)

    def test_unknown_top_level_field_fails_closed(self):
        raw = base_ingress(); raw["semantic_truth"] = True
        with self.assertRaisesRegex(IngressAdmissionError, "INGRESS_KEYSET_INVALID"):
            admit(raw)

    def test_scale_ceiling_is_not_silently_exceeded(self):
        raw = base_ingress(); raw["resource_budget"]["max_logical_cells"] = 601
        with self.assertRaisesRegex(IngressAdmissionError, "ABOVE_CURRENT_RESEARCH_CEILING"):
            admit(raw)


if __name__ == "__main__":
    unittest.main()
