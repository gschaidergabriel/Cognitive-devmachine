import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import mini_cognition_object_store as store


class CognitionObjectStoreTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.execute(
            """CREATE TABLE entity_state(
                 id INTEGER PRIMARY KEY CHECK(id=1),
                 generation INTEGER NOT NULL,
                 active_profile TEXT,
                 created_at TEXT NOT NULL,
                 updated_at TEXT NOT NULL)"""
        )
        self.db.execute(
            "INSERT INTO entity_state(id,generation,active_profile,created_at,updated_at) VALUES(1,7,NULL,'t','t')"
        )
        store.install_schema(self.db)
        self._seed("ZERO_IDENTITY", "ZERO", {"identity_id": "ZERO"})
        self._seed("GRF", "GRF:v1", {"framework": "GRF", "active": True})
        store.bind_slot(
            self.db,
            slot="ZERO_IDENTITY",
            object_kind="ZERO_IDENTITY",
            object_id="ZERO",
            object_version=1,
            expected_generation=7,
        )
        store.bind_slot(
            self.db,
            slot="GRF",
            object_kind="GRF",
            object_id="GRF:v1",
            object_version=1,
            expected_generation=7,
        )
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def _seed(self, kind, oid, payload, version=1):
        return store.put_object(
            self.db,
            object_kind=kind,
            object_id=oid,
            object_version=version,
            payload=payload,
            provenance={"source": "test", "source_sha256": "1" * 64},
            expected_generation=7,
        )

    def test_resolve_exact_generation_and_stable_digest(self):
        a = store.resolve_snapshot(
            self.db, expected_generation=7, required_slots=["ZERO_IDENTITY", "GRF"]
        )
        b = store.resolve_snapshot(
            self.db, expected_generation=7, required_slots=["GRF", "ZERO_IDENTITY"]
        )
        self.assertEqual(a["snapshot_sha256"], b["snapshot_sha256"])
        self.assertEqual(a["authority"]["durable_state"], "MiniUnifiedDB")
        self.assertEqual(a["authority"]["truth"], "NONE_FROM_BINDING_ALONE")

    def test_stale_generation_fails_closed(self):
        with self.assertRaisesRegex(store.CognitionStoreError, "GENERATION_MISMATCH"):
            store.resolve_snapshot(
                self.db, expected_generation=6, required_slots=["ZERO_IDENTITY", "GRF"]
            )

    def test_missing_required_binding_fails_closed(self):
        with self.assertRaisesRegex(store.CognitionStoreError, "MISSING_BINDING:WORKSPACE"):
            store.resolve_snapshot(
                self.db,
                expected_generation=7,
                required_slots=["ZERO_IDENTITY", "GRF", "WORKSPACE"],
            )

    def test_immutable_object_version_cannot_be_overwritten(self):
        with self.assertRaisesRegex(store.CognitionStoreError, "IMMUTABLE_OBJECT_VERSION_CONFLICT"):
            store.put_object(
                self.db,
                object_kind="ZERO_IDENTITY",
                object_id="ZERO",
                object_version=1,
                payload={"identity_id": "NOT_ZERO"},
                provenance={"source": "test", "source_sha256": "1" * 64},
                expected_generation=7,
            )

    def test_rehashed_object_substitution_still_breaks_binding_ancestry(self):
        """GO unusual experiment: rehash stored bytes, leave canonical binding untouched."""
        mutated_json = store.canonical_json({"identity_id": "SUBSTITUTED_ZERO"})
        mutated_sha = store.sha256_text(mutated_json)
        self.db.execute(
            """UPDATE cognition_objects
               SET object_json=?,object_sha256=?
               WHERE object_kind='ZERO_IDENTITY' AND object_id='ZERO' AND object_version=1""",
            (mutated_json, mutated_sha),
        )
        self.db.commit()
        with self.assertRaisesRegex(
            store.CognitionStoreError, "BINDING_OBJECT_HASH_MISMATCH:ZERO_IDENTITY"
        ):
            store.resolve_snapshot(
                self.db, expected_generation=7, required_slots=["ZERO_IDENTITY", "GRF"]
            )

    def test_binding_digest_mutation_fails_closed(self):
        self.db.execute(
            "UPDATE cognition_bindings SET binding_sha256=? WHERE slot='GRF'",
            (store.sha256_text("mutated-binding"),),
        )
        self.db.commit()
        with self.assertRaisesRegex(store.CognitionStoreError, "BINDING_DIGEST_MISMATCH:GRF"):
            store.resolve_snapshot(
                self.db, expected_generation=7, required_slots=["ZERO_IDENTITY", "GRF"]
            )


if __name__ == "__main__":
    unittest.main()
