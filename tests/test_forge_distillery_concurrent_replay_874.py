import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest

from tests.test_forge_distillery_replay_identity_873 import accepted_row, bridge


class ConcurrentReplayTransaction874Tests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)
        self.eval = self.root / "eval.jsonl"
        self.db = self.root / "distillery.sqlite3"
        self.eval.write_text(json.dumps(accepted_row()) + "\n", encoding="utf-8")

    def tearDown(self):
        self.td.cleanup()

    def prepare_schema(self):
        con = sqlite3.connect(self.db, timeout=30)
        bridge.ensure_schema(con)
        con.commit()
        con.close()

    def run_concurrently(self, *paths):
        original_ensure_schema = bridge.ensure_schema
        bridge.ensure_schema = lambda con: None
        barrier = threading.Barrier(len(paths))
        outputs = []
        errors = []
        lock = threading.Lock()

        def worker(path):
            try:
                barrier.wait(timeout=5)
                result = bridge.ingest(path, self.db)
                with lock:
                    outputs.append(result)
            except Exception as exc:  # pragma: no cover - asserted below
                with lock:
                    errors.append(repr(exc))

        threads = [threading.Thread(target=worker, args=(path,)) for path in paths]
        try:
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=10)
        finally:
            bridge.ensure_schema = original_ensure_schema
        return outputs, errors

    def test_ingest_holds_write_intent_before_first_replay_lookup(self):
        observed = {"in_transaction": False, "contender_locked": False}
        original_admit_one = bridge.admit_one

        def probe(con, row):
            observed["in_transaction"] = bool(con.in_transaction)
            contender = sqlite3.connect(self.db, timeout=0)
            try:
                try:
                    contender.execute("BEGIN IMMEDIATE")
                except sqlite3.OperationalError as exc:
                    observed["contender_locked"] = "locked" in str(exc).lower()
                else:
                    contender.rollback()
            finally:
                contender.close()
            return original_admit_one(con, row)

        bridge.admit_one = probe
        try:
            out = bridge.ingest(self.eval, self.db)
        finally:
            bridge.admit_one = original_admit_one

        self.assertEqual(out["admitted"], 1)
        self.assertTrue(observed["in_transaction"])
        self.assertTrue(observed["contender_locked"])

    def test_two_concurrent_same_replay_writers_classify_cleanly(self):
        self.prepare_schema()
        outputs, errors = self.run_concurrently(self.eval, self.eval)

        self.assertFalse(errors, errors)
        self.assertEqual(len(outputs), 2)
        self.assertEqual(sorted(out["admitted"] for out in outputs), [0, 1])
        self.assertEqual(sorted(out["duplicates"] for out in outputs), [0, 1])

        con = sqlite3.connect(self.db, timeout=30)
        try:
            ingest_rows = con.execute("SELECT COUNT(*) FROM forge_execution_ingest").fetchone()[0]
            token_row = con.execute("SELECT value FROM counters WHERE key='accepted_dataset_tokens'").fetchone()
        finally:
            con.close()
        self.assertEqual(ingest_rows, 1)
        self.assertIsNotNone(token_row)
        self.assertGreater(int(token_row[0]), 0)
        self.assertEqual({out["accepted_dataset_tokens_counter"] for out in outputs}, {int(token_row[0])})

    def test_concurrent_measured_mutation_is_one_admit_plus_one_conflict(self):
        conflict_eval = self.root / "conflict.jsonl"
        conflict_eval.write_text(
            json.dumps(accepted_row(relative_improvement_pct=75.0)) + "\n",
            encoding="utf-8",
        )
        self.prepare_schema()
        outputs, errors = self.run_concurrently(self.eval, conflict_eval)

        self.assertFalse(errors, errors)
        self.assertEqual(len(outputs), 2)
        self.assertEqual(sorted(out["admitted"] for out in outputs), [0, 1])
        self.assertEqual(sum(out["duplicates"] for out in outputs), 0)
        self.assertEqual(
            sum(out["rejected"].get("REPLAY_IDENTITY_CONFLICT", 0) for out in outputs),
            1,
        )

        con = sqlite3.connect(self.db, timeout=30)
        try:
            ingest_rows = con.execute("SELECT COUNT(*) FROM forge_execution_ingest").fetchone()[0]
            token_row = con.execute("SELECT value FROM counters WHERE key='accepted_dataset_tokens'").fetchone()
        finally:
            con.close()
        self.assertEqual(ingest_rows, 1)
        self.assertIsNotNone(token_row)
        self.assertGreater(int(token_row[0]), 0)
        self.assertEqual({out["accepted_dataset_tokens_counter"] for out in outputs}, {int(token_row[0])})


if __name__ == "__main__":
    unittest.main()
