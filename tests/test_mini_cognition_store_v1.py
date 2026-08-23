from __future__ import annotations

import sqlite3
import unittest

from tools import mini_cognition_store_v1 as store


class CognitionStoreTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.execute("CREATE TABLE entity_state(id INTEGER PRIMARY KEY, generation INTEGER NOT NULL)")
        self.db.execute("INSERT INTO entity_state(id,generation) VALUES(1,0)")
        store.ensure_schema(self.db)

    def tearDown(self):
        self.db.close()

    def _objects(self):
        ids = {}
        for kind in store.REQUIRED_BINDING_KINDS + store.OPTIONAL_BINDING_KINDS:
            result = store.install_object(
                self.db,
                kind=kind,
                version="v1",
                payload={"kind": kind, "value": kind.lower()},
                provenance_refs=[f"git:example:{kind.lower()}"],
            )
            ids[kind] = result["object_id"]
        return ids

    def test_roundtrip_binding_is_generation_fenced_and_object_verified(self):
        ids = self._objects()
        created = store.activate_binding(self.db, generation=0, object_ids=ids)
        loaded = store.load_active_binding(self.db, expected_generation=0)
        self.assertEqual(loaded["binding_digest"], created["binding_digest"])
        self.assertEqual(loaded["objects"]["ZERO_IDENTITY"]["object_id"], ids["ZERO_IDENTITY"])
        self.assertEqual(loaded["authority"], "MINIUNIFIEDDB_CANONICAL_CONFIGURATION_ONLY")

    def test_stale_generation_blocks_before_new_activation(self):
        ids = self._objects()
        store.activate_binding(self.db, generation=0, object_ids=ids)
        self.db.execute("UPDATE entity_state SET generation=1 WHERE id=1")
        with self.assertRaisesRegex(store.CognitionStoreError, "STALE_ACTIVE_BINDING_GENERATION"):
            store.load_active_binding(self.db, expected_generation=1)
        with self.assertRaisesRegex(store.CognitionStoreError, "STALE_GENERATION"):
            store.activate_binding(self.db, generation=0, object_ids=ids)

    def test_payload_tamper_is_detected(self):
        ids = self._objects()
        store.activate_binding(self.db, generation=0, object_ids=ids)
        self.db.execute(
            "UPDATE cognition_objects SET payload_json='{}' WHERE object_id=?",
            (ids["GRF"],),
        )
        with self.assertRaisesRegex(store.CognitionStoreError, "OBJECT_PAYLOAD_DIGEST_MISMATCH"):
            store.load_active_binding(self.db, expected_generation=0)

    def test_wrong_kind_cannot_be_laundered_into_binding(self):
        ids = self._objects()
        poisoned = dict(ids)
        poisoned["GRF"] = ids["ZERO_IDENTITY"]
        with self.assertRaisesRegex(store.CognitionStoreError, "OBJECT_KIND_MISMATCH:GRF"):
            store.activate_binding(self.db, generation=0, object_ids=poisoned)
        active = self.db.execute("SELECT COUNT(*) FROM cognition_bindings WHERE retired_at IS NULL").fetchone()[0]
        self.assertEqual(active, 0)

    def test_failed_replacement_preserves_existing_active_binding(self):
        ids = self._objects()
        first = store.activate_binding(self.db, generation=0, object_ids=ids)
        poisoned = dict(ids)
        poisoned["WORKSPACE"] = "0" * 64
        with self.assertRaisesRegex(store.CognitionStoreError, "PLACEHOLDER_REJECTED"):
            store.activate_binding(self.db, generation=0, object_ids=poisoned)
        loaded = store.load_active_binding(self.db, expected_generation=0)
        self.assertEqual(loaded["binding_digest"], first["binding_digest"])

    def test_replayed_binding_digest_cannot_be_rebound_to_new_generation(self):
        # Unusual experiment: poison a copied valid row by changing only its generation.
        ids = self._objects()
        first = store.activate_binding(self.db, generation=0, object_ids=ids)
        self.db.execute("UPDATE entity_state SET generation=1 WHERE id=1")
        self.db.execute("UPDATE cognition_bindings SET generation=1 WHERE binding_digest=?", (first["binding_digest"],))
        with self.assertRaisesRegex(store.CognitionStoreError, "BINDING_DIGEST_MISMATCH"):
            store.load_active_binding(self.db, expected_generation=1)


if __name__ == "__main__":
    unittest.main()
