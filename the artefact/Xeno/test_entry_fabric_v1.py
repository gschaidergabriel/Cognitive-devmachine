import copy
import hashlib
import json
import unittest

from entry_fabric_v1 import EntryAdmissionError, PACKET_SCHEMA, admit_ingress, packet_json


def _payload(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest(), len(raw)


def base_request(payload=None):
    payload = {"event": "hello"} if payload is None else payload
    digest, size = _payload(payload)
    return {
        "schema": "XENO_INGRESS_REQUEST/v1",
        "causal_id": "causal:test:1",
        "entity_generation": 7,
        "source": "human_prompt",
        "provenance": ["session:andreas", "turn:1"],
        "modality": "text",
        "observed_at": "2026-08-23T16:00:00+00:00",
        "received_at": "2026-08-23T16:00:00.100000Z",
        "permissions": ["read:canonical"],
        "capability_scope": [],
        "resource_budget": {"max_model_calls": 2, "max_tokens": 2048, "max_wall_ms": 5000},
        "payload_ref": "unifieddb:pending:turn:1",
        "payload_sha256": digest,
        "payload_size_bytes": size,
    }


class EntryFabricTests(unittest.TestCase):
    def test_same_request_has_stable_identity(self):
        a = admit_ingress(base_request(), current_generation=7)
        b = admit_ingress(base_request(), current_generation=7)
        self.assertEqual(a, b)
        self.assertEqual(a.schema, PACKET_SCHEMA)
        self.assertTrue(a.ingress_id.endswith(a.ingress_sha256))

    def test_equivalent_set_order_and_timestamp_offsets_normalize(self):
        a = base_request()
        b = copy.deepcopy(a)
        b["provenance"] = list(reversed(a["provenance"]))
        b["permissions"] = ["read:canonical", "read:canonical"]
        b["observed_at"] = "2026-08-23T18:00:00+02:00"
        self.assertEqual(
            admit_ingress(a, current_generation=7).ingress_sha256,
            admit_ingress(b, current_generation=7).ingress_sha256,
        )

    def test_payload_digest_change_changes_ingress_identity(self):
        a = base_request({"event": "a"})
        b = base_request({"event": "b"})
        pa = admit_ingress(a, current_generation=7)
        pb = admit_ingress(b, current_generation=7)
        self.assertNotEqual(pa.ingress_sha256, pb.ingress_sha256)

    def test_causal_id_change_changes_ingress_identity(self):
        a = base_request()
        b = copy.deepcopy(a)
        b["causal_id"] = "causal:test:2"
        self.assertNotEqual(
            admit_ingress(a, current_generation=7).ingress_sha256,
            admit_ingress(b, current_generation=7).ingress_sha256,
        )

    def test_stale_generation_fails_closed(self):
        with self.assertRaisesRegex(EntryAdmissionError, "STALE_ENTITY_GENERATION"):
            admit_ingress(base_request(), current_generation=8)

    def test_unbound_unknown_field_fails_closed(self):
        request = base_request()
        request["semantic_truth"] = True
        with self.assertRaisesRegex(EntryAdmissionError, "UNBOUND_FIELDS_FORBIDDEN"):
            admit_ingress(request, current_generation=7)

    def test_invalid_payload_digest_fails_closed(self):
        request = base_request()
        request["payload_sha256"] = "not-a-digest"
        with self.assertRaisesRegex(EntryAdmissionError, "SHA256_HEX_REQUIRED"):
            admit_ingress(request, current_generation=7)

    def test_received_before_observed_fails_closed(self):
        request = base_request()
        request["received_at"] = "2026-08-23T15:59:59Z"
        with self.assertRaisesRegex(EntryAdmissionError, "RECEIVED_BEFORE_OBSERVED"):
            admit_ingress(request, current_generation=7)

    def test_boolean_budget_value_is_not_an_integer(self):
        request = base_request()
        request["resource_budget"]["max_model_calls"] = True
        with self.assertRaisesRegex(EntryAdmissionError, "NONNEGATIVE_INT_REQUIRED"):
            admit_ingress(request, current_generation=7)

    def test_packet_json_is_deterministic(self):
        packet = admit_ingress(base_request(), current_generation=7)
        self.assertEqual(packet_json(packet), packet_json(packet))


if __name__ == "__main__":
    unittest.main()
