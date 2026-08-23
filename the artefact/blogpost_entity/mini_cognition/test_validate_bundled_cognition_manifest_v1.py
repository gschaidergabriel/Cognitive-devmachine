#!/usr/bin/env python3
import copy
import unittest

from validate_bundled_cognition_manifest_v1 import (
    ManifestError,
    compute_integration_fingerprint,
    validate_boot_binding,
    validate_manifest,
)


def h(char: str) -> str:
    return char * 64


def manifest_a() -> dict:
    m = {
        "schema": "bundled-cognition-manifest/v1",
        "engine_id": "bundled-qwen35-08b",
        "model_family": "Qwen3.5-0.8B",
        "checkpoint_digest": h("1"),
        "tokenizer_digest": h("2"),
        "jspace_profile_digest": h("3"),
        "lens_profile_digest": h("4"),
        "workspace_calibration_digest": h("5"),
        "steering_calibration_digest": h("6"),
        "quantization_runtime_identity": "gguf:q4_k_m:llama.cpp-build-x",
        "claycode_contract_version": "claycode-cognition/v1",
        "grf_contract_version": "grf/v1",
        "hyperposition_contract_version": "hyperposition/v1",
        "compatible_entityos_range": ">=0.1,<0.2",
        "provenance": "repo@exact-source+measured-calibration-receipt",
    }
    m["integration_fingerprint"] = compute_integration_fingerprint(m)
    return m


def receipt_for(m: dict) -> dict:
    return {
        "schema": "jspace-gwt-boot-binding-receipt/v1",
        "engine_id": m["engine_id"],
        "checkpoint_digest": m["checkpoint_digest"],
        "tokenizer_digest": m["tokenizer_digest"],
        "jspace_profile_digest": m["jspace_profile_digest"],
        "lens_profile_digest": m["lens_profile_digest"],
        "workspace_calibration_digest": m["workspace_calibration_digest"],
        "bundled_cognition_integration_fingerprint": m["integration_fingerprint"],
    }


class BundledCognitionManifestTests(unittest.TestCase):
    def test_clean_manifest_and_boot_binding_pass(self):
        m = manifest_a()
        self.assertEqual(validate_manifest(m), m["integration_fingerprint"])
        self.assertEqual(validate_boot_binding(m, receipt_for(m)), m["integration_fingerprint"])

    def test_placeholder_digest_fails_closed(self):
        m = manifest_a()
        m["lens_profile_digest"] = "0" * 64
        with self.assertRaisesRegex(ManifestError, "PLACEHOLDER_DIGEST_FORBIDDEN"):
            compute_integration_fingerprint(m)

    def test_stale_boot_receipt_fails_after_workspace_calibration_change(self):
        m = manifest_a()
        receipt = receipt_for(m)
        m2 = copy.deepcopy(m)
        m2["workspace_calibration_digest"] = h("7")
        m2["integration_fingerprint"] = compute_integration_fingerprint(m2)
        with self.assertRaisesRegex(ManifestError, "integration_fingerprint:MISMATCH"):
            validate_boot_binding(m2, receipt)

    def test_unusual_cross_bundle_calibration_mix_and_match_fails_closed(self):
        # UNUSUAL EXPERIMENT: reproduce the weak "individual digests only" contract
        # implied by source architecture before an atomic bundle identity exists.
        a = manifest_a()
        mixed = copy.deepcopy(a)
        mixed["jspace_profile_digest"] = h("a")

        def legacy_individual_only_accepts(candidate: dict) -> bool:
            required = (
                "checkpoint_digest",
                "tokenizer_digest",
                "jspace_profile_digest",
                "lens_profile_digest",
                "workspace_calibration_digest",
            )
            return all(
                isinstance(candidate.get(field), str)
                and len(candidate[field]) == 64
                and all(ch in "0123456789abcdef" for ch in candidate[field])
                for field in required
            )

        # Pre-gate falsification: the mixed bundle still looks valid if components
        # are checked independently.
        self.assertTrue(legacy_individual_only_accepts(mixed))

        # Hardened manifest identity rejects the stale composite identity.
        with self.assertRaisesRegex(ManifestError, "integration_fingerprint:MISMATCH"):
            validate_manifest(mixed)

        # Recomputing a new bundle identity still cannot authorize a stale boot receipt.
        mixed["integration_fingerprint"] = compute_integration_fingerprint(mixed)
        with self.assertRaisesRegex(ManifestError, "integration_fingerprint:MISMATCH"):
            validate_boot_binding(mixed, receipt_for(a))


if __name__ == "__main__":
    unittest.main(verbosity=2)
