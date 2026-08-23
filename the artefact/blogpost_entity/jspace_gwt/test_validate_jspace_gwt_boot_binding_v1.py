import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
VALIDATOR_PATH = HERE / "validate_jspace_gwt_boot_binding_v1.py"
H40 = "a" * 40
H64 = "b" * 64
C64 = "c" * 64

spec = importlib.util.spec_from_file_location("jspace_boot_validator", VALIDATOR_PATH)
VALIDATOR = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(VALIDATOR)


def valid_source_lock():
    return {
        "schema": "mini-entity-bundled-cognition-source-lock/v1",
        "status": "BOUND",
        "manifest_identity_sha256": H64,
        "integration_identity_sha256": C64,
        "authority": "repository_source_tree",
        "evidence_receipt": "receipts/exact-bundle.json",
        "note": "synthetic-test-fixture-only",
    }


def valid_receipt():
    return {
        "schema": "JSPACE_GWT_BOOT_BINDING_RECEIPT/v1",
        "source": {"main_sha": H40, "tree_sha": H40, "dirty": False},
        "executor": {
            "host_class": "UBUNTU",
            "host_identity_sha256": H64,
            "kernel": "Linux 6.x",
        },
        "bundled_core": {
            "manifest_version": "1",
            "engine_id": "claycog-08b",
            "model_family": "Qwen3.5-0.8B",
            "checkpoint_sha256": H64,
            "tokenizer_sha256": H64,
            "runtime_sha256": H64,
            "manifest_sha256": H64,
            "integration_identity_sha256": C64,
            "exact_bytes_verified": True,
        },
        "jspace": {
            "jlens_upstream_commit": H40,
            "lens_file_sha256": H64,
            "lens_profile_sha256": H64,
            "fit_corpus_sha256": H64,
            "n_prompts": 100,
            "skip_first_positions": 16,
            "storage_dtype": "float32",
            "numeric_integrity": {
                "pre_save_all_finite": True,
                "post_load_all_finite": True,
                "max_abs_pre_save": 12.5,
                "max_abs_post_load": 12.5,
            },
            "measurement_policy": {
                "minimum_readout_position": 16,
                "observed_readout_positions": [16, 17, 31],
                "prompt_copy_confound_guard_enabled": True,
            },
        },
        "gwt": {
            "workspace_policy_sha256": H64,
            "calibration_sha256": H64,
            "slot_count": 3,
            "calibration_status": "UNMEASURED_SOURCE_ONLY",
        },
        "zero_grf": {
            "zero_identity_sha256": H64,
            "grf_sha256": H64,
            "projection_policy_sha256": H64,
        },
        "claude_adapter": {
            "adapter_version": "0",
            "capability_profile_sha256": H64,
            "enabled": False,
        },
        "inference": {
            "first_engine_choice": "BUNDLED_LOCAL_08B",
            "origin_attribution": "boot-probe",
        },
        "authority": {
            "miniunifieddb_is_truth_authority": True,
            "claude_result_is_candidate_only": True,
            "jspace_measurement_is_not_truth": True,
            "gwt_workspace_is_not_truth": True,
            "effect_gate_required": True,
        },
        "claims": {"whole_gwt_credit": "ZERO", "whole_product": "IN_PROGRESS"},
    }


def validate_error(receipt, lock=None):
    try:
        VALIDATOR.validate(receipt, source_lock=lock or valid_source_lock())
    except VALIDATOR.ValidationError as exc:
        return str(exc)
    return None


class BootBindingValidatorTests(unittest.TestCase):
    def test_valid_bound_source_lock_receipt_passes(self):
        VALIDATOR.validate(valid_receipt(), source_lock=valid_source_lock())

    def test_repository_lock_is_intentionally_unbound_and_cli_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "receipt.json"
            path.write_text(json.dumps(valid_receipt()), encoding="utf-8")
            cp = subprocess.run(
                [sys.executable, str(VALIDATOR_PATH), str(path)],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("SOURCE_LOCK_NOT_BOUND", cp.stdout)

    def test_poison_post_load_nonfinite_fails_closed(self):
        receipt = valid_receipt()
        receipt["jspace"]["numeric_integrity"]["post_load_all_finite"] = False
        self.assertEqual(validate_error(receipt), "LENS_POST_LOAD_NONFINITE")

    def test_poison_unfitted_readout_position_fails_closed(self):
        receipt = valid_receipt()
        receipt["jspace"]["measurement_policy"]["observed_readout_positions"] = [8, 16]
        self.assertEqual(validate_error(receipt), "JSPACE_UNFITTED_POSITION")

    def test_prompt_copy_guard_cannot_be_disabled(self):
        receipt = valid_receipt()
        receipt["jspace"]["measurement_policy"]["prompt_copy_confound_guard_enabled"] = False
        self.assertEqual(validate_error(receipt), "PROMPT_COPY_CONFOUND_GUARD_DISABLED")

    def test_boot_receipt_cannot_claim_whole_gwt(self):
        receipt = valid_receipt()
        receipt["claims"]["whole_gwt_credit"] = "PASS"
        self.assertEqual(validate_error(receipt), "BOOT_RECEIPT_CANNOT_GRANT_WHOLE_GWT_CREDIT")

    def test_self_consistent_manifest_substitution_cannot_self_lock(self):
        receipt = copy.deepcopy(valid_receipt())
        receipt["bundled_core"]["manifest_sha256"] = "d" * 64
        receipt["bundled_core"]["integration_identity_sha256"] = "e" * 64
        self.assertEqual(
            validate_error(receipt),
            "BUNDLED_MANIFEST_SOURCE_LOCK_MISMATCH",
        )

    def test_source_lock_unknown_field_fails_closed(self):
        lock = valid_source_lock()
        lock["runtime_observed_manifest"] = H64
        self.assertEqual(
            validate_error(valid_receipt(), lock),
            "SOURCE_LOCK_UNKNOWN_FIELDS:runtime_observed_manifest",
        )


if __name__ == "__main__":
    unittest.main()
