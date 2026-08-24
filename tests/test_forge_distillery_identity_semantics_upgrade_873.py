import importlib.util
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
MODULE_PATH = TOOLS / "ingest_forge_accepts_into_distillery.py"
spec = importlib.util.spec_from_file_location("bridge_identity_upgrade_873", MODULE_PATH)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


def admission():
    return {
        "schema": "CLAY_FORGE_EXECUTION_ADMISSION/v1",
        "source_scope": "EXACT_WORKER_PROMPT_HEAD",
        "source_identity_admitted": True,
        "source_head": "a" * 40,
        "source_tree": "1" * 40,
        "evaluation_checkout_head": "c" * 40,
        "evaluation_checkout_tree": "2" * 40,
        "decisions": [
            {
                "admitted": True,
                "reason": "TEST_ALLOWLIST",
                "argv": ["python3", "-m", "unittest", "-q", "tests.example"],
                "class": "TEST_OR_STATIC",
            }
        ],
        "all_commands_admitted": True,
        "candidate_is_canonical_truth": False,
        "backend": {
            "admitted": True,
            "backend": "bubblewrap_unshare_all",
            "network_namespace": "ISOLATED",
            "secret_environment_inherited": False,
            "host_secret_paths_exposed": False,
        },
    }


def accepted_row(**overrides):
    row = {
        "schema": "CLAY_FORGE_DELTA_EVALUATION/v1",
        "record_type": "forge_evaluation",
        "delta_id": "new-envelope-id",
        "source_class": "free_swarm",
        "provider": "local_deterministic",
        "model": "none",
        "role": "RUNTIME",
        "worker_sha": "b" * 64,
        "source_repo_head": "a" * 40,
        "evaluation_repo_head": "c" * 40,
        "source_scope": "EXACT_WORKER_PROMPT_HEAD",
        "evaluated_at": "2026-08-25T01:06:00+07:00",
        "status": "accepted",
        "metric": "execution_admission_causal_regression_pass_rate",
        "relative_improvement_pct": 100.0,
        "reproducible_runs": 2,
        "tests_passed": 2,
        "tests_failed": 0,
        "negative_tests_passed": 1,
        "negative_tests_failed": 0,
        "static_checks_passed": 1,
        "static_checks_failed": 0,
        "benchmark_non_regression": True,
        "reverted": False,
        "target_blob_identities": {"tools/example.py": "d" * 40},
        "requires_rebase_to_evaluation_head": False,
        "execution_admission": admission(),
        "proposal_hypothesis": "candidate narration",
        "falsifier": "candidate falsifier",
    }
    row.update(overrides)
    return row


class IdentitySemanticsUpgrade873Tests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)
        self.eval = self.root / "eval.jsonl"
        self.db = self.root / "distillery.sqlite3"

    def tearDown(self):
        self.td.cleanup()

    def write(self, row):
        self.eval.write_text(json.dumps(row) + "\n", encoding="utf-8")

    def test_changed_preimages_have_new_explicit_versions(self):
        row = accepted_row()
        self.assertEqual(bridge.measured_packet(row)["schema"], "CLAY_DISTILLERY_FORGE_EXECUTION_PACKET/v3")
        self.assertEqual(bridge.execution_replay_identity(row)["schema"], "CLAY_FORGE_EXECUTION_REPLAY_IDENTITY/v2")
        self.assertEqual(bridge.measured_evidence_identity(row)["schema"], "CLAY_FORGE_MEASURED_EVIDENCE_IDENTITY/v2")

    def test_new_row_persists_identity_semantics_marker(self):
        self.write(accepted_row())
        out = bridge.ingest(self.eval, self.db)
        self.assertEqual(out["admitted"], 1)
        self.assertEqual(out["identity_semantics"], bridge.IDENTITY_SEMANTICS)
        con = sqlite3.connect(self.db)
        semantics = con.execute("SELECT identity_semantics FROM forge_execution_ingest").fetchone()[0]
        con.close()
        self.assertEqual(semantics, bridge.IDENTITY_SEMANTICS)

    def test_preupgrade_nonnull_digest_row_blocks_semantic_reemission(self):
        row = accepted_row(delta_id="new-envelope-id", evaluated_at="2026-08-25T01:07:00+07:00")
        con = sqlite3.connect(self.db)
        bridge.ensure_schema(con)
        # Simulate a row written by the prior replay implementation: it already has
        # non-null replay/measured digests, but no marker proving which preimage schema
        # produced those digests. The new envelope must not be admitted by guessing.
        con.execute(
            "INSERT INTO forge_execution_ingest("
            "evaluation_sha256,execution_replay_identity_sha256,measured_evidence_sha256,"
            "packet_id,delta_id,worker_sha,source_repo_head,evaluation_repo_head,admitted_at,approx_tokens"
            ") VALUES(?,?,?,?,?,?,?,?,?,?)",
            (
                "9" * 64,
                "8" * 64,
                "7" * 64,
                "kf-preupgrade-existing",
                "old-envelope-id",
                row["worker_sha"],
                row["source_repo_head"],
                row["evaluation_repo_head"],
                "2026-08-24T00:00:00+00:00",
                123,
            ),
        )
        con.commit()
        con.close()

        self.write(row)
        out = bridge.ingest(self.eval, self.db)
        self.assertEqual(out["admitted"], 0)
        self.assertEqual(out["duplicates"], 0)
        self.assertEqual(out["rejected"].get("LEGACY_REPLAY_IDENTITY_UNRESOLVED"), 1)
        self.assertEqual(out["knowledge_packets_total"], 0)
        self.assertEqual(out["forge_execution_packets_total"], 1)

    def test_exact_preupgrade_full_evaluation_replay_remains_safe_duplicate(self):
        row = accepted_row()
        eval_sha = bridge.digest_json(row)
        con = sqlite3.connect(self.db)
        bridge.ensure_schema(con)
        con.execute(
            "INSERT INTO forge_execution_ingest("
            "evaluation_sha256,execution_replay_identity_sha256,measured_evidence_sha256,"
            "packet_id,delta_id,worker_sha,source_repo_head,evaluation_repo_head,admitted_at,approx_tokens"
            ") VALUES(?,?,?,?,?,?,?,?,?,?)",
            (
                eval_sha,
                "8" * 64,
                "7" * 64,
                "kf-preupgrade-existing",
                row["delta_id"],
                row["worker_sha"],
                row["source_repo_head"],
                row["evaluation_repo_head"],
                "2026-08-24T00:00:00+00:00",
                123,
            ),
        )
        con.commit()
        con.close()

        self.write(row)
        out = bridge.ingest(self.eval, self.db)
        self.assertEqual(out["admitted"], 0)
        self.assertEqual(out["duplicates"], 1)
        self.assertEqual(out["rejected"].get("LEGACY_REPLAY_IDENTITY_UNRESOLVED", 0), 0)


if __name__ == "__main__":
    unittest.main()
