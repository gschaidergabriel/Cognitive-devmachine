#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

import trigger1_source_bound_promotion as guard


class SourceBoundPromotionTests(unittest.TestCase):
    def setUp(self) -> None:
        self._old_root = guard.ROOT
        self.repo_tmp = tempfile.TemporaryDirectory()
        self.artifact_tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.repo_tmp.name)
        self.artifacts = Path(self.artifact_tmp.name)
        tools = self.root / "tools"
        tools.mkdir(parents=True)
        (tools / "trigger1_local_qwen06_activation_api_execute.py").write_text("print('executor')\n", encoding="utf-8")
        (tools / "trigger1_jspace_research.sh").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        (tools / "trigger1_jspace_promotion_gate.py").write_text(
            "import json\n"
            "print(json.dumps({'schema':'DUMMY_BASE_GATE/v1','owner_trigger1_goal_credit_candidate':True,"
            "'mechanism_runtime_vector_credit_candidate':True,'candidate_sha256':'0'*64}))\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.email", "trigger1-test@example.invalid"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.name", "Trigger1 Test"], cwd=self.root, check=True)
        subprocess.run(["git", "add", "tools"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-qm", "fixture"], cwd=self.root, check=True)
        guard.ROOT = self.root

    def tearDown(self) -> None:
        guard.ROOT = self._old_root
        self.artifact_tmp.cleanup()
        self.repo_tmp.cleanup()

    def _head_tree(self) -> tuple[str, str]:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.root, text=True).strip()
        tree = subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=self.root, text=True).strip()
        return head, tree

    def _candidate_result(self) -> tuple[Path, Path]:
        head, tree = self._head_tree()
        candidate = self.artifacts / "candidate.json"
        result = self.artifacts / "result.json"
        candidate.write_text(
            json.dumps({
                "source_identity": {"repo_head": head},
                "target": {"local_runtime_execution_receipt_sha256": "a" * 64},
            }),
            encoding="utf-8",
        )
        result.write_text(
            json.dumps({
                "source": {"repo_head": head, "repo_tree": tree},
                "status": "PASS",
                "zero_provider_billing": True,
                "external_provider_credentials_read": False,
            }),
            encoding="utf-8",
        )
        return candidate, result

    def test_clean_stable_source_can_chain_base_gate(self) -> None:
        pre = self.artifacts / "pre.json"
        self.assertEqual(guard.write_pre(pre), 0)
        candidate, result = self._candidate_result()
        verdict = guard.verify(candidate, result, pre, self.root / "tools" / "trigger1_jspace_promotion_gate.py")
        self.assertTrue(verdict["source_bound_runtime_evidence"])
        self.assertTrue(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertEqual(verdict["failures"], [])

    def test_post_runtime_dirty_state_fails_closed(self) -> None:
        pre = self.artifacts / "pre.json"
        self.assertEqual(guard.write_pre(pre), 0)
        candidate, result = self._candidate_result()
        (self.root / "untracked-after-pre.txt").write_text("dirty\n", encoding="utf-8")
        verdict = guard.verify(candidate, result, pre, self.root / "tools" / "trigger1_jspace_promotion_gate.py")
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertIn("POST_RUNTIME_WORKTREE_NOT_CLEAN", verdict["failures"])

    def test_dirty_pre_snapshot_blocks_local_fastpath(self) -> None:
        (self.root / "untracked-before-pre.txt").write_text("dirty\n", encoding="utf-8")
        pre = self.artifacts / "pre.json"
        self.assertEqual(guard.write_pre(pre), 4)
        payload = json.loads(pre.read_text(encoding="utf-8"))
        self.assertFalse(payload["worktree_clean"])


if __name__ == "__main__":
    unittest.main()
