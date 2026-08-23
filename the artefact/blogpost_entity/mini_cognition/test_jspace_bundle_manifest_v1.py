import copy
import unittest

from jspace_bundle_manifest_v1 import ManifestError, admit_boot, bundle_identity, validate_structure

H = "a" * 64
G = "b" * 40


def manifest():
    return {
        "schema_version": "BundledCognitionManifest/v1",
        "status": "MEASURED",
        "engine_id": "qwen35-08b-claycog",
        "model_family": "Qwen3.5-0.8B",
        "checkpoint_digest": H,
        "tokenizer_digest": "b" * 64,
        "runtime_binding": {
            "runtime_id": "llama.cpp:test-build",
            "quantization": "Q4_K_M",
            "artifact_digest": "c" * 64,
        },
        "jspace_profile_digest": "d" * 64,
        "lens_profile_digest": "e" * 64,
        "lens_semantics": {"d_model": 1024, "source_layers": [4, 5, 6, 7], "n_prompts": 100},
        "workspace_calibration_digest": "f" * 64,
        "steering_calibration_digest": None,
        "claycode_contract_version": "v1",
        "grf_contract_version": "R0-R6/v1",
        "hyperposition_contract_version": "v1",
        "compatible_entityos_range": ">=0.1,<0.2",
        "provenance": {
            "source_commit": G,
            "source_tree": "c" * 40,
            "lens_source": "anthropics/jacobian-lens@pinned-revision",
            "calibration_receipt": "receipts/JSPACE_GWT_CALIBRATION_v1.json",
        },
    }


class ManifestTests(unittest.TestCase):
    def test_measured_manifest_boots_with_exact_identity(self):
        m = manifest()
        ident = admit_boot(m)
        self.assertEqual(admit_boot(m, expected_identity=ident), ident)

    def test_source_only_never_receives_boot_credit(self):
        m = manifest()
        m["status"] = "SOURCE_ONLY"
        validate_structure(m)
        with self.assertRaisesRegex(ManifestError, "BOOT_ADMISSION_REQUIRES_MEASURED_STATUS"):
            admit_boot(m)

    def test_lens_layer_semantics_are_sorted_unique(self):
        m = manifest()
        m["lens_semantics"]["source_layers"] = [4, 6, 6, 5]
        with self.assertRaisesRegex(ManifestError, "SORTED_UNIQUE_REQUIRED"):
            validate_structure(m)

    def test_bool_is_not_an_integer_dimension(self):
        m = manifest()
        m["lens_semantics"]["d_model"] = True
        with self.assertRaisesRegex(ManifestError, "POSITIVE_INT_REQUIRED"):
            validate_structure(m)

    def test_unknown_top_level_semantics_fail_closed(self):
        m = manifest()
        m["workspace_truth_threshold"] = 0.99
        with self.assertRaisesRegex(ManifestError, "KEYSET_MISMATCH"):
            validate_structure(m)

    def test_calibration_digest_swap_invalidates_bound_identity(self):
        # Single bounded unusual discriminator for this go: a calibration
        # substitution must not inherit a previously admitted bundle identity.
        m1 = manifest()
        id1 = admit_boot(m1)
        m2 = copy.deepcopy(m1)
        m2["workspace_calibration_digest"] = "0" * 64
        id2 = bundle_identity(validate_structure(m2))
        self.assertNotEqual(id1, id2)
        with self.assertRaisesRegex(ManifestError, "STALE_OR_SUBSTITUTED_BUNDLE_IDENTITY"):
            admit_boot(m2, expected_identity=id1)


if __name__ == "__main__":
    unittest.main()
