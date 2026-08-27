from __future__ import annotations

import importlib
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

forge = importlib.import_module("run_free_evidence_forge")


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return proc.stdout.strip()


class ForgeSourceIdentityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ctx = tempfile.TemporaryDirectory()
        self.tmp = Path(self.ctx.name)
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q")
        git(self.repo, "config", "user.email", "forge-test@example.invalid")
        git(self.repo, "config", "user.name", "Forge Test")

        (self.repo / "sample.py").write_text("value = 1\n", encoding="utf-8")
        git(self.repo, "add", "sample.py")
        git(self.repo, "commit", "-q", "-m", "source A")
        self.source_head = git(self.repo, "rev-parse", "HEAD")

        # Move the live checkout so the worker's exact source is no longer HEAD.
        # A moving-head Forge would reject the A patch below against this B tree.
        (self.repo / "sample.py").write_text("value = 10\n", encoding="utf-8")
        git(self.repo, "add", "sample.py")
        git(self.repo, "commit", "-q", "-m", "source B")
        self.evaluation_head = git(self.repo, "rev-parse", "HEAD")

        self.artifacts = self.tmp / "artifacts"
        self.forge_root = self.artifacts / "forge"
        self.forge_root.mkdir(parents=True)

        self.old = {
            "ROOT": forge.ROOT,
            "ARTIFACT_ROOT": forge.ARTIFACT_ROOT,
            "FORGE_ROOT": forge.FORGE_ROOT,
            "DB_PATH": forge.DB_PATH,
            "STATUS_PATH": forge.STATUS_PATH,
            "EVAL_PATH": forge.EVAL_PATH,
            "DISCOVERY_PATH": forge.DISCOVERY_PATH,
            "DISTILLERY_DB": forge.DISTILLERY_DB,
        }
        forge.ROOT = self.repo
        forge.ARTIFACT_ROOT = self.artifacts
        forge.FORGE_ROOT = self.forge_root
        forge.DB_PATH = self.forge_root / "forge.sqlite3"
        forge.STATUS_PATH = self.forge_root / "STATUS.json"
        forge.EVAL_PATH = self.forge_root / "architecture_delta_evaluations.jsonl"
        forge.DISCOVERY_PATH = self.forge_root / "discoveries.jsonl"
        forge.DISTILLERY_DB = self.artifacts / "distillery" / "distillery.sqlite3"

    def tearDown(self) -> None:
        for name, value in self.old.items():
            setattr(forge, name, value)
        self.ctx.cleanup()

    def candidate_row(self, repo_head: str) -> tuple[sqlite3.Connection, sqlite3.Row]:
        con = sqlite3.connect(":memory:")
        con.row_factory = sqlite3.Row
        con.execute(
            """
            CREATE TABLE candidates(
              candidate_hash TEXT PRIMARY KEY,
              delta_id TEXT, provider TEXT, model TEXT, role TEXT,
              worker_sha TEXT, repo_head TEXT, proposal_json TEXT NOT NULL,
              ready INTEGER, state TEXT, ingested_at TEXT
            )
            """
        )
        proposal = {
            "hypothesis": "exact source identity prevents moving-head false rejection",
            "target_files": ["sample.py"],
            "patch_unified_diff": (
                "diff --git a/sample.py b/sample.py\n"
                "--- a/sample.py\n"
                "+++ b/sample.py\n"
                "@@ -1 +1 @@\n"
                "-value = 1\n"
                "+value = 2\n"
            ),
            "test_commands": [
                "python3 -c \"import sample; assert sample.value == 2\""
            ],
            "falsifier": "patch fails or test does not improve at exact source A",
            "ready_for_forge": True,
        }
        con.execute(
            "INSERT INTO candidates VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (
                "candidate", "delta", "test", "model", "role", "worker-sha",
                repo_head, json.dumps(proposal), 1, "NEW", "now",
            ),
        )
        return con, con.execute("SELECT * FROM candidates").fetchone()

    def test_validation_checks_out_exact_worker_head_before_apply(self) -> None:
        con, row = self.candidate_row(self.source_head)
        try:
            result = forge.validate_candidate(con, row)
        finally:
            con.close()
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(result["source_repo_head"], self.source_head)
        self.assertEqual(result["evaluation_repo_head"], self.evaluation_head)
        self.assertTrue(result["requires_rebase_to_evaluation_head"])
        self.assertRegex(result["target_blob_identities"]["sample.py"], r"^[0-9a-f]{40}$")
        self.assertEqual(result["baseline_test_passes"], 0)
        self.assertEqual(result["patched_test_passes"], 2)

    def test_unbound_source_identity_fails_before_clone_or_patch(self) -> None:
        con, row = self.candidate_row("")
        try:
            result = forge.validate_candidate(con, row)
        finally:
            con.close()
        self.assertEqual(result["status"], "source_identity_unbound")
        self.assertIn("repo_head_at_prompt", result["reason"])

    def test_connect_migrates_existing_candidate_db_additively(self) -> None:
        forge.FORGE_ROOT.mkdir(parents=True, exist_ok=True)
        legacy = sqlite3.connect(forge.DB_PATH)
        legacy.execute(
            """
            CREATE TABLE candidates(
              candidate_hash TEXT PRIMARY KEY,
              delta_id TEXT, provider TEXT, model TEXT, role TEXT,
              worker_sha TEXT, proposal_json TEXT NOT NULL,
              ready INTEGER NOT NULL DEFAULT 0,
              state TEXT NOT NULL DEFAULT 'NEW',
              ingested_at TEXT NOT NULL, evaluated_at TEXT,
              last_reason TEXT
            )
            """
        )
        legacy.commit()
        legacy.close()

        con = forge.connect()
        try:
            columns = {row[1] for row in con.execute("PRAGMA table_info(candidates)")}
        finally:
            con.close()
        self.assertIn("repo_head", columns)


if __name__ == "__main__":
    unittest.main()
