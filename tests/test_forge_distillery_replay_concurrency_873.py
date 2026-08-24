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
spec = importlib.util.spec_from_file_location("bridge_concurrency_873", MODULE_PATH)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


class ReplayConcurrency873Tests(unittest.TestCase):
    def test_write_intent_is_held_before_replay_lookup(self):
        """The replay read must occur only after this writer owns SQLite write intent."""
        with tempfile.TemporaryDirectory() as root:
            root_path = Path(root)
            eval_path = root_path / "eval.jsonl"
            db_path = root_path / "distillery.sqlite3"
            eval_path.write_text(json.dumps({"synthetic": "probe"}) + "\n", encoding="utf-8")

            original_admit_one = bridge.admit_one
            observed = {}

            def probe_admit_one(con: sqlite3.Connection, row: dict):
                observed["in_transaction"] = con.in_transaction
                contender = sqlite3.connect(db_path, timeout=0)
                try:
                    with self.assertRaises(sqlite3.OperationalError) as ctx:
                        contender.execute("BEGIN IMMEDIATE")
                    self.assertIn("locked", str(ctx.exception).lower())
                finally:
                    contender.close()
                # No evidence admission is needed for this transaction-order probe.
                return False, "DUPLICATE", None

            bridge.admit_one = probe_admit_one
            try:
                result = bridge.ingest(eval_path, db_path)
            finally:
                bridge.admit_one = original_admit_one

            self.assertIs(observed.get("in_transaction"), True)
            self.assertEqual(result["seen"], 1)
            self.assertEqual(result["admitted"], 0)
            self.assertEqual(result["duplicates"], 1)

            # After the ingest unit commits, write intent must be released.
            contender = sqlite3.connect(db_path, timeout=0)
            try:
                contender.execute("BEGIN IMMEDIATE")
                self.assertTrue(contender.in_transaction)
                contender.rollback()
            finally:
                contender.close()


if __name__ == "__main__":
    unittest.main()
