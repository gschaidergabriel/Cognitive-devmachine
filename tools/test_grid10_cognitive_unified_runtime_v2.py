#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from grid10_fabric import Fabric
from grid10_cognitive_heartbeat_v1 import CognitiveHeartbeatStore, _trusted_normal_axes
from grid10_cognitive_unified_runtime_v2 import (
    assert_shared_unifieddb_authority,
    build_shared_runtime,
    fingerprint_sqlite,
    run_bounded,
)


class UnifiedRuntimeV2Tests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)

    def tearDown(self):
        self.td.cleanup()

    def test_one_physical_db_contains_fabric_and_heartbeat_tables(self):
        db = self.root / "unified.sqlite"
        fabric, store, _, fp = build_shared_runtime(db)
        self.assertEqual(Path(fabric.path).resolve(), Path(store.path).resolve())
        self.assertEqual(fp, fingerprint_sqlite(db))
        con = sqlite3.connect(str(db))
        try:
            names = {r[0] for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )}
        finally:
            con.close()
        self.assertIn("nodes", names)
        self.assertIn("regulators", names)
        self.assertIn("ticks", names)
        self.assertIn("meta", names)

    def test_split_database_authority_fails_closed(self):
        fabric = Fabric(self.root / "fabric.sqlite")
        store = CognitiveHeartbeatStore(self.root / "heartbeat.sqlite")
        with self.assertRaisesRegex(RuntimeError, "UNIFIEDDB_AUTHORITY_SPLIT"):
            assert_shared_unifieddb_authority(fabric, store)

    def test_restart_reopens_same_authority_and_keeps_tick_history(self):
        db = self.root / "unified.sqlite"
        _, store1, runtime1, fp1 = build_shared_runtime(db)
        first = runtime1.tick_once(tick_id="restart-before", trusted_axes=_trusted_normal_axes())
        self.assertEqual(first.assurance_mode.value, "NORMAL")
        self.assertTrue(store1.load_previous_projected())

        # New objects simulate process/session re-entry. No in-memory runtime state is reused.
        _, store2, runtime2, fp2 = build_shared_runtime(db)
        second = runtime2.tick_once(tick_id="restart-after", trusted_axes=_trusted_normal_axes())
        self.assertEqual(second.assurance_mode.value, "NORMAL")
        self.assertEqual(fp1, fp2)
        self.assertTrue(store2.load_previous_projected())

        con = sqlite3.connect(str(db))
        try:
            tick_ids = [r[0] for r in con.execute(
                "SELECT tick_id FROM ticks ORDER BY created_ts"
            )]
            last = con.execute("SELECT v FROM meta WHERE k='last_tick_id'").fetchone()[0]
        finally:
            con.close()
        self.assertEqual(tick_ids, ["restart-before", "restart-after"])
        self.assertEqual(last, "restart-after")

    def test_bounded_entry_emits_two_replayable_frames_on_shared_db(self):
        db = self.root / "unified.sqlite"
        frames = self.root / "frames.jsonl"
        rows = run_bounded(
            unified_db=db,
            frames_jsonl=frames,
            ticks=2,
            interval=0.0,
            trusted_normal_test_fixture=True,
        )
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(r["assurance_mode"] == "NORMAL" for r in rows))
        parsed = [json.loads(line) for line in frames.read_text().splitlines() if line.strip()]
        self.assertEqual(len(parsed), 2)
        self.assertTrue(all(r["schema"] == "COGNITIVE_LOOP_FRAME/v1" for r in parsed))
        self.assertEqual(fingerprint_sqlite(db).realpath, str(db.resolve()))


if __name__ == "__main__":
    unittest.main()
