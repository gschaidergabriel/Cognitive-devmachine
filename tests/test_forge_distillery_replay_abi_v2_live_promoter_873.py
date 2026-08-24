import importlib.util
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

bridge_spec = importlib.util.spec_from_file_location(
    "bridge_replay_abi_v2_live_873", TOOLS / "ingest_forge_accepts_into_distillery.py"
)
bridge = importlib.util.module_from_spec(bridge_spec)
bridge_spec.loader.exec_module(bridge)

promoter_spec = importlib.util.spec_from_file_location(
    "promoter_replay_abi_v2_live_873", TOOLS / "promote_forge_distillery_runtime_gate.py"
)
promoter = importlib.util.module_from_spec(promoter_spec)
promoter_spec.loader.exec_module(promoter)

SOURCE_SHA = "a" * 40
SOURCE_TREE = "1" * 40


def admission():
    return {
        "schema": "CLAY_FORGE_EXECUTION_ADMISSION/v1",
        "source_scope": "EXACT_WORKER_PROMPT_HEAD",
        "source_identity_admitted": True,
        "source_head": SOURCE_SHA,
        "source_tree": SOURCE_TREE,
        "evaluation_checkout_head": SOURCE_SHA,
        "evaluation_checkout_tree": SOURCE_TREE,
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


def evaluation(**overrides):
    row = {
        "schema": "CLAY_FORGE_DELTA_EVALUATION/v1",
        "record_type": "forge_evaluation",
        "delta_id": "d-live-current-envelope",
        "source_class": "exact_current_runtime_successor_gate",
        "provider": "local_deterministic",
        "model": "none",
        "role": "RUNTIME",
        "worker_sha": "b" * 64,
        "source_repo_head": SOURCE_SHA,
        "evaluation_repo_head": SOURCE_SHA,
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
        "target_blob_identities": {"tools/ingest_forge_accepts_into_distillery.py": "d" * 40},
        "requires_rebase_to_evaluation_head": False,
        "execution_admission": admission(),
        "proposal_hypothesis": "current candidate narration",
        "falsifier": "current candidate falsifier",
    }
    row.update(overrides)
    return row


def gate_result(row):
    disposable_tokens = 123
    return {
        "schema": promoter.PASS_SCHEMA,
        "pass": True,
        "status": promoter.PASS_STATUS,
        "source_sha": SOURCE_SHA,
        "source_tree": SOURCE_TREE,
        "network_used": False,
        "provider_calls": 0,
        "paid_fallback_attempt_count": 0,
        "acceptance_witness": {
            "nominal_without_execution_admission_rejected": True,
            "exact_evidence_qualified_accept": 1,
            "first_new_distillery_packets": 1,
            "accepted_dataset_tokens_after_first": disposable_tokens,
            "replay_new_packets": 0,
            "replay_duplicates": 1,
            "accepted_dataset_tokens_after_replay": disposable_tokens,
            "token_delta_on_replay": 0,
        },
        "distillery_first": {
            "admitted": 1,
            "accepted_dataset_tokens_counter": disposable_tokens,
        },
        "distillery_replay": {
            "admitted": 0,
            "duplicates": 1,
            "accepted_dataset_tokens_counter": disposable_tokens,
        },
        "forge_evaluation": row,
    }


def create_pre_v2_db(db: Path, historical_row):
    packet_text = bridge.canonical_json(bridge.measured_packet(historical_row))
    metadata_json = bridge.canonical_json(
        {
            "source_class": historical_row["source_class"],
            "provider": historical_row["provider"],
            "model": historical_row["model"],
            "role": historical_row["role"],
        }
    )
    tok = bridge.approx_tokens(packet_text)
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
    con.execute(
        "INSERT INTO knowledge_packets("
        "id,question_id,root_problem,packet_text,metadata_json,intrinsic_score,grf_score,project_fit,novelty_score,approx_tokens,created_at"
        ") VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (
            "kf-pre-v2-live",
            "forge-pre-v2-live",
            "historical live packet",
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
            "9" * 64,
            "1" * 64,
            "2" * 64,
            "kf-pre-v2-live",
            historical_row["delta_id"],
            historical_row["worker_sha"],
            historical_row["source_repo_head"],
            historical_row["evaluation_repo_head"],
            "2026-08-24T00:00:00+00:00",
            tok,
        ),
    )
    for key, value in (
        ("accepted_dataset_tokens", tok),
        ("accepted_packets", 1),
        ("forge_execution_packets", 1),
        ("forge_evidence_qualified_packets", 1),
    ):
        con.execute("INSERT INTO counters(key,value) VALUES(?,?)", (key, value))
    con.commit()
    con.close()
    return tok


class ReplayAbiV2LivePromoter873Tests(unittest.TestCase):
    def test_existing_pre_v2_semantic_execution_is_detected_after_backfill_and_not_repromoted(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            db = root / "distillery.sqlite3"
            current = evaluation()
            historical = evaluation(
                delta_id="d-old-envelope",
                evaluated_at="2026-08-24T00:00:00+00:00",
                proposal_hypothesis="old narration",
                falsifier="old falsifier",
            )
            token_count = create_pre_v2_db(db, historical)
            gate = root / "gate.json"
            gate.write_text(json.dumps(gate_result(current)), encoding="utf-8")

            result = promoter.promote(
                gate,
                SOURCE_SHA,
                db,
                expected_source_tree=SOURCE_TREE,
                github_run_id="12345",
                github_event_name="workflow_dispatch",
                source_selection=promoter.CANONICAL_SOURCE_SELECTION,
            )

            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["outcome"], "ALREADY_PROMOTED_IDEMPOTENT")
            self.assertEqual(result["execution_replay_identity_schema"], "CLAY_FORGE_EXECUTION_REPLAY_IDENTITY/v2")
            self.assertEqual(result["measured_evidence_schema"], "CLAY_FORGE_MEASURED_EVIDENCE_IDENTITY/v2")
            self.assertEqual(result["before"]["replay_identity_column"], "execution_replay_identity_v2_sha256")
            self.assertTrue(result["before"]["replay_identity_present"])
            self.assertEqual(result["first_token_delta"], 0)
            self.assertEqual(result["replay_token_delta"], 0)
            self.assertEqual(result["measured_conflict_token_delta"], 0)
            self.assertEqual(result["after"]["accepted_dataset_tokens_counter"], token_count)

            con = sqlite3.connect(db)
            old_replay, old_measured, replay_v2, measured_v2 = con.execute(
                "SELECT execution_replay_identity_sha256,measured_evidence_sha256,"
                "execution_replay_identity_v2_sha256,measured_evidence_v2_sha256 "
                "FROM forge_execution_ingest"
            ).fetchone()
            con.close()
            self.assertEqual(old_replay, "1" * 64)
            self.assertEqual(old_measured, "2" * 64)
            self.assertEqual(replay_v2, bridge.digest_json(bridge.execution_replay_identity(current)))
            self.assertEqual(measured_v2, bridge.digest_json(bridge.measured_evidence_identity(current)))


if __name__ == "__main__":
    unittest.main()
