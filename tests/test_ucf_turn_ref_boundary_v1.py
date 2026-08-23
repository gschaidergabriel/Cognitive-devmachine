from __future__ import annotations

import hashlib
import importlib.util
import sqlite3
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bridge = load(ROOT / "tools" / "mini_entity_cognition_turn_ref_v1.py", "turn_ref_bridge")
guard = load(ROOT / "tools" / "check_ucf_turn_ref_source_v1.py", "turn_ref_guard")


class FakeStore:
    @staticmethod
    def resolve_prepare_binding(db, *, entity_generation, causal_turn_id, task_text):
        row = db.execute("SELECT generation,causal_turn_id,task_text FROM binding WHERE id=1").fetchone()
        if row is None:
            raise ValueError("TURN_BINDING_UNAVAILABLE")
        if entity_generation != row[0]:
            raise ValueError("STALE_GENERATION")
        if causal_turn_id != row[1]:
            raise ValueError("TURN_BINDING_UNAVAILABLE")
        if task_text != row[2]:
            raise ValueError("TURN_TASK_BINDING_MISMATCH")
        return {
            "ok": True,
            "entity_generation": entity_generation,
            "causal_turn_id": causal_turn_id,
            "task_sha256": hashlib.sha256(task_text.encode()).hexdigest(),
            "workspace_digest": "ab" * 32,
        }


class TurnRefBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "mini.db"
        db = sqlite3.connect(self.db_path)
        db.execute("CREATE TABLE binding(id INTEGER PRIMARY KEY,generation INTEGER,causal_turn_id TEXT,task_text TEXT)")
        db.execute("INSERT INTO binding VALUES(1,7,'turn-7','exact task')")
        db.commit()
        db.close()

    def tearDown(self):
        self.tmp.cleanup()

    def ref(self, *, causal_turn_id="turn-7", task_text="exact task"):
        return {
            "schema": bridge.SCHEMA,
            "causal_turn_id": causal_turn_id,
            "task_text": task_text,
            "task_sha256": hashlib.sha256(task_text.encode()).hexdigest(),
        }

    def test_exact_untrusted_lookup_ref_must_revalidate_in_minunifieddb(self):
        out = bridge.resolve_turn_ref(
            self.db_path, entity_generation=7, turn_ref=self.ref(), store=FakeStore
        )
        self.assertTrue(out["ok"])
        self.assertEqual(out["causal_turn_id"], "turn-7")

    def test_task_text_tamper_fails_at_same_db_resolver(self):
        with self.assertRaisesRegex(bridge.TurnRefError, "TURN_TASK_BINDING_MISMATCH"):
            bridge.resolve_turn_ref(
                self.db_path,
                entity_generation=7,
                turn_ref=self.ref(task_text="tampered task"),
                store=FakeStore,
            )

    def test_stale_generation_fails_at_same_db_resolver(self):
        with self.assertRaisesRegex(bridge.TurnRefError, "STALE_GENERATION"):
            bridge.resolve_turn_ref(
                self.db_path, entity_generation=8, turn_ref=self.ref(), store=FakeStore
            )

    def test_current_main_shape_is_explicitly_nonconverged(self):
        source = '''
        let cognition_data = map_new()
        map_set(cognition_data,"compiled",compiled)
        map_set(cognition_data,"prompt",prompt)
        let admitted = phase("pipeline_cognitive_fabric_admit",entity_db,source_db,profile,previous,cognition_data)
        '''
        report = guard.evaluate(source)
        self.assertFalse(report["pass"])
        self.assertIn("MISSING_CAUSAL_TURN_LOOKUP_KEY", report["errors"])
        self.assertIn("MISSING_TASK_LOOKUP_KEY", report["errors"])

    def test_explicit_turn_ref_shape_is_source_admissible(self):
        source = '''
        let cognition_data = map_new()
        map_set(cognition_data,"compiled",compiled)
        map_set(cognition_data,"prompt",prompt)
        map_set(cognition_data,"turn_ref",turn_ref)
        let prepared = phase("pipeline_cognitive_fabric_prepare",entity_db,source_db,profile,previous,cognition_data)
        '''
        self.assertTrue(guard.evaluate(source)["pass"])

    def test_unusual_packet_hash_turn_alias_poison_fails_closed(self):
        # Exactly one unusual intervention for this go macrocycle: deliberately derive
        # a causal turn lookup key from packet_hash and require the source guard to reject it.
        poisoned = '''
        let cognition_data = map_new()
        map_set(cognition_data,"compiled",compiled)
        map_set(cognition_data,"prompt",prompt)
        map_set(cognition_data,"causal_turn_id",compiled.packet_hash)
        map_set(cognition_data,"task_text",turn_ref.task_text)
        let admitted = phase("pipeline_cognitive_fabric_admit",entity_db,source_db,profile,previous,cognition_data)
        '''
        report = guard.evaluate(poisoned)
        self.assertFalse(report["pass"])
        self.assertIn("UNSAFE_CAUSAL_TURN_DERIVATION", report["errors"])


if __name__ == "__main__":
    unittest.main()
