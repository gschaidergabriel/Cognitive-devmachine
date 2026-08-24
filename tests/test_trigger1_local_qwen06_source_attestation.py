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

import trigger1_local_qwen06_activation_api_execute as local_qwen

HEAD40 = "a" * 40
TREE40 = "b" * 40


class Trigger1LocalQwenSourceAttestationTests(unittest.TestCase):
    def test_exact_source_identity_binds_clean_status_digest(self):
        def fake_git_text(*args: str) -> str:
            if args == ("rev-parse", "HEAD"):
                return HEAD40
            if args == ("rev-parse", "HEAD^{tree}"):
                return TREE40
            if args == ("status", "--porcelain=v1", "--untracked-files=all"):
                return ""
            return "UNKNOWN"

        with mock.patch.object(local_qwen, "git_text", side_effect=fake_git_text):
            identity = local_qwen.exact_source_identity()

        self.assertEqual(HEAD40, identity["repo_head"])
        self.assertEqual(TREE40, identity["repo_tree"])
        self.assertFalse(identity["repo_dirty"])
        self.assertEqual(hashlib.sha256(b"").hexdigest(), identity["repo_status_sha256"])

    def test_dirty_source_fails_before_model_load(self):
        dirty_identity = {
            "repo_head": HEAD40,
            "repo_tree": TREE40,
            "repo_dirty": True,
            "repo_status_sha256": hashlib.sha256(b" M tools/example.py").hexdigest(),
        }
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(local_qwen, "exact_source_identity", return_value=dirty_identity), mock.patch.object(
                local_qwen, "load_exact_runtime"
            ) as load_runtime, mock.patch.object(
                sys, "argv", ["trigger1_local_qwen06_activation_api_execute.py", "--output-dir", tmp]
            ):
                rc = local_qwen.main()

            self.assertEqual(3, rc)
            load_runtime.assert_not_called()
            result = json.loads((Path(tmp) / "trigger1_local_activation_api_result.json").read_text(encoding="utf-8"))
            self.assertEqual("BLOCKED_LOCAL_FASTPATH", result["status"])
            self.assertIn("DIRTY_SOURCE_TREE_FAIL_CLOSED", result["reason"])
            self.assertTrue(result["source"]["repo_dirty"])

    def test_unresolved_git_identity_fails_closed(self):
        with mock.patch.object(local_qwen, "git_text", return_value="UNKNOWN"):
            with self.assertRaisesRegex(RuntimeError, "SOURCE_IDENTITY_UNRESOLVED"):
                local_qwen.exact_source_identity()


if __name__ == "__main__":
    unittest.main()
