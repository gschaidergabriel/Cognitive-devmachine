#!/usr/bin/env python3
from __future__ import annotations

import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import miniunifieddb_cognition_store_v1 as store


class CognitionSchemaTransactionTests(unittest.TestCase):
    def test_schema_install_preserves_caller_bootstrap_transaction(self):
        db = sqlite3.connect(":memory:")
        db.execute("PRAGMA foreign_keys=ON")
        self.assertEqual(1, db.execute("PRAGMA foreign_keys").fetchone()[0])
        db.execute("BEGIN IMMEDIATE")
        db.execute(
            "CREATE TABLE entity_state(id INTEGER PRIMARY KEY, generation INTEGER NOT NULL)"
        )
        db.execute("INSERT INTO entity_state(id,generation) VALUES(1,0)")
        self.assertTrue(db.in_transaction)

        store.install_schema(db)

        self.assertTrue(db.in_transaction)
        tables = {
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
            tables,
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

    def test_missing_pretransaction_fk_enforcement_fails_without_commit(self):
        db = sqlite3.connect(":memory:")
        db.execute("BEGIN IMMEDIATE")
        db.execute(
            "CREATE TABLE entity_state(id INTEGER PRIMARY KEY, generation INTEGER NOT NULL)"
        )
        db.execute("INSERT INTO entity_state(id,generation) VALUES(1,0)")
        self.assertEqual(0, db.execute("PRAGMA foreign_keys").fetchone()[0])
        self.assertTrue(db.in_transaction)

        with self.assertRaisesRegex(
            store.CognitionStoreError, "FOREIGN_KEYS_REQUIRED_BEFORE_TRANSACTION"
        ):
            store.install_schema(db)

        self.assertTrue(db.in_transaction)
        db.rollback()
        self.assertIsNone(
            db.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='entity_state'"
            ).fetchone()
        )


if __name__ == "__main__":
    unittest.main()
