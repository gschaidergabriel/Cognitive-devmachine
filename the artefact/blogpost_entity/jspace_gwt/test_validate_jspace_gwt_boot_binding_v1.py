import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
MINI_COGNITION = HERE.parent / "mini_cognition"
if str(MINI_COGNITION) not in sys.path:
    sys.path.insert(0, str(MINI_COGNITION))
from bundled_cognition_manifest_v1 import validate_manifest

VALIDATOR = HERE / "validate_jspace_gwt_boot_binding_v1.py"
H40 = "a" * 40
H64 = "b" * 64


def valid_manifest():
    return {
        "schema": "mini-entity-bundled-cognition-manifest/v1",
        "engine_id": "claycog-08b",
        "model_family": "Qwen3.5-0.8B",
        "checkpoint_digest": "1" * 64,
        "tokenizer_digest": "2" * 64,
        "quantization_runtime_identity": "qwen35-08b:q4_k_m:llama.cpp-fixture",
        "runtime_digest": "3" * 64,
        "jspace_profile_digest": "4" * 64,
        "lens_profile_digest": "5" * 64,
        "workspace_calibration_digest": "6" * 64,
        "steering_calibration_digest": "7" * 64,
        "claycode_contract_version": "v1",
        "grf_contract_version": "r0-r6/v1",
        "hyperposition_contract_version": "v1",
        "compatible_entityos_range": ">=0.1,<1.0",
        "provenance": {"kind": "TEST_FIXTURE", "source": "unit"},
    }


def valid_receipt(manifest=None):
    manifest = valid_manifest() if manifest is None else manifest
    identity = validate_manifest(manifest)
    return {
        "schema": "JSPACE_GWT_BOOT_BINDING_RECEIPT/v1",
        "source": {"main_sha": H40, "tree_sha": H40, "dirty": False},
        "executor": {"host_class": "UBUNTU", "host_identity_sha256": H64, "kernel": "Linux 6.x"},
        "bundled_core": {
            "manifest_version": "1",
            "engine_id": manifest["engine_id"],
            "model_family": manifest["model_family"],
            "runtime_identity": manifest["quantization_runtime_identity"],
            "checkpoint_sha256": manifest["checkpoint_digest"],
            "tokenizer_sha256": manifest["tokenizer_digest"],
            "runtime_sha256": manifest["runtime_digest"],
            "manifest_sha256": identity.manifest_identity_sha256,
            "integration_identity_sha256": identity.integration_identity_sha256,
            "exact_bytes_verified": True,
        },
        "jspace": {
            "jlens_upstream_commit": H40,
            "jspace_profile_sha256": manifest["jspace_profile_digest"],
            "lens_file_sha256": H64,
            "lens_profile_sha256": manifest["lens_profile_digest"],
            "fit_corpus_sha256": H64,
            "n_prompts": 100,
            "skip_first_positions": 16,
            "storage_dtype": "float32",
            "numeric_integrity": {"pre_save_all_finite": True, "post_load_all_finite": True, "max_abs_pre_save": 12.5, "max_abs_post_load": 12.5},
            "measurement_policy": {"minimum_readout_position": 16, "observed_readout_positions": [16, 17, 31], "prompt_copy_confound_guard_enabled": True},
        },
        "gwt": {"workspace_policy_sha256": H64, "calibration_sha256": manifest["workspace_calibration_digest"], "slot_count": 3, "calibration_status": "UNMEASURED_SOURCE_ONLY"},
        "zero_grf": {"zero_identity_sha256": H64, "grf_sha256": H64, "projection_policy_sha256": H64},
        "claude_adapter": {"adapter_version": "0", "capability_profile_sha256": H64, "enabled": False},
        "inference": {"first_engine_choice": "BUNDLED_LOCAL_08B", "origin_attribution": "ZERO"},
        "authority": {"miniunifieddb_is_truth_authority": True, "claude_result_is_candidate_only": True, "jspace_measurement_is_not_truth": True, "gwt_workspace_is_not_truth": True, "effect_gate_required": True},
        "claims": {
            "bundled_08b_exact_runtime_credit": "ZERO",
            "jspace_runtime_credit": "ZERO",
            "whole_gwt_credit": "ZERO",
            "claude_code_adapter_runtime_credit": "ZERO",
            "canonical_semantics_credit": "ZERO",
            "whole_product": "IN_PROGRESS",
        },
    }


def run_validator(receipt, manifest=None, expected_manifest_sha=None):
    manifest = valid_manifest() if manifest is None else manifest
    expected_manifest_sha = validate_manifest(manifest).manifest_identity_sha256 if expected_manifest_sha is None else expected_manifest_sha
    with tempfile.TemporaryDirectory() as td:
        receipt_path = Path(td) / "receipt.json"
        manifest_path = Path(td) / "manifest.json"
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(VALIDATOR), str(receipt_path), "--manifest", str(manifest_path), "--expected-manifest-sha256", expected_manifest_sha, "--expected-main-sha", H40, "--expected-tree-sha", H40],
            text=True,
            capture_output=True,
            check=False,
        )


class BootBindingValidatorTests(unittest.TestCase):
    def test_valid_source_locked_receipt_passes(self):
        cp = run_validator(valid_receipt())
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
        self.assertIn("SOURCE_LOCKED_MANIFEST", cp.stdout)

    def test_poison_post_load_nonfinite_fails_closed(self):
        receipt = valid_receipt()
        receipt["jspace"]["numeric_integrity"]["post_load_all_finite"] = False
        cp = run_validator(receipt)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("LENS_POST_LOAD_NONFINITE", cp.stdout)

    def test_poison_unfitted_readout_position_fails_closed(self):
        receipt = valid_receipt()
        receipt["jspace"]["measurement_policy"]["observed_readout_positions"] = [8, 16]
        cp = run_validator(receipt)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("JSPACE_UNFITTED_POSITION", cp.stdout)

    def test_prompt_copy_guard_cannot_be_disabled(self):
        receipt = valid_receipt()
        receipt["jspace"]["measurement_policy"]["prompt_copy_confound_guard_enabled"] = False
        cp = run_validator(receipt)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("PROMPT_COPY_CONFOUND_GUARD_DISABLED", cp.stdout)

    def test_component_alias_with_expected_manifest_digest_fails_closed(self):
        receipt = valid_receipt()
        receipt["bundled_core"]["tokenizer_sha256"] = "f" * 64
        cp = run_validator(receipt)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("MANIFEST_COMPONENT_MISMATCH:tokenizer_digest", cp.stdout)

    def test_self_consistent_manifest_replacement_still_fails_source_lock(self):
        original = valid_manifest()
        expected = validate_manifest(original).manifest_identity_sha256
        replacement = copy.deepcopy(original)
        replacement["jspace_profile_digest"] = "e" * 64
        receipt = valid_receipt(replacement)
        cp = run_validator(receipt, replacement, expected_manifest_sha=expected)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("SOURCE_LOCK_MANIFEST_MISMATCH", cp.stdout)

    def test_boot_requires_runtime_digest_in_manifest(self):
        manifest = valid_manifest()
        receipt = valid_receipt(manifest)
        del manifest["runtime_digest"]
        identity = validate_manifest(manifest)
        receipt["bundled_core"]["manifest_sha256"] = identity.manifest_identity_sha256
        receipt["bundled_core"]["integration_identity_sha256"] = identity.integration_identity_sha256
        cp = run_validator(receipt, manifest)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("BOOT_MANIFEST_RUNTIME_DIGEST_REQUIRED", cp.stdout)

    def test_dirty_source_requires_diff_digest(self):
        receipt = valid_receipt()
        receipt["source"]["dirty"] = True
        cp = run_validator(receipt)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("MISSING_STRING:dirty_diff_sha256", cp.stdout)

    def test_unknown_action_origin_fails_closed(self):
        receipt = valid_receipt()
        receipt["inference"]["origin_attribution"] = "MODEL_GUESSED"
        cp = run_validator(receipt)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("INVALID_ORIGIN_ATTRIBUTION", cp.stdout)

    def test_boot_receipt_cannot_claim_jspace_runtime_credit(self):
        receipt = valid_receipt()
        receipt["claims"]["jspace_runtime_credit"] = "PASS"
        cp = run_validator(receipt)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("BOOT_RECEIPT_CANNOT_GRANT_CREDIT:jspace_runtime_credit", cp.stdout)

    def test_source_commit_must_match_external_expectation(self):
        receipt = valid_receipt()
        receipt["source"]["main_sha"] = "c" * 40
        cp = run_validator(receipt)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("SOURCE_MAIN_SHA_MISMATCH", cp.stdout)


if __name__ == "__main__":
    unittest.main()
