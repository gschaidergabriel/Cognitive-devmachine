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


def prepare(*, generation: int = 12, boot_digest: str | None = None) -> dict:
    value = {
        "ok": True,
        "entity_generation": generation,
        "causal_turn_id": "ct:g12:a1",
        "turn_binding_digest": h("turn-binding"),
        "boot_binding_digest": boot_digest or h("boot-binding"),
        "workspace_digest": h("workspace"),
    }
    for field in cap.PREPARE_DIGEST_FIELDS:
        value[field] = h(field)
    return value


def profile(binding: dict) -> dict:
    return {
        "schema": "clay-pipeline-profile/v2",
        "profile_id": "cap-fence-test",
        "inference": {"kind": "local_exec", "capability_binding": binding},
        "_runtime_profile_snapshot": {
            "profile_id": "cap-fence-test",
            "profile_hash": h("profile"),
        },
    }


def local_binding(*, capability_receipt_digest: str, evidence_kind: str = "BUNDLED_MANIFEST") -> dict:
    return cap.compile_binding(
        binding_id="bundled-08b-local",
        engine_class="BUNDLED_LOCAL_08B",
        jspace_mode="LOCAL_OBSERVE_ONLY",
        local_activation_access=True,
        external_hidden_state_claimed=False,
        provider_observability_claim_supported=True,
        adapter_version="bundled-08b/v1",
        capability_evidence_kind=evidence_kind,
        capability_receipt_digest=capability_receipt_digest,
        provenance_refs=["test:capability"],
    )


class CapabilityBootAncestryFenceTests(unittest.TestCase):
    def test_random_valid_sha256_cannot_authorize_local_latent(self):
        p = prepare()
        binding = local_binding(capability_receipt_digest=h("arbitrary-well-formed-receipt"))
        with self.assertRaisesRegex(
            cap.CapabilityBindingError,
            "BUNDLED_MANIFEST_CAPABILITY_RECEIPT_NOT_CURRENT_BOOT_BINDING",
        ):
            cap.resolve_bound_route(profile(binding), p, expected_generation=12)

    def test_exact_current_boot_binding_can_authorize_candidate_local_route(self):
        p = prepare()
        binding = local_binding(capability_receipt_digest=p["boot_binding_digest"])
        out = cap.resolve_bound_route(profile(binding), p, expected_generation=12)
        self.assertTrue(out["ok"])
        self.assertEqual(out["capability_receipt_digest"], p["boot_binding_digest"])
        self.assertEqual(out["jspace_mode"], "LOCAL_OBSERVE_ONLY")
        self.assertEqual(out["authority"], "ROUTING_ONLY_BOUND_TO_CANONICAL_PREPARE")

    def test_boot_generation_rebinding_invalidates_old_capability_receipt(self):
        old_boot = h("boot-binding:g11")
        new_boot = h("boot-binding:g12")
        p = prepare(boot_digest=new_boot)
        binding = local_binding(capability_receipt_digest=old_boot)
        with self.assertRaisesRegex(
            cap.CapabilityBindingError,
            "BUNDLED_MANIFEST_CAPABILITY_RECEIPT_NOT_CURRENT_BOOT_BINDING",
        ):
            cap.resolve_bound_route(profile(binding), p, expected_generation=12)

    def test_runtime_probe_digest_is_not_treated_as_evidence_without_typed_resolver(self):
        p = prepare()
        binding = local_binding(
            capability_receipt_digest=p["boot_binding_digest"],
            evidence_kind="RUNTIME_PROBE",
        )
        with self.assertRaisesRegex(
            cap.CapabilityBindingError,
            "RUNTIME_PROBE_CAPABILITY_EVIDENCE_RESOLUTION_REQUIRED",
        ):
            cap.resolve_bound_route(profile(binding), p, expected_generation=12)

    def test_external_static_route_remains_independent_of_boot_receipt(self):
        p = prepare()
        binding = cap.compile_binding(
            binding_id="external",
            engine_class="ADAPTIVE_BACKEND",
            jspace_mode="COMPILED_EXTERNAL",
            local_activation_access=False,
            external_hidden_state_claimed=False,
            provider_observability_claim_supported=True,
            adapter_version="external/v1",
            capability_evidence_kind="STATIC_CONSERVATIVE",
            capability_receipt_digest=h("policy-receipt"),
            provenance_refs=["test:external"],
        )
        out = cap.resolve_bound_route(profile(binding), p, expected_generation=12)
        self.assertTrue(out["ok"])
        self.assertFalse(out["local_activation_access"])
        self.assertEqual(out["jspace_mode"], "COMPILED_EXTERNAL")


if __name__ == "__main__":
    unittest.main()
