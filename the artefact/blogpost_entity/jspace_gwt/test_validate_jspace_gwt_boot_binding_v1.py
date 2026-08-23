import importlib.util
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

SPEC = importlib.util.spec_from_file_location("boot_validator", VALIDATOR)
boot_validator = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(boot_validator)

try:
    import torch
except ImportError:  # pragma: no cover - CI environment dependent
    torch = None


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
            "lens_semantic_sha256": "c" * 64,
            "lens_semantic_digest_method": "ordered-fp32-finite-v1",
            "lens_profile_sha256": H64,
            "fit_corpus_sha256": H64,
            "n_prompts": 100,
            "d_model": 2,
            "source_layers": [1, 2],
            "sparsity_k": 8,
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
        "policy": {
            "free_only": True,
            "paid_or_unknown_network_attempts": 0,
            "paid_or_unknown_secret_lookups": 0,
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


def run_validator(receipt, lens_path=None):
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "receipt.json"
        path.write_text(json.dumps(receipt), encoding="utf-8")
        command = [sys.executable, str(VALIDATOR), str(path)]
        if lens_path is not None:
            command.append(str(lens_path))
        return subprocess.run(command, text=True, capture_output=True, check=False)


def lens_checkpoint():
    if torch is None:
        raise unittest.SkipTest("torch unavailable")
    return {
        "J": {
            1: torch.tensor([[1.0, 2.0], [3.0, 4.0]]),
            2: torch.tensor([[5.0, 6.0], [7.0, 8.0]]),
        },
        "n_prompts": 100,
        "source_layers": [1, 2],
        "d_model": 2,
    }


class BootBindingValidatorTests(unittest.TestCase):
    def test_valid_source_only_receipt_passes_structural_only(self):
        cp = run_validator(valid_receipt())
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
        self.assertIn("STRUCTURAL_ONLY", cp.stdout)

    def test_dirty_source_fails_closed(self):
        receipt = valid_receipt()
        receipt["source"]["dirty"] = True
        cp = run_validator(receipt)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("SOURCE_DIRTY", cp.stdout)

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

    def test_semantic_digest_is_mandatory(self):
        receipt = valid_receipt()
        del receipt["jspace"]["lens_semantic_sha256"]
        cp = run_validator(receipt)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("MISSING_STRING:lens_semantic_sha256", cp.stdout)

    def test_jspace_sparsity_k_is_mandatory(self):
        receipt = valid_receipt()
        receipt["jspace"]["sparsity_k"] = 0
        cp = run_validator(receipt)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("INVALID_INT:sparsity_k", cp.stdout)

    def test_free_only_secret_lookup_fails_closed(self):
        receipt = valid_receipt()
        receipt["policy"]["paid_or_unknown_secret_lookups"] = 1
        cp = run_validator(receipt)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("FREE_ONLY_BOUNDARY_BREACH", cp.stdout)

    @unittest.skipIf(torch is None, "torch unavailable")
    def test_equivalent_save_semantics_regression(self):
        checkpoint = lens_checkpoint()
        with tempfile.TemporaryDirectory() as td:
            first = Path(td) / "first.pt"
            second = Path(td) / "second.pt"
            torch.save(checkpoint, first)
            torch.save(checkpoint, second)
            a = boot_validator.semantic_digest_from_lens_checkpoint(first)
            b = boot_validator.semantic_digest_from_lens_checkpoint(second)
            self.assertNotEqual(a["artifact_sha256"], b["artifact_sha256"])
            self.assertEqual(a["semantic_sha256"], b["semantic_sha256"])

    @unittest.skipIf(torch is None, "torch unavailable")
    def test_exact_lens_artifact_binds_byte_and_semantic_identity(self):
        checkpoint = lens_checkpoint()
        with tempfile.TemporaryDirectory() as td:
            lens_path = Path(td) / "lens.pt"
            torch.save(checkpoint, lens_path)
            observed = boot_validator.semantic_digest_from_lens_checkpoint(lens_path)
            receipt = valid_receipt()
            receipt["jspace"].update(
                {
                    "lens_file_sha256": observed["artifact_sha256"],
                    "lens_semantic_sha256": observed["semantic_sha256"],
                    "n_prompts": observed["n_prompts"],
                    "d_model": observed["d_model"],
                    "source_layers": observed["source_layers"],
                }
            )
            cp = run_validator(receipt, lens_path)
            self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
            self.assertIn("EXACT_LENS_ARTIFACT_VERIFIED", cp.stdout)

    @unittest.skipIf(torch is None, "torch unavailable")
    def test_exact_lens_artifact_rejects_nonfinite_matrix(self):
        checkpoint = lens_checkpoint()
        checkpoint["J"][1][0, 0] = float("inf")
        with tempfile.TemporaryDirectory() as td:
            lens_path = Path(td) / "lens.pt"
            torch.save(checkpoint, lens_path)
            receipt = valid_receipt()
            cp = run_validator(receipt, lens_path)
            self.assertNotEqual(cp.returncode, 0)
            self.assertIn("LENS_POST_LOAD_NONFINITE", cp.stdout)


if __name__ == "__main__":
    unittest.main()
