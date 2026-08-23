import unittest

from entry_fabric_v1 import EntryAdmissionError, bind_entry


def base_entry():
    return {
        "schema": "ENTITYOS_ENTRY/v1",
        "event_id": "evt-001",
        "source": "urn:entityos:test",
        "event_type": "human.prompt",
        "causal_id": "cause-001",
        "entity_generation": 7,
        "modality": "text",
        "observed_at": "2026-08-23T15:00:00Z",
        "received_at": "2026-08-23T15:00:00+00:00",
        "capability_scope": ["state.read", "cognition.request", "state.read"],
        "budget": {"max_cells": 10, "max_tokens": 2048, "max_ms": 4000},
        "payload_ref": "unifieddb://entry/evt-001",
        "payload_sha256": "a" * 64,
        "provenance_sha256": "b" * 64,
        "parent_id": None,
        "stream_id": "session-1",
    }


class EntryFabricTests(unittest.TestCase):
    def test_same_semantics_are_deterministic_and_normalized(self):
        a = base_entry()
        b = base_entry()
        b["capability_scope"] = ["cognition.request", "state.read"]
        b["observed_at"] = "2026-08-23T17:00:00+02:00"
        pa = bind_entry(a, current_generation=7)
        pb = bind_entry(b, current_generation=7)
        self.assertEqual(pa.entry_sha256, pb.entry_sha256)
        self.assertEqual(pa.capability_scope, ("cognition.request", "state.read"))
        self.assertEqual(pa.observed_at, "2026-08-23T15:00:00Z")

    def test_distinct_event_identity_changes_packet_identity(self):
        a = base_entry()
        b = base_entry()
        b["event_id"] = "evt-002"
        self.assertNotEqual(
            bind_entry(a, current_generation=7).entry_sha256,
            bind_entry(b, current_generation=7).entry_sha256,
        )

    def test_distinct_payload_digest_changes_packet_identity(self):
        a = base_entry()
        b = base_entry()
        b["payload_sha256"] = "c" * 64
        self.assertNotEqual(
            bind_entry(a, current_generation=7).entry_sha256,
            bind_entry(b, current_generation=7).entry_sha256,
        )

    def test_stale_generation_fails_closed(self):
        with self.assertRaisesRegex(EntryAdmissionError, "STALE_ENTITY_GENERATION"):
            bind_entry(base_entry(), current_generation=8)

    def test_unknown_budget_key_fails_closed(self):
        e = base_entry()
        e["budget"]["gpu_seconds"] = 1
        with self.assertRaisesRegex(EntryAdmissionError, "budget:UNKNOWN_KEY"):
            bind_entry(e, current_generation=7)

    def test_invalid_digest_fails_closed(self):
        e = base_entry()
        e["provenance_sha256"] = "not-a-digest"
        with self.assertRaisesRegex(EntryAdmissionError, "provenance_sha256:HEX_FORMAT_INVALID"):
            bind_entry(e, current_generation=7)

    def test_partial_trace_context_fails_closed(self):
        e = base_entry()
        e["trace_id"] = "1" * 32
        with self.assertRaisesRegex(EntryAdmissionError, "TRACE_CONTEXT_PARTIAL"):
            bind_entry(e, current_generation=7)

    def test_valid_trace_context_is_bound(self):
        e = base_entry()
        e["trace_id"] = "1" * 32
        e["parent_span_id"] = "2" * 16
        p = bind_entry(e, current_generation=7)
        self.assertEqual(p.trace_id, "1" * 32)
        self.assertEqual(p.parent_span_id, "2" * 16)

    def test_boolean_generation_is_rejected(self):
        e = base_entry()
        e["entity_generation"] = True
        with self.assertRaisesRegex(EntryAdmissionError, "ENTITY_GENERATION_INVALID"):
            bind_entry(e, current_generation=1)


if __name__ == "__main__":
    unittest.main()
