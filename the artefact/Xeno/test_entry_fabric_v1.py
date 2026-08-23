import unittest

from entry_fabric_v1 import EntryAdmissionError, admit_ingress, route_decision_sha256


PAYLOAD_A = "0" * 64
PAYLOAD_B = "1" * 64
POLICY_A = "2" * 64


def packet():
    return {
        "schema": "XENO_INGRESS_PACKET/v1",
        "ingress_id": "ing-001",
        "causal_id": "cause-001",
        "entity_generation": 7,
        "source": "human",
        "provenance": {"kind": "direct_user_input", "subject": "canonical_user"},
        "modality": "text",
        "observed_at": "2026-08-23T23:24:00+07:00",
        "received_at": "2026-08-23T23:24:01+07:00",
        "permissions": ["read_state"],
        "capability_scope": ["cognition.request"],
        "resource_budget": {"logical_cells": 10, "latency_ms": 5000},
        "payload_ref": "unifieddb://ingress/ing-001",
        "payload_sha256": PAYLOAD_A,
    }


class EntryFabricTests(unittest.TestCase):
    def test_same_packet_is_deterministic(self):
        a = admit_ingress(packet(), current_generation=7)
        b = admit_ingress(packet(), current_generation=7)
        self.assertEqual(a, b)

    def test_transport_replay_keeps_event_identity_but_changes_admission_identity(self):
        a = admit_ingress(packet(), current_generation=7)
        replay = packet()
        replay["ingress_id"] = "ing-002"
        replay["received_at"] = "2026-08-23T23:25:01+07:00"
        replay["payload_ref"] = "unifieddb://ingress/ing-002"
        b = admit_ingress(replay, current_generation=7)
        self.assertEqual(a.event_sha256, b.event_sha256)
        self.assertNotEqual(a.admission_sha256, b.admission_sha256)

    def test_payload_content_change_changes_event_identity(self):
        a = admit_ingress(packet(), current_generation=7)
        changed = packet()
        changed["payload_sha256"] = PAYLOAD_B
        b = admit_ingress(changed, current_generation=7)
        self.assertNotEqual(a.event_sha256, b.event_sha256)

    def test_stale_generation_fails_closed(self):
        with self.assertRaisesRegex(EntryAdmissionError, "STALE_ENTITY_GENERATION"):
            admit_ingress(packet(), current_generation=8)

    def test_payload_digest_is_required(self):
        missing = packet()
        del missing["payload_sha256"]
        with self.assertRaisesRegex(EntryAdmissionError, "payload_sha256:NONEMPTY_STRING_REQUIRED"):
            admit_ingress(missing, current_generation=7)

    def test_permission_order_does_not_change_admission_identity(self):
        first = packet()
        first["permissions"] = ["read_state", "read_graph"]
        second = packet()
        second["permissions"] = ["read_graph", "read_state", "read_graph"]
        a = admit_ingress(first, current_generation=7)
        b = admit_ingress(second, current_generation=7)
        self.assertEqual(a.admission_sha256, b.admission_sha256)

    def test_route_binding_separates_different_events_with_same_result(self):
        result = {"model_lanes": ["critic", "world"], "zero_projection": True}
        a = route_decision_sha256(
            event_sha256="3" * 64,
            route_policy_sha256=POLICY_A,
            requested_engine_identity="hcu.local_08b",
            resolved_engine_identity="hcu.local_08b",
            resolved_engine_class="HCU_LOCAL_SHARED_WEIGHT",
            route_result=result,
        )
        b = route_decision_sha256(
            event_sha256="4" * 64,
            route_policy_sha256=POLICY_A,
            requested_engine_identity="hcu.local_08b",
            resolved_engine_identity="hcu.local_08b",
            resolved_engine_class="HCU_LOCAL_SHARED_WEIGHT",
            route_result=result,
        )
        self.assertNotEqual(a, b)

    def test_route_binding_separates_different_engines_with_same_event_and_result(self):
        result = {"model_lanes": ["critic", "world"], "zero_projection": True}
        a = route_decision_sha256(
            event_sha256="3" * 64,
            route_policy_sha256=POLICY_A,
            requested_engine_identity="hcu.local_08b",
            resolved_engine_identity="hcu.local_08b",
            resolved_engine_class="HCU_LOCAL_SHARED_WEIGHT",
            route_result=result,
        )
        b = route_decision_sha256(
            event_sha256="3" * 64,
            route_policy_sha256=POLICY_A,
            requested_engine_identity="hcu.local_alt",
            resolved_engine_identity="hcu.local_alt",
            resolved_engine_class="HCU_LOCAL_SHARED_WEIGHT",
            route_result=result,
        )
        self.assertNotEqual(a, b)

    def test_route_binding_replay_is_deterministic(self):
        kwargs = dict(
            event_sha256="3" * 64,
            route_policy_sha256=POLICY_A,
            requested_engine_identity="hcu.local_08b",
            resolved_engine_identity="hcu.local_08b",
            resolved_engine_class="HCU_LOCAL_SHARED_WEIGHT",
            route_result={"model_lanes": ["critic", "world"], "zero_projection": True},
        )
        self.assertEqual(route_decision_sha256(**kwargs), route_decision_sha256(**kwargs))


if __name__ == "__main__":
    unittest.main()
