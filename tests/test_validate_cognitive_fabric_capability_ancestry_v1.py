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


def bound_route(*, receipt: str = "cap-a", binding: str = "binding-a", mode: str = "COMPILED_EXTERNAL"):
    material = {
        "schema": v.BOUND_ROUTE_SCHEMA,
        "entity_generation": 7,
        "causal_turn_id": "turn-7",
        "turn_binding_digest": h("turn"),
        "boot_binding_digest": h("boot"),
        "workspace_digest": h("workspace"),
        "profile_id": "default",
        "profile_hash": h("profile"),
        "capability_binding_digest": h(binding),
        "capability_receipt_digest": h(receipt),
        "target_engine_class": "ADAPTIVE_BACKEND",
        "ucf_engine_class": "adaptive_backend",
        "jspace_mode": mode,
        "cognition": {"local_model_digest": h("model"), "jspace_profile_digest": h("jspace")},
    }
    return {"ok": True, **material, "route_digest": v.sha256_obj(material)}


def admission(route: dict):
    receipt = {
        "schema": v.ADMISSION_SCHEMA,
        "generation": route["entity_generation"],
        "profile_id": route["profile_id"],
        "profile_hash": route["profile_hash"],
        "inference_route_digest": route["route_digest"],
        "capability_binding_digest": route["capability_binding_digest"],
        "capability_receipt_digest": route["capability_receipt_digest"],
        "target_engine_class": route["target_engine_class"],
        "jspace_mode": route["jspace_mode"],
        "inference_packet_digest": h("packet"),
    }
    return {
        "ok": True,
        "schema": v.ADMISSION_SCHEMA,
        "generation": route["entity_generation"],
        "profile_id": route["profile_id"],
        "profile_hash": route["profile_hash"],
        "inference_route_digest": route["route_digest"],
        "capability_binding_digest": route["capability_binding_digest"],
        "capability_receipt_digest": route["capability_receipt_digest"],
        "target_engine_class": route["target_engine_class"],
        "jspace_mode": route["jspace_mode"],
        "inference_packet_digest": h("packet"),
        "admission_receipt": receipt,
        "cognitive_fabric_receipt_digest": v.sha256_obj(receipt),
    }


class CapabilityAdmissionAncestryTests(unittest.TestCase):
    def test_exact_bound_route_ancestry_passes(self):
        route = bound_route()
        out = v.validate_capability_ancestry(admission(route), route)
        self.assertTrue(out["ok"])
        self.assertEqual(out["inference_route_digest"], route["route_digest"])

    def test_same_engine_jspace_different_capability_receipt_fails_closed(self):
        route_a = bound_route(receipt="cap-a", binding="binding-a")
        route_b = bound_route(receipt="cap-b", binding="binding-b")
        with self.assertRaisesRegex(v.CapabilityAncestryError, "BOUND_ROUTE_IDENTITY_MISMATCH"):
            v.validate_capability_ancestry(admission(route_a), route_b)

    def test_missing_bound_route_identity_fails_closed(self):
        route = bound_route()
        candidate = admission(route)
        del candidate["inference_route_digest"]
        with self.assertRaisesRegex(v.CapabilityAncestryError, "SHA256_REQUIRED"):
            v.validate_capability_ancestry(candidate, route)

    def test_route_digest_tamper_fails_closed_before_admission_comparison(self):
        route = bound_route()
        route["cognition"]["local_model_digest"] = h("different-model")
        with self.assertRaisesRegex(v.CapabilityAncestryError, "BOUND_ROUTE_DIGEST_MISMATCH"):
            v.validate_capability_ancestry(admission(bound_route()), route)

    def test_profile_snapshot_drift_fails_closed(self):
        route = bound_route()
        candidate = admission(route)
        candidate["profile_hash"] = h("other-profile")
        with self.assertRaisesRegex(v.CapabilityAncestryError, "BOUND_ROUTE_PROFILE_HASH_MISMATCH"):
            v.validate_capability_ancestry(candidate, route)

    def test_route_mode_drift_fails_closed(self):
        route = bound_route()
        candidate = admission(route)
        candidate["jspace_mode"] = "PLAIN_COMPATIBILITY"
        with self.assertRaisesRegex(v.CapabilityAncestryError, "CAPABILITY_JSPACE_ROUTE_MISMATCH"):
            v.validate_capability_ancestry(candidate, route)

    def test_receipt_mutation_after_digest_fails_closed(self):
        route = bound_route()
        candidate = admission(route)
        candidate["admission_receipt"]["profile_id"] = "mutated"
        with self.assertRaisesRegex(
            v.CapabilityAncestryError,
            "ADMISSION_RECEIPT_PROFILE_ID_MISMATCH|ADMISSION_RECEIPT_DIGEST_MISMATCH",
        ):
            v.validate_capability_ancestry(candidate, route)


if __name__ == "__main__":
    unittest.main()
