#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import validate_cognitive_fabric_capability_ancestry_v1 as v


def h(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def capability(*, receipt: str = "cap-a", binding: str = "binding-a", profile_hash: str | None = None):
    return {
        "ok": True,
        "schema": v.CAPABILITY_SCHEMA,
        "binding_digest": h(binding),
        "capability_receipt_digest": h(receipt),
        "target_engine_class": "ADAPTIVE_BACKEND",
        "jspace_mode": "COMPILED_EXTERNAL",
        "profile_id": "default",
        "profile_hash": profile_hash or h("profile"),
    }


def admission(cap: dict):
    receipt = {
        "schema": v.ADMISSION_SCHEMA,
        "generation": 7,
        "profile_id": cap["profile_id"],
        "profile_hash": cap["profile_hash"],
        "capability_binding_digest": cap["binding_digest"],
        "capability_receipt_digest": cap["capability_receipt_digest"],
        "target_engine_class": cap["target_engine_class"],
        "jspace_mode": cap["jspace_mode"],
        "inference_packet_digest": h("packet"),
    }
    return {
        "ok": True,
        "schema": v.ADMISSION_SCHEMA,
        "generation": 7,
        "profile_id": cap["profile_id"],
        "profile_hash": cap["profile_hash"],
        "capability_binding_digest": cap["binding_digest"],
        "capability_receipt_digest": cap["capability_receipt_digest"],
        "target_engine_class": cap["target_engine_class"],
        "jspace_mode": cap["jspace_mode"],
        "inference_packet_digest": h("packet"),
        "admission_receipt": receipt,
        "cognitive_fabric_receipt_digest": v.sha256_obj(receipt),
    }


class CapabilityAdmissionAncestryTests(unittest.TestCase):
    def test_exact_capability_ancestry_passes(self):
        cap = capability()
        out = v.validate_capability_ancestry(admission(cap), cap)
        self.assertTrue(out["ok"])
        self.assertEqual(out["capability_receipt_digest"], cap["capability_receipt_digest"])

    def test_same_route_different_capability_receipt_fails_closed(self):
        cap_a = capability(receipt="cap-a", binding="binding-a")
        cap_b = capability(receipt="cap-b", binding="binding-b")
        with self.assertRaisesRegex(v.CapabilityAncestryError, "CAPABILITY_BINDING_DIGEST_MISMATCH"):
            v.validate_capability_ancestry(admission(cap_a), cap_b)

    def test_missing_capability_binding_identity_fails_closed(self):
        cap = capability()
        candidate = admission(cap)
        del candidate["capability_binding_digest"]
        with self.assertRaisesRegex(v.CapabilityAncestryError, "SHA256_REQUIRED"):
            v.validate_capability_ancestry(candidate, cap)

    def test_profile_snapshot_drift_fails_closed(self):
        cap = capability()
        candidate = admission(cap)
        candidate["profile_hash"] = h("other-profile")
        with self.assertRaisesRegex(v.CapabilityAncestryError, "CAPABILITY_PROFILE_HASH_MISMATCH"):
            v.validate_capability_ancestry(candidate, cap)

    def test_route_drift_fails_closed(self):
        cap = capability()
        candidate = admission(cap)
        candidate["jspace_mode"] = "PLAIN_COMPATIBILITY"
        with self.assertRaisesRegex(v.CapabilityAncestryError, "CAPABILITY_JSPACE_ROUTE_MISMATCH"):
            v.validate_capability_ancestry(candidate, cap)

    def test_receipt_mutation_after_digest_fails_closed(self):
        cap = capability()
        candidate = admission(cap)
        candidate["admission_receipt"]["profile_id"] = "mutated"
        with self.assertRaisesRegex(
            v.CapabilityAncestryError,
            "ADMISSION_RECEIPT_PROFILE_ID_MISMATCH|ADMISSION_RECEIPT_DIGEST_MISMATCH",
        ):
            v.validate_capability_ancestry(candidate, cap)


if __name__ == "__main__":
    unittest.main()
