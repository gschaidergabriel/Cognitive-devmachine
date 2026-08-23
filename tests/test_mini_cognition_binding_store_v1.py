import hashlib
import sqlite3
import unittest

from tools import mini_cognition_binding_store_v1 as store


class MiniCognitionBindingStoreV1Tests(unittest.TestCase):
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
        self.object_ids = {}
        self.subjects = {}
        for kind in store.REQUIRED_BINDING_KINDS:
            subject = hashlib.sha256(("subject:" + kind).encode()).hexdigest()
            self.subjects[kind] = subject
            result = store.put_object(
                self.db,
                kind=kind,
                version="v1",
                subject_sha256=subject,
                payload={"kind": kind, "fixture": True},
                provenance_refs=["fixture:" + kind.lower()],
            )
            self.object_ids[kind] = result["object_id"]
        self.binding = store.create_binding(
            self.db,
            object_ids=self.object_ids,
            boot_binding_receipt_sha256=hashlib.sha256(b"boot").hexdigest(),
            policy_authority_sha256=hashlib.sha256(b"policy").hexdigest(),
            source_ref="fixture:exact-source",
        )
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_activation_is_generation_cas_and_read_is_exact(self):
        activated = store.activate_binding(
            self.db, binding_id=self.binding["binding_id"], expected_generation=7
        )
        self.assertEqual(activated["generation"], 8)
        read = store.read_active_binding(self.db, expected_generation=8)
        self.assertEqual(read["authority"], "MiniUnifiedDB")
        self.assertEqual(read["zero_identity_digest"], self.subjects["ZERO_IDENTITY"])
        self.assertEqual(read["grf_digest"], self.subjects["GRF"])
        self.assertEqual(read["local_model_digest"], self.subjects["BUNDLED_MODEL"])
        self.assertEqual(read["runtime_credit"], "ZERO_UNTIL_EXECUTED")

    def test_stale_activation_fails_closed_without_generation_change(self):
        with self.assertRaisesRegex(store.CognitionBindingError, "STALE_GENERATION"):
            store.activate_binding(
                self.db, binding_id=self.binding["binding_id"], expected_generation=6
            )
        generation = self.db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()[0]
        self.assertEqual(generation, 7)

    def test_stale_read_fails_closed(self):
        store.activate_binding(self.db, binding_id=self.binding["binding_id"], expected_generation=7)
        with self.assertRaisesRegex(store.CognitionBindingError, "STALE_GENERATION"):
            store.read_active_binding(self.db, expected_generation=7)

    def test_binding_kind_swap_fails_closed(self):
        poisoned = dict(self.object_ids)
        poisoned["GRF"] = self.object_ids["ZERO_IDENTITY"]
        with self.assertRaisesRegex(store.CognitionBindingError, "BINDING_OBJECT_KIND_MISMATCH:GRF"):
            store.create_binding(
                self.db,
                object_ids=poisoned,
                boot_binding_receipt_sha256=hashlib.sha256(b"boot2").hexdigest(),
                policy_authority_sha256=hashlib.sha256(b"policy2").hexdigest(),
                source_ref="fixture:poison",
            )

    def test_placeholder_subject_digest_is_rejected(self):
        with self.assertRaisesRegex(store.CognitionBindingError, "PLACEHOLDER_FORBIDDEN"):
            store.put_object(
                self.db,
                kind="ZERO_IDENTITY",
                version="v2",
                subject_sha256="0" * 64,
                payload={"fixture": False},
                provenance_refs=["fixture:placeholder"],
            )

    def test_binding_is_single_activation_event(self):
        store.activate_binding(self.db, binding_id=self.binding["binding_id"], expected_generation=7)
        with self.assertRaisesRegex(store.CognitionBindingError, "BINDING_ALREADY_ACTIVATED"):
            store.activate_binding(self.db, binding_id=self.binding["binding_id"], expected_generation=8)

    def test_mutated_binding_bytes_fail_hash_check(self):
        store.activate_binding(self.db, binding_id=self.binding["binding_id"], expected_generation=7)
        self.db.execute(
            "UPDATE cognition_bindings SET binding_json=replace(binding_json,'fixture:exact-source','fixture:mutated')"
        )
        self.db.commit()
        with self.assertRaisesRegex(store.CognitionBindingError, "BINDING_HASH_MISMATCH"):
            store.read_active_binding(self.db, expected_generation=8)


if __name__ == "__main__":
    unittest.main()
