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
    def test_rejects_shell_and_network_forms(self):
        for cmd in (
            "python3 -c print(1)",
            "pytest tests/test_x.py | cat",
            "pytest tests/test_x.py > out.txt",
            "pytest $(env)",
            "bash -lc env",
            "curl https://example.com",
        ):
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
                self.assertTrue(f.admit_command(cmd).admitted)

    def test_minimal_environment_does_not_inherit_credentials(self):
        with mock.patch.dict(os.environ, {"GROQ_API_KEY": "do-not-copy", "OTHER_SECRET": "x"}, clear=False):
            env = f._minimal_env()
        self.assertNotIn("GROQ_API_KEY", env)
        self.assertNotIn("OTHER_SECRET", env)
        f.assert_no_secret_names(env)

    def test_missing_isolated_executor_blocks_execution(self):
        with mock.patch.object(f.shutil, "which", return_value=None):
            result = f.run_cmd(Path("/tmp/work"), "pytest -q tests/test_demo.py", 5)
        self.assertEqual(126, result["rc"])
        self.assertIn("NO_ISOLATED_EXECUTOR", result["stderr"])

    def test_safe_wrapper_refuses_model_command_outside_disposable_forge_root(self, tmp_path):
        fake = mock.Mock(return_value={"rc": 0})
        forge_root = tmp_path / "forge"
        forge_root.mkdir()
        outside = tmp_path / "outside"
        outside.mkdir()
        with (
            mock.patch.object(safe.base, "FORGE_ROOT", forge_root),
            mock.patch.object(safe, "_ORIGINAL_ADMISSION_RUN_CMD", fake),
        ):
            result = safe.run_cmd(outside, "pytest -q tests/test_x.py", 5)
        self.assertEqual(126, result["rc"])
        self.assertIn("WORKDIR_OUTSIDE_DISPOSABLE_FORGE_ROOT", result["stderr"])
        fake.assert_not_called()

    def test_only_disposable_forge_worktree_becomes_writable(self, tmp_path):
        forge_root = tmp_path / "forge"
        forge_root.mkdir()
        work = forge_root / "candidate" / "patched"
        work.mkdir(parents=True)
        donor = ["bwrap", "--unshare-all", "--ro-bind", str(work.resolve()), "/work", "--chdir", "/work", "--"]
        with (
            mock.patch.object(safe.base, "FORGE_ROOT", forge_root),
            mock.patch.object(safe, "_ORIGINAL_BWRAP_PREFIX", return_value=donor.copy()),
        ):
            prefix = safe._writable_disposable_bwrap_prefix(work)
        self.assertIsNotNone(prefix)
        self.assertIn("--bind", prefix)
        self.assertNotIn(["--ro-bind", str(work.resolve()), "/work"], [prefix[i:i+3] for i in range(len(prefix)-2)])

    def test_unbound_source_blocks_before_original_validation(self):
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
            "worker_source_head": None,
            "worker_source_tree": None,
            "source_identity_bound": False,
            "all_commands_admitted": True,
            "backend": {"admitted": True},
        }
        with (
            mock.patch.object(safe.admission, "candidate_execution_manifest", return_value=manifest),
            mock.patch.object(safe, "_ORIGINAL_VALIDATE", side_effect=AssertionError("must not execute")),
        ):
            got = safe.validate_candidate(None, row)
        self.assertEqual("source_identity_unbound", got["status"])
        self.assertFalse(got["execution_admission"]["source_identity_admitted"])

    def test_supervisor_prefers_safe_forge_and_keeps_distillery_bridge(self):
        text = (ROOT / "tools/run_24h_entityos_swarm_supervisor.sh").read_text(encoding="utf-8")
        self.assertIn("run_free_evidence_forge_safe_871.py", text)
        self.assertIn("FORGE_ENTRYPOINT", text)
        self.assertIn("run_forge_distillery_bridge", text)
        self.assertIn("ingest_forge_accepts_into_distillery.py", text)


if __name__ == "__main__":
    unittest.main()
