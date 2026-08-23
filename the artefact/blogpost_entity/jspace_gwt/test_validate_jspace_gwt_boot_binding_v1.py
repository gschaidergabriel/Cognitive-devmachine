import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

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
            "first_actions": [
                {"action_id": "boot-1", "origin": "ZERO", "effect_requested": False}
            ],
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


def run_validator(receipt, source_lock=None):
    try:
        VALIDATOR.validate(receipt, source_lock=source_lock or valid_source_lock())
    except VALIDATOR.ValidationError as exc:
        return SimpleNamespace(returncode=1, stdout=f"FAIL {exc}\n", stderr="")
    return SimpleNamespace(
        returncode=0,
        stdout="PASS JSPACE_GWT_BOOT_BINDING_RECEIPT/v1\n",
        stderr="",
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

    def test_dirty_source_requires_diff_digest(self):
        receipt = valid_receipt()
        receipt["source"]["dirty"] = True
        cp = run_validator(receipt)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("dirty_diff_sha256", cp.stdout)

    def test_dirty_source_with_diff_digest_passes(self):
        receipt = valid_receipt()
        receipt["source"]["dirty"] = True
        receipt["source"]["dirty_diff_sha256"] = H64
        cp = run_validator(receipt)
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)

    def test_unknown_first_action_origin_fails_closed(self):
        receipt = valid_receipt()
        receipt["inference"]["first_actions"][0]["origin"] = "MODEL_GUESSED"
        cp = run_validator(receipt)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("INVALID_FIRST_ACTION_ORIGIN", cp.stdout)

    def test_duplicate_first_action_id_fails_closed(self):
        receipt = valid_receipt()
        receipt["inference"]["first_actions"].append(
            {"action_id": "boot-1", "origin": "CLAUDE_CODE", "effect_requested": False}
        )
        cp = run_validator(receipt)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("DUPLICATE_FIRST_ACTION_ID", cp.stdout)

    def test_other_first_action_origin_requires_detail(self):
        receipt = valid_receipt()
        receipt["inference"]["first_actions"][0]["origin"] = "OTHER"
        cp = run_validator(receipt)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("origin_detail", cp.stdout)

    def test_first_action_effect_flag_must_be_boolean(self):
        receipt = valid_receipt()
        receipt["inference"]["first_actions"][0]["effect_requested"] = 1
        cp = run_validator(receipt)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("effect_requested", cp.stdout)

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

    def test_self_consistent_manifest_substitution_cannot_self_lock(self):
        receipt = valid_receipt()
        receipt["bundled_core"]["manifest_sha256"] = "d" * 64
        receipt["bundled_core"]["integration_identity_sha256"] = "e" * 64
        cp = run_validator(receipt)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("BUNDLED_MANIFEST_SOURCE_LOCK_MISMATCH", cp.stdout)

    def test_source_lock_unknown_field_fails_closed(self):
        lock = valid_source_lock()
        lock["runtime_observed_manifest"] = H64
        cp = run_validator(valid_receipt(), source_lock=lock)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("SOURCE_LOCK_UNKNOWN_FIELDS:runtime_observed_manifest", cp.stdout)


if __name__ == "__main__":
    unittest.main()
