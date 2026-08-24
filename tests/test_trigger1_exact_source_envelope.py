#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from trigger1_exact_source_envelope import build_envelope, capture_source_identity


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


class ExactSourceEnvelopeTests(unittest.TestCase):
    def make_repo(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        git(root, "init", "-q")
        git(root, "config", "user.email", "test@example.invalid")
        git(root, "config", "user.name", "test")
        (root / "executor.py").write_text("print('x')\n")
        git(root, "add", "executor.py")
        git(root, "commit", "-qm", "init")
        return td, root

    def test_clean_and_dirty_identity_are_distinct_and_stable(self):
        td, root = self.make_repo()
        try:
            clean1 = capture_source_identity(root, [root / "executor.py"])
            clean2 = capture_source_identity(root, [root / "executor.py"])
            self.assertFalse(clean1["dirty"])
            self.assertEqual(clean1["source_identity_sha256"], clean2["source_identity_sha256"])

            (root / "executor.py").write_text("print('changed')\n")
            dirty = capture_source_identity(root, [root / "executor.py"])
            self.assertTrue(dirty["dirty"])
            self.assertNotEqual(clean1["source_identity_sha256"], dirty["source_identity_sha256"])

            (root / "new.txt").write_text("untracked\n")
            dirty2 = capture_source_identity(root, [root / "executor.py"])
            self.assertNotEqual(dirty["source_identity_sha256"], dirty2["source_identity_sha256"])
            self.assertEqual(1, len(dirty2["untracked_manifest"]))
        finally:
            td.cleanup()

    def test_envelope_passes_only_with_stable_exact_bindings(self):
        td, root = self.make_repo()
        out_td = tempfile.TemporaryDirectory()
        try:
            out = Path(out_td.name)
            pre = capture_source_identity(root, [root / "executor.py"])
            post = capture_source_identity(root, [root / "executor.py"])
            result = {
                "status": "SCIENTIFIC_NEGATIVE",
                "source": {"repo_head": pre["repo_head"], "repo_tree": pre["repo_tree"]},
                "runtime_manifest": {
                    "python_version": "3.x", "python_executable_sha256": "a",
                    "torch_version": "x", "torch_module_sha256": "b",
                    "transformers_version": "y", "transformers_module_sha256": "c",
                },
                "runtime_build_sha256": "d",
                "model": "Qwen/Qwen3-0.6B",
                "model_revision": "rev",
                "checkpoint_sha256": "checkpoint",
                "tokenizer_sha256": "tokenizer",
                "api_endpoint": "http://127.0.0.1:12345/v1/jspace/intermediate",
                "api_loopback_only": True,
                "zero_provider_billing": True,
                "external_provider_credentials_read": False,
                "provider_network_calls": 0,
            }
            (out / "trigger1_intermediate_result.json").write_text(json.dumps(result))
            envelope, exact = build_envelope(root=root, out_dir=out, pre=pre, post=post, delegated_returncode=2)
            self.assertTrue(exact)
            self.assertEqual("PASS_EXACT_SOURCE_BINDING", envelope["status"])
            self.assertEqual("SCIENTIFIC_NEGATIVE", envelope["delegated_experiment_status"])
            self.assertEqual(0, envelope["jspace_model_runtime_credit"])
        finally:
            td.cleanup(); out_td.cleanup()

    def test_source_mutation_withholds_candidate(self):
        td, root = self.make_repo()
        out_td = tempfile.TemporaryDirectory()
        try:
            out = Path(out_td.name)
            pre = capture_source_identity(root, [root / "executor.py"])
            result = {
                "status": "PASS",
                "source": {"repo_head": pre["repo_head"], "repo_tree": pre["repo_tree"]},
                "runtime_manifest": {
                    "python_version": "3.x", "python_executable_sha256": "a",
                    "torch_version": "x", "torch_module_sha256": "b",
                    "transformers_version": "y", "transformers_module_sha256": "c",
                },
                "model_revision": "rev", "checkpoint_sha256": "checkpoint", "tokenizer_sha256": "tokenizer",
                "api_endpoint": "http://127.0.0.1:12345/v1/jspace/intermediate",
                "api_loopback_only": True, "zero_provider_billing": True,
                "external_provider_credentials_read": False, "provider_network_calls": 0,
            }
            (out / "trigger1_intermediate_result.json").write_text(json.dumps(result))
            (out / "trigger1_intermediate_candidate.json").write_text("{}")
            (root / "executor.py").write_text("print('mutated')\n")
            post = capture_source_identity(root, [root / "executor.py"])
            envelope, exact = build_envelope(root=root, out_dir=out, pre=pre, post=post, delegated_returncode=0)
            self.assertFalse(exact)
            self.assertFalse((out / "trigger1_intermediate_candidate.json").exists())
            self.assertEqual("BLOCKED_EXACT_SOURCE_BINDING", envelope["status"])
        finally:
            td.cleanup(); out_td.cleanup()


if __name__ == "__main__":
    unittest.main()
