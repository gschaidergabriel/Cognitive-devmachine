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


class PromotionSourceGuards872(unittest.TestCase):
    def test_wrong_source_sha_is_rejected(self):
        result = {
            "schema": promotion.PASS_SCHEMA,
            "pass": True,
            "status": promotion.PASS_STATUS,
            "source_sha": "1" * 40,
        }
        with self.assertRaises(promotion.PromotionError):
            promotion.validate_gate_result(result, "2" * 40)

    def test_non_pass_receipt_is_rejected(self):
        result = {
            "schema": promotion.PASS_SCHEMA,
            "pass": False,
            "status": "FAIL_RUNTIME_GATE",
            "source_sha": "1" * 40,
        }
        with self.assertRaises(promotion.PromotionError):
            promotion.validate_gate_result(result, "1" * 40)

    def test_inspect_db_preserves_existing_token_counter_before_first_forge_table(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "distillery.sqlite3"
            con = sqlite3.connect(db)
            try:
                con.execute("CREATE TABLE counters(key TEXT PRIMARY KEY, value INTEGER NOT NULL DEFAULT 0)")
                con.execute("INSERT INTO counters(key,value) VALUES('accepted_dataset_tokens', 1234)")
                con.commit()
            finally:
                con.close()

            observed = promotion.inspect_db(db, "a" * 64)
            self.assertTrue(observed["db_exists"])
            self.assertFalse(observed["evaluation_present"])
            self.assertEqual(observed["accepted_dataset_tokens_counter"], 1234)
            self.assertEqual(observed["packet_tokens"], 0)


if __name__ == "__main__":
    unittest.main()
