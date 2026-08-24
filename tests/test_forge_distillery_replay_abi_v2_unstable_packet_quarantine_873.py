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
spec = importlib.util.spec_from_file_location("bridge_replay_abi_v2_quarantine_873", MODULE_PATH)
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
        "decisions": [{
            "admitted": True,
            "reason": "TEST_ALLOWLIST",
            "argv": ["python3", "-m", "unittest", "-q", "tests.example"],
            "class": "TEST_OR_STATIC",
        }],
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


def row(**overrides):
    value = {
        "schema": "CLAY_FORGE_DELTA_EVALUATION/v1",
        "record_type": "forge_evaluation",
        "delta_id": "current-envelope",
        "source_class": "free_swarm",
        "provider": "local_deterministic",
        "model": "none",
        "role": "RUNTIME",
        "worker_sha": "b" * 64,
        "source_repo_head": "a" * 40,
        "evaluation_repo_head": "c" * 40,
        "source_scope": "EXACT_WORKER_PROMPT_HEAD",
        "evaluated_at": "2026-08-25T01:20:00+07:00",
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
        "proposal_hypothesis": "current narration",
        "falsifier": "current falsifier",
    }
    value.update(overrides)
    return value


def make_pre_v2_db(db: Path, current: dict) -> int:
    stable = bridge.measured_packet(current)
    historical_packet = dict(stable)
    historical_packet["delta_id"] = "historical-envelope"
    historical_packet["evaluated_at"] = "2026-08-24T00:00:00+00:00"
    packet_text = bridge.canonical_json(historical_packet)
    token_count = bridge.approx_tokens(packet_text)
    metadata = bridge.canonical_json({
        "source_class": current["source_class"],
        "provider": current["provider"],
        "model": current["model"],
        "role": current["role"],
    })

    con = sqlite3.connect(db)
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
        CREATE TABLE counters(key TEXT PRIMARY KEY,value INTEGER NOT NULL DEFAULT 0);
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
    con.execute(
        "INSERT INTO knowledge_packets VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (
            "kf-volatile-history",
            "forge-volatile-history",
            "historical packet carrying volatile envelope fields",
            packet_text,
            metadata,
            1.0, 0.0, 1.0, 0.0,
            token_count,
            "2026-08-24T00:00:00+00:00",
        ),
    )
    con.execute(
        "INSERT INTO forge_execution_ingest VALUES(?,?,?,?,?,?,?,?,?,?)",
        (
            "9" * 64,
            "1" * 64,
            "2" * 64,
            "kf-volatile-history",
            "historical-envelope",
            current["worker_sha"],
            current["source_repo_head"],
            current["evaluation_repo_head"],
            "2026-08-24T00:00:00+00:00",
            token_count,
        ),
    )
    for key, value in (
        ("accepted_dataset_tokens", token_count),
        ("accepted_packets", 1),
        ("forge_execution_packets", 1),
        ("forge_evidence_qualified_packets", 1),
    ):
        con.execute("INSERT INTO counters(key,value) VALUES(?,?)", (key, value))
    con.commit()
    con.close()
    return token_count


class ReplayAbiV2UnstablePacketQuarantine873Tests(unittest.TestCase):
    def test_old_packet_with_volatile_envelope_fields_is_not_auto_backfilled(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "distillery.sqlite3"
            current = row()
            original_tokens = make_pre_v2_db(db, current)

            con = sqlite3.connect(db)
            bridge.ensure_schema(con)
            replay_v2, measured_v2 = con.execute(
                "SELECT execution_replay_identity_v2_sha256,measured_evidence_v2_sha256 "
                "FROM forge_execution_ingest"
            ).fetchone()
            stored_packet = json.loads(
                con.execute("SELECT packet_text FROM knowledge_packets").fetchone()[0]
            )
            counter = con.execute(
                "SELECT value FROM counters WHERE key='accepted_dataset_tokens'"
            ).fetchone()[0]
            con.close()

            self.assertIsNone(replay_v2)
            self.assertIsNone(measured_v2)
            self.assertEqual(stored_packet["delta_id"], "historical-envelope")
            self.assertIn("evaluated_at", stored_packet)
            self.assertEqual(counter, original_tokens)

    def test_semantic_replay_against_quarantined_packet_fails_closed_without_new_credit(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            db = root / "distillery.sqlite3"
            eval_path = root / "eval.jsonl"
            current = row(
                delta_id="new-envelope-after-upgrade",
                evaluated_at="2099-01-01T00:00:00+00:00",
                proposal_hypothesis="renarrated candidate",
                falsifier="renarrated falsifier",
            )
            original_tokens = make_pre_v2_db(db, current)
            eval_path.write_text(json.dumps(current) + "\n", encoding="utf-8")

            out = bridge.ingest(eval_path, db)
            self.assertEqual(out["admitted"], 0)
            self.assertEqual(out["duplicates"], 0)
            self.assertEqual(out["rejected"].get("LEGACY_REPLAY_IDENTITY_UNRESOLVED"), 1)
            self.assertEqual(out["forge_execution_packets_total"], 1)
            self.assertEqual(out["forge_replay_identity_v2_unresolved_rows"], 1)
            self.assertEqual(out["accepted_dataset_tokens_counter"], original_tokens)

            con = sqlite3.connect(db)
            packet_count = con.execute("SELECT COUNT(*) FROM knowledge_packets").fetchone()[0]
            replay_v2 = con.execute(
                "SELECT execution_replay_identity_v2_sha256 FROM forge_execution_ingest"
            ).fetchone()[0]
            con.close()
            self.assertEqual(packet_count, 1)
            self.assertIsNone(replay_v2)


if __name__ == "__main__":
    unittest.main()
