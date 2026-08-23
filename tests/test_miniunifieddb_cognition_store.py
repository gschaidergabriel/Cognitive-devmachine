import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import miniunifieddb_cognition_store as store


def db():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE entity_state(id INTEGER PRIMARY KEY, generation INTEGER NOT NULL)")
    conn.execute("INSERT INTO entity_state(id,generation) VALUES(1,0)")
    store.init_schema(conn)
    conn.commit()
    return conn


class CognitionStoreTests(unittest.TestCase):

    def test_schema_init_joins_existing_runtime_bootstrap_transaction_without_committing_it(self):
        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE TABLE entity_state(id INTEGER PRIMARY KEY, generation INTEGER NOT NULL)")
        conn.execute("INSERT INTO entity_state(id,generation) VALUES(1,0)")
        self.assertTrue(conn.in_transaction)
        store.init_schema(conn)
        self.assertTrue(conn.in_transaction)
        names = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'cognition_%'"
        )}
        self.assertEqual(
            {"cognition_objects", "cognition_bindings", "cognition_binding_snapshots"},
            names,
        )
        conn.rollback()
        self.assertIsNotNone(conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='entity_state'"
        ).fetchone())
        self.assertIsNone(conn.execute("SELECT 1 FROM entity_state WHERE id=1").fetchone())
        self.assertEqual([], conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'cognition_%'"
        ).fetchall())

    def test_content_addressed_object_is_idempotent_and_secret_values_fail(self):
        conn = db()
        a = store.put_object(
            conn,
            object_kind="ZERO_IDENTITY",
            object_version="1",
            payload={"identity_id": "ZERO", "mode": "runtime_configuration"},
            provenance={"source": "owner-directive", "sha256": "abc"},
        )
        b = store.put_object(
            conn,
            object_kind="ZERO_IDENTITY",
            object_version="1",
            payload={"identity_id": "ZERO", "mode": "runtime_configuration"},
            provenance={"source": "owner-directive", "sha256": "abc"},
        )
        self.assertEqual(a["object_digest"], b["object_digest"])
        self.assertEqual(1, conn.execute("SELECT COUNT(*) FROM cognition_objects").fetchone()[0])
        with self.assertRaisesRegex(store.CognitionStoreError, "CONTAINS_SECRET_VALUE"):
            store.put_object(
                conn,
                object_kind="GRF",
                object_version="1",
                payload={"api_key": "must-not-persist"},
                provenance={"source": "test"},
            )

    def test_role_kind_and_missing_binding_fail_closed(self):
        conn = db()
        zero = store.put_object(
            conn,
            object_kind="ZERO_IDENTITY",
            object_version="1",
            payload={"identity_id": "ZERO"},
            provenance={"source": "test"},
        )
        with self.assertRaisesRegex(store.CognitionStoreError, "ROLE_OBJECT_KIND_MISMATCH"):
            store.activate_binding(
                conn, role="GRF", object_digest=zero["object_digest"], expected_generation=0
            )
        with self.assertRaisesRegex(store.CognitionStoreError, "REQUIRED_BINDING_MISSING:ZERO_IDENTITY"):
            store.read_snapshot(conn, expected_generation=0, required_roles=["ZERO_IDENTITY"])

    def test_binding_activation_bumps_single_entity_generation_and_snapshot_binds_roles(self):
        conn = db()
        zero = store.put_object(
            conn,
            object_kind="ZERO_IDENTITY",
            object_version="1",
            payload={"identity_id": "ZERO"},
            provenance={"source": "test"},
        )
        grf = store.put_object(
            conn,
            object_kind="GRF",
            object_version="1",
            payload={"framework_id": "GENERATIVE_REALITY_FRAMEWORK"},
            provenance={"source": "test"},
        )
        z = store.activate_binding(
            conn, role="ZERO_IDENTITY", object_digest=zero["object_digest"], expected_generation=0
        )
        self.assertEqual(1, z["generation"])
        g = store.activate_binding(
            conn, role="GRF", object_digest=grf["object_digest"], expected_generation=1
        )
        self.assertEqual(2, g["generation"])
        snap = store.read_snapshot(
            conn, expected_generation=2, required_roles=["ZERO_IDENTITY", "GRF"]
        )
        self.assertEqual(zero["object_digest"], snap["objects"]["ZERO_IDENTITY"]["object_digest"])
        self.assertEqual(grf["object_digest"], snap["objects"]["GRF"]["object_digest"])
        self.assertEqual(2, snap["generation"])

    def test_rehashed_stale_generation_binding_regression_fails_closed(self):
        # Ordinary regression: create a fully valid, freshly content-addressed GRF object
        # but deliberately attempt to bind it using a stale generation after another
        # binding advanced CAS. The macrocycle unusual-experiment slot is already consumed.
        conn = db()
        zero = store.put_object(
            conn,
            object_kind="ZERO_IDENTITY",
            object_version="1",
            payload={"identity_id": "ZERO"},
            provenance={"source": "poison-control"},
        )
        grf = store.put_object(
            conn,
            object_kind="GRF",
            object_version="2",
            payload={"framework_id": "GENERATIVE_REALITY_FRAMEWORK", "nonce": "fresh-valid-bytes"},
            provenance={"source": "poison-control"},
        )
        store.activate_binding(
            conn, role="ZERO_IDENTITY", object_digest=zero["object_digest"], expected_generation=0
        )
        with self.assertRaisesRegex(store.CognitionStoreError, "STALE_GENERATION"):
            store.activate_binding(
                conn, role="GRF", object_digest=grf["object_digest"], expected_generation=0
            )
        self.assertEqual(1, conn.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()[0])
        self.assertIsNone(conn.execute("SELECT 1 FROM cognition_bindings WHERE role='GRF'").fetchone())

    def test_tampered_bound_object_is_rejected_even_when_binding_row_survives(self):
        conn = db()
        zero = store.put_object(
            conn,
            object_kind="ZERO_IDENTITY",
            object_version="1",
            payload={"identity_id": "ZERO"},
            provenance={"source": "test"},
        )
        store.activate_binding(
            conn, role="ZERO_IDENTITY", object_digest=zero["object_digest"], expected_generation=0
        )
        conn.execute(
            "UPDATE cognition_objects SET envelope_json='{}' WHERE object_digest=?",
            (zero["object_digest"],),
        )
        with self.assertRaisesRegex(store.CognitionStoreError, "BOUND_OBJECT_DIGEST_MISMATCH"):
            store.read_snapshot(conn, expected_generation=1, required_roles=["ZERO_IDENTITY"])


if __name__ == "__main__":
    unittest.main()
