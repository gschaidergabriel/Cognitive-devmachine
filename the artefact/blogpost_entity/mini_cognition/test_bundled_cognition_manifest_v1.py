import copy
import unittest

from bundled_cognition_manifest_v1 import ManifestError, validate_manifest

D0 = "0" * 64
D1 = "1" * 64
D2 = "2" * 64
D3 = "3" * 64
D4 = "4" * 64
D5 = "5" * 64
D6 = "6" * 64


def base_manifest():
    return {
        "schema": "mini-entity-bundled-cognition-manifest/v1",
        "engine_id": "bundled-qwen35-08b",
        "model_family": "Qwen3.5-0.8B",
        "checkpoint_digest": D0,
        "tokenizer_digest": D1,
        "quantization_runtime_identity": "gguf-q4_k_m+llama.cpp:test-fixture",
        "runtime_digest": D6,
        "jspace_profile_digest": D2,
        "lens_profile_digest": D3,
        "workspace_calibration_digest": D4,
        "steering_calibration_digest": D5,
        "claycode_contract_version": "v1",
        "grf_contract_version": "r0-r6/v1",
        "hyperposition_contract_version": "v1",
        "compatible_entityos_range": ">=0.1,<1.0",
        "provenance": {"kind": "TEST_FIXTURE", "source": "unit"},
    }


class BundledCognitionManifestTests(unittest.TestCase):
    def test_valid_manifest_has_stable_identity(self):
        a = validate_manifest(base_manifest())
        b = validate_manifest(copy.deepcopy(base_manifest()))
        self.assertEqual(a.integration_identity_sha256, b.integration_identity_sha256)
        self.assertEqual(64, len(a.integration_identity_sha256))
        self.assertEqual(64, len(a.manifest_identity_sha256))

    def test_unusual_jspace_calibration_alias_poison(self):
        # Regression-only rerun of the already-consumed discriminator for this go.
        a = base_manifest()
        b = copy.deepcopy(a)
        b["jspace_profile_digest"] = "a" * 64
        self.assertNotEqual(validate_manifest(a).integration_identity_sha256, validate_manifest(b).integration_identity_sha256)

    def test_lens_and_workspace_are_identity_bound(self):
        base = validate_manifest(base_manifest()).integration_identity_sha256
        for field in ("lens_profile_digest", "workspace_calibration_digest"):
            poisoned = base_manifest()
            poisoned[field] = "b" * 64
            self.assertNotEqual(base, validate_manifest(poisoned).integration_identity_sha256)

    def test_runtime_digest_is_identity_bound_when_present(self):
        a = base_manifest()
        b = copy.deepcopy(a)
        b["runtime_digest"] = "a" * 64
        self.assertNotEqual(validate_manifest(a).integration_identity_sha256, validate_manifest(b).integration_identity_sha256)

    def test_malformed_runtime_digest_fails_closed(self):
        data = base_manifest()
        data["runtime_digest"] = "ABC"
        with self.assertRaisesRegex(ManifestError, "runtime_digest:LOWERCASE_SHA256_REQUIRED"):
            validate_manifest(data)

    def test_missing_calibration_digest_fails_closed(self):
        data = base_manifest()
        del data["lens_profile_digest"]
        with self.assertRaisesRegex(ManifestError, "MISSING_REQUIRED_FIELDS:lens_profile_digest"):
            validate_manifest(data)

    def test_malformed_digest_fails_closed(self):
        data = base_manifest()
        data["checkpoint_digest"] = "ABC"
        with self.assertRaisesRegex(ManifestError, "LOWERCASE_SHA256_REQUIRED"):
            validate_manifest(data)

    def test_unknown_semantic_field_fails_closed(self):
        data = base_manifest()
        data["truth_threshold"] = 0.9
        with self.assertRaisesRegex(ManifestError, "UNKNOWN_FIELDS:truth_threshold"):
            validate_manifest(data)

    def test_provenance_does_not_change_integration_identity(self):
        a = base_manifest()
        b = copy.deepcopy(a)
        b["provenance"] = {"kind": "TEST_FIXTURE", "source": "replica"}
        va = validate_manifest(a)
        vb = validate_manifest(b)
        self.assertEqual(va.integration_identity_sha256, vb.integration_identity_sha256)
        self.assertNotEqual(va.manifest_identity_sha256, vb.manifest_identity_sha256)

    def test_optional_steering_digest_is_identity_bound_when_present(self):
        a = base_manifest()
        b = copy.deepcopy(a)
        del b["steering_calibration_digest"]
        self.assertNotEqual(validate_manifest(a).integration_identity_sha256, validate_manifest(b).integration_identity_sha256)


if __name__ == "__main__":
    unittest.main()
