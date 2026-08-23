import copy
import tempfile
import unittest
from pathlib import Path

import torch

from jspace_boot_binding_v1 import (
    ReceiptError,
    semantic_digest_from_lens_checkpoint,
    validate_receipt,
    verify_lens_artifact,
)

H = "a" * 64
G = "b" * 40


def good():
    return {
        "schema": "JSPACE_GWT_BOOT_BINDING_RECEIPT/v1",
        "source": {"repo_commit": G, "repo_tree": G, "dirty": False},
        "bundled_core": {
            "engine_id": "bundled-08b",
            "model_family": "qwen3.5-0.8b",
            "checkpoint_sha256": H,
            "tokenizer_sha256": H,
            "runtime_identity": "torch-test",
        },
        "lens": {
            "implementation_commit": G,
            "artifact_sha256": H,
            "semantic_content_sha256": "c" * 64,
            "semantic_digest_method": "ordered-fp32-finite-v1",
            "fit_corpus_sha256": H,
            "fit_prompt_count": 100,
            "source_layers": [1, 2, 3],
            "target_layer": 4,
            "finite_check_passed": True,
        },
        "workspace": {
            "jspace_profile_sha256": H,
            "lens_profile_sha256": H,
            "gwt_policy_sha256": H,
            "workspace_calibration_sha256": H,
            "jspace_mode": "FULL_LOCAL_LATENT",
            "jspace_sparsity_k": 8,
            "gwt_slot_limit": 3,
        },
        "control_projection": {
            "zero_identity_sha256": H,
            "grf_sha256": H,
            "hyperposition_state_sha256": None,
        },
        "claude_adapter": {
            "adapter_version": "v1",
            "capability_profile_sha256": H,
            "transport_profile_sha256": H,
        },
        "runtime": {
            "execution_surface": "authorized-isolated-test",
            "started": True,
            "first_engine_choice": "bundled-08b",
            "first_action_origin": "zero",
        },
        "policy": {
            "free_only": True,
            "paid_or_unknown_network_attempts": 0,
            "paid_or_unknown_secret_lookups": 0,
        },
    }


def lens_checkpoint():
    return {
        "J": {
            1: torch.tensor([[1.0, 2.0], [3.0, 4.0]]),
            2: torch.tensor([[5.0, 6.0], [7.0, 8.0]]),
        },
        "n_prompts": 100,
        "source_layers": [1, 2],
        "d_model": 2,
    }


class ContractTests(unittest.TestCase):
    def test_accepts_complete_binding(self):
        self.assertTrue(validate_receipt(good())["ok"])

    def test_rejects_file_hash_as_only_lens_identity(self):
        receipt = good()
        del receipt["lens"]["semantic_content_sha256"]
        with self.assertRaisesRegex(ReceiptError, "MISSING_STRING:semantic_content_sha256"):
            validate_receipt(receipt)

    def test_rejects_nonfinite_lens_flag(self):
        receipt = good()
        receipt["lens"]["finite_check_passed"] = False
        with self.assertRaisesRegex(ReceiptError, "NONFINITE_LENS_REJECTED"):
            validate_receipt(receipt)

    def test_rejects_noncanonical_layer_identity(self):
        receipt = good()
        receipt["lens"]["source_layers"] = [2, 1, 2]
        with self.assertRaisesRegex(ReceiptError, "SOURCE_LAYERS_NOT_CANONICAL"):
            validate_receipt(receipt)

    def test_requires_jspace_sparsity_k(self):
        receipt = good()
        receipt["workspace"]["jspace_sparsity_k"] = 0
        with self.assertRaisesRegex(ReceiptError, "ZERO_INT:jspace_sparsity_k"):
            validate_receipt(receipt)

    def test_free_only_fail_closed(self):
        receipt = good()
        receipt["policy"]["paid_or_unknown_secret_lookups"] = 1
        with self.assertRaisesRegex(ReceiptError, "FREE_ONLY_BOUNDARY_BREACH"):
            validate_receipt(receipt)

    def test_source_must_be_clean(self):
        receipt = good()
        receipt["source"]["dirty"] = True
        with self.assertRaisesRegex(ReceiptError, "DIRTY_SOURCE_FORBIDDEN"):
            validate_receipt(receipt)

    def test_semantic_digest_rejects_nonfinite_tensor(self):
        checkpoint = lens_checkpoint()
        checkpoint["J"][1][0, 0] = float("inf")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "lens.pt"
            torch.save(checkpoint, path)
            with self.assertRaisesRegex(ReceiptError, "NONFINITE_LENS_REJECTED"):
                semantic_digest_from_lens_checkpoint(path)

    def test_equivalent_save_semantics_regression(self):
        """Regression-only replay of the already-observed serialization condition."""
        checkpoint = lens_checkpoint()
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.pt"
            second = Path(directory) / "second.pt"
            torch.save(checkpoint, first)
            torch.save(checkpoint, second)
            a = semantic_digest_from_lens_checkpoint(first)
            b = semantic_digest_from_lens_checkpoint(second)
            self.assertNotEqual(a["artifact_sha256"], b["artifact_sha256"])
            self.assertEqual(a["semantic_content_sha256"], b["semantic_content_sha256"])

    def test_verify_lens_artifact_binds_both_identities(self):
        checkpoint = lens_checkpoint()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "lens.pt"
            torch.save(checkpoint, path)
            observed = semantic_digest_from_lens_checkpoint(path)
            receipt = good()
            receipt["lens"].update(
                {
                    "artifact_sha256": observed["artifact_sha256"],
                    "semantic_content_sha256": observed["semantic_content_sha256"],
                    "fit_prompt_count": observed["n_prompts"],
                    "source_layers": observed["source_layers"],
                    "target_layer": 3,
                }
            )
            self.assertTrue(verify_lens_artifact(receipt, path)["lens_artifact_verified"])
            tampered = copy.deepcopy(receipt)
            tampered["lens"]["artifact_sha256"] = H
            with self.assertRaisesRegex(ReceiptError, "LENS_ARTIFACT_HASH_MISMATCH"):
                verify_lens_artifact(tampered, path)


if __name__ == "__main__":
    unittest.main()
