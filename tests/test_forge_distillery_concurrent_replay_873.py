import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest

from tests.test_forge_distillery_replay_identity_873 import accepted_row, bridge


class ConcurrentReplayAdmission873Tests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)
        self.db = self.root / "distillery.sqlite3"
        # Initialize schema before the race so the discriminator measures replay
        # admission serialization rather than first-create DDL behavior.
        con = sqlite3.connect(self.db)
        try:
            bridge.ensure_schema(con)
            con.commit()
        finally:
            con.close()

    def tearDown(self):
        self.td.cleanup()

    def run_concurrently(self, rows):
        barrier = threading.Barrier(len(rows))
        results = []
        errors = []
        lock = threading.Lock()

        def worker(index, row):
            eval_path = self.root / f"eval-{index}.jsonl"
            eval_path.write_text(json.dumps(row) + "\n", encoding="utf-8")
            try:
                barrier.wait(timeout=5)
                result = bridge.ingest(eval_path, self.db)
                with lock:
                    results.append(result)
            except BaseException as exc:  # test must surface any raw SQLite race failure
                with lock:
                    errors.append(exc)

        threads = [
            threading.Thread(target=worker, args=(index, row), daemon=True)
            for index, row in enumerate(rows)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=15)

        self.assertTrue(all(not thread.is_alive() for thread in threads), "concurrent ingest deadlocked")
        self.assertEqual(errors, [], f"raw concurrent admission exception(s): {errors!r}")
        self.assertEqual(len(results), len(rows))
        return results

    def test_equivalent_concurrent_replay_is_one_admit_plus_clean_duplicate(self):
        first = accepted_row(
            delta_id="envelope-a",
            evaluated_at="2026-08-25T00:00:00+00:00",
            proposal_hypothesis="candidate-a",
        )
        replay = accepted_row(
            delta_id="envelope-b",
            evaluated_at="2026-08-25T00:01:00+00:00",
            proposal_hypothesis="candidate-b",
            falsifier="different candidate-only falsifier",
        )
        self.assertEqual(bridge.execution_replay_identity(first), bridge.execution_replay_identity(replay))
        self.assertEqual(bridge.measured_packet(first), bridge.measured_packet(replay))

        results = self.run_concurrently([first, replay])
        self.assertEqual(sorted(result["admitted"] for result in results), [0, 1])
        self.assertEqual(sorted(result["duplicates"] for result in results), [0, 1])
        self.assertTrue(all(result["rejected"] == {} for result in results))

        con = sqlite3.connect(self.db)
        try:
            packets = int(con.execute("SELECT COUNT(*) FROM forge_execution_ingest").fetchone()[0])
            knowledge = int(con.execute("SELECT COUNT(*) FROM knowledge_packets").fetchone()[0])
            token_counter = int(
                con.execute("SELECT value FROM counters WHERE key='accepted_dataset_tokens'").fetchone()[0]
            )
            stored_tokens = int(con.execute("SELECT approx_tokens FROM forge_execution_ingest").fetchone()[0])
        finally:
            con.close()
        self.assertEqual(packets, 1)
        self.assertEqual(knowledge, 1)
        self.assertEqual(token_counter, stored_tokens)

    def test_concurrent_mutated_measurement_is_one_admit_plus_clean_conflict(self):
        first = accepted_row(relative_improvement_pct=100.0)
        conflict = accepted_row(
            delta_id="other-envelope",
            evaluated_at="2026-08-25T00:02:00+00:00",
            relative_improvement_pct=99.0,
        )
        self.assertEqual(bridge.execution_replay_identity(first), bridge.execution_replay_identity(conflict))
        self.assertNotEqual(bridge.measured_evidence_identity(first), bridge.measured_evidence_identity(conflict))

        results = self.run_concurrently([first, conflict])
        self.assertEqual(sorted(result["admitted"] for result in results), [0, 1])
        rejected_reasons = [reason for result in results for reason, count in result["rejected"].items() for _ in range(count)]
        self.assertEqual(rejected_reasons, ["REPLAY_IDENTITY_CONFLICT"])

        con = sqlite3.connect(self.db)
        try:
            packets = int(con.execute("SELECT COUNT(*) FROM forge_execution_ingest").fetchone()[0])
            token_counter = int(
                con.execute("SELECT value FROM counters WHERE key='accepted_dataset_tokens'").fetchone()[0]
            )
            stored_tokens = int(con.execute("SELECT approx_tokens FROM forge_execution_ingest").fetchone()[0])
        finally:
            con.close()
        self.assertEqual(packets, 1)
        self.assertEqual(token_counter, stored_tokens)

    def test_distinct_concurrent_execution_identities_remain_separately_admissible(self):
        first = accepted_row(metric="metric-a")
        second = accepted_row(metric="metric-b", delta_id="other-envelope")
        self.assertNotEqual(bridge.execution_replay_identity(first), bridge.execution_replay_identity(second))

        results = self.run_concurrently([first, second])
        self.assertEqual(sorted(result["admitted"] for result in results), [1, 1])
        self.assertTrue(all(result["duplicates"] == 0 for result in results))
        self.assertTrue(all(result["rejected"] == {} for result in results))

        con = sqlite3.connect(self.db)
        try:
            packets = int(con.execute("SELECT COUNT(*) FROM forge_execution_ingest").fetchone()[0])
            token_counter = int(
                con.execute("SELECT value FROM counters WHERE key='accepted_dataset_tokens'").fetchone()[0]
            )
            stored_tokens = int(con.execute("SELECT COALESCE(SUM(approx_tokens),0) FROM forge_execution_ingest").fetchone()[0])
        finally:
            con.close()
        self.assertEqual(packets, 2)
        self.assertEqual(token_counter, stored_tokens)

    def test_source_acquires_write_intent_before_replay_loop(self):
        source = (Path(__file__).resolve().parents[1] / "tools" / "ingest_forge_accepts_into_distillery.py").read_text(
            encoding="utf-8"
        )
        schema = source.index("ensure_schema(con)", source.index("def ingest("))
        write_intent = source.index('con.execute("BEGIN IMMEDIATE")', schema)
        loop = source.index("for line in forge_eval_path", write_intent)
        self.assertLess(schema, write_intent)
        self.assertLess(write_intent, loop)


if __name__ == "__main__":
    unittest.main()
