import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
VALIDATOR = HERE / "validate_jspace_gwt_boot_binding_v1.py"
H40 = "a" * 40
H64 = "b" * 64
C64 = "c" * 64
D64 = "d" * 64
E64 = "e" * 64
F64 = "f" * 64


def canonical_json_sha256(value):
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def valid_receipt():
    measurement = {
        "minimum_readout_position": 16,
        "observed_readout_positions": [16, 17, 31],
        "prompt_copy_confound_guard_enabled": True,
    }
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
            "tokenizer_sha256": C64,
            "runtime_sha256": D64,
            "manifest_sha256": E64,
            "integration_identity_sha256": F64,
            "source_lock_sha256": H64,
            "exact_bytes_verified": True,
        },
        "jspace": {
            "local_mode": "LOCAL_OBSERVE_ONLY",
            "jlens_upstream_commit": H40,
            "profile_sha256": C64,
            "lens_file_sha256": D64,
            "lens_profile_sha256": E64,
            "fit_corpus_sha256": F64,
            "n_prompts": 100,
            "skip_first_positions": 16,
            "storage_dtype": "float32",
            "numeric_integrity": {
                "pre_save_all_finite": True,
                "post_load_all_finite": True,
                "max_abs_pre_save": 12.5,
                "max_abs_post_load": 12.5,
            },
            "measurement_policy": measurement,
            "measurement_policy_sha256": canonical_json_sha256(measurement),
        },
        "gwt": {
            "workspace_policy_sha256": H64,
            "calibration_sha256": C64,
            "slot_count": 3,
            "calibration_status": "MEASURED_EXACT_BUNDLE",
        },
        "zero_grf": {
            "zero_identity_sha256": H64,
            "grf_sha256": C64,
            "projection_policy_sha256": D64,
        },
        "claude_adapter": {
            "adapter_version": "0",
            "capability_profile_sha256": E64,
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


def bound_source_lock(receipt):
    return {
        "schema": "mini-entity-bundled-cognition-source-lock/v1",
        "status": "BOUND",
        "lock_revision": 1,
        "engine_id": receipt["bundled_core"]["engine_id"],
        "model_family": receipt["bundled_core"]["model_family"],
        "manifest_version": receipt["bundled_core"]["manifest_version"],
        "checkpoint_sha256": receipt["bundled_core"]["checkpoint_sha256"],
        "tokenizer_sha256": receipt["bundled_core"]["tokenizer_sha256"],
        "runtime_sha256": receipt["bundled_core"]["runtime_sha256"],
        "manifest_identity_sha256": receipt["bundled_core"]["manifest_sha256"],
        "integration_identity_sha256": receipt["bundled_core"]["integration_identity_sha256"],
        "local_jspace_mode": receipt["jspace"]["local_mode"],
        "jlens_upstream_commit": receipt["jspace"]["jlens_upstream_commit"],
        "jspace_profile_sha256": receipt["jspace"]["profile_sha256"],
        "lens_file_sha256": receipt["jspace"]["lens_file_sha256"],
        "lens_profile_sha256": receipt["jspace"]["lens_profile_sha256"],
        "fit_corpus_sha256": receipt["jspace"]["fit_corpus_sha256"],
        "measurement_policy_sha256": receipt["jspace"]["measurement_policy_sha256"],
        "workspace_policy_sha256": receipt["gwt"]["workspace_policy_sha256"],
        "workspace_calibration_sha256": receipt["gwt"]["calibration_sha256"],
        "admission_evidence_receipt_sha256": D64,
        "note": "synthetic bound source lock for deterministic component regression only",
    }


def lock_bytes(lock):
    return (json.dumps(lock, indent=2, sort_keys=True) + "\n").encode("utf-8")


def run_validator(receipt, *, source_lock=None):
    receipt = copy.deepcopy(receipt)
    lock = copy.deepcopy(source_lock if source_lock is not None else bound_source_lock(receipt))
    raw_lock = lock_bytes(lock)
    receipt["bundled_core"]["source_lock_sha256"] = hashlib.sha256(raw_lock).hexdigest()

    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "blogpost_entity"
        jspace_dir = root / "jspace_gwt"
        cognition_dir = root / "mini_cognition"
        jspace_dir.mkdir(parents=True)
        cognition_dir.mkdir(parents=True)
        validator = jspace_dir / VALIDATOR.name
        shutil.copyfile(VALIDATOR, validator)
        (cognition_dir / "BUNDLED_COGNITION_SOURCE_LOCK_V1.json").write_bytes(raw_lock)
        path = Path(td) / "receipt.json"
        path.write_text(json.dumps(receipt), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(validator), str(path)],
            text=True,
            capture_output=True,
            check=False,
        )


def run_repository_validator(receipt):
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
    def test_bound_exact_fixture_receipt_passes(self):
        cp = run_validator(valid_receipt())
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
        self.assertIn("SOURCE_LOCK_BOUND", cp.stdout)

    def test_repository_source_lock_is_intentionally_unbound_and_fails_closed(self):
        cp = run_repository_validator(valid_receipt())
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("SOURCE_LOCK_UNBOUND", cp.stdout)

    def test_self_consistent_false_receipt_cannot_self_lock(self):
        receipt = valid_receipt()
        lock = bound_source_lock(receipt)
        # Coherently substitute every self-reported bundle/J-Space/GWT identity
        # while the independently repository-owned expected lock stays unchanged.
        receipt["bundled_core"].update(
            checkpoint_sha256="1" * 64,
            tokenizer_sha256="2" * 64,
            runtime_sha256="3" * 64,
            manifest_sha256="4" * 64,
            integration_identity_sha256="5" * 64,
        )
        receipt["jspace"].update(
            profile_sha256="6" * 64,
            lens_file_sha256="7" * 64,
            lens_profile_sha256="8" * 64,
            fit_corpus_sha256="9" * 64,
        )
        receipt["gwt"].update(
            workspace_policy_sha256="0" * 64,
            calibration_sha256="1" * 64,
        )
        cp = run_validator(receipt, source_lock=lock)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("EXPECTED_BUNDLE_MISMATCH", cp.stdout)

    def test_source_lock_byte_identity_mismatch_fails_closed(self):
        receipt = valid_receipt()
        lock = bound_source_lock(receipt)
        cp = run_validator(receipt, source_lock=lock)
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
        # Directly exercise a bad reported lock digest against the same fixed lock.
        raw_lock = lock_bytes(lock)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "blogpost_entity"
            jspace_dir = root / "jspace_gwt"
            cognition_dir = root / "mini_cognition"
            jspace_dir.mkdir(parents=True)
            cognition_dir.mkdir(parents=True)
            validator = jspace_dir / VALIDATOR.name
            shutil.copyfile(VALIDATOR, validator)
            (cognition_dir / "BUNDLED_COGNITION_SOURCE_LOCK_V1.json").write_bytes(raw_lock)
            bad = valid_receipt()
            bad["bundled_core"]["source_lock_sha256"] = "f" * 64
            path = Path(td) / "receipt.json"
            path.write_text(json.dumps(bad), encoding="utf-8")
            cp = subprocess.run(
                [sys.executable, str(validator), str(path)],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("SOURCE_LOCK_BYTE_IDENTITY_MISMATCH", cp.stdout)

    def test_unmeasured_gwt_cannot_pass_bound_source_lock(self):
        receipt = valid_receipt()
        receipt["gwt"]["calibration_status"] = "UNMEASURED_SOURCE_ONLY"
        cp = run_validator(receipt, source_lock=bound_source_lock(valid_receipt()))
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("BOUND_SOURCE_LOCK_REQUIRES_MEASURED_GWT_CALIBRATION", cp.stdout)

    def test_poison_post_load_nonfinite_fails_closed(self):
        receipt = valid_receipt()
        receipt["jspace"]["numeric_integrity"]["post_load_all_finite"] = False
        cp = run_validator(receipt)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("LENS_POST_LOAD_NONFINITE", cp.stdout)

    def test_poison_unfitted_readout_position_fails_closed(self):
        receipt = valid_receipt()
        receipt["jspace"]["measurement_policy"]["observed_readout_positions"] = [8, 16]
        cp = run_validator(receipt, source_lock=bound_source_lock(valid_receipt()))
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("JSPACE_UNFITTED_POSITION", cp.stdout)

    def test_measurement_policy_digest_is_not_self_report_only(self):
        receipt = valid_receipt()
        receipt["jspace"]["measurement_policy"]["observed_readout_positions"] = [16, 18, 31]
        cp = run_validator(receipt, source_lock=bound_source_lock(valid_receipt()))
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("MEASUREMENT_POLICY_DIGEST_MISMATCH", cp.stdout)

    def test_prompt_copy_guard_cannot_be_disabled(self):
        receipt = valid_receipt()
        receipt["jspace"]["measurement_policy"]["prompt_copy_confound_guard_enabled"] = False
        cp = run_validator(receipt, source_lock=bound_source_lock(valid_receipt()))
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


if __name__ == "__main__":
    unittest.main()
