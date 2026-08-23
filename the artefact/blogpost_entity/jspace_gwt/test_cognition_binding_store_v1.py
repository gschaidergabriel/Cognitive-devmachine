#!/usr/bin/env python3
import sqlite3
import unittest

import cognition_binding_store_v1 as store


class CognitionBindingStoreTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.execute("CREATE TABLE entity_state(id INTEGER PRIMARY KEY, generation INTEGER NOT NULL)")
        self.db.execute("INSERT INTO entity_state(id,generation) VALUES(1,7)")
        store.ensure_schema(self.db)
        self.digests = {}
        for name in store.OBJECT_TYPES:
            self.digests[name] = store.put_object(self.db, name, {"kind": name, "version": 1})

    def tearDown(self):
        self.db.close()

    def test_complete_exact_generation_bundle_roundtrip(self):
        bound = store.bind_bundle(self.db, expected_generation=7, object_digests=self.digests)
        resolved = store.resolve_bundle(self.db, expected_generation=7)
        self.assertTrue(bound["ok"])
        self.assertEqual(resolved["bundle_digest"], bound["bundle_digest"])
        self.assertEqual(set(resolved["objects"]), set(store.OBJECT_TYPES))
        self.assertEqual(resolved["authority"], "MiniUnifiedDB")

    def test_missing_object_blocks_bundle(self):
        poisoned = dict(self.digests)
        poisoned["WORKSPACE"] = "1" * 64
        with self.assertRaisesRegex(store.CognitionBindingError, "COGNITION_OBJECT_MISSING:WORKSPACE"):
            store.bind_bundle(self.db, expected_generation=7, object_digests=poisoned)

    def test_incomplete_bundle_blocks(self):
        incomplete = dict(self.digests)
        incomplete.pop("JACOBIAN_LENS")
        with self.assertRaisesRegex(store.CognitionBindingError, "COGNITION_BUNDLE_INCOMPLETE"):
            store.bind_bundle(self.db, expected_generation=7, object_digests=incomplete)

    def test_placeholder_digest_blocks(self):
        poisoned = dict(self.digests)
        poisoned["LOCAL_MODEL"] = "0" * 64
        with self.assertRaisesRegex(store.CognitionBindingError, "PLACEHOLDER_REJECTED"):
            store.bind_bundle(self.db, expected_generation=7, object_digests=poisoned)

    def test_generation_advance_invalidates_active_bundle(self):
        store.bind_bundle(self.db, expected_generation=7, object_digests=self.digests)
        self.db.execute("UPDATE entity_state SET generation=8 WHERE id=1")
        with self.assertRaisesRegex(store.CognitionBindingError, "STALE_GENERATION"):
            store.resolve_bundle(self.db, expected_generation=7)
        with self.assertRaisesRegex(store.CognitionBindingError, "COGNITION_BUNDLE_STALE"):
            store.resolve_bundle(self.db, expected_generation=8)

    def test_same_db_object_tamper_is_detected(self):
        store.bind_bundle(self.db, expected_generation=7, object_digests=self.digests)
        self.db.execute(
            "UPDATE cognition_objects SET object_json='{}' WHERE object_type='GRF' AND object_digest=?",
            (self.digests["GRF"],),
        )
        with self.assertRaisesRegex(store.CognitionBindingError, "COGNITION_OBJECT_DIGEST_MISMATCH:GRF"):
            store.resolve_bundle(self.db, expected_generation=7)

    def test_bundle_tamper_is_detected(self):
        store.bind_bundle(self.db, expected_generation=7, object_digests=self.digests)
        self.db.execute("UPDATE cognition_bundles SET bundle_json='{}' WHERE singleton=1")
        with self.assertRaisesRegex(store.CognitionBindingError, "COGNITION_BUNDLE_DIGEST_MISMATCH"):
            store.resolve_bundle(self.db, expected_generation=7)


if __name__ == "__main__":
    unittest.main()
