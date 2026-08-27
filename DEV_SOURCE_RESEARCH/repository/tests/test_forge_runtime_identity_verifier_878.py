from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from verify_forge_runtime_identity_878 import PENDING, REJECTED, VERIFIED, verify_runtime_identity


class ForgeRuntimeIdentityVerifier878Tests(unittest.TestCase):
    NOW = 1_800_000_000.0
    PID = 4321
    NONCE = "nonce-generation-1"

    def _git(self, root: Path, *args: str) -> str:
        env = {
            **os.environ,
            "GIT_AUTHOR_NAME": "Clay Test",
            "GIT_AUTHOR_EMAIL": "clay@example.invalid",
            "GIT_COMMITTER_NAME": "Clay Test",
            "GIT_COMMITTER_EMAIL": "clay@example.invalid",
        }
        proc = subprocess.run(
            ["git", "-C", str(root), *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            env=env,
        )
        return proc.stdout.strip()

    def _fixture(self, root: Path):
        self._git(root, "init")
        entrypoint = root / "forge.py"
        entrypoint.write_text("VALUE = 1\n", encoding="utf-8")
        self._git(root, "add", "forge.py")
        self._git(root, "commit", "-m", "fixture")
        commit = self._git(root, "rev-parse", "HEAD")
        tree = self._git(root, "rev-parse", "HEAD^{tree}")
        sha256 = hashlib.sha256(entrypoint.read_bytes()).hexdigest()
        expectation = root / "expectation.json"
        expectation.write_text(json.dumps({
            "schema": "CLAY_FORGE_RUNTIME_EXPECTATION/v1",
            "nonce": self.NONCE,
            "pid": self.PID,
            "spawned_at_unix": self.NOW - 10,
        }), encoding="utf-8")
        identity = {
            "schema": "CLAY_FORGE_RUNTIME_IDENTITY/v1",
            "runtime_entrypoint_path": str(entrypoint.resolve()),
            "runtime_entrypoint_sha256": sha256,
            "source_commit": commit,
            "source_tree": tree,
            "source_identity_admitted": True,
            "material_sources_match": True,
            "process_generation_identity": f"pid:{self.PID}:start_ns:123456789",
            "supervisor_generation_or_start_nonce": self.NONCE,
        }
        status = {
            "generated_at": dt.datetime.fromtimestamp(self.NOW - 2, tz=dt.timezone.utc).isoformat(),
            "runtime_identity": identity,
        }
        status_path = root / "STATUS.json"
        status_path.write_text(json.dumps(status), encoding="utf-8")
        return entrypoint, expectation, status_path, status

    def _verify(self, root: Path, entrypoint: Path, expectation: Path, status: Path, **kwargs):
        return verify_runtime_identity(
            status_path=status,
            expectation_path=expectation,
            expected_entrypoint=entrypoint,
            repo_root=root,
            actual_pid=kwargs.pop("actual_pid", self.PID),
            now=self.NOW,
            max_age_seconds=90,
            grace_seconds=60,
            **kwargs,
        )

    def test_matching_fresh_identity_is_verified(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            entry, expectation, status_path, _ = self._fixture(root)
            report = self._verify(root, entry, expectation, status_path)
            self.assertEqual(report["state"], VERIFIED)

    def test_missing_runtime_identity_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            entry, expectation, status_path, status = self._fixture(root)
            status.pop("runtime_identity")
            status_path.write_text(json.dumps(status), encoding="utf-8")
            report = self._verify(root, entry, expectation, status_path)
            self.assertEqual(report["state"], REJECTED)
            self.assertEqual(report["reason"], "RUNTIME_IDENTITY_MISSING")

    def test_wrong_entrypoint_hash_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            entry, expectation, status_path, status = self._fixture(root)
            status["runtime_identity"]["runtime_entrypoint_sha256"] = "0" * 64
            status_path.write_text(json.dumps(status), encoding="utf-8")
            report = self._verify(root, entry, expectation, status_path)
            self.assertEqual(report["reason"], "ENTRYPOINT_SHA256_MISMATCH")

    def test_wrong_source_commit_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            entry, expectation, status_path, status = self._fixture(root)
            status["runtime_identity"]["source_commit"] = "0" * 40
            status_path.write_text(json.dumps(status), encoding="utf-8")
            report = self._verify(root, entry, expectation, status_path)
            self.assertEqual(report["reason"], "SOURCE_COMMIT_MISMATCH")

    def test_unadmitted_material_source_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            entry, expectation, status_path, status = self._fixture(root)
            status["runtime_identity"]["material_sources_match"] = False
            status_path.write_text(json.dumps(status), encoding="utf-8")
            report = self._verify(root, entry, expectation, status_path)
            self.assertEqual(report["reason"], "PUBLISHER_MATERIAL_SOURCE_BINDING_NOT_ADMITTED")

    def test_wrong_supervisor_nonce_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            entry, expectation, status_path, status = self._fixture(root)
            status["runtime_identity"]["supervisor_generation_or_start_nonce"] = "old-nonce"
            status_path.write_text(json.dumps(status), encoding="utf-8")
            report = self._verify(root, entry, expectation, status_path)
            self.assertEqual(report["reason"], "SUPERVISOR_NONCE_MISMATCH")

    def test_process_generation_must_bind_actual_pid(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            entry, expectation, status_path, status = self._fixture(root)
            status["runtime_identity"]["process_generation_identity"] = "pid:9999:start_ns:1"
            status_path.write_text(json.dumps(status), encoding="utf-8")
            report = self._verify(root, entry, expectation, status_path)
            self.assertEqual(report["reason"], "PROCESS_GENERATION_PID_MISMATCH")

    def test_pre_spawn_status_is_pending_during_grace(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            entry, expectation, status_path, status = self._fixture(root)
            status["generated_at"] = dt.datetime.fromtimestamp(self.NOW - 20, tz=dt.timezone.utc).isoformat()
            status_path.write_text(json.dumps(status), encoding="utf-8")
            report = self._verify(root, entry, expectation, status_path)
            self.assertEqual(report["state"], PENDING)
            self.assertEqual(report["reason"], "STATUS_PREDATES_CURRENT_SPAWN")


if __name__ == "__main__":
    unittest.main()
