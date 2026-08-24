from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import promote_forge_distillery_runtime_gate as promotion

SOURCE = "1" * 40
WORKER = "a" * 64
TARGET_BLOB = "b" * 40


def qualified_evaluation() -> dict:
    backend = {
        "admitted": True,
        "backend": "bubblewrap_unshare_all",
        "network_namespace": "ISOLATED",
        "secret_environment_inherited": False,
        "host_secret_paths_exposed": False,
    }
    admission = {
        "schema": "CLAY_FORGE_EXECUTION_ADMISSION/v1",
        "source_scope": "EXACT_WORKER_PROMPT_HEAD",
        "source_identity_admitted": True,
        "source_head": SOURCE,
        "evaluation_checkout_head": SOURCE,
        "decisions": [{"admitted": True, "argv": ["python3", "-m", "unittest"]}],
        "all_commands_admitted": True,
        "candidate_is_canonical_truth": False,
        "backend": backend,
    }
    return {
        "schema": "CLAY_FORGE_DELTA_EVALUATION/v1",
        "delta_id": "promotion-regression",
        "source_class": "deterministic_test_fixture",
        "provider": "local_deterministic",
        "model": "none",
        "role": "RUNTIME",
        "worker_sha": WORKER,
        "source_repo_head": SOURCE,
        "evaluation_repo_head": SOURCE,
        "source_scope": "EXACT_WORKER_PROMPT_HEAD",
        "evaluated_at": "2026-08-24T00:00:00+00:00",
        "status": "accepted",
        "metric": "deterministic_test_metric",
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
        "target_blob_identities": {"tools/ingest_forge_accepts_into_distillery.py": TARGET_BLOB},
        "requires_rebase_to_evaluation_head": False,
        "execution_admission": admission,
    }


def passing_gate(evaluation: dict | None = None) -> dict:
    return {
        "schema": promotion.PASS_SCHEMA,
        "pass": True,
        "status": promotion.PASS_STATUS,
        "source_sha": SOURCE,
        "network_used": False,
        "provider_calls": 0,
        "paid_fallback_attempt_count": 0,
        "acceptance_witness": {
            "nominal_without_execution_admission_rejected": True,
            "exact_evidence_qualified_accept": 1,
            "first_new_distillery_packets": 1,
            "accepted_dataset_tokens_after_first": 10,
            "replay_new_packets": 0,
            "replay_duplicates": 1,
            "token_delta_on_replay": 0,
            "accepted_dataset_tokens_after_replay": 10,
        },
        "distillery_first": {
            "admitted": 1,
            "accepted_dataset_tokens_counter": 10,
        },
        "distillery_replay": {
            "admitted": 0,
            "duplicates": 1,
            "accepted_dataset_tokens_counter": 10,
        },
        "forge_evaluation": evaluation if evaluation is not None else qualified_evaluation(),
    }


class PromotionSourceGuards872(unittest.TestCase):
    def test_wrong_source_sha_is_rejected(self):
        result = passing_gate()
        with self.assertRaises(promotion.PromotionError):
            promotion.validate_gate_result(result, "2" * 40)

    def test_non_pass_receipt_is_rejected(self):
        result = passing_gate()
        result["pass"] = False
        result["status"] = "FAIL_RUNTIME_GATE"
        with self.assertRaises(promotion.PromotionError):
            promotion.validate_gate_result(result, SOURCE)

    def test_nested_execution_admission_must_remain_evidence_qualified(self):
        evaluation = qualified_evaluation()
        evaluation["execution_admission"]["all_commands_admitted"] = False
        with self.assertRaises(promotion.PromotionError):
            promotion.validate_gate_result(passing_gate(evaluation), SOURCE)

    def test_inspect_db_preserves_counter_before_forge_schema_exists(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "distillery.sqlite3"
            con = sqlite3.connect(db)
            try:
                con.execute("CREATE TABLE counters(key TEXT PRIMARY KEY, value INTEGER NOT NULL DEFAULT 0)")
                con.execute("INSERT INTO counters(key,value) VALUES('accepted_dataset_tokens',123)")
                con.commit()
            finally:
                con.close()

            snap = promotion.inspect_db(db, "f" * 64)
            self.assertTrue(snap["db_exists"])
            self.assertFalse(snap["evaluation_present"])
            self.assertEqual(snap["accepted_dataset_tokens_counter"], 123)

    def test_live_first_promotion_then_immediate_replay_is_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            gate_path = root / "gate.json"
            db = root / "distillery.sqlite3"
            gate_path.write_text(json.dumps(passing_gate()) + "\n", encoding="utf-8")

            out = promotion.promote(gate_path, SOURCE, db)

            self.assertEqual(out["status"], "PASS")
            self.assertEqual(out["outcome"], "PROMOTED_NEW_PACKET")
            self.assertEqual(out["first"]["admitted"], 1)
            self.assertEqual(out["first"]["duplicates"], 0)
            self.assertGreater(out["first_token_delta"], 0)
            self.assertEqual(out["replay"]["admitted"], 0)
            self.assertEqual(out["replay"]["duplicates"], 1)
            self.assertEqual(out["replay_token_delta"], 0)
            self.assertTrue(out["after"]["evaluation_present"])
            self.assertGreater(out["after"]["packet_tokens"], 0)

    def test_first_delta_excludes_preexisting_non_forge_dataset_tokens(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            gate_path = root / "gate.json"
            db = root / "distillery.sqlite3"
            gate_path.write_text(json.dumps(passing_gate()) + "\n", encoding="utf-8")
            con = sqlite3.connect(db)
            try:
                con.execute("CREATE TABLE counters(key TEXT PRIMARY KEY, value INTEGER NOT NULL DEFAULT 0)")
                con.execute("INSERT INTO counters(key,value) VALUES('accepted_dataset_tokens',123)")
                con.commit()
            finally:
                con.close()

            out = promotion.promote(gate_path, SOURCE, db)

            self.assertEqual(out["before"]["accepted_dataset_tokens_counter"], 123)
            self.assertEqual(out["outcome"], "PROMOTED_NEW_PACKET")
            self.assertGreater(out["first_token_delta"], 0)
            self.assertEqual(out["first_token_delta"], out["after"]["packet_tokens"])
            self.assertEqual(out["replay_token_delta"], 0)

    def test_restarting_same_promotion_is_still_zero_delta(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            gate_path = root / "gate.json"
            db = root / "distillery.sqlite3"
            gate_path.write_text(json.dumps(passing_gate()) + "\n", encoding="utf-8")

            first_process = promotion.promote(gate_path, SOURCE, db)
            second_process = promotion.promote(gate_path, SOURCE, db)

            self.assertEqual(first_process["outcome"], "PROMOTED_NEW_PACKET")
            self.assertEqual(second_process["status"], "PASS")
            self.assertEqual(second_process["outcome"], "ALREADY_PROMOTED_IDEMPOTENT")
            self.assertEqual(second_process["first"]["admitted"], 0)
            self.assertEqual(second_process["first"]["duplicates"], 1)
            self.assertEqual(second_process["first_token_delta"], 0)
            self.assertEqual(second_process["replay"]["admitted"], 0)
            self.assertEqual(second_process["replay"]["duplicates"], 1)
            self.assertEqual(second_process["replay_token_delta"], 0)
            self.assertEqual(
                second_process["after"]["accepted_dataset_tokens_counter"],
                first_process["after"]["accepted_dataset_tokens_counter"],
            )


if __name__ == "__main__":
    unittest.main()
