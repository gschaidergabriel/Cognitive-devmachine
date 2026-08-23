#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import mini_capability_evidence_resolution_v1 as evidence
import mini_inference_capability_binding_v1 as cap


def h(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def digest_obj(value) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


KINDS = {
    "zero_identity_digest": "ZERO_IDENTITY",
    "grf_digest": "GRF",
    "hyperposition_digest": "HYPERPOSITION",
    "bundled_manifest_digest": "BUNDLED_MANIFEST",
    "local_model_digest": "LOCAL_MODEL_CHECKPOINT",
    "tokenizer_digest": "TOKENIZER",
    "jspace_profile_digest": "JSPACE_PROFILE",
    "jacobian_lens_digest": "JACOBIAN_LENS_PROFILE",
    "workspace_calibration_digest": "WORKSPACE_CALIBRATION",
    "boot_source_lock_digest": "BOOT_SOURCE_LOCK",
    "policy_authority_digest": "POLICY_AUTHORITY",
}


def prepare():
    out = {
        "ok": True,
        "entity_generation": 7,
        "causal_turn_id": "turn-7",
        "turn_binding_digest": h("turn-binding"),
        "boot_binding_digest": h("boot-binding"),
        "workspace_digest": h("workspace"),
    }
    for field in cap.PREPARE_DIGEST_FIELDS:
        out[field] = h(field)
    return out


def semantic(p=None):
    p = p or prepare()
    objects = {}
    for field, kind in KINDS.items():
        objects[field] = {
            "object_kind": kind,
            "object_version": "v1",
            "object_digest": p[field],
            "payload_digest": h("payload:" + field),
            "admission_receipt_digest": (
                h("manifest-admission") if field == "bundled_manifest_digest" else h("admit:" + field)
            ),
        }
    out = {
        "schema": evidence.SEMANTIC_SCHEMA,
        "entity_generation": p["entity_generation"],
        "causal_turn_id": p["causal_turn_id"],
        "turn_binding_digest": p["turn_binding_digest"],
        "boot_binding_digest": p["boot_binding_digest"],
        "workspace_digest": p["workspace_digest"],
        "objects": objects,
        "authority": "VERSION_BINDING_ONLY_NO_TRUTH_STATE_EFFECT_AUTHORITY",
    }
    out["semantic_binding_digest"] = digest_obj(out)
    return out


def local_binding(**overrides):
    values = dict(
        binding_id="bundled-08b",
        engine_class="BUNDLED_LOCAL_08B",
        jspace_mode="FULL_LOCAL_LATENT",
        local_activation_access=True,
        external_hidden_state_claimed=False,
        provider_observability_claim_supported=True,
        adapter_version="local-08b/v1",
        capability_evidence_kind="BUNDLED_MANIFEST",
        capability_receipt_digest=h("manifest-admission"),
        provenance_refs=["profile:test", "boot:test"],
    )
    values.update(overrides)
    return cap.compile_binding(**values)


def external_binding():
    return cap.compile_binding(
        binding_id="remote",
        engine_class="ADAPTIVE_BACKEND",
        jspace_mode="COMPILED_EXTERNAL",
        local_activation_access=False,
        external_hidden_state_claimed=False,
        provider_observability_claim_supported=True,
        adapter_version="remote/v1",
        capability_evidence_kind="STATIC_CONSERVATIVE",
        capability_receipt_digest=h("static-capability"),
        provenance_refs=["profile:test"],
    )


def profile(binding):
    return {
        "schema": "clay-pipeline-profile/v2",
        "profile_id": "p1",
        "inference": {"kind": "local_exec", "capability_binding": binding},
        "_runtime_profile_snapshot": {"profile_id": "p1", "profile_hash": h("profile")},
    }


class CapabilitySemanticEvidenceTests(unittest.TestCase):
    def test_local_route_is_bound_to_exact_manifest_admission(self):
        p = prepare()
        out = cap.resolve_bound_route(
            profile(local_binding()),
            p,
            expected_generation=7,
            semantic_binding=semantic(p),
        )
        self.assertEqual(
            out["capability_evidence_resolution"],
            "CURRENT_SEMANTIC_BINDING_BUNDLED_MANIFEST_ADMISSION",
        )
        self.assertEqual(len(out["capability_evidence_binding_digest"]), 64)
        self.assertEqual(len(out["route_digest"]), 64)

    def test_random_valid_sha_cannot_masquerade_as_manifest_admission(self):
        with self.assertRaisesRegex(
            cap.CapabilityBindingError,
            "CAPABILITY_RECEIPT_NOT_CURRENT_BUNDLED_MANIFEST_ADMISSION",
        ):
            cap.resolve_bound_route(
                profile(local_binding(capability_receipt_digest=h("random-valid-sha"))),
                prepare(),
                expected_generation=7,
                semantic_binding=semantic(),
            )

    def test_local_route_without_semantic_binding_fails_closed(self):
        with self.assertRaisesRegex(cap.CapabilityBindingError, "LOCAL_LATENT_SEMANTIC_BINDING_REQUIRED"):
            cap.resolve_bound_route(profile(local_binding()), prepare(), expected_generation=7)

    def test_semantic_binding_digest_tamper_fails_closed(self):
        poisoned = semantic()
        poisoned["semantic_binding_digest"] = h("tampered")
        with self.assertRaisesRegex(cap.CapabilityBindingError, "SEMANTIC_BINDING_DIGEST_MISMATCH"):
            cap.resolve_bound_route(
                profile(local_binding()),
                prepare(),
                expected_generation=7,
                semantic_binding=poisoned,
            )

    def test_boot_object_drift_fails_closed_even_with_rehashed_semantic_binding(self):
        poisoned = semantic()
        poisoned["objects"]["tokenizer_digest"]["object_digest"] = h("other-tokenizer")
        unsigned = dict(poisoned)
        unsigned.pop("semantic_binding_digest")
        poisoned["semantic_binding_digest"] = digest_obj(unsigned)
        with self.assertRaisesRegex(cap.CapabilityBindingError, "SEMANTIC_OBJECT_DIGEST_DRIFT:tokenizer_digest"):
            cap.resolve_bound_route(
                profile(local_binding()),
                prepare(),
                expected_generation=7,
                semantic_binding=poisoned,
            )

    def test_runtime_probe_stays_fail_closed_until_canonical_typed_evidence_exists(self):
        with self.assertRaisesRegex(cap.CapabilityBindingError, "RUNTIME_PROBE_EVIDENCE_NOT_CANONICALLY_RESOLVED"):
            cap.resolve_bound_route(
                profile(local_binding(capability_evidence_kind="RUNTIME_PROBE")),
                prepare(),
                expected_generation=7,
                semantic_binding=semantic(),
            )

    def test_external_route_needs_no_local_semantic_authority(self):
        out = cap.resolve_bound_route(profile(external_binding()), prepare(), expected_generation=7)
        self.assertIsNone(out["capability_evidence_binding_digest"])
        self.assertEqual(out["capability_evidence_resolution"], "NONLOCAL_NO_LATENT_AUTHORITY")


if __name__ == "__main__":
    unittest.main()
