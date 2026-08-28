import importlib.util
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "test_forge_distillery_replay_identity_873.py"
spec = importlib.util.spec_from_file_location("forge_replay_identity_873_fixture", FIXTURE_PATH)
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)
bridge = fixture.bridge
accepted_row = fixture.accepted_row
admission = fixture.admission


class ConcurrentReplayAdmission873Tests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)
        self.db = self.root / "distillery.sqlite3"

    def tearDown(self):
        self.td.cleanup()

    def _run_concurrent(self, rows):
        eval_paths = []
        for index, row in enumerate(rows):
            path = self.root / f"eval-{index}.jsonl"
            path.write_text(bridge.canonical_json(row) + "\n", encoding="utf-8")
            eval_paths.append(path)

        # Isolate the discriminator to replay admission rather than first-use schema
        # creation. Production schema migration is covered separately; here both
        # writers begin against the same already-initialized WAL database.
        setup_con = sqlite3.connect(self.db)
        try:
            bridge.ensure_schema(setup_con)
            setup_con.commit()
        finally:
            setup_con.close()

        results = [None] * len(rows)
        errors = []
        missing_write_intent = []
        original_admit_one = bridge.admit_one
        lock = threading.Lock()

        def guarded_admit_one(con, row):
            # The replay lookup in admit_one must only be reachable after BEGIN
            # IMMEDIATE acquired write intent. This makes the regression deterministic:
            # a pre-fix SELECT-before-write caller fails here even when scheduler timing
            # happens to hide its later unique-index race.
            if not con.in_transaction:
                with lock:
                    missing_write_intent.append(True)
            return original_admit_one(con, row)

        def worker(index):
            try:
                results[index] = bridge.ingest(eval_paths[index], self.db)
            except Exception as exc:
                with lock:
                    errors.append(exc)

        bridge.admit_one = guarded_admit_one
        try:
            threads = [threading.Thread(target=worker, args=(index,)) for index in range(len(rows))]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=10)
            self.assertTrue(all(not thread.is_alive() for thread in threads), "concurrent ingest deadlocked")
        finally:
            bridge.admit_one = original_admit_one

        self.assertEqual(errors, [])
        self.assertEqual(missing_write_intent, [])
        self.assertTrue(all(result is not None for result in results))
        return results

    def _db_counts(self):
        con = sqlite3.connect(self.db)
        try:
            rows = int(con.execute("SELECT COUNT(*) FROM forge_execution_ingest").fetchone()[0])
            packets = int(con.execute("SELECT COUNT(*) FROM knowledge_packets").fetchone()[0])
            token_row = con.execute("SELECT value FROM counters WHERE key='accepted_dataset_tokens'").fetchone()
            tokens = int(token_row[0]) if token_row else 0
            return rows, packets, tokens
        finally:
            con.close()

    def test_same_replay_concurrently_is_one_admission_plus_one_duplicate(self):
        base = accepted_row()
        replay = accepted_row(
            delta_id="different-envelope-id",
            evaluated_at="2026-08-25T01:07:00+07:00",
            proposal_hypothesis="different candidate narration",
            falsifier="different candidate falsifier",
        )
        results = self._run_concurrent([base, replay])

        self.assertEqual(sum(result["admitted"] for result in results), 1)
        self.assertEqual(sum(result["duplicates"] for result in results), 1)
        self.assertEqual(sum(result["rejected"].get("REPLAY_IDENTITY_CONFLICT", 0) for result in results), 0)
        rows, packets, tokens = self._db_counts()
        self.assertEqual(rows, 1)
        self.assertEqual(packets, 1)
        self.assertGreater(tokens, 0)

    def test_same_replay_with_mutated_measurement_concurrently_fails_closed(self):
        base = accepted_row()
        conflicting = accepted_row(
            delta_id="different-envelope-id",
            evaluated_at="2026-08-25T01:08:00+07:00",
            relative_improvement_pct=75.0,
        )
        results = self._run_concurrent([base, conflicting])

        self.assertEqual(sum(result["admitted"] for result in results), 1)
        self.assertEqual(sum(result["duplicates"] for result in results), 0)
        self.assertEqual(sum(result["rejected"].get("REPLAY_IDENTITY_CONFLICT", 0) for result in results), 1)
        rows, packets, tokens = self._db_counts()
        self.assertEqual(rows, 1)
        self.assertEqual(packets, 1)
        self.assertGreater(tokens, 0)

    def test_distinct_execution_identities_concurrently_remain_admissible(self):
        first = accepted_row()
        second = accepted_row(
            delta_id="distinct-envelope",
            worker_sha="f" * 64,
            evaluation_repo_head="e" * 40,
            execution_admission=admission(evaluation_head="e" * 40),
            evaluated_at="2026-08-25T01:09:00+07:00",
        )
        results = self._run_concurrent([first, second])

        self.assertEqual(sum(result["admitted"] for result in results), 2)
        self.assertEqual(sum(result["duplicates"] for result in results), 0)
        self.assertEqual(sum(result["rejected"].get("REPLAY_IDENTITY_CONFLICT", 0) for result in results), 0)
        rows, packets, tokens = self._db_counts()
        self.assertEqual(rows, 2)
        self.assertEqual(packets, 2)
        self.assertGreater(tokens, 0)


if __name__ == "__main__":
    unittest.main()
