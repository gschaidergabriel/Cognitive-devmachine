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
spec = importlib.util.spec_from_file_location("bridge_replay_873", MODULE_PATH)
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
        "decisions": [{"admitted": True, "reason": "TEST_ALLOWLIST", "argv": ["python3", "-m", "unittest", "-q", "tests.example"], "class": "TEST_OR_STATIC"}],
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
        "delta_id": "d-replay-1",
        "source_class": "free_swarm",
        "provider": "local_deterministic",
        "model": "none",
        "role": "RUNTIME",
        "worker_sha": "b" * 64,
        "source_repo_head": "a" * 40,
        "evaluation_repo_head": "c" * 40,
        "source_scope": "EXACT_WORKER_PROMPT_HEAD",
        "evaluated_at": "2026-08-24T16:30:00+00:00",
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
        "proposal_hypothesis": "candidate narration one",
        "falsifier": "candidate falsifier one",
    }
    row.update(overrides)
    return row


class ReplayIdentity873Tests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)
        self.eval = self.root / "eval.jsonl"
        self.db = self.root / "distillery.sqlite3"

    def tearDown(self):
        self.td.cleanup()

    def write(self, *rows):
        self.eval.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

    def test_timestamp_and_candidate_narration_replay_is_duplicate_and_token_stable(self):
        self.write(accepted_row())
        first = bridge.ingest(self.eval, self.db)
        tokens = first["accepted_dataset_tokens_counter"]
        replay = accepted_row(
            evaluated_at="2026-08-24T16:31:37+00:00",
            proposal_hypothesis="different non-measured narration",
            falsifier="different non-measured falsifier",
        )
        self.write(replay)
        second = bridge.ingest(self.eval, self.db)
        self.assertEqual(first["admitted"], 1)
        self.assertEqual(second["admitted"], 0)
        self.assertEqual(second["duplicates"], 1)
        self.assertEqual(second["accepted_dataset_tokens_counter"], tokens)
        self.assertEqual(second["forge_execution_packets_total"], 1)

    def test_same_execution_identity_with_mutated_measurement_fails_closed(self):
        self.write(accepted_row())
        first = bridge.ingest(self.eval, self.db)
        tokens = first["accepted_dataset_tokens_counter"]
        self.write(accepted_row(evaluated_at="2026-08-24T16:32:00+00:00", relative_improvement_pct=75.0))
        second = bridge.ingest(self.eval, self.db)
        self.assertEqual(second["admitted"], 0)
        self.assertEqual(second["duplicates"], 0)
        self.assertEqual(second["rejected"].get("REPLAY_IDENTITY_CONFLICT"), 1)
        self.assertEqual(second["accepted_dataset_tokens_counter"], tokens)
        self.assertEqual(second["forge_execution_packets_total"], 1)

    def test_different_execution_identity_remains_separately_admissible(self):
        second_admission = admission(evaluation_head="e" * 40)
        self.write(
            accepted_row(),
            accepted_row(
                delta_id="d-replay-2",
                worker_sha="f" * 64,
                evaluation_repo_head="e" * 40,
                execution_admission=second_admission,
                evaluated_at="2026-08-24T16:33:00+00:00",
            ),
        )
        out = bridge.ingest(self.eval, self.db)
        self.assertEqual(out["admitted"], 2)
        self.assertEqual(out["forge_execution_packets_total"], 2)

    def test_legacy_table_migrates_additively(self):
        con = sqlite3.connect(self.db)
        con.execute(
            "CREATE TABLE forge_execution_ingest("
            "evaluation_sha256 TEXT PRIMARY KEY, packet_id TEXT NOT NULL UNIQUE, "
            "delta_id TEXT, worker_sha TEXT NOT NULL, source_repo_head TEXT NOT NULL, "
            "evaluation_repo_head TEXT NOT NULL, admitted_at TEXT NOT NULL, approx_tokens INTEGER NOT NULL)"
        )
        con.commit()
        bridge.ensure_schema(con)
        columns = {row[1] for row in con.execute("PRAGMA table_info(forge_execution_ingest)")}
        con.close()
        self.assertIn("execution_replay_identity_sha256", columns)
        self.assertIn("measured_evidence_sha256", columns)


if __name__ == "__main__":
    unittest.main()
