from __future__ import annotations

import importlib.util
from pathlib import Path
import sqlite3
import sys
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

BRIDGE_PATH = TOOLS / "ingest_forge_accepts_into_distillery.py"
bridge_spec = importlib.util.spec_from_file_location("bridge_concurrent_873", BRIDGE_PATH)
bridge = importlib.util.module_from_spec(bridge_spec)
assert bridge_spec.loader is not None
bridge_spec.loader.exec_module(bridge)

FIXTURE_PATH = ROOT / "tests" / "test_forge_distillery_replay_identity_873.py"
fixture_spec = importlib.util.spec_from_file_location("replay_fixture_873", FIXTURE_PATH)
fixture = importlib.util.module_from_spec(fixture_spec)
assert fixture_spec.loader is not None
fixture_spec.loader.exec_module(fixture)


class ConcurrentReplayAdmission873Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.td = tempfile.TemporaryDirectory()
        self.db = Path(self.td.name) / "distillery.sqlite3"
        con = sqlite3.connect(self.db, timeout=10)
        try:
            bridge.ensure_schema(con)
            con.commit()
        finally:
            con.close()

    def tearDown(self) -> None:
        self.td.cleanup()

    def _race(self, rows: list[dict]) -> tuple[list[tuple[bool, str, str | None]], list[str]]:
        barrier = threading.Barrier(len(rows))
        results: list[tuple[bool, str, str | None]] = []
        errors: list[str] = []
        lock = threading.Lock()

        def worker(row: dict) -> None:
            con = sqlite3.connect(self.db, timeout=10)
            try:
                barrier.wait(timeout=5)
                result = bridge.admit_one_serialized(con, row)
                with lock:
                    results.append(result)
            except Exception as exc:  # regression records any leaked lock/integrity failure
                with lock:
                    errors.append(f"{type(exc).__name__}:{exc}")
            finally:
                con.close()

        threads = [threading.Thread(target=worker, args=(row,), daemon=True) for row in rows]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=15)
        self.assertTrue(all(not thread.is_alive() for thread in threads), "concurrent admission deadlocked")
        return results, errors

    def _db_counts(self) -> dict[str, int]:
        con = sqlite3.connect(self.db, timeout=10)
        try:
            def counter(key: str) -> int:
                row = con.execute("SELECT value FROM counters WHERE key=?", (key,)).fetchone()
                return int(row[0]) if row else 0

            return {
                "ingest_rows": int(con.execute("SELECT COUNT(*) FROM forge_execution_ingest").fetchone()[0]),
                "knowledge_packets": int(con.execute("SELECT COUNT(*) FROM knowledge_packets").fetchone()[0]),
                "accepted_packets": counter("accepted_packets"),
                "accepted_dataset_tokens": counter("accepted_dataset_tokens"),
            }
        finally:
            con.close()

    def test_same_replay_concurrently_is_one_admission_plus_clean_duplicate(self) -> None:
        row = fixture.accepted_row()
        results, errors = self._race([row, fixture.accepted_row()])

        self.assertEqual(errors, [])
        self.assertEqual(len(results), 2)
        self.assertEqual(sum(1 for admitted, _, _ in results if admitted), 1)
        self.assertEqual(sum(1 for admitted, reason, _ in results if not admitted and reason == "DUPLICATE"), 1)

        counts = self._db_counts()
        self.assertEqual(counts["ingest_rows"], 1)
        self.assertEqual(counts["knowledge_packets"], 1)
        self.assertEqual(counts["accepted_packets"], 1)
        self.assertGreater(counts["accepted_dataset_tokens"], 0)

    def test_same_replay_with_concurrent_measurement_mutation_is_clean_conflict(self) -> None:
        original = fixture.accepted_row()
        mutated = fixture.accepted_row(
            evaluated_at="2026-08-25T01:06:01+07:00",
            relative_improvement_pct=75.0,
        )
        results, errors = self._race([original, mutated])

        self.assertEqual(errors, [])
        self.assertEqual(len(results), 2)
        self.assertEqual(sum(1 for admitted, _, _ in results if admitted), 1)
        self.assertEqual(
            sum(1 for admitted, reason, _ in results if not admitted and reason == "REPLAY_IDENTITY_CONFLICT"),
            1,
        )

        counts = self._db_counts()
        self.assertEqual(counts["ingest_rows"], 1)
        self.assertEqual(counts["knowledge_packets"], 1)
        self.assertEqual(counts["accepted_packets"], 1)
        self.assertGreater(counts["accepted_dataset_tokens"], 0)

    def test_reopen_preserves_semantic_replay_classification(self) -> None:
        con = sqlite3.connect(self.db, timeout=10)
        try:
            admitted, _, _ = bridge.admit_one_serialized(con, fixture.accepted_row())
            self.assertTrue(admitted)
        finally:
            con.close()

        reopened = sqlite3.connect(self.db, timeout=10)
        try:
            replay = fixture.accepted_row(
                evaluated_at="2026-08-25T01:07:00+07:00",
                proposal_hypothesis="changed candidate-only narration after reopen",
                falsifier="changed candidate-only falsifier after reopen",
            )
            admitted, reason, packet_id = bridge.admit_one_serialized(reopened, replay)
        finally:
            reopened.close()

        self.assertFalse(admitted)
        self.assertEqual(reason, "DUPLICATE")
        self.assertIsNone(packet_id)
        counts = self._db_counts()
        self.assertEqual(counts["ingest_rows"], 1)
        self.assertEqual(counts["accepted_packets"], 1)


if __name__ == "__main__":
    unittest.main()
