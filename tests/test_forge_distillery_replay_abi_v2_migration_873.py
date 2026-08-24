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
spec = importlib.util.spec_from_file_location("bridge_replay_abi_v2_873", MODULE_PATH)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


def admission(source_head="a" * 40, evaluation_head="c" * 40):
    return {
        "schema": "CLAY_FORGE_EXECUTION_ADMISSION/v1",
        "source_scope": "EXACT_WORKER_PROMPT_HEAD",
        "source_identity_admitted": True,
        "source_head": source_head,
        "source_tree": "1" * 40,
        "evaluation_checkout_head": evaluation_head,
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
        "delta_id": "d-abi-v2-1",
        "source_class": "free_swarm",
        "provider": "local_deterministic",
        "model": "none",
        "role": "RUNTIME",
        "worker_sha": "b" * 64,
        "source_repo_head": "a" * 40,
        "evaluation_repo_head": "c" * 40,
        "source_scope": "EXACT_WORKER_PROMPT_HEAD",
        "evaluated_at": "2026-08-25T01:15:00+07:00",
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


def minimal_metadata(row):
    return {
        "source_class": row["source_class"],
        "provider": row["provider"],
        "model": row["model"],
        "role": row["role"],
    }


def create_pre_v2_tables(con):
    con.executescript(
        """
        CREATE TABLE knowledge_packets(
          id TEXT PRIMARY KEY,
          question_id TEXT NOT NULL,
          root_problem TEXT NOT NULL,
          packet_text TEXT NOT NULL,
          metadata_json TEXT NOT NULL,
          intrinsic_score REAL NOT NULL,
          grf_score REAL NOT NULL,
          project_fit REAL NOT NULL,
          novelty_score REAL NOT NULL,
          approx_tokens INTEGER NOT NULL,
          created_at TEXT NOT NULL
        );
        CREATE TABLE counters(
          key TEXT PRIMARY KEY,
          value INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE forge_execution_ingest(
          evaluation_sha256 TEXT PRIMARY KEY,
          execution_replay_identity_sha256 TEXT,
          measured_evidence_sha256 TEXT,
          packet_id TEXT NOT NULL UNIQUE,
          delta_id TEXT,
          worker_sha TEXT NOT NULL,
          source_repo_head TEXT NOT NULL,
          evaluation_repo_head TEXT NOT NULL,
          admitted_at TEXT NOT NULL,
          approx_tokens INTEGER NOT NULL
        );
        """
    )


def insert_historical(con, *, row, eval_sha, packet_id, old_replay_sha, old_measured_sha):
    packet_text = bridge.canonical_json(bridge.measured_packet(row))
    metadata_json = bridge.canonical_json(minimal_metadata(row))
    tok = bridge.approx_tokens(packet_text)
    con.execute(
        "INSERT INTO knowledge_packets("
        "id,question_id,root_problem,packet_text,metadata_json,intrinsic_score,grf_score,project_fit,novelty_score,approx_tokens,created_at"
        ") VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (
            packet_id,
            "forge-historical",
            "historical test row",
            packet_text,
            metadata_json,
            1.0,
            0.0,
            1.0,
            0.0,
            tok,
            "2026-08-24T00:00:00+00:00",
        ),
    )
    con.execute(
        "INSERT INTO forge_execution_ingest("
        "evaluation_sha256,execution_replay_identity_sha256,measured_evidence_sha256,"
        "packet_id,delta_id,worker_sha,source_repo_head,evaluation_repo_head,admitted_at,approx_tokens"
        ") VALUES(?,?,?,?,?,?,?,?,?,?)",
        (
            eval_sha,
            old_replay_sha,
            old_measured_sha,
            packet_id,
            row["delta_id"],
            row["worker_sha"],
            row["source_repo_head"],
            row["evaluation_repo_head"],
            "2026-08-24T00:00:00+00:00",
            tok,
        ),
    )


class ReplayAbiV2Migration873Tests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)
        self.db = self.root / "distillery.sqlite3"
        self.eval = self.root / "eval.jsonl"

    def tearDown(self):
        self.td.cleanup()

    def test_current_identity_schemas_are_explicit_v2(self):
        row = accepted_row()
        self.assertEqual(bridge.execution_replay_identity(row)["schema"], "CLAY_FORGE_EXECUTION_REPLAY_IDENTITY/v2")
        self.assertEqual(bridge.measured_evidence_identity(row)["schema"], "CLAY_FORGE_MEASURED_EVIDENCE_IDENTITY/v2")

    def test_pre_v2_row_backfills_from_packet_evidence_without_rewriting_historical_hashes(self):
        row = accepted_row()
        con = sqlite3.connect(self.db)
        create_pre_v2_tables(con)
        insert_historical(
            con,
            row=row,
            eval_sha="9" * 64,
            packet_id="kf-historical-one",
            old_replay_sha="1" * 64,
            old_measured_sha="2" * 64,
        )
        con.commit()

        bridge.ensure_schema(con)
        stored = con.execute(
            "SELECT execution_replay_identity_sha256,measured_evidence_sha256,"
            "execution_replay_identity_v2_sha256,measured_evidence_v2_sha256 "
            "FROM forge_execution_ingest"
        ).fetchone()
        columns = {r[1] for r in con.execute("PRAGMA table_info(forge_execution_ingest)")}
        con.close()

        self.assertEqual(stored[0], "1" * 64)
        self.assertEqual(stored[1], "2" * 64)
        self.assertEqual(stored[2], bridge.digest_json(bridge.execution_replay_identity(row)))
        self.assertEqual(stored[3], bridge.digest_json(bridge.measured_evidence_identity(row)))
        self.assertIn("execution_replay_identity_v2_sha256", columns)
        self.assertIn("measured_evidence_v2_sha256", columns)

    def test_backfilled_row_blocks_semantic_replay_even_when_delta_id_changes(self):
        row = accepted_row()
        con = sqlite3.connect(self.db)
        create_pre_v2_tables(con)
        insert_historical(
            con,
            row=row,
            eval_sha="9" * 64,
            packet_id="kf-historical-one",
            old_replay_sha="1" * 64,
            old_measured_sha="2" * 64,
        )
        con.commit()
        con.close()

        replay = accepted_row(
            delta_id="d-new-envelope-after-upgrade",
            evaluated_at="2099-01-01T00:00:00+00:00",
            proposal_hypothesis="renarrated",
            falsifier="renarrated falsifier",
        )
        self.eval.write_text(json.dumps(replay) + "\n", encoding="utf-8")
        result = bridge.ingest(self.eval, self.db)
        self.assertEqual(result["admitted"], 0)
        self.assertEqual(result["duplicates"], 1)
        self.assertEqual(result["forge_execution_packets_total"], 1)
        self.assertEqual(result["forge_replay_identity_v2_unresolved_rows"], 0)

    def test_historical_duplicate_collapse_fails_closed_before_unique_v2_index(self):
        row = accepted_row()
        con = sqlite3.connect(self.db)
        create_pre_v2_tables(con)
        insert_historical(
            con,
            row=row,
            eval_sha="8" * 64,
            packet_id="kf-historical-a",
            old_replay_sha="1" * 64,
            old_measured_sha="2" * 64,
        )
        insert_historical(
            con,
            row=accepted_row(delta_id="different-old-envelope"),
            eval_sha="9" * 64,
            packet_id="kf-historical-b",
            old_replay_sha="3" * 64,
            old_measured_sha="4" * 64,
        )
        con.commit()
        with self.assertRaisesRegex(RuntimeError, "REPLAY_IDENTITY_V2_MIGRATION_DUPLICATE"):
            bridge.ensure_schema(con)
        con.close()

    def test_historical_same_execution_with_different_measurement_fails_closed_as_migration_conflict(self):
        con = sqlite3.connect(self.db)
        create_pre_v2_tables(con)
        first = accepted_row()
        changed_measurement = accepted_row(
            delta_id="different-old-envelope",
            relative_improvement_pct=75.0,
        )
        insert_historical(
            con,
            row=first,
            eval_sha="8" * 64,
            packet_id="kf-historical-a",
            old_replay_sha="1" * 64,
            old_measured_sha="2" * 64,
        )
        insert_historical(
            con,
            row=changed_measurement,
            eval_sha="9" * 64,
            packet_id="kf-historical-b",
            old_replay_sha="3" * 64,
            old_measured_sha="4" * 64,
        )
        con.commit()
        with self.assertRaisesRegex(RuntimeError, "REPLAY_IDENTITY_V2_MIGRATION_CONFLICT"):
            bridge.ensure_schema(con)
        con.close()

    def test_incomplete_historical_row_remains_unresolved_and_fails_closed(self):
        row = accepted_row(delta_id="new-envelope")
        con = sqlite3.connect(self.db)
        bridge.ensure_schema(con)
        con.execute(
            "INSERT INTO forge_execution_ingest("
            "evaluation_sha256,packet_id,delta_id,worker_sha,source_repo_head,evaluation_repo_head,admitted_at,approx_tokens"
            ") VALUES(?,?,?,?,?,?,?,?)",
            (
                "9" * 64,
                "kf-no-packet-evidence",
                "old-envelope",
                row["worker_sha"],
                row["source_repo_head"],
                row["evaluation_repo_head"],
                "2026-08-24T00:00:00+00:00",
                123,
            ),
        )
        con.commit()
        con.close()

        self.eval.write_text(json.dumps(row) + "\n", encoding="utf-8")
        out = bridge.ingest(self.eval, self.db)
        self.assertEqual(out["admitted"], 0)
        self.assertEqual(out["duplicates"], 0)
        self.assertEqual(out["rejected"].get("LEGACY_REPLAY_IDENTITY_UNRESOLVED"), 1)
        self.assertEqual(out["forge_replay_identity_v2_unresolved_rows"], 1)


if __name__ == "__main__":
    unittest.main()
