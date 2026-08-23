import unittest

from typed_entry_canonical_v1 import (
    CANONICALIZATION_SCHEMA,
    CanonicalEncodingError,
    encode_canonical,
)
from xeno_entry_fabric_v1 import admit_entry, to_hcu_reactive_event
from reactive_event_router_v1 import route_event


CAPABILITY_BINDING_SHA256 = "b" * 64
ADMITTED_CAPABILITIES = ("memory.read", "hcu.route")
ADMITTED_BUDGET = {"max_model_calls": 4, "max_tokens": 4096, "max_wall_ms": 10000}


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
        "budget": {"max_model_calls": 2, "max_tokens": 2048, "max_wall_ms": 5000},
        "payload_ref": "unifieddb:payload:test:1",
        "payload_sha256": "c" * 64,
    }


def admit(entry):
    return admit_entry(
        entry,
        current_generation=7,
        expected_capability_binding_sha256=CAPABILITY_BINDING_SHA256,
        admitted_capabilities=ADMITTED_CAPABILITIES,
        admitted_budget=ADMITTED_BUDGET,
    )


class TypedEntryCanonicalTests(unittest.TestCase):
    def test_adapter_now_emits_main_selected_jcs_vectors(self):
        vectors = [
            (None, b"null"),
            (False, b"false"),
            (True, b"true"),
            (0, b"0"),
            (24, b"24"),
            (-1, b"-1"),
            ("a", b'"a"'),
            ([1, 2, 3], b"[1,2,3]"),
            ({"b": 2, "a": 1}, b'{"a":1,"b":2}'),
        ]
        self.assertEqual(CANONICALIZATION_SCHEMA, "RFC8785_JCS_IJSON/v1")
        for value, expected in vectors:
            self.assertEqual(encode_canonical(value), expected)

    def test_map_order_is_deterministic(self):
        a = {"z": 1, "aa": 2, "a": 3}
        b = {"a": 3, "aa": 2, "z": 1}
        self.assertEqual(encode_canonical(a), encode_canonical(b))

    def test_binary64_domain_and_precision_loss_fail_closed(self):
        self.assertEqual(encode_canonical(0.5), b"0.5")
        self.assertEqual(encode_canonical(9_007_199_254_740_992), b"9007199254740992")
        with self.assertRaisesRegex(CanonicalEncodingError, "INTEGER_NOT_EXACT_BINARY64"):
            encode_canonical(9_007_199_254_740_993)

    def test_transport_replay_preserves_causal_event_and_route_identity(self):
        first = admit(base_entry())
        replay = base_entry()
        replay["ingress_id"] = "ingress:test:2"
        replay["received_time"] = "2026-08-23T23:29:01+07:00"
        second = admit(replay)
        self.assertEqual(first.event_sha256, second.event_sha256)
        self.assertNotEqual(first.admission_sha256, second.admission_sha256)

        first_event = to_hcu_reactive_event(first, novelty=0.1)
        second_event = to_hcu_reactive_event(second, novelty=0.1)
        self.assertEqual(first_event["entry_event_sha256"], second_event["entry_event_sha256"])
        self.assertNotEqual(first_event["entry_admission_sha256"], second_event["entry_admission_sha256"])
        self.assertEqual(first_event["entry_canonicalization_schema"], CANONICALIZATION_SCHEMA)
        self.assertEqual(second_event["entry_canonicalization_schema"], CANONICALIZATION_SCHEMA)

        admitted_bindings = {
            first.admission_sha256: first.event_sha256,
            second.admission_sha256: second.event_sha256,
        }
        first_route = route_event(
            first_event,
            current_generation=7,
            admitted_entry_bindings=admitted_bindings,
        )
        second_route = route_event(
            second_event,
            current_generation=7,
            admitted_entry_bindings=admitted_bindings,
        )
        self.assertEqual(first_route.event_sha256, second_route.event_sha256)
        self.assertEqual(first_route.decision_sha256, second_route.decision_sha256)
        self.assertNotEqual(first_route.entry_admission_sha256, second_route.entry_admission_sha256)

    def test_equivalent_observed_timestamp_offsets_canonicalize_to_same_event(self):
        first = admit(base_entry())
        same_instant = base_entry()
        same_instant["observed_time"] = "2026-08-23T16:24:00Z"
        second = admit(same_instant)
        self.assertEqual(first.observed_time, "2026-08-23T16:24:00.000000Z")
        self.assertEqual(first.event_sha256, second.event_sha256)

    def test_payload_change_changes_causal_event_identity(self):
        first = admit(base_entry())
        changed = base_entry()
        changed["payload_sha256"] = "d" * 64
        second = admit(changed)
        self.assertNotEqual(first.event_sha256, second.event_sha256)


if __name__ == "__main__":
    unittest.main()
