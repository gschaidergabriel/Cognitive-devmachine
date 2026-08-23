import hashlib
import unittest

from entry_fabric_v1 import IngressAdmissionError, admit_ingress

ALLOWED_SOURCES = ("human",)
ALLOWED_SOURCE_REFS = ("user:andreas",)
ALLOWED_PERMISSIONS = ("state.read",)
ALLOWED = ("state.read", "hcu.route")
MAX_BUDGET = {"logical_cells": 10, "model_tokens": 4096, "compute_ms": 5000}


def packet():
    payload = b"hello xeno"
    return {
        "schema": "XENO_INGRESS_PACKET/v1",
        "ingress_id": "ingress-001",
        "causal_id": "causal-001",
        "generation": 7,
        "source": "human",
        "source_ref": "user:andreas",
        "provenance": ["ui:websocket", "auth:verified"],
        "modality": "text",
        "observed_at": "2026-08-23T23:24:00+07:00",
        "received_at": "2026-08-23T16:24:00Z",
        "permissions": ["state.read"],
        "capability_scope": ["hcu.route"],
        "parent_or_stream_id": None,
        "resource_budget": {"logical_cells": 10, "model_tokens": 2048, "compute_ms": 1000},
        "payload_ref": "mem://turn/current/prompt",
        "payload_sha256": hashlib.sha256(payload).hexdigest(),
    }


class EntryFabricTests(unittest.TestCase):
    def admit(self, value=None):
        return admit_ingress(
            packet() if value is None else value,
            current_generation=7,
            allowed_sources=ALLOWED_SOURCES,
            allowed_source_refs=ALLOWED_SOURCE_REFS,
            allowed_permissions=ALLOWED_PERMISSIONS,
            allowed_capabilities=ALLOWED,
            max_budget=MAX_BUDGET,
        )

    def test_exact_packet_admits_and_binds_causal_identity(self):
        out = self.admit()
        self.assertEqual(len(out.ingress_sha256), 64)
        self.assertEqual(out.causal_binding()["ingress_sha256"], out.ingress_sha256)
        self.assertEqual(out.generation, 7)

    def test_mapping_and_set_order_do_not_change_ingress_identity(self):
        a = packet()
        b = dict(reversed(list(a.items())))
        b["provenance"] = list(reversed(a["provenance"]))
        b["permissions"] = list(reversed(a["permissions"]))
        self.assertEqual(self.admit(a), self.admit(b))

    def test_timezone_equivalent_timestamps_canonicalize_identically(self):
        a = packet()
        b = packet(); b["observed_at"] = "2026-08-23T16:24:00Z"
        self.assertEqual(self.admit(a), self.admit(b))

    def test_payload_change_changes_ingress_identity(self):
        a = packet()
        b = packet(); b["payload_sha256"] = hashlib.sha256(b"different").hexdigest()
        self.assertNotEqual(self.admit(a).ingress_sha256, self.admit(b).ingress_sha256)

    def test_causal_id_change_changes_ingress_identity(self):
        a = packet()
        b = packet(); b["causal_id"] = "causal-002"
        self.assertNotEqual(self.admit(a).ingress_sha256, self.admit(b).ingress_sha256)

    def test_stale_generation_fails_closed(self):
        with self.assertRaisesRegex(IngressAdmissionError, "STALE_GENERATION"):
            admit_ingress(
                packet(),
                current_generation=8,
                allowed_sources=ALLOWED_SOURCES,
                allowed_source_refs=ALLOWED_SOURCE_REFS,
                allowed_permissions=ALLOWED_PERMISSIONS,
                allowed_capabilities=ALLOWED,
                max_budget=MAX_BUDGET,
            )

    def test_source_class_spoof_fails_closed(self):
        p = packet(); p["source"] = "tool"
        with self.assertRaisesRegex(IngressAdmissionError, "SOURCE_NOT_ADMITTED"):
            self.admit(p)

    def test_source_identity_spoof_fails_closed(self):
        p = packet(); p["source_ref"] = "user:mallory"
        with self.assertRaisesRegex(IngressAdmissionError, "SOURCE_REF_NOT_ADMITTED"):
            self.admit(p)

    def test_permission_escalation_fails_closed(self):
        p = packet(); p["permissions"] = ["state.write"]
        with self.assertRaisesRegex(IngressAdmissionError, "PERMISSIONS_NOT_ADMITTED"):
            self.admit(p)

    def test_capability_escalation_fails_closed(self):
        p = packet(); p["capability_scope"] = ["effect.exec"]
        with self.assertRaisesRegex(IngressAdmissionError, "CAPABILITY_SCOPE_NOT_ADMITTED"):
            self.admit(p)

    def test_budget_escalation_fails_closed(self):
        p = packet(); p["resource_budget"]["logical_cells"] = 11
        with self.assertRaisesRegex(IngressAdmissionError, "POLICY_LIMIT_EXCEEDED"):
            self.admit(p)

    def test_malformed_budget_policy_fails_closed_even_if_dimension_unused(self):
        with self.assertRaisesRegex(IngressAdmissionError, "policy.max_budget.bad:INVALID"):
            admit_ingress(
                packet(),
                current_generation=7,
                allowed_sources=ALLOWED_SOURCES,
                allowed_source_refs=ALLOWED_SOURCE_REFS,
                allowed_permissions=ALLOWED_PERMISSIONS,
                allowed_capabilities=ALLOWED,
                max_budget={**MAX_BUDGET, "bad": True},
            )

    def test_invalid_budget_policy_key_fails_closed(self):
        with self.assertRaisesRegex(IngressAdmissionError, "IDENTIFIER_INVALID"):
            admit_ingress(
                packet(),
                current_generation=7,
                allowed_sources=ALLOWED_SOURCES,
                allowed_source_refs=ALLOWED_SOURCE_REFS,
                allowed_permissions=ALLOWED_PERMISSIONS,
                allowed_capabilities=ALLOWED,
                max_budget={**MAX_BUDGET, "bad key": 1},
            )

    def test_unknown_budget_dimension_fails_closed(self):
        p = packet(); p["resource_budget"]["gpu_count"] = 1
        with self.assertRaisesRegex(IngressAdmissionError, "UNKNOWN_DIMENSION"):
            self.admit(p)

    def test_unknown_top_level_field_fails_closed(self):
        p = packet(); p["truth"] = True
        with self.assertRaisesRegex(IngressAdmissionError, "UNKNOWN_TOP_LEVEL_FIELD"):
            self.admit(p)

    def test_invalid_payload_digest_fails_closed(self):
        p = packet(); p["payload_sha256"] = "abc"
        with self.assertRaisesRegex(IngressAdmissionError, "SHA256_REQUIRED"):
            self.admit(p)

    def test_naive_timestamp_fails_closed(self):
        p = packet(); p["received_at"] = "2026-08-23T16:24:00"
        with self.assertRaisesRegex(IngressAdmissionError, "TIMEZONE_REQUIRED"):
            self.admit(p)


if __name__ == "__main__":
    unittest.main()
