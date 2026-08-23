import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import miniunifieddb_cognition_store_v1 as store


class CognitionSchemaTransactionTests(unittest.TestCase):
    def test_install_schema_preserves_caller_owned_bootstrap_transaction(self):
        db = sqlite3.connect(":memory:")
        db.execute("BEGIN IMMEDIATE")
        db.execute(
            """CREATE TABLE entity_state(
                 id INTEGER PRIMARY KEY CHECK(id=1),
                 generation INTEGER NOT NULL,
                 active_profile TEXT)"""
        )
        db.execute("INSERT INTO entity_state(id,generation,active_profile) VALUES(1,0,NULL)")
        self.assertTrue(db.in_transaction)

        store.install_schema(db)

        self.assertTrue(db.in_transaction)
        names = {
            row[0]
            for row in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'mini_cognition_%'"
            )
        }
        self.assertEqual(
            {
                "mini_cognition_objects",
                "mini_cognition_object_admissions",
                "mini_cognition_boot_bindings",
                "mini_cognition_turn_bindings",
            },
            names,
        )

        db.rollback()
        self.assertIsNone(
            db.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='entity_state'"
            ).fetchone()
        )
        self.assertEqual(
            [],
            db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'mini_cognition_%'"
            ).fetchall(),
        )


if __name__ == "__main__":
    unittest.main()
