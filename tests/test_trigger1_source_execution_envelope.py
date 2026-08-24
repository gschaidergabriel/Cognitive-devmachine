from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_attested_local_qwen_api as envelope
import trigger1_source_attestation as attest

HEX64 = "a" * 64
HEAD40 = "b" * 40
TREE40 = "c" * 40


class Trigger1SourceExecutionEnvelopeTests(unittest.TestCase):
    def test_clean_porcelain_status_is_explicit_false_and_digest_bound(self):
        def fake_git(_root: Path, *args: str, strip: bool = True) -> str:
            if args == ("rev-parse", "HEAD"):
                return HEAD40
            if args == ("rev-parse", "HEAD^{tree}"):
                return TREE40
            if args == ("status", "--porcelain=v1", "--untracked-files=all"):
                self.assertFalse(strip)
                return ""
            raise AssertionError(args)

        with mock.patch.object(attest, "_git", side_effect=fake_git):
            identity = attest.exact_source_identity(ROOT)
        self.assertEqual(HEAD40, identity["repo_head"])
        self.assertEqual(TREE40, identity["repo_tree"])
        self.assertFalse(identity["repo_dirty"])
        self.assertEqual(hashlib.sha256(b"").hexdigest(), identity["repo_status_sha256"])

    def test_require_clean_source_rejects_dirty_checkout(self):
        dirty = {
            "repo_head": HEAD40,
            "repo_tree": TREE40,
            "repo_dirty": True,
            "repo_status_sha256": HEX64,
        }
        with mock.patch.object(attest, "exact_source_identity", return_value=dirty):
            with self.assertRaisesRegex(RuntimeError, "DIRTY_SOURCE_TREE_FAIL_CLOSED"):
                attest.require_clean_source(ROOT)

    def test_candidate_receipt_is_wrapped_with_source_executor_and_result_identity(self):
        source = {
            "repo_head": HEAD40,
            "repo_tree": TREE40,
            "repo_dirty": False,
            "repo_status_sha256": hashlib.sha256(b"").hexdigest(),
        }
        candidate = {
            "source_identity": {
                "repo_head": HEAD40,
                "runtime_build_sha256": HEX64,
                "checkpoint_sha256": HEX64,
                "tokenizer_sha256": HEX64,
            },
            "transport": {"endpoint": "http://127.0.0.1:8089/v1/jspace/logits"},
            "target": {"local_runtime_execution_receipt_sha256": HEX64},
        }
        result = {
            "source": {"repo_head": HEAD40, "repo_tree": TREE40},
            "result_sha256": HEX64,
        }
        with tempfile.TemporaryDirectory() as tmp:
            candidate_path = Path(tmp) / "trigger1_direct_steering_candidate.json"
            result_path = Path(tmp) / "trigger1_local_activation_api_result.json"
            candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
            result_path.write_text(json.dumps(result), encoding="utf-8")
            binding_sha = envelope.bind_candidate(
                candidate_path,
                result_path,
                "intermediate",
                source,
                ROOT / "tools" / "trigger1_local_qwen06_intermediate_api_execute.py",
            )
            rebound = json.loads(candidate_path.read_text(encoding="utf-8"))
            binding = json.loads((Path(tmp) / "trigger1_source_execution_binding.json").read_text(encoding="utf-8"))
        self.assertEqual(source, {k: rebound["source_identity"][k] for k in source})
        self.assertEqual(HEX64, rebound["target"]["executor_local_runtime_receipt_sha256"])
        self.assertEqual(binding_sha, rebound["target"]["local_runtime_execution_receipt_sha256"])
        self.assertEqual(binding_sha, rebound["target"]["source_execution_binding_sha256"])
        self.assertEqual(binding_sha, binding["binding_sha256"])


if __name__ == "__main__":
    unittest.main()
