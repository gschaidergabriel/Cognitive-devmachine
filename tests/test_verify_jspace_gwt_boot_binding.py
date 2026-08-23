from __future__ import annotations

import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "verify_jspace_gwt_boot_binding.py"
SPEC = importlib.util.spec_from_file_location("jspace_boot", MODULE_PATH)
mod = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(mod)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class JspaceBootBindingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.payloads = {
            "bundled_core_manifest": b"manifest",
            "checkpoint": b"checkpoint-A",
            "tokenizer": b"tokenizer-A",
            "local_runtime": b"runtime-A",
            "jacobian_lens": b"lens-A",
            "workspace_policy": b"workspace-A",
            "zero_identity": b"zero-A",
            "grf_projection": b"grf-A",
            "claude_adapter": b"claude-adapter-A",
            "claude_capability_profile": b"claude-profile-A",
        }
        artifacts = []
        for role, data in self.payloads.items():
            path = f"artifacts/{role}.bin"
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            artifacts.append({"role": role, "path": path, "sha256": sha(data), "size_bytes": len(data)})
        by = {x["role"]: x for x in artifacts}
        self.receipt = {
            "receipt_version": mod.RECEIPT_VERSION,
            "macrocycle_id": "224d2054-d027-4783-aabe-62e2bd9ee9ff",
            "source": {"commit_sha": "a"*40, "tree_sha": "b"*40, "dirty_state": "CLEAN"},
            "artifacts": artifacts,
            "core": {
                "checkpoint_sha256": by["checkpoint"]["sha256"],
                "tokenizer_sha256": by["tokenizer"]["sha256"],
                "layer_count": 24,
                "d_model": 2048,
            },
            "jspace_lens": {
                "artifact_sha256": by["jacobian_lens"]["sha256"],
                "source_checkpoint_sha256": by["checkpoint"]["sha256"],
                "source_tokenizer_sha256": by["tokenizer"]["sha256"],
                "d_model": 2048,
                "source_layers": [4, 8, 12, 16, 20],
                "n_prompts": 128,
            },
            "workspace": {
                "fabric_mode": "UNIFIED_JSPACE_GWT",
                "workspace_policy_sha256": by["workspace_policy"]["sha256"],
                "zero_identity_sha256": by["zero_identity"]["sha256"],
                "grf_projection_sha256": by["grf_projection"]["sha256"],
            },
            "claude_adapter": {
                "adapter_sha256": by["claude_adapter"]["sha256"],
                "capability_profile_sha256": by["claude_capability_profile"]["sha256"],
                "tool_less_expected": True,
                "ephemeral_expected": True,
                "structured_output_expected": True,
                "env_isolated_expected": True,
            },
            "first_action": {
                "engine_class": "LOCAL_HOOKABLE",
                "origin": "LOCAL_HOOKABLE",
                "inference_packet_sha256": "c"*64,
            },
            "control": {
                "free_only": True,
                "paid_or_unknown_provider_network_attempted": False,
            },
            "unusual_experiment": {
                "count_for_this_macrocycle": 0,
                "id": None,
            },
        }

    def tearDown(self):
        self.tmp.cleanup()

    def verify(self):
        return mod.verify_receipt(self.receipt, self.root)

    def test_valid_receipt_passes_boot_binding_only(self):
        result = self.verify()
        self.assertEqual("PASS", result["status"])
        self.assertEqual("BOOT_BINDING_ONLY", result["credit"])
        self.assertEqual(0, result["whole_runtime_credit"])

    def test_digest_mismatch_fails_closed(self):
        self.receipt["artifacts"][0]["sha256"] = "f"*64
        self.assertIn("DIGEST_MISMATCH:bundled_core_manifest", self.verify()["errors"])

    def test_path_escape_fails_closed(self):
        self.receipt["artifacts"][0]["path"] = "../outside"
        self.assertIn("PATH_NOT_BOUND_INSIDE_ROOT:bundled_core_manifest", self.verify()["errors"])

    def test_lens_layer_geometry_must_match_core(self):
        self.receipt["jspace_lens"]["d_model"] = 4096
        self.receipt["jspace_lens"]["source_layers"] = [4, 24]
        errors = self.verify()["errors"]
        self.assertIn("LENS_D_MODEL_MISMATCH", errors)
        self.assertIn("LENS_SOURCE_LAYER_OUT_OF_RANGE", errors)

    def test_unified_fabric_mode_required(self):
        self.receipt["workspace"]["fabric_mode"] = "SEPARATE_JSPACE_THEN_GWT"
        self.assertIn("WORKSPACE_FABRIC_MODE_INVALID", self.verify()["errors"])

    def test_free_only_requires_zero_paid_unknown_network(self):
        self.receipt["control"]["paid_or_unknown_provider_network_attempted"] = True
        self.assertIn("PAID_OR_UNKNOWN_NETWORK_ATTEMPT_NOT_ZERO", self.verify()["errors"])

    def test_cross_checkpoint_lens_transplant_poison_is_rejected(self):
        """Macrocycle unusual experiment: syntactically valid foreign-lens provenance."""
        foreign_checkpoint = sha(b"checkpoint-B")
        self.receipt["jspace_lens"]["source_checkpoint_sha256"] = foreign_checkpoint
        self.receipt["unusual_experiment"] = {
            "count_for_this_macrocycle": 1,
            "id": "CROSS_CHECKPOINT_LENS_TRANSPLANT_POISON",
        }
        result = self.verify()
        self.assertEqual("FAIL", result["status"])
        self.assertIn("LENS_SOURCE_CHECKPOINT_MISMATCH", result["errors"])


if __name__ == "__main__":
    unittest.main()
