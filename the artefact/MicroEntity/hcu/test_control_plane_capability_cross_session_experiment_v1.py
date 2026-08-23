import sqlite3
import unittest

from control_plane_capability_binding_v1 import snapshot_capability_authority


class CanonicalDBFixture:
    def __init__(self):
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.db.execute(
            "CREATE TABLE sessions (session_id TEXT PRIMARY KEY, user_id TEXT NOT NULL, generation INTEGER NOT NULL)"
        )
        self.db.executemany(
            "INSERT INTO sessions(session_id,user_id,generation) VALUES(?,?,?)",
            (("session:a", "user:a", 7), ("session:b", "user:b", 7)),
        )
        self.live = {"session:a": 7, "session:b": 7}

    def assert_live_generation(self, session_id, generation):
        if self.live.get(session_id) != generation:
            raise RuntimeError("stale generation")


class EffectGateFixture:
    def __init__(self, db):
        self.db = db

    def available_capabilities(self):
        return ("state.noop",)


class CrossSessionCapabilityAliasExperiment(unittest.TestCase):
    def test_equal_rights_equal_generation_cannot_alias_binding(self):
        db = CanonicalDBFixture()
        gate = EffectGateFixture(db)
        a = snapshot_capability_authority(
            db, gate, user_id="user:a", session_id="session:a"
        )
        b = snapshot_capability_authority(
            db, gate, user_id="user:b", session_id="session:b"
        )
        self.assertEqual(a.entity_generation, b.entity_generation)
        self.assertEqual(a.admitted_capabilities, b.admitted_capabilities)
        self.assertNotEqual(a.binding_sha256, b.binding_sha256)
        print("EXPERIMENT_A_BINDING=" + a.binding_sha256)
        print("EXPERIMENT_B_BINDING=" + b.binding_sha256)


if __name__ == "__main__":
    unittest.main()
