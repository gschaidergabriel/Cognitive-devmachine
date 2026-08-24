from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"
TOOLS = ROOT / "tools"
for path in (str(TESTS), str(TOOLS)):
    if path not in sys.path:
        sys.path.insert(0, path)

import test_forge_distillery_promotion_872 as base
import promote_forge_distillery_runtime_gate as promotion


class LivePromotionSemanticReplay873(unittest.TestCase):
    def test_timestamp_narration_and_delta_rekey_replay_is_zero_delta(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            gate_path = root / "gate.json"
            db = root / "distillery.sqlite3"

            first_gate = base.passing_gate()
            gate_path.write_text(json.dumps(first_gate) + "\n", encoding="utf-8")
            first = promotion.promote(gate_path, base.SOURCE, db, **base.workflow_context())

            semantic_replay = copy.deepcopy(first_gate)
            evaluation = semantic_replay["forge_evaluation"]
            evaluation["evaluated_at"] = "2026-08-25T01:15:00+07:00"
            evaluation["delta_id"] = "promotion-regression-envelope-rekeyed"
            evaluation["proposal_hypothesis"] = "new candidate-only narration"
            evaluation["falsifier"] = "new candidate-only falsifier"
            gate_path.write_text(json.dumps(semantic_replay) + "\n", encoding="utf-8")

            second = promotion.promote(gate_path, base.SOURCE, db, **base.workflow_context())

            self.assertEqual(first["outcome"], "PROMOTED_NEW_PACKET")
            self.assertEqual(second["status"], "PASS")
            self.assertEqual(second["outcome"], "ALREADY_PROMOTED_IDEMPOTENT")
            self.assertNotEqual(first["evaluation_sha256"], second["evaluation_sha256"])
            self.assertEqual(
                first["execution_replay_identity_sha256"],
                second["execution_replay_identity_sha256"],
            )
            self.assertEqual(second["before"]["matched_by"], "execution_replay_identity_sha256")
            self.assertEqual(second["first"]["admitted"], 0)
            self.assertEqual(second["first"]["duplicates"], 1)
            self.assertEqual(second["first_token_delta"], 0)
            self.assertEqual(second["replay"]["admitted"], 0)
            self.assertEqual(second["replay"]["duplicates"], 1)
            self.assertEqual(second["replay_token_delta"], 0)
            self.assertEqual(
                second["after"]["accepted_dataset_tokens_counter"],
                first["after"]["accepted_dataset_tokens_counter"],
            )
            self.assertEqual(second["after"]["packet_id"], first["after"]["packet_id"])

    def test_same_execution_identity_with_changed_measurement_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            gate_path = root / "gate.json"
            db = root / "distillery.sqlite3"

            first_gate = base.passing_gate()
            gate_path.write_text(json.dumps(first_gate) + "\n", encoding="utf-8")
            first = promotion.promote(gate_path, base.SOURCE, db, **base.workflow_context())

            conflict = copy.deepcopy(first_gate)
            evaluation = conflict["forge_evaluation"]
            evaluation["evaluated_at"] = "2026-08-25T01:16:00+07:00"
            evaluation["delta_id"] = "promotion-regression-conflicting-envelope"
            evaluation["tests_passed"] = 3
            gate_path.write_text(json.dumps(conflict) + "\n", encoding="utf-8")

            with self.assertRaisesRegex(promotion.PromotionError, "LIVE_REPLAY_IDENTITY_CONFLICT"):
                promotion.promote(gate_path, base.SOURCE, db, **base.workflow_context())

            snap = promotion.inspect_db(
                db,
                first["evaluation_sha256"],
                first["execution_replay_identity_sha256"],
            )
            self.assertEqual(
                snap["accepted_dataset_tokens_counter"],
                first["after"]["accepted_dataset_tokens_counter"],
            )
            self.assertEqual(snap["packet_id"], first["after"]["packet_id"])


if __name__ == "__main__":
    unittest.main()
