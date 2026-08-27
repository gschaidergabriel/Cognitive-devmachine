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

import forge_execution_admission_871 as f
import run_free_evidence_forge_safe_871 as safe


class ForgeExecutionAdmission871(unittest.TestCase):
    def test_rejects_inline_python_and_shell_forms(self):
        bad = [
            "python3 -c print(1)",
            "pytest tests/test_x.py | cat",
            "pytest tests/test_x.py > out.txt",
            "pytest $(env)",
            "echo `env`",
            "bash -lc env",
            "curl https://example.com",
        ]
        for cmd in bad:
            with self.subTest(cmd=cmd):
                self.assertFalse(f.admit_command(cmd).admitted)

    def test_rejects_absolute_and_parent_escape(self):
        for cmd in (
            "pytest /tmp/test_x.py",
            "pytest ../../test_x.py",
            "pytest --rootdir=/run/secrets tests/test_x.py",
            "pytest --basetemp=../../artifacts tests/test_x.py",
        ):
            self.assertFalse(f.admit_command(cmd).admitted)

    def test_allows_bounded_test_and_static_grammar(self):
        good = [
            "python3 -m unittest tests.test_demo",
            "python3 -m pytest -q tests/test_demo.py",
            "pytest -q tests/test_demo.py::Demo::test_one",
            "python3 -m py_compile tools/demo.py",
            "bash -n tools/demo.sh",
            "git diff --check",
            "cargo test --offline",
            "go test ./...",
        ]
        for cmd in good:
            with self.subTest(cmd=cmd):
                self.assertTrue(f.admit_command(cmd).admitted)

    def test_minimal_environment_does_not_inherit_credentials(self):
        with mock.patch.dict(os.environ, {"GROQ_API_KEY": "do-not-copy", "OTHER_SECRET": "x"}, clear=False):
            env = f._minimal_env()
        self.assertNotIn("GROQ_API_KEY", env)
        self.assertNotIn("OTHER_SECRET", env)
        f.assert_no_secret_names(env)

    def test_bubblewrap_hides_host_secret_locations_and_unshares(self):
        with mock.patch.object(f.shutil, "which", return_value="/usr/bin/bwrap"):
            argv = f._bubblewrap_prefix(Path("/tmp/work"))
        self.assertIsNotNone(argv)
        joined = " ".join(argv)
        self.assertIn("--unshare-all", argv)
        self.assertIn("--tmpfs /tmp", joined)
        self.assertNotIn("/run", argv)
        self.assertNotIn("/artifacts", argv)
        self.assertNotIn("/home", argv)

    def test_backend_presence_without_functional_namespace_is_blocked(self):
        failed_probe = mock.Mock(returncode=1, stdout="", stderr="namespace denied")
        with (
            mock.patch.object(f.shutil, "which", return_value="/usr/bin/bwrap"),
            mock.patch.object(f.subprocess, "run", return_value=failed_probe),
        ):
            status = f.execution_backend_status(Path("/tmp/work"))
        self.assertFalse(status["admitted"])
        self.assertEqual("UNAVAILABLE", status["network_namespace"])
        self.assertIn("PROBE_RC_1", status["reason"])

    def test_run_cmd_never_uses_shell_or_inherited_env(self):
        fake = mock.Mock(returncode=0, stdout="ok", stderr="")
        with (
            mock.patch.object(f.shutil, "which", return_value="/usr/bin/bwrap"),
            mock.patch.object(f.subprocess, "run", return_value=fake) as run,
            mock.patch.dict(os.environ, {"NVIDIA_API_KEY": "do-not-copy"}, clear=False),
        ):
            result = f.run_cmd(Path("/tmp/work"), "pytest -q tests/test_demo.py", 5)
        self.assertEqual(result["rc"], 0)
        args, kwargs = run.call_args
        self.assertIsInstance(args[0], list)
        self.assertNotIn("shell", kwargs)
        self.assertNotIn("NVIDIA_API_KEY", kwargs["env"])
        self.assertNotIn("bash", args[0])

    def test_missing_isolated_executor_is_blocked_not_executed(self):
        with mock.patch.object(f.shutil, "which", return_value=None):
            result = f.run_cmd(Path("/tmp/work"), "pytest -q tests/test_demo.py", 5)
        self.assertEqual(result["rc"], 126)
        self.assertIn("NO_ISOLATED_EXECUTOR", result["stderr"])

    def test_empty_command_set_is_not_admitted(self):
        row = {"repo_head": "1" * 40, "candidate_hash": "c" * 64}
        proposal = {"test_commands": [], "negative_test_commands": []}
        fake_git = mock.Mock(stdout="3" * 40)
        with (
            mock.patch.object(f.subprocess, "run", return_value=fake_git),
            mock.patch.object(f, "execution_backend_status", return_value={"admitted": True}),
        ):
            manifest = f.candidate_execution_manifest(row, proposal, ROOT)
        self.assertEqual([], manifest["decisions"])
        self.assertFalse(manifest["all_commands_admitted"])

    def test_execution_manifest_binds_worker_and_evaluation_identity(self):
        source_head = "1" * 40
        source_tree = "2" * 40
        evaluation_head = "3" * 40
        evaluation_tree = "4" * 40
        row = {"repo_head": source_head, "candidate_hash": "c" * 64}
        proposal = {"test_commands": ["pytest -q tests/test_x.py"]}
        moving = {
            "schema": f.POLICY_SCHEMA,
            "worker_source_head": source_head,
            "worker_source_tree": source_tree,
            "evaluation_head": evaluation_head,
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
            if args == ("rev-parse", evaluation_head + "^{tree}"):
                return 0, evaluation_tree, ""
            raise AssertionError(args)

        with (
            mock.patch.object(safe, "_ORIGINAL_MANIFEST", return_value=moving.copy()),
            mock.patch.object(safe.base, "_git_text", side_effect=git_text),
        ):
            manifest = safe._source_bound_manifest(row, proposal, ROOT)

        self.assertTrue(manifest["source_identity_admitted"])
        self.assertEqual(source_head, manifest["source_head"])
        self.assertEqual(source_tree, manifest["source_tree"])
        self.assertEqual(evaluation_head, manifest["evaluation_checkout_head"])
        self.assertEqual(evaluation_tree, manifest["evaluation_checkout_tree"])
        self.assertEqual("EXACT_WORKER_PROMPT_HEAD", manifest["source_scope"])

    def test_evaluation_head_drift_downgrades_nominal_accept(self):
        row = {
            "repo_head": "1" * 40,
            "candidate_hash": "c" * 64,
            "delta_id": "d1",
            "provider": "test",
            "model": "m",
            "role": "HCU_CAUSAL",
            "worker_sha": "w" * 64,
            "proposal_json": json.dumps({"test_commands": ["pytest -q tests/test_x.py"]}),
        }
        manifest = {
            "schema": f.POLICY_SCHEMA,
            "source_head": "1" * 40,
            "source_tree": "2" * 40,
            "evaluation_checkout_head": "3" * 40,
            "evaluation_checkout_tree": "4" * 40,
            "source_identity_admitted": True,
            "all_commands_admitted": True,
            "backend": {"admitted": True},
        }
        nominal = {"status": "accepted", "evaluation_repo_head": "5" * 40}
        with (
            mock.patch.object(safe, "_source_bound_manifest", return_value=manifest),
            mock.patch.object(safe, "_ORIGINAL_VALIDATE", return_value=nominal),
        ):
            got = safe.validate_candidate(None, row)
        self.assertEqual("evaluation_identity_drift", got["status"])
        self.assertEqual("EVALUATION_HEAD_CHANGED_AFTER_EXECUTION_ADMISSION", got["reason"])

    def test_unbound_worker_source_blocks_before_original_validation(self):
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
            "schema": f.POLICY_SCHEMA,
            "evaluation_head": "3" * 40,
            "all_commands_admitted": True,
            "backend": {"admitted": True},
        }
        with (
            mock.patch.object(safe, "_ORIGINAL_MANIFEST", return_value=manifest),
            mock.patch.object(safe, "_ORIGINAL_VALIDATE", side_effect=AssertionError("must not execute")),
        ):
            got = safe.validate_candidate(None, row)
        self.assertEqual("source_identity_unbound", got["status"])
        self.assertFalse(got["execution_admission"]["source_identity_admitted"])


if __name__ == "__main__":
    unittest.main()
