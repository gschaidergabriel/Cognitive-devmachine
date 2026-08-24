#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import forge_execution_admission_871 as execution
import run_free_evidence_forge_safe_871 as safe


class SafeForgePipeline871Tests(unittest.TestCase):
    def test_rejects_shell_inline_and_network_command_forms(self):
        for cmd in (
            "python3 -c print(1)",
            "pytest tests/test_x.py | cat",
            "pytest tests/test_x.py > out.txt",
            "pytest $(env)",
            "bash -lc env",
            "curl https://example.com",
        ):
            with self.subTest(cmd=cmd):
                self.assertFalse(execution.admit_command(cmd).admitted)

    def test_rejects_absolute_and_parent_escape(self):
        for cmd in (
            "pytest /tmp/test_x.py",
            "pytest ../../test_x.py",
            "pytest --rootdir=/run/secrets tests/test_x.py",
            "pytest --basetemp=../../artifacts tests/test_x.py",
        ):
            self.assertFalse(execution.admit_command(cmd).admitted)

    def test_allows_bounded_test_and_static_grammar(self):
        for cmd in (
            "python3 -m unittest tests.test_demo",
            "python3 -m pytest -q tests/test_demo.py",
            "pytest -q tests/test_demo.py::Demo::test_one",
            "python3 -m py_compile tools/demo.py",
            "bash -n tools/demo.sh",
            "git diff --check",
            "cargo test --offline",
            "go test ./...",
        ):
            with self.subTest(cmd=cmd):
                self.assertTrue(execution.admit_command(cmd).admitted)

    def test_minimal_environment_never_inherits_credentials(self):
        with mock.patch.dict(os.environ, {"GROQ_API_KEY": "x", "NVIDIA_API_KEY": "y", "OTHER_SECRET": "z"}, clear=False):
            env = execution._minimal_env()
        self.assertNotIn("GROQ_API_KEY", env)
        self.assertNotIn("NVIDIA_API_KEY", env)
        self.assertNotIn("OTHER_SECRET", env)
        execution.assert_no_secret_names(env)

    def test_namespace_exposes_only_writable_disposable_checkout(self):
        with mock.patch.object(execution.shutil, "which", return_value="/usr/bin/bwrap"):
            argv = execution._bubblewrap_prefix(Path("/tmp/disposable"))
        self.assertIsNotNone(argv)
        joined = " ".join(argv)
        self.assertIn("--unshare-all", argv)
        self.assertIn("--bind /tmp/disposable /work", joined)
        self.assertNotIn("--ro-bind /tmp/disposable /work", joined)
        self.assertNotIn("/run", argv)
        self.assertNotIn("/artifacts", argv)
        self.assertNotIn("/home", argv)

    def test_missing_isolated_executor_blocks_without_execution(self):
        with mock.patch.object(execution.shutil, "which", return_value=None):
            got = execution.run_cmd(Path("/tmp/disposable"), "pytest -q tests/test_demo.py", 5)
        self.assertEqual(126, got["rc"])
        self.assertIn("NO_ISOLATED_EXECUTOR", got["stderr"])

    def test_run_cmd_uses_argv_and_minimal_environment(self):
        fake = mock.Mock(returncode=0, stdout="ok", stderr="")
        with (
            mock.patch.object(execution.shutil, "which", return_value="/usr/bin/bwrap"),
            mock.patch.object(execution.subprocess, "run", return_value=fake) as run,
            mock.patch.dict(os.environ, {"NVIDIA_API_KEY": "do-not-copy"}, clear=False),
        ):
            got = execution.run_cmd(Path("/tmp/disposable"), "pytest -q tests/test_demo.py", 5)
        self.assertEqual(0, got["rc"])
        args, kwargs = run.call_args
        self.assertIsInstance(args[0], list)
        self.assertNotIn("shell", kwargs)
        self.assertNotIn("NVIDIA_API_KEY", kwargs["env"])

    def test_source_manifest_binds_worker_head_and_evaluation_head(self):
        source_head = "1" * 40
        source_tree = "2" * 40
        evaluation_head = "3" * 40
        row = {"repo_head": source_head, "candidate_hash": "c" * 64}
        proposal = {"test_commands": ["pytest -q tests/test_x.py"]}
        base_manifest = {
            "schema": execution.POLICY_SCHEMA,
            "source_scope": "EXACT_WORKER_PROMPT_HEAD",
            "source_head": source_head,
            "source_tree": None,
            "source_identity_admitted": False,
            "source_identity_reason": "VALID_REPO_HEAD_AT_PROMPT_REQUIRED",
            "evaluation_checkout_head": None,
            "all_commands_admitted": True,
            "decisions": [{"admitted": True}],
            "backend": {"admitted": True},
            "candidate_is_canonical_truth": False,
        }

        def git_text(_cwd, *args, **_kwargs):
            if args[:2] == ("cat-file", "-e"):
                return 0, "", ""
            if args == ("rev-parse", source_head + "^{tree}"):
                return 0, source_tree, ""
            if args == ("rev-parse", "HEAD"):
                return 0, evaluation_head, ""
            raise AssertionError(args)

        with (
            mock.patch.object(safe.execution, "candidate_execution_manifest", return_value=base_manifest.copy()),
            mock.patch.object(safe.base, "_git_text", side_effect=git_text),
        ):
            manifest = safe._source_bound_manifest(row, proposal)
        self.assertTrue(manifest["source_identity_admitted"])
        self.assertEqual(source_head, manifest["source_head"])
        self.assertEqual(source_tree, manifest["source_tree"])
        self.assertEqual(evaluation_head, manifest["evaluation_checkout_head"])

    def test_unbound_worker_source_blocks_before_base_validation(self):
        row = {
            "repo_head": "",
            "candidate_hash": "c" * 64,
            "delta_id": "d1",
            "provider": "test",
            "model": "m",
            "role": "HCU_CAUSAL",
            "worker_sha": "w" * 64,
            "proposal_json": json.dumps({"test_commands": ["pytest -q tests/test_x.py"]}),
        }
        manifest = {
            "schema": execution.POLICY_SCHEMA,
            "source_scope": "EXACT_WORKER_PROMPT_HEAD",
            "source_head": None,
            "source_tree": None,
            "source_identity_admitted": False,
            "source_identity_reason": "VALID_REPO_HEAD_AT_PROMPT_REQUIRED",
            "evaluation_checkout_head": None,
            "all_commands_admitted": True,
            "decisions": [{"admitted": True}],
            "backend": {"admitted": True},
            "candidate_is_canonical_truth": False,
        }
        with (
            mock.patch.object(safe.execution, "candidate_execution_manifest", return_value=manifest),
            mock.patch.object(safe, "_ORIGINAL_VALIDATE", side_effect=AssertionError("must not execute")),
        ):
            got = safe.validate_candidate(None, row)
        self.assertEqual("source_identity_unbound", got["status"])


if __name__ == "__main__":
    unittest.main()
