from __future__ import annotations

import importlib.util
from pathlib import Path
import sqlite3
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    if spec is None or spec.loader is None:
        raise RuntimeError(rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = load_module("free_swarm_raw_generation_gate_878", "tools/free_swarm_raw_generation_gate_878.py")
patcher = load_module("apply_go878_raw_generation_backpressure", "tools/apply_go878_raw_generation_backpressure.py")


class RawGenerationGate878Tests(unittest.TestCase):
    def make_root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        worker = root / "active-fabric6000-v2-test" / "workers.jsonl"
        worker.parent.mkdir(parents=True)
        worker.write_text('{"http_status":200,"text":"x"}\n', encoding="utf-8")
        forge = root / "forge"
        forge.mkdir()
        db = forge / "forge.sqlite3"
        con = sqlite3.connect(db)
        con.executescript(
            """
            CREATE TABLE candidates(candidate_hash TEXT PRIMARY KEY, ready INTEGER, state TEXT);
            CREATE TABLE historical_chunks(chunk_id TEXT PRIMARY KEY, state TEXT);
            CREATE TABLE backfill_files(source_path TEXT PRIMARY KEY, inode INTEGER, byte_offset INTEGER, file_size INTEGER);
            """
        )
        st = worker.stat()
        con.execute(
            "INSERT INTO backfill_files(source_path,inode,byte_offset,file_size) VALUES(?,?,?,?)",
            (str(worker), int(st.st_ino), int(st.st_size), int(st.st_size)),
        )
        con.commit()
        return td, root, worker, con

    def test_allows_only_caught_up_saturated_low_backlog(self):
        td, root, _, con = self.make_root()
        try:
            con.execute("INSERT INTO historical_chunks VALUES('c1','SATURATED')")
            con.commit()
            out = gate.evaluate(root, threshold=64)
            self.assertTrue(out["allow_raw_generation"])
            self.assertEqual(out["blockers"], [])
            self.assertEqual(out["non_saturated_chunks"], 0)
        finally:
            con.close()
            td.cleanup()

    def test_blocks_unscanned_worker_bytes(self):
        td, root, worker, con = self.make_root()
        try:
            con.execute("UPDATE backfill_files SET byte_offset=0 WHERE source_path=?", (str(worker),))
            con.commit()
            out = gate.evaluate(root)
            self.assertFalse(out["allow_raw_generation"])
            self.assertIn("HISTORICAL_SCAN_NOT_CAUGHT_UP", out["blockers"])
        finally:
            con.close()
            td.cleanup()

    def test_blocks_any_non_saturated_historical_chunk(self):
        td, root, _, con = self.make_root()
        try:
            con.execute("INSERT INTO historical_chunks VALUES('c1','PENDING_EXTRACTION')")
            con.commit()
            out = gate.evaluate(root)
            self.assertFalse(out["allow_raw_generation"])
            self.assertIn("HISTORICAL_CHUNKS_NOT_SATURATED", out["blockers"])
        finally:
            con.close()
            td.cleanup()

    def test_blocks_max_passes_reached(self):
        td, root, _, con = self.make_root()
        try:
            con.execute("INSERT INTO historical_chunks VALUES('c1','MAX_PASSES_REACHED')")
            con.commit()
            out = gate.evaluate(root)
            self.assertFalse(out["allow_raw_generation"])
            self.assertIn("MAX_PASSES_REACHED_UNRESOLVED", out["blockers"])
        finally:
            con.close()
            td.cleanup()

    def test_blocks_conversion_pressure_at_threshold(self):
        td, root, _, con = self.make_root()
        try:
            con.execute("INSERT INTO historical_chunks VALUES('c1','SATURATED')")
            con.executemany(
                "INSERT INTO candidates(candidate_hash,ready,state) VALUES(?,?,?)",
                [(f"r{i}", 1, "NEW") for i in range(64)],
            )
            con.commit()
            out = gate.evaluate(root, threshold=64)
            self.assertFalse(out["allow_raw_generation"])
            self.assertEqual(out["conversion_pressure"], 64)
            self.assertIn("CONVERSION_PRESSURE_AT_OR_ABOVE_THRESHOLD", out["blockers"])
        finally:
            con.close()
            td.cleanup()

    def test_blocks_workers_jsonl_toctou(self):
        td, root, _, con = self.make_root()
        try:
            con.execute("INSERT INTO historical_chunks VALUES('c1','SATURATED')")
            con.commit()
            stable = gate.worker_snapshot(root)
            calls = 0

            def changing(_root):
                nonlocal calls
                calls += 1
                if calls == 1:
                    return stable
                changed = [dict(row) for row in stable]
                changed[0]["mtime_ns"] += 1
                return changed

            out = gate.evaluate(root, snapshot_fn=changing)
            self.assertFalse(out["allow_raw_generation"])
            self.assertIn("WORKERS_JSONL_CHANGED_DURING_GATE", out["blockers"])
        finally:
            con.close()
            td.cleanup()

    def test_patcher_routes_supervisor_through_single_helper(self):
        source = (
            "start_6000(){\n  :\n}\n\n"
            "  reconcile_6000_admission\n"
            "  start_6000\n"
            "  refresh_root_results\n"
        )
        patched = patcher.patch(source)
        self.assertEqual(patched.count("free_swarm_raw_generation_gate_878.py"), 1)
        self.assertIn("if raw_generation_allowed; then\n    start_6000\n  else\n    stop_6000", patched)
        with self.assertRaises(SystemExit):
            patcher.patch(patched)


if __name__ == "__main__":
    unittest.main()
