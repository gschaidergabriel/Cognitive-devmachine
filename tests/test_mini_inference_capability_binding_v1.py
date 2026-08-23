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

import mini_inference_capability_binding_v1 as cap


def h(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def binding(**changes):
    values = dict(
        binding_id="remote-v1",
        engine_class="ADAPTIVE_BACKEND",
        jspace_mode="COMPILED_EXTERNAL",
        local_activation_access=False,
        external_hidden_state_claimed=False,
        provider_observability_claim_supported=True,
        adapter_version="adaptive-http/v1",
        capability_evidence_kind="STATIC_CONSERVATIVE",
        capability_receipt_digest=h("capability-receipt"),
        provenance_refs=["profile:test", "policy:free-only"],
    )
    values.update(changes)
    return cap.compile_binding(**values)


def profile(b):
    return {
        "schema": "clay-pipeline-profile/v2",
        "profile_id": "test",
        "inference": {
            "kind": "local_exec",  # deliberately misleading metadata in one falsifier
            "model": "totally-hookable-sounding-model",
            "capability_binding": b,
        },
        "_runtime_profile_snapshot": {"profile_id": "test", "profile_hash": h("profile")},
    }


def prepare(generation: int = 9):
    out = {
        "ok": True,
        "entity_generation": generation,
        "causal_turn_id": f"turn-{generation}-a",
        "task_text": "measure first",
        "turn_binding_digest": h("turn-binding"),
        "boot_binding_digest": h("boot-binding"),
        "workspace_digest": h("workspace"),
    }
    for field in cap.PREPARE_DIGEST_FIELDS:
        out[field] = h(field)
    return out


def local_evidence(p, b):
    return {
        "ok": True,
        "schema": cap.CAPABILITY_EVIDENCE_SCHEMA,
        "entity_generation": p["entity_generation"],
        "causal_turn_id": p["causal_turn_id"],
        "turn_binding_digest": p["turn_binding_digest"],
        "boot_binding_digest": p["boot_binding_digest"],
        "capability_binding_digest": b["binding_digest"],
        "capability_receipt_digest": b["capability_receipt_digest"],
        "capability_evidence_kind": b["capability_evidence_kind"],
        "cognition": {field: p[field] for field in cap.PREPARE_DIGEST_FIELDS},
        "evidence_binding_digest": h("resolved-capability-evidence"),
        "direct_truth_authority": False,
        "direct_effect_authority": False,
    }


class CapabilityBindingTests(unittest.TestCase):
    def test_closed_api_compiled_external_resolves(self):
        out = cap.resolve_from_profile(profile(binding()))
        self.assertEqual(out["target_engine_class"], "ADAPTIVE_BACKEND")
        self.assertEqual(out["jspace_mode"], "COMPILED_EXTERNAL")
        self.assertFalse(out["local_activation_access"])

    def test_claude_cannot_claim_local_latent(self):
        with self.assertRaisesRegex(cap.CapabilityBindingError, "LOCAL_JSPACE_REQUIRES_MEASURED_OR_MANIFEST_EVIDENCE|CLAUDE_MUST_BE_COMPILED_EXTERNAL"):
            binding(engine_class="CLAUDE_CODE", jspace_mode="FULL_LOCAL_LATENT", local_activation_access=True)

    def test_static_config_cannot_authorize_local_latent(self):
        with self.assertRaisesRegex(cap.CapabilityBindingError, "LOCAL_JSPACE_REQUIRES_MEASURED_OR_MANIFEST_EVIDENCE"):
            binding(jspace_mode="FULL_LOCAL_LATENT", local_activation_access=True)

    def test_bundled_local_requires_local_mode_and_evidence(self):
        local = binding(
            binding_id="bundled-08b",
            engine_class="BUNDLED_LOCAL_08B",
            jspace_mode="LOCAL_OBSERVE_ONLY",
            local_activation_access=True,
            capability_evidence_kind="BUNDLED_MANIFEST",
            capability_receipt_digest=h("bundled-manifest-capability"),
        )
        out = cap.validate_binding(local)
        self.assertEqual(out["ucf_engine_class"], "local_08b")

    def test_digest_tamper_fails_closed(self):
        doc = binding()
        doc["jspace_mode"] = "PLAIN_COMPATIBILITY"
        with self.assertRaisesRegex(cap.CapabilityBindingError, "CAPABILITY_BINDING_DIGEST_MISMATCH"):
            cap.validate_binding(doc)

    def test_profile_snapshot_is_mandatory(self):
        p = profile(binding())
        del p["_runtime_profile_snapshot"]
        with self.assertRaisesRegex(cap.CapabilityBindingError, "PROFILE_SNAPSHOT_MISSING"):
            cap.resolve_from_profile(p)

    def test_unusual_provider_name_poison_cannot_upgrade_capability(self):
        # Historical regression: provider/model/kind strings scream "local/hookable", but the
        # explicit hash-bound capability says external. Resolution must remain external.
        p = profile(binding())
        p["inference"].update({
            "kind": "local_exec",
            "provider": "FULL_LOCAL_LATENT_SUPER_HOOKABLE",
            "model": "claude-local-activations-available",
            "local_activation_access": True,
            "jspace_mode": "FULL_LOCAL_LATENT",
        })
        out = cap.resolve_from_profile(p)
        self.assertEqual(out["target_engine_class"], "ADAPTIVE_BACKEND")
        self.assertEqual(out["jspace_mode"], "COMPILED_EXTERNAL")
        self.assertFalse(out["local_activation_access"])

    def test_bound_route_uses_canonical_prepare_ancestry_without_profile_duplication(self):
        p = profile(binding())
        prep = prepare()
        out = cap.resolve_bound_route(p, prep, expected_generation=9)
        self.assertEqual(out["target_engine_class"], "ADAPTIVE_BACKEND")
        self.assertEqual(out["cognition"]["jspace_profile_digest"], h("jspace_profile_digest"))
        self.assertEqual(len(out["route_digest"]), 64)
        self.assertNotIn("cognition", p["inference"]["capability_binding"])

    def test_bound_route_rejects_stale_prepare_generation(self):
        p = profile(binding())
        prep = prepare(8)
        with self.assertRaisesRegex(cap.CapabilityBindingError, "STALE_GENERATION"):
            cap.resolve_bound_route(p, prep, expected_generation=9)

    def test_bound_route_rejects_missing_prepare_cognition_digest(self):
        p = profile(binding())
        prep = prepare()
        del prep["policy_authority_digest"]
        with self.assertRaisesRegex(cap.CapabilityBindingError, "prepare.policy_authority_digest:SHA256_REQUIRED"):
            cap.resolve_bound_route(p, prep, expected_generation=9)

    def test_local_route_rejects_opaque_receipt_without_resolved_evidence(self):
        local = binding(
            binding_id="bundled-08b",
            engine_class="BUNDLED_LOCAL_08B",
            jspace_mode="FULL_LOCAL_LATENT",
            local_activation_access=True,
            capability_evidence_kind="BUNDLED_MANIFEST",
            capability_receipt_digest=h("manifest-admission"),
        )
        with self.assertRaisesRegex(cap.CapabilityBindingError, "LOCAL_CAPABILITY_EVIDENCE_REQUIRED"):
            cap.resolve_bound_route(profile(local), prepare(), expected_generation=9)

    def test_local_route_accepts_only_crossbound_resolved_evidence(self):
        local = binding(
            binding_id="bundled-08b",
            engine_class="BUNDLED_LOCAL_08B",
            jspace_mode="LOCAL_OBSERVE_ONLY",
            local_activation_access=True,
            capability_evidence_kind="BUNDLED_MANIFEST",
            capability_receipt_digest=h("manifest-admission"),
        )
        prep = prepare()
        evidence = local_evidence(prep, local)
        out = cap.resolve_bound_route(
            profile(local),
            prep,
            expected_generation=9,
            capability_evidence=evidence,
        )
        self.assertEqual(out["capability_evidence_binding_digest"], h("resolved-capability-evidence"))
        self.assertEqual(out["jspace_mode"], "LOCAL_OBSERVE_ONLY")

    def test_local_route_rejects_evidence_from_other_boot(self):
        local = binding(
            binding_id="bundled-08b",
            engine_class="BUNDLED_LOCAL_08B",
            jspace_mode="LOCAL_OBSERVE_ONLY",
            local_activation_access=True,
            capability_evidence_kind="BUNDLED_MANIFEST",
            capability_receipt_digest=h("manifest-admission"),
        )
        prep = prepare()
        evidence = local_evidence(prep, local)
        evidence["boot_binding_digest"] = h("other-boot")
        with self.assertRaisesRegex(cap.CapabilityBindingError, "CAPABILITY_EVIDENCE_BOOT_BINDING_DRIFT"):
            cap.resolve_bound_route(
                profile(local),
                prep,
                expected_generation=9,
                capability_evidence=evidence,
            )


if __name__ == "__main__":
    unittest.main()
