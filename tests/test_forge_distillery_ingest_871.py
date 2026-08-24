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
spec = importlib.util.spec_from_file_location("bridge", MODULE_PATH)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


def execution_admission(source_head="a" * 40, **overrides):
    obj = {
        "schema": "CLAY_FORGE_EXECUTION_ADMISSION/v1",
        "source_scope": "EXACT_WORKER_PROMPT_HEAD",
        "source_identity_admitted": True,
        "source_head": source_head,
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
    obj.update(overrides)
    return obj


def accepted_row(**overrides):
    row = {
        "schema": "CLAY_FORGE_DELTA_EVALUATION/v1",
        "record_type": "forge_evaluation",
        "delta_id": "d-1",
        "source_class": "free_swarm",
        "provider": "openrouter",
        "model": "qwen/qwen3-0.6b-04-28:free",
        "role": "RUNTIME",
        "worker_sha": "b" * 64,
        "source_repo_head": "a" * 40,
        "evaluation_repo_head": "c" * 40,
        "source_scope": "EXACT_WORKER_PROMPT_HEAD",
        "evaluated_at": "2026-08-24T14:13:00+00:00",
        "status": "accepted",
        "metric": "test_pass_rate",
        "relative_improvement_pct": 50.0,
        "reproducible_runs": 2,
        "tests_passed": 4,
        "tests_failed": 0,
        "negative_tests_passed": 2,
        "negative_tests_failed": 0,
        "static_checks_passed": 1,
        "static_checks_failed": 0,
        "benchmark_non_regression": True,
        "reverted": False,
        "target_blob_identities": {"tools/example.py": "d" * 40},
        "execution_admission": execution_admission(),
        "requires_rebase_to_evaluation_head": True,
        "proposal_hypothesis": "candidate narration must not become measured packet text",
        "falsifier": "candidate falsifier also remains metadata-only",
    }
    row.update(overrides)
    return row


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)
        self.eval = self.root / "eval.jsonl"
        self.db = self.root / "distillery.sqlite3"

    def tearDown(self):
        self.td.cleanup()

    def write_rows(self, *rows):
        self.eval.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

    def test_evidence_qualified_evaluation_becomes_one_packet(self):
        self.write_rows(accepted_row())
        out = bridge.ingest(self.eval, self.db)
        self.assertEqual(out["admitted"], 1)
        self.assertEqual(out["acceptance_semantics"], "EVIDENCE_QUALIFIED_ONLY")
        self.assertGreater(out["accepted_dataset_tokens_counter"], 0)
        self.assertEqual(out["forge_execution_packets_total"], 1)
        self.assertEqual(out["forge_evidence_qualified_packets_counter"], 1)
        con = sqlite3.connect(self.db)
        packet_text, meta = con.execute("SELECT packet_text,metadata_json FROM knowledge_packets").fetchone()
        con.close()
        self.assertNotIn("candidate narration", packet_text)
        self.assertNotIn("candidate falsifier", packet_text)
        self.assertIn("proposal_hypothesis_candidate_only", meta)
        self.assertIn("EVIDENCE_QUALIFIED_ACCEPT", packet_text)
        self.assertIn("execution_admission_sha256", packet_text)
        self.assertIn("EXECUTION_EVIDENCE_ONLY_NOT_JSPACE_CAUSAL_CREDIT", packet_text)

    def test_idempotent_duplicate_does_not_double_count(self):
        self.write_rows(accepted_row())
        first = bridge.ingest(self.eval, self.db)
        second = bridge.ingest(self.eval, self.db)
        self.assertEqual(first["admitted"], 1)
        self.assertEqual(second["admitted"], 0)
        self.assertEqual(second["duplicates"], 1)
        self.assertEqual(first["accepted_dataset_tokens_counter"], second["accepted_dataset_tokens_counter"])
        self.assertEqual(first["forge_evidence_qualified_packets_counter"], second["forge_evidence_qualified_packets_counter"])

    def test_nominal_accept_without_execution_admission_is_rejected(self):
        row = accepted_row()
        row.pop("execution_admission")
        self.write_rows(row)
        out = bridge.ingest(self.eval, self.db)
        self.assertEqual(out["admitted"], 0)
        self.assertEqual(out["rejected"].get("EXECUTION_ADMISSION_MISSING"), 1)

    def test_unisolated_backend_is_rejected(self):
        row = accepted_row()
        row["execution_admission"]["backend"]["network_namespace"] = "UNAVAILABLE"
        self.write_rows(row)
        out = bridge.ingest(self.eval, self.db)
        self.assertEqual(out["admitted"], 0)
        self.assertEqual(out["rejected"].get("ISOLATION_NOT_PROVEN"), 1)

    def test_secret_inheritance_is_rejected(self):
        row = accepted_row()
        row["execution_admission"]["backend"]["secret_environment_inherited"] = True
        self.write_rows(row)
        out = bridge.ingest(self.eval, self.db)
        self.assertEqual(out["admitted"], 0)
        self.assertEqual(out["rejected"].get("SECRET_FENCE_NOT_PROVEN"), 1)

    def test_execution_source_mismatch_is_rejected(self):
        self.write_rows(accepted_row(execution_admission=execution_admission(source_head="e" * 40)))
        out = bridge.ingest(self.eval, self.db)
        self.assertEqual(out["admitted"], 0)
        self.assertEqual(out["rejected"].get("EXECUTION_SOURCE_HEAD_MISMATCH"), 1)

    def test_nonaccepted_is_rejected(self):
        self.write_rows(accepted_row(status="validated_not_better"))
        out = bridge.ingest(self.eval, self.db)
        self.assertEqual(out["admitted"], 0)
        self.assertEqual(out["rejected"].get("NOT_NOMINAL_ACCEPT"), 1)

    def test_missing_exact_source_identity_fails_closed(self):
        self.write_rows(accepted_row(source_repo_head=None))
        out = bridge.ingest(self.eval, self.db)
        self.assertEqual(out["admitted"], 0)
        self.assertEqual(out["rejected"].get("SOURCE_HEAD_UNBOUND"), 1)

    def test_failed_negative_control_fails_closed(self):
        self.write_rows(accepted_row(negative_tests_failed=1))
        out = bridge.ingest(self.eval, self.db)
        self.assertEqual(out["admitted"], 0)
        self.assertEqual(out["rejected"].get("NOT_NOMINAL_ACCEPT"), 1)

    def test_no_positive_improvement_fails_closed(self):
        self.write_rows(accepted_row(relative_improvement_pct=0.0))
        out = bridge.ingest(self.eval, self.db)
        self.assertEqual(out["admitted"], 0)
        self.assertEqual(out["rejected"].get("NOT_NOMINAL_ACCEPT"), 1)

    def test_path_escape_in_target_identity_fails_closed(self):
        self.write_rows(accepted_row(target_blob_identities={"../secret": "d" * 40}))
        out = bridge.ingest(self.eval, self.db)
        self.assertEqual(out["admitted"], 0)
        self.assertEqual(out["rejected"].get("TARGET_BLOBS_UNBOUND"), 1)

    def test_invalid_json_is_counted_and_does_not_abort(self):
        self.eval.write_text("not-json\n" + json.dumps(accepted_row()) + "\n", encoding="utf-8")
        out = bridge.ingest(self.eval, self.db)
        self.assertEqual(out["admitted"], 1)
        self.assertEqual(out["rejected"].get("INVALID_JSON"), 1)


if __name__ == "__main__":
    unittest.main()
