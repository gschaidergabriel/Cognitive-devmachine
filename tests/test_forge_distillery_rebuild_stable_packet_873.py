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
spec = importlib.util.spec_from_file_location("bridge_rebuild_873", MODULE_PATH)
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


def accepted_row(*, evaluated_at: str, hypothesis: str, falsifier: str, delta_id: str = "d-rebuild-1"):
    return {
        "schema": "CLAY_FORGE_DELTA_EVALUATION/v1",
        "record_type": "forge_evaluation",
        "delta_id": delta_id,
        "source_class": "free_swarm",
        "provider": "local_deterministic",
        "model": "none",
        "role": "RUNTIME",
        "worker_sha": "b" * 64,
        "source_repo_head": "a" * 40,
        "evaluation_repo_head": "c" * 40,
        "source_scope": "EXACT_WORKER_PROMPT_HEAD",
        "evaluated_at": evaluated_at,
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
        "proposal_hypothesis": hypothesis,
        "falsifier": falsifier,
    }


class RebuildStablePacket873Tests(unittest.TestCase):
    def test_measured_packet_excludes_observation_envelope_fields(self):
        first = accepted_row(
            evaluated_at="2026-08-24T16:30:00+00:00",
            hypothesis="candidate narration one",
            falsifier="candidate falsifier one",
            delta_id="d-envelope-one",
        )
        replay = accepted_row(
            evaluated_at="2026-08-24T17:30:00+00:00",
            hypothesis="different narration",
            falsifier="different falsifier",
            delta_id="d-envelope-two",
        )
        packet_first = bridge.measured_packet(first)
        packet_replay = bridge.measured_packet(replay)
        self.assertNotIn("evaluated_at", packet_first)
        self.assertNotIn("delta_id", packet_first)
        self.assertEqual(packet_first, packet_replay)
        self.assertEqual(
            bridge.execution_replay_identity(first),
            bridge.execution_replay_identity(replay),
        )
        self.assertEqual(
            bridge.measured_evidence_identity(first),
            bridge.measured_evidence_identity(replay),
        )

    def test_fresh_rebuilds_from_equivalent_envelopes_emit_identical_training_packet(self):
        rows = [
            accepted_row(
                evaluated_at="2026-08-24T16:30:00+00:00",
                hypothesis="candidate narration one",
                falsifier="candidate falsifier one",
                delta_id="d-rebuild-envelope-one",
            ),
            accepted_row(
                evaluated_at="2026-08-24T18:45:17+00:00",
                hypothesis="different narration",
                falsifier="different falsifier",
                delta_id="d-rebuild-envelope-two",
            ),
        ]
        observed = []
        with tempfile.TemporaryDirectory() as root:
            root_path = Path(root)
            for index, row in enumerate(rows):
                eval_path = root_path / f"eval-{index}.jsonl"
                db_path = root_path / f"distillery-{index}.sqlite3"
                eval_path.write_text(json.dumps(row) + "\n", encoding="utf-8")
                result = bridge.ingest(eval_path, db_path)
                self.assertEqual(result["admitted"], 1)
                con = sqlite3.connect(db_path)
                packet_id, packet_text = con.execute(
                    "SELECT id,packet_text FROM knowledge_packets"
                ).fetchone()
                replay_sha, measured_sha = con.execute(
                    "SELECT execution_replay_identity_sha256,measured_evidence_sha256 "
                    "FROM forge_execution_ingest"
                ).fetchone()
                con.close()
                observed.append(
                    (
                        result["packet_ids"],
                        result["accepted_dataset_tokens_counter"],
                        packet_id,
                        packet_text,
                        replay_sha,
                        measured_sha,
                    )
                )
        self.assertEqual(observed[0], observed[1])

    def test_same_execution_rekeyed_delta_id_is_duplicate_after_reopen(self):
        with tempfile.TemporaryDirectory() as root:
            root_path = Path(root)
            eval_path = root_path / "eval.jsonl"
            db_path = root_path / "distillery.sqlite3"
            first = accepted_row(
                evaluated_at="2026-08-24T16:30:00+00:00",
                hypothesis="candidate narration one",
                falsifier="candidate falsifier one",
            )
            eval_path.write_text(json.dumps(first) + "\n", encoding="utf-8")
            first_result = bridge.ingest(eval_path, db_path)
            token_count = first_result["accepted_dataset_tokens_counter"]

            replay = accepted_row(
                evaluated_at="2026-08-24T19:00:00+00:00",
                hypothesis="renarrated candidate",
                falsifier="renarrated falsifier",
                delta_id="d-rebuild-envelope-renamed",
            )
            eval_path.write_text(json.dumps(replay) + "\n", encoding="utf-8")
            replay_result = bridge.ingest(eval_path, db_path)

            self.assertEqual(first_result["admitted"], 1)
            self.assertEqual(replay_result["admitted"], 0)
            self.assertEqual(replay_result["duplicates"], 1)
            self.assertEqual(replay_result["forge_execution_packets_total"], 1)
            self.assertEqual(replay_result["accepted_dataset_tokens_counter"], token_count)

    def test_legacy_collision_cannot_be_evaded_by_delta_id_rekey(self):
        row = accepted_row(
            evaluated_at="2026-08-24T16:30:00+00:00",
            hypothesis="candidate narration one",
            falsifier="candidate falsifier one",
            delta_id="d-rebuild-envelope-renamed",
        )
        with tempfile.TemporaryDirectory() as root:
            root_path = Path(root)
            eval_path = root_path / "eval.jsonl"
            db_path = root_path / "distillery.sqlite3"
            con = sqlite3.connect(db_path)
            bridge.ensure_schema(con)
            con.execute(
                "INSERT INTO forge_execution_ingest("
                "evaluation_sha256,packet_id,delta_id,worker_sha,source_repo_head,evaluation_repo_head,admitted_at,approx_tokens"
                ") VALUES(?,?,?,?,?,?,?,?)",
                (
                    "9" * 64,
                    "kf-legacy-existing",
                    "different-legacy-envelope-id",
                    row["worker_sha"],
                    row["source_repo_head"],
                    row["evaluation_repo_head"],
                    "2026-08-24T00:00:00+00:00",
                    123,
                ),
            )
            con.commit()
            con.close()

            eval_path.write_text(json.dumps(row) + "\n", encoding="utf-8")
            result = bridge.ingest(eval_path, db_path)
            self.assertEqual(result["admitted"], 0)
            self.assertEqual(result["duplicates"], 0)
            self.assertEqual(result["rejected"].get("LEGACY_REPLAY_IDENTITY_UNRESOLVED"), 1)
            self.assertEqual(result["forge_execution_packets_total"], 1)
            self.assertEqual(result["knowledge_packets_total"], 0)


if __name__ == "__main__":
    unittest.main()
