import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
VALIDATOR = HERE / "validate_jspace_gwt_boot_binding_v1.py"
MINI_COGNITION = HERE.parent / "mini_cognition"
if str(MINI_COGNITION) not in sys.path:
    sys.path.insert(0, str(MINI_COGNITION))
from bundled_cognition_manifest_v1 import validate_manifest

H40 = "a" * 40
D0 = "0" * 64
D1 = "1" * 64
D2 = "2" * 64
D3 = "3" * 64
D4 = "4" * 64
D5 = "5" * 64
D6 = "6" * 64
D7 = "7" * 64
D8 = "8" * 64
D9 = "9" * 64


def valid_manifest():
    return {
        "schema": "mini-entity-bundled-cognition-manifest/v1",
        "engine_id": "bundled-qwen35-08b",
        "model_family": "Qwen3.5-0.8B",
        "checkpoint_digest": D8,
        "tokenizer_digest": D1,
        "quantization_runtime_identity": "gguf-q4_k_m+llama.cpp:test-fixture",
        "runtime_digest": D7,
        "lens_artifact_digest": D9,
        "fit_corpus_digest": D6,
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


def manifest_bytes(manifest):
    return json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def source_lock_for(manifest, raw):
    validated = validate_manifest(manifest)
    return {
        "schema": "BUNDLED_COGNITION_SOURCE_LOCK/v1",
        "status": "BOUND",
        "authority": "repository_source_tree",
        "manifest_file_sha256": hashlib.sha256(raw).hexdigest(),
        "manifest_identity_sha256": validated.manifest_identity_sha256,
        "integration_identity_sha256": validated.integration_identity_sha256,
        "note": "unit fixture",
    }


def valid_receipt(manifest, raw):
    return {
        "schema": "JSPACE_GWT_BOOT_BINDING_RECEIPT/v1",
        "source": {"main_sha": H40, "tree_sha": H40, "dirty": False},
        "runtime": {"entity_generation": 276},
        "executor": {"host_class": "UBUNTU", "host_identity_sha256": D6, "kernel": "Linux 6.x"},
        "bundled_core": {
            "manifest_version": manifest["schema"],
            "engine_id": manifest["engine_id"],
            "model_family": manifest["model_family"],
            "checkpoint_sha256": manifest["checkpoint_digest"],
            "tokenizer_sha256": manifest["tokenizer_digest"],
            "runtime_sha256": manifest["runtime_digest"],
            "manifest_sha256": hashlib.sha256(raw).hexdigest(),
            "quantization_runtime_identity": manifest["quantization_runtime_identity"],
            "exact_bytes_verified": True,
        },
        "jspace": {
            "jlens_upstream_commit": H40,
            "jspace_profile_sha256": manifest["jspace_profile_digest"],
            "lens_file_sha256": manifest["lens_artifact_digest"],
            "lens_profile_sha256": manifest["lens_profile_digest"],
            "steering_calibration_sha256": manifest["steering_calibration_digest"],
            "fit_corpus_sha256": manifest["fit_corpus_digest"],
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
            "workspace_policy_sha256": D6,
            "calibration_sha256": manifest["workspace_calibration_digest"],
            "slot_count": None,
            "calibration_status": "UNMEASURED_SOURCE_ONLY",
        },
        "zero_grf": {"zero_identity_sha256": D6, "grf_sha256": D6, "projection_policy_sha256": D6},
        "claude_adapter": {"adapter_version": "0", "capability_profile_sha256": D6, "enabled": False},
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


def run_validator(receipt=None, manifest=None, source_lock=None):
    manifest = valid_manifest() if manifest is None else manifest
    raw = manifest_bytes(manifest)
    receipt = valid_receipt(manifest, raw) if receipt is None else receipt
    source_lock = source_lock_for(manifest, raw) if source_lock is None else source_lock
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        receipt_path = td / "receipt.json"
        manifest_path = td / "manifest.json"
        lock_path = td / "lock.json"
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
        manifest_path.write_bytes(raw)
        lock_path.write_text(json.dumps(source_lock), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(VALIDATOR), str(receipt_path), str(manifest_path), str(lock_path)],
            text=True,
            capture_output=True,
            check=False,
        )


class BootBindingValidatorTests(unittest.TestCase):
    def test_valid_bound_receipt_passes(self):
        cp = run_validator()
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)

    def test_runtime_generation_is_required_and_not_boolean(self):
        m = valid_manifest(); raw = manifest_bytes(m); r = valid_receipt(m, raw); r.pop("runtime")
        cp = run_validator(receipt=r)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("MISSING_OBJECT:runtime", cp.stdout)

        r = valid_receipt(m, raw); r["runtime"]["entity_generation"] = True
        cp = run_validator(receipt=r)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("INVALID_INT:entity_generation", cp.stdout)

    def test_source_lock_must_be_bound(self):
        m = valid_manifest(); raw = manifest_bytes(m); lock = source_lock_for(m, raw); lock["status"] = "UNBOUND"
        cp = run_validator(source_lock=lock)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("SOURCE_LOCK_NOT_BOUND", cp.stdout)

    def test_dirty_source_requires_diff_digest(self):
        m = valid_manifest(); raw = manifest_bytes(m); r = valid_receipt(m, raw); r["source"]["dirty"] = True
        cp = run_validator(receipt=r)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("dirty_diff_sha256", cp.stdout)

    def test_dirty_source_with_diff_digest_passes(self):
        m = valid_manifest(); raw = manifest_bytes(m); r = valid_receipt(m, raw); r["source"]["dirty"] = True; r["source"]["dirty_diff_sha256"] = D6
        cp = run_validator(receipt=r)
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)

    def test_unknown_first_action_origin_fails_closed(self):
        m = valid_manifest(); raw = manifest_bytes(m); r = valid_receipt(m, raw); r["inference"]["first_actions"][0]["origin"] = "MODEL_GUESSED"
        cp = run_validator(receipt=r)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("INVALID_FIRST_ACTION_ORIGIN", cp.stdout)

    def test_duplicate_first_action_id_fails_closed(self):
        m = valid_manifest(); raw = manifest_bytes(m); r = valid_receipt(m, raw); r["inference"]["first_actions"].append({"action_id": "boot-1", "origin": "CLAUDE_CODE", "effect_requested": False})
        cp = run_validator(receipt=r)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("DUPLICATE_FIRST_ACTION_ID", cp.stdout)

    def test_other_first_action_origin_requires_detail(self):
        m = valid_manifest(); raw = manifest_bytes(m); r = valid_receipt(m, raw); r["inference"]["first_actions"][0]["origin"] = "OTHER"
        cp = run_validator(receipt=r)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("origin_detail", cp.stdout)

    def test_first_action_effect_flag_must_be_boolean(self):
        m = valid_manifest(); raw = manifest_bytes(m); r = valid_receipt(m, raw); r["inference"]["first_actions"][0]["effect_requested"] = 1
        cp = run_validator(receipt=r)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("effect_requested", cp.stdout)

    def test_boot_checkpoint_must_match_manifest(self):
        m = valid_manifest(); raw = manifest_bytes(m); r = valid_receipt(m, raw); r["bundled_core"]["checkpoint_sha256"] = D7
        cp = run_validator(receipt=r)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("BOOT_CHECKPOINT_MISMATCH", cp.stdout)

    def test_boot_runtime_digest_must_match_manifest(self):
        m = valid_manifest(); raw = manifest_bytes(m); r = valid_receipt(m, raw); r["bundled_core"]["runtime_sha256"] = D6
        cp = run_validator(receipt=r)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("BOOT_RUNTIME_DIGEST_MISMATCH", cp.stdout)

    def test_boot_manifest_requires_runtime_digest(self):
        m = valid_manifest(); del m["runtime_digest"]; raw = manifest_bytes(m)
        r = valid_receipt(valid_manifest(), manifest_bytes(valid_manifest()))
        r["bundled_core"]["manifest_sha256"] = hashlib.sha256(raw).hexdigest()
        lock = source_lock_for(m, raw)
        cp = run_validator(receipt=r, manifest=m, source_lock=lock)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("BOOT_MANIFEST_RUNTIME_DIGEST_REQUIRED", cp.stdout)

    def test_boot_jspace_profile_must_match_manifest(self):
        m = valid_manifest(); raw = manifest_bytes(m); r = valid_receipt(m, raw); r["jspace"]["jspace_profile_sha256"] = D7
        cp = run_validator(receipt=r)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("BOOT_JSPACE_PROFILE_MISMATCH", cp.stdout)

    def test_boot_lens_artifact_digest_must_match_manifest(self):
        m = valid_manifest(); raw = manifest_bytes(m); r = valid_receipt(m, raw); r["jspace"]["lens_file_sha256"] = D6
        cp = run_validator(receipt=r)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("BOOT_LENS_ARTIFACT_DIGEST_MISMATCH", cp.stdout)

    def test_boot_manifest_requires_lens_artifact_digest(self):
        m = valid_manifest(); del m["lens_artifact_digest"]; raw = manifest_bytes(m)
        r = valid_receipt(valid_manifest(), manifest_bytes(valid_manifest()))
        r["bundled_core"]["manifest_sha256"] = hashlib.sha256(raw).hexdigest()
        lock = source_lock_for(m, raw)
        cp = run_validator(receipt=r, manifest=m, source_lock=lock)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("BOOT_MANIFEST_LENS_ARTIFACT_DIGEST_REQUIRED", cp.stdout)

    def test_boot_fit_corpus_must_match_manifest(self):
        m = valid_manifest(); raw = manifest_bytes(m); r = valid_receipt(m, raw); r["jspace"]["fit_corpus_sha256"] = D7
        cp = run_validator(receipt=r)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("BOOT_FIT_CORPUS_MISMATCH", cp.stdout)

    def test_boot_manifest_requires_fit_corpus_digest(self):
        m = valid_manifest(); del m["fit_corpus_digest"]; raw = manifest_bytes(m)
        r = valid_receipt(valid_manifest(), manifest_bytes(valid_manifest()))
        r["bundled_core"]["manifest_sha256"] = hashlib.sha256(raw).hexdigest()
        lock = source_lock_for(m, raw)
        cp = run_validator(receipt=r, manifest=m, source_lock=lock)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("BOOT_MANIFEST_FIT_CORPUS_DIGEST_REQUIRED", cp.stdout)

    def test_source_lock_rejects_alternate_manifest_identity(self):
        m = valid_manifest(); raw = manifest_bytes(m); lock = source_lock_for(m, raw)
        m2 = copy.deepcopy(m); m2["workspace_calibration_digest"] = D7
        raw2 = manifest_bytes(m2); r2 = valid_receipt(m2, raw2)
        cp = run_validator(receipt=r2, manifest=m2, source_lock=lock)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("SOURCE_LOCK_MANIFEST_FILE_MISMATCH", cp.stdout)

    def test_poison_post_load_nonfinite_fails_closed(self):
        m = valid_manifest(); raw = manifest_bytes(m); r = valid_receipt(m, raw); r["jspace"]["numeric_integrity"]["post_load_all_finite"] = False
        cp = run_validator(receipt=r)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("LENS_POST_LOAD_NONFINITE", cp.stdout)

    def test_poison_unfitted_readout_position_fails_closed(self):
        m = valid_manifest(); raw = manifest_bytes(m); r = valid_receipt(m, raw); r["jspace"]["measurement_policy"]["observed_readout_positions"] = [8, 16]
        cp = run_validator(receipt=r)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("JSPACE_UNFITTED_POSITION", cp.stdout)

    def test_prompt_copy_guard_cannot_be_disabled(self):
        m = valid_manifest(); raw = manifest_bytes(m); r = valid_receipt(m, raw); r["jspace"]["measurement_policy"]["prompt_copy_confound_guard_enabled"] = False
        cp = run_validator(receipt=r)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("PROMPT_COPY_CONFOUND_GUARD_DISABLED", cp.stdout)

    def test_boot_receipt_cannot_claim_whole_gwt(self):
        m = valid_manifest(); raw = manifest_bytes(m); r = valid_receipt(m, raw); r["claims"]["whole_gwt_credit"] = "PASS"
        cp = run_validator(receipt=r)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("BOOT_RECEIPT_CANNOT_GRANT_WHOLE_GWT_CREDIT", cp.stdout)

    def test_placeholder_digest_fails_closed(self):
        m = valid_manifest(); raw = manifest_bytes(m); r = valid_receipt(m, raw); r["bundled_core"]["runtime_sha256"] = D0
        cp = run_validator(receipt=r)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("PLACEHOLDER_SHA64:runtime_sha256", cp.stdout)

    def test_unmeasured_gwt_cannot_bind_slot_count(self):
        m = valid_manifest(); raw = manifest_bytes(m); r = valid_receipt(m, raw); r["gwt"]["slot_count"] = 3
        cp = run_validator(receipt=r)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("UNMEASURED_GWT_SLOT_COUNT_MUST_BE_NULL", cp.stdout)

    def test_measured_gwt_requires_positive_slot_count(self):
        m = valid_manifest(); raw = manifest_bytes(m); r = valid_receipt(m, raw)
        r["gwt"]["calibration_status"] = "MEASURED_EXACT_BUNDLE"
        r["gwt"]["slot_count"] = None
        cp = run_validator(receipt=r)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("INVALID_INT:slot_count", cp.stdout)
        r["gwt"]["slot_count"] = 3
        cp = run_validator(receipt=r)
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)


if __name__ == "__main__":
    unittest.main()
