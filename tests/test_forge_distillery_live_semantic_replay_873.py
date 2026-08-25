from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE_TEST = ROOT / "tests" / "test_forge_distillery_promotion_872.py"

spec = importlib.util.spec_from_file_location("promotion_872_helpers", BASE_TEST)
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)

promotion = helpers.promotion


class LiveSemanticReplay873(unittest.TestCase):
    def write_gate(self, path: Path, evaluation: dict) -> None:
        path.write_text(json.dumps(helpers.passing_gate(evaluation)) + "\n", encoding="utf-8")

    def test_live_promoter_proves_semantic_replay_and_measured_conflict_zero_delta(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            gate = root / "gate.json"
            db = root / "distillery.sqlite3"
            evaluation = helpers.qualified_evaluation()
            self.write_gate(gate, evaluation)

            out = promotion.promote(gate, helpers.SOURCE, db, **helpers.workflow_context())

            self.assertEqual(out["status"], "PASS")
            self.assertEqual(out["outcome"], "PROMOTED_NEW_PACKET")
            self.assertTrue(out["semantic_replay_db_reopen_proven"])
            self.assertEqual(out["semantic_replay"]["admitted"], 0)
            self.assertEqual(out["semantic_replay"]["duplicates"], 1)
            self.assertEqual(out["replay_token_delta"], 0)
            self.assertEqual(out["measured_conflict"]["admitted"], 0)
            self.assertEqual(out["measured_conflict"]["duplicates"], 0)
            self.assertEqual(
                out["measured_conflict"]["rejected"].get("REPLAY_IDENTITY_CONFLICT"),
                1,
            )
            self.assertEqual(out["measured_conflict_token_delta"], 0)
            self.assertTrue(out["after"]["replay_identity_present"])
            self.assertEqual(
                out["after"]["accepted_dataset_tokens_counter"],
                out["first"]["accepted_dataset_tokens_counter"],
            )

    def test_changed_delta_timestamp_and_narration_reuse_existing_stable_execution_identity(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            first_gate = root / "first.json"
            second_gate = root / "second.json"
            db = root / "distillery.sqlite3"

            first_eval = helpers.qualified_evaluation()
            self.write_gate(first_gate, first_eval)
            first = promotion.promote(first_gate, helpers.SOURCE, db, **helpers.workflow_context())

            replay_eval = helpers.qualified_evaluation()
            replay_eval["delta_id"] = "different-evaluation-envelope-id"
            replay_eval["evaluated_at"] = "2026-08-25T00:01:00+00:00"
            replay_eval["proposal_hypothesis"] = "different candidate narration"
            replay_eval["falsifier"] = "different candidate falsifier"
            self.write_gate(second_gate, replay_eval)
            second = promotion.promote(second_gate, helpers.SOURCE, db, **helpers.workflow_context())

            self.assertEqual(first["outcome"], "PROMOTED_NEW_PACKET")
            self.assertEqual(second["outcome"], "ALREADY_PROMOTED_IDEMPOTENT")
            self.assertFalse(second["before"]["evaluation_present"])
            self.assertTrue(second["before"]["replay_identity_present"])
            self.assertEqual(second["first_token_delta"], 0)
            self.assertEqual(second["replay_token_delta"], 0)
            self.assertEqual(second["measured_conflict_token_delta"], 0)
            self.assertEqual(
                second["after"]["accepted_dataset_tokens_counter"],
                first["after"]["accepted_dataset_tokens_counter"],
            )

    def test_genuinely_different_execution_identity_is_separately_admissible(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            first_gate = root / "first.json"
            second_gate = root / "second.json"
            db = root / "distillery.sqlite3"

            first_eval = helpers.qualified_evaluation()
            self.write_gate(first_gate, first_eval)
            first = promotion.promote(first_gate, helpers.SOURCE, db, **helpers.workflow_context())

            distinct_eval = helpers.qualified_evaluation()
            distinct_eval["worker_sha"] = "c" * 64
            distinct_eval["delta_id"] = "distinct-measured-execution-envelope"
            distinct_eval["evaluated_at"] = "2026-08-25T00:02:00+00:00"
            self.write_gate(second_gate, distinct_eval)
            second = promotion.promote(second_gate, helpers.SOURCE, db, **helpers.workflow_context())

            self.assertEqual(first["outcome"], "PROMOTED_NEW_PACKET")
            self.assertEqual(second["outcome"], "PROMOTED_NEW_PACKET")
            self.assertNotEqual(first["execution_replay_identity_sha256"], second["execution_replay_identity_sha256"])
            self.assertNotEqual(first["after"]["packet_id"], second["after"]["packet_id"])
            self.assertGreater(second["first_token_delta"], 0)
            self.assertEqual(second["replay_token_delta"], 0)
            self.assertEqual(second["measured_conflict_token_delta"], 0)
            self.assertGreater(
                second["after"]["accepted_dataset_tokens_counter"],
                first["after"]["accepted_dataset_tokens_counter"],
            )


if __name__ == "__main__":
    unittest.main()
