# GO878 exact-current replay-v2 execution trigger; semantic test behavior unchanged.
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
spec = importlib.util.spec_from_file_location("bridge_replay_deltaid_v2", MODULE_PATH)
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
        "delta_id": "d-replay-1",
        "source_class": "free_swarm",
        "provider": "local_deterministic",
        "model": "none",
        "role": "RUNTIME",
        "worker_sha": "b" * 64,
        "source_repo_head": "a" * 40,
        "evaluation_repo_head": "c" * 40,
        "source_scope": "EXACT_WORKER_PROMPT_HEAD",
        "evaluated_at": "2026-08-25T00:30:00+00:00",
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


class ReplayIdentityDeltaIdV2Tests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)
        self.eval = self.root / "eval.jsonl"
        self.db = self.root / "distillery.sqlite3"

    def tearDown(self):
        self.td.cleanup()

    def write(self, *rows):
        self.eval.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

    def test_delta_id_timestamp_and_narration_only_replay_is_duplicate_after_reopen(self):
        first_row = accepted_row()
        self.write(first_row)
        first = bridge.ingest(self.eval, self.db)
        token_count = first["accepted_dataset_tokens_counter"]
        expected_replay_sha = bridge.digest_json(bridge.execution_replay_identity(first_row))
        self.assertEqual(first["packet_ids"], ["kf-" + expected_replay_sha[:18]])

        replay = accepted_row(
            delta_id="d-replay-envelope-renamed",
            evaluated_at="2026-08-25T00:31:37+00:00",
            proposal_hypothesis="different non-measured narration",
            falsifier="different non-measured falsifier",
        )
        self.assertEqual(
            bridge.digest_json(bridge.execution_replay_identity(first_row)),
            bridge.digest_json(bridge.execution_replay_identity(replay)),
        )
        self.assertEqual(
            bridge.digest_json(bridge.measured_evidence_identity(first_row)),
            bridge.digest_json(bridge.measured_evidence_identity(replay)),
        )

        # bridge.ingest opens and closes SQLite on every call; this is the process-reopen
        # persistence boundary relevant to the on-disk replay identity.
        self.write(replay)
        second = bridge.ingest(self.eval, self.db)
        self.assertEqual(second["admitted"], 0)
        self.assertEqual(second["duplicates"], 1)
        self.assertEqual(second["accepted_dataset_tokens_counter"], token_count)
        self.assertEqual(second["forge_execution_packets_total"], 1)

    def test_delta_id_change_cannot_hide_measured_evidence_conflict(self):
        first_row = accepted_row()
        self.write(first_row)
        first = bridge.ingest(self.eval, self.db)
        token_count = first["accepted_dataset_tokens_counter"]

        mutated = accepted_row(
            delta_id="d-replay-envelope-renamed",
            evaluated_at="2026-08-25T00:32:00+00:00",
            relative_improvement_pct=75.0,
        )
        self.assertEqual(
            bridge.digest_json(bridge.execution_replay_identity(first_row)),
            bridge.digest_json(bridge.execution_replay_identity(mutated)),
        )
        self.assertNotEqual(
            bridge.digest_json(bridge.measured_evidence_identity(first_row)),
            bridge.digest_json(bridge.measured_evidence_identity(mutated)),
        )
        self.write(mutated)
        second = bridge.ingest(self.eval, self.db)
        self.assertEqual(second["admitted"], 0)
        self.assertEqual(second["duplicates"], 0)
        self.assertEqual(second["rejected"].get("REPLAY_IDENTITY_CONFLICT"), 1)
        self.assertEqual(second["accepted_dataset_tokens_counter"], token_count)
        self.assertEqual(second["forge_execution_packets_total"], 1)

    def test_pre_v2_row_with_changed_delta_id_fails_closed(self):
        original = accepted_row()
        con = sqlite3.connect(self.db)
        bridge.ensure_schema(con)
        legacy_eval_sha = bridge.digest_json(original)
        legacy_replay_sha = bridge.digest_json(bridge._execution_replay_identity_v1(original))
        legacy_measured_sha = bridge.digest_json(bridge._measured_evidence_identity_v1(original))
        con.execute(
            "INSERT INTO forge_execution_ingest("
            "evaluation_sha256,execution_replay_identity_sha256,measured_evidence_sha256,"
            "execution_replay_identity_v2_sha256,measured_evidence_v2_sha256,"
            "packet_id,delta_id,worker_sha,source_repo_head,evaluation_repo_head,admitted_at,approx_tokens"
            ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                legacy_eval_sha,
                legacy_replay_sha,
                legacy_measured_sha,
                None,
                None,
                "kf-pre-v2-existing",
                original["delta_id"],
                original["worker_sha"],
                original["source_repo_head"],
                original["evaluation_repo_head"],
                "2026-08-24T00:00:00+00:00",
                123,
            ),
        )
        con.commit()
        con.close()

        replay = accepted_row(
            delta_id="d-replay-envelope-renamed",
            evaluated_at="2026-08-25T00:33:00+00:00",
        )
        self.write(replay)
        out = bridge.ingest(self.eval, self.db)
        self.assertEqual(out["admitted"], 0)
        self.assertEqual(out["duplicates"], 0)
        self.assertEqual(out["rejected"].get("LEGACY_REPLAY_IDENTITY_UNRESOLVED"), 1)

        con = sqlite3.connect(self.db)
        ingest_count = con.execute("SELECT COUNT(*) FROM forge_execution_ingest").fetchone()[0]
        con.close()
        self.assertEqual(ingest_count, 1)


if __name__ == "__main__":
    unittest.main()
