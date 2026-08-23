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
H40 = "a" * 40
H64 = "b" * 64
ROLES = {
    "bundled_manifest": ("bundled_core", "manifest_sha256"),
    "checkpoint": ("bundled_core", "checkpoint_sha256"),
    "tokenizer": ("bundled_core", "tokenizer_sha256"),
    "runtime": ("bundled_core", "runtime_sha256"),
    "lens_file": ("jspace", "lens_file_sha256"),
    "lens_profile": ("jspace", "lens_profile_sha256"),
    "fit_corpus": ("jspace", "fit_corpus_sha256"),
    "workspace_policy": ("gwt", "workspace_policy_sha256"),
    "gwt_calibration": ("gwt", "calibration_sha256"),
    "zero_identity": ("zero_grf", "zero_identity_sha256"),
    "grf": ("zero_grf", "grf_sha256"),
    "projection_policy": ("zero_grf", "projection_policy_sha256"),
    "claude_capability_profile": ("claude_adapter", "capability_profile_sha256"),
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def valid_receipt(root: Path):
    payloads = {role: f"artifact:{role}".encode() for role in ROLES}
    digests = {role: sha(data) for role, data in payloads.items()}
    for role, data in payloads.items():
        path = root / "artifacts" / f"{role}.bin"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    receipt = {
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
            "checkpoint_sha256": digests["checkpoint"],
            "tokenizer_sha256": digests["tokenizer"],
            "runtime_sha256": digests["runtime"],
            "manifest_sha256": digests["bundled_manifest"],
            "layer_count": 24,
            "d_model": 2048,
            "exact_bytes_verified": True,
        },
        "jspace": {
            "jlens_upstream_commit": H40,
            "lens_file_sha256": digests["lens_file"],
            "lens_profile_sha256": digests["lens_profile"],
            "fit_corpus_sha256": digests["fit_corpus"],
            "source_checkpoint_sha256": digests["checkpoint"],
            "source_tokenizer_sha256": digests["tokenizer"],
            "d_model": 2048,
            "source_layers": [4, 8, 12, 16, 20],
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
            "workspace_policy_sha256": digests["workspace_policy"],
            "calibration_sha256": digests["gwt_calibration"],
            "slot_count": 3,
            "calibration_status": "UNMEASURED_SOURCE_ONLY",
        },
        "zero_grf": {
            "zero_identity_sha256": digests["zero_identity"],
            "grf_sha256": digests["grf"],
            "projection_policy_sha256": digests["projection_policy"],
        },
        "claude_adapter": {
            "adapter_version": "0",
            "capability_profile_sha256": digests["claude_capability_profile"],
            "enabled": False,
        },
        "inference": {
            "first_engine_choice": "BUNDLED_LOCAL_08B",
            "origin_attribution": "boot-probe",
            "inference_packet_sha256": H64,
        },
        "control": {
            "free_only": True,
            "paid_or_unknown_provider_network_attempted": False,
        },
        "artifact_bindings": {
            role: {
                "path": f"artifacts/{role}.bin",
                "sha256": digests[role],
                "size_bytes": len(payloads[role]),
            }
            for role in ROLES
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
    return receipt


def run_validator(receipt, root: Path):
    path = root / "receipt.json"
    path.write_text(json.dumps(receipt), encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(path), str(root)],
        text=True,
        capture_output=True,
        check=False,
    )


class BootBindingValidatorTests(unittest.TestCase):
    def with_fixture(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        return td, root, valid_receipt(root)

    def test_valid_source_only_receipt_passes(self):
        td, root, receipt = self.with_fixture()
        try:
            cp = run_validator(receipt, root)
            self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
        finally:
            td.cleanup()

    def test_actual_checkpoint_bytes_are_hashed_not_boolean_trusted(self):
        td, root, receipt = self.with_fixture()
        try:
            (root / receipt["artifact_bindings"]["checkpoint"]["path"]).write_bytes(b"substituted")
            cp = run_validator(receipt, root)
            self.assertNotEqual(cp.returncode, 0)
            self.assertIn("ARTIFACT_SIZE_MISMATCH:checkpoint", cp.stdout)
        finally:
            td.cleanup()

    def test_path_escape_fails_closed(self):
        td, root, receipt = self.with_fixture()
        try:
            receipt["artifact_bindings"]["checkpoint"]["path"] = "../checkpoint.bin"
            cp = run_validator(receipt, root)
            self.assertNotEqual(cp.returncode, 0)
            self.assertIn("ARTIFACT_PATH_OUTSIDE_ROOT_OR_MISSING:checkpoint", cp.stdout)
        finally:
            td.cleanup()

    def test_foreign_checkpoint_lens_provenance_fails_closed(self):
        td, root, receipt = self.with_fixture()
        try:
            receipt["jspace"]["source_checkpoint_sha256"] = H64
            cp = run_validator(receipt, root)
            self.assertNotEqual(cp.returncode, 0)
            self.assertIn("JSPACE_CHECKPOINT_PROVENANCE_MISMATCH", cp.stdout)
        finally:
            td.cleanup()

    def test_lens_geometry_must_match_core(self):
        td, root, receipt = self.with_fixture()
        try:
            receipt["jspace"]["d_model"] = 4096
            cp = run_validator(receipt, root)
            self.assertNotEqual(cp.returncode, 0)
            self.assertIn("JSPACE_D_MODEL_MISMATCH", cp.stdout)
        finally:
            td.cleanup()

    def test_lens_source_layer_must_be_inside_core(self):
        td, root, receipt = self.with_fixture()
        try:
            receipt["jspace"]["source_layers"] = [4, 24]
            cp = run_validator(receipt, root)
            self.assertNotEqual(cp.returncode, 0)
            self.assertIn("JSPACE_SOURCE_LAYER_OUT_OF_RANGE", cp.stdout)
        finally:
            td.cleanup()

    def test_free_only_forbids_paid_unknown_network(self):
        td, root, receipt = self.with_fixture()
        try:
            receipt["control"]["paid_or_unknown_provider_network_attempted"] = True
            cp = run_validator(receipt, root)
            self.assertNotEqual(cp.returncode, 0)
            self.assertIn("PAID_OR_UNKNOWN_PROVIDER_NETWORK_ATTEMPTED", cp.stdout)
        finally:
            td.cleanup()

    def test_poison_post_load_nonfinite_fails_closed(self):
        td, root, receipt = self.with_fixture()
        try:
            receipt["jspace"]["numeric_integrity"]["post_load_all_finite"] = False
            cp = run_validator(receipt, root)
            self.assertNotEqual(cp.returncode, 0)
            self.assertIn("LENS_POST_LOAD_NONFINITE", cp.stdout)
        finally:
            td.cleanup()

    def test_poison_unfitted_readout_position_fails_closed(self):
        td, root, receipt = self.with_fixture()
        try:
            receipt["jspace"]["measurement_policy"]["observed_readout_positions"] = [8, 16]
            cp = run_validator(receipt, root)
            self.assertNotEqual(cp.returncode, 0)
            self.assertIn("JSPACE_UNFITTED_POSITION", cp.stdout)
        finally:
            td.cleanup()

    def test_prompt_copy_guard_cannot_be_disabled(self):
        td, root, receipt = self.with_fixture()
        try:
            receipt["jspace"]["measurement_policy"]["prompt_copy_confound_guard_enabled"] = False
            cp = run_validator(receipt, root)
            self.assertNotEqual(cp.returncode, 0)
            self.assertIn("PROMPT_COPY_CONFOUND_GUARD_DISABLED", cp.stdout)
        finally:
            td.cleanup()

    def test_boot_receipt_cannot_claim_whole_gwt(self):
        td, root, receipt = self.with_fixture()
        try:
            receipt["claims"]["whole_gwt_credit"] = "PASS"
            cp = run_validator(receipt, root)
            self.assertNotEqual(cp.returncode, 0)
            self.assertIn("BOOT_RECEIPT_CANNOT_GRANT_WHOLE_GWT_CREDIT", cp.stdout)
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
