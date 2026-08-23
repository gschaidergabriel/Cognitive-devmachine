import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
VALIDATOR = HERE / "validate_jspace_gwt_boot_binding_v1.py"
H40 = "a" * 40
H64 = "b" * 64


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


def run_validator(receipt):
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "receipt.json"
        path.write_text(json.dumps(receipt), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(VALIDATOR), str(path)],
            text=True,
            capture_output=True,
            check=False,
        )


class BootBindingValidatorTests(unittest.TestCase):
    def test_valid_source_only_receipt_passes(self):
        cp = run_validator(valid_receipt())
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)

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

    def test_boot_receipt_cannot_claim_whole_gwt(self):
        receipt = valid_receipt()
        receipt["claims"]["whole_gwt_credit"] = "PASS"
        cp = run_validator(receipt)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("BOOT_RECEIPT_CANNOT_GRANT_WHOLE_GWT_CREDIT", cp.stdout)


if __name__ == "__main__":
    unittest.main()
