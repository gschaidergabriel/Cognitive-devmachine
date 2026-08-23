import sqlite3
import unittest

from cognition_store_v1 import (
    CognitionStoreError,
    bind_role,
    install_schema,
    load_snapshot,
    put_object,
)


class CognitionStoreV1Tests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.execute(
            "CREATE TABLE entity_state(singleton INTEGER PRIMARY KEY, generation INTEGER NOT NULL)"
        )
        self.db.execute("INSERT INTO entity_state(singleton,generation) VALUES(1,7)")
        install_schema(self.db)

    def add_zero_and_grf(self):
        put_object(
            self.db,
            object_kind="runtime_identity",
            object_id="zero",
            version=1,
            body={"name": "Zero", "authority": "runtime_config_only"},
            provenance={"source": "owner-bound"},
        )
        put_object(
            self.db,
            object_kind="method_framework",
            object_id="grf",
            version=3,
            body={"framework": "GRF", "truth_authority": False},
            provenance={"source": "repo"},
        )
        for role, kind, oid, version in (
            ("zero_identity", "runtime_identity", "zero", 1),
            ("grf", "method_framework", "grf", 3),
        ):
            bind_role(
                self.db,
                role=role,
                generation=7,
                object_kind=kind,
                object_id=oid,
                object_version=version,
                causal_id="turn-9",
                source_lock_digest="lock-a",
            )

    def test_requires_existing_entity_state_authority(self):
        db = sqlite3.connect(":memory:")
        with self.assertRaisesRegex(CognitionStoreError, "ENTITY_STATE_REQUIRED"):
            install_schema(db)

    def test_versioned_objects_and_bindings_load_as_one_snapshot(self):
        self.add_zero_and_grf()
        snap = load_snapshot(
            self.db,
            generation=7,
            required_roles=["zero_identity", "grf"],
            causal_id="turn-9",
        )
        self.assertEqual(set(snap["roles"]), {"zero_identity", "grf"})
        self.assertEqual(snap["roles"]["zero_identity"]["body"]["name"], "Zero")
        self.assertEqual(len(snap["snapshot_digest"]), 64)

    def test_same_object_insert_is_idempotent_but_conflict_fails(self):
        kwargs = dict(
            object_kind="runtime_identity",
            object_id="zero",
            version=1,
            body={"name": "Zero"},
            provenance={"source": "owner"},
        )
        first = put_object(self.db, **kwargs)
        self.assertEqual(first, put_object(self.db, **kwargs))
        kwargs["body"] = {"name": "NotZero"}
        with self.assertRaisesRegex(CognitionStoreError, "IMMUTABLE_OBJECT_CONFLICT"):
            put_object(self.db, **kwargs)

    def test_binding_same_generation_cannot_be_repointed(self):
        self.add_zero_and_grf()
        put_object(
            self.db,
            object_kind="runtime_identity",
            object_id="zero-alt",
            version=1,
            body={"name": "Zero alt"},
            provenance={"source": "test"},
        )
        with self.assertRaisesRegex(CognitionStoreError, "IMMUTABLE_BINDING_CONFLICT"):
            bind_role(
                self.db,
                role="zero_identity",
                generation=7,
                object_kind="runtime_identity",
                object_id="zero-alt",
                object_version=1,
                causal_id="turn-9",
                source_lock_digest="lock-a",
            )

    def test_missing_required_role_fails_closed(self):
        put_object(
            self.db,
            object_kind="runtime_identity",
            object_id="zero",
            version=1,
            body={"name": "Zero"},
            provenance={"source": "owner"},
        )
        bind_role(
            self.db,
            role="zero_identity",
            generation=7,
            object_kind="runtime_identity",
            object_id="zero",
            object_version=1,
            causal_id="turn-9",
            source_lock_digest="lock-a",
        )
        with self.assertRaisesRegex(CognitionStoreError, "MISSING_ROLE:grf"):
            load_snapshot(
                self.db,
                generation=7,
                required_roles=["zero_identity", "grf"],
                causal_id="turn-9",
            )

    def test_causal_id_mismatch_fails_closed(self):
        self.add_zero_and_grf()
        with self.assertRaisesRegex(CognitionStoreError, "CAUSAL_ID_MISMATCH"):
            load_snapshot(
                self.db,
                generation=7,
                required_roles=["zero_identity", "grf"],
                causal_id="turn-other",
            )

    def test_body_digest_tamper_fails_closed(self):
        self.add_zero_and_grf()
        self.db.execute(
            "UPDATE mini_cognition_objects SET body_json='{}' "
            "WHERE object_kind='runtime_identity' AND object_id='zero' AND version=1"
        )
        with self.assertRaisesRegex(CognitionStoreError, "OBJECT_DIGEST_MISMATCH"):
            load_snapshot(
                self.db,
                generation=7,
                required_roles=["zero_identity", "grf"],
                causal_id="turn-9",
            )

    def test_provenance_tamper_fails_closed(self):
        self.add_zero_and_grf()
        self.db.execute(
            "UPDATE mini_cognition_objects SET provenance_json='{\"source\":\"forged\"}' "
            "WHERE object_kind='runtime_identity' AND object_id='zero' AND version=1"
        )
        with self.assertRaisesRegex(CognitionStoreError, "OBJECT_DIGEST_MISMATCH"):
            load_snapshot(
                self.db,
                generation=7,
                required_roles=["zero_identity", "grf"],
                causal_id="turn-9",
            )

    def test_unusual_stale_generation_poison_is_rejected(self):
        # Unusual experiment: simulate restart/generation advance after a valid binding.
        # The old Zero/GRF snapshot must not remain loadable under the new live generation.
        self.add_zero_and_grf()
        self.db.execute("UPDATE entity_state SET generation=8 WHERE singleton=1")
        with self.assertRaisesRegex(CognitionStoreError, "STALE_GENERATION"):
            load_snapshot(
                self.db,
                generation=7,
                required_roles=["zero_identity", "grf"],
                causal_id="turn-9",
            )


if __name__ == "__main__":
    unittest.main()
