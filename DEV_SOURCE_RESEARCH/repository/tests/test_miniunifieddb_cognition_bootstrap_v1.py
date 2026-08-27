#!/usr/bin/env python3
from __future__ import annotations

import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import miniunifieddb_cognition_bootstrap_v1 as bootstrap


class CognitionBootstrapTests(unittest.TestCase):
    @staticmethod
    def base_db(*, prepared: bool = True) -> sqlite3.Connection:
        db = sqlite3.connect(":memory:")
        if prepared:
            bootstrap.prepare_connection(db)
        db.execute(
            "CREATE TABLE entity_state(id INTEGER PRIMARY KEY, generation INTEGER NOT NULL)"
        )
        db.execute("INSERT INTO entity_state(id,generation) VALUES(1,7)")
        db.commit()
        return db

    def test_installs_real_cognition_schemas_inside_caller_transaction(self):
        db = self.base_db()
        db.execute("BEGIN IMMEDIATE")
        result = bootstrap.install_cognition_schema(db)
        self.assertTrue(result["ok"])
        self.assertTrue(db.in_transaction)
        self.assertEqual(result["entity_generation"], 7)
        self.assertEqual(result["authority"]["durable_state"], "MiniUnifiedDB")
        for table in result["installed_tables"]:
            self.assertIsNotNone(
                db.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
                ).fetchone()
            )
        db.rollback()
        for table in result["installed_tables"]:
            self.assertIsNone(
                db.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
                ).fetchone()
            )

    def test_commit_persists_one_same_db_schema_set(self):
        db = self.base_db()
        db.execute("BEGIN IMMEDIATE")
        result = bootstrap.install_cognition_schema(db)
        db.commit()
        self.assertFalse(db.in_transaction)
        names = {
            row[0]
            for row in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'mini_cognition_%'"
            ).fetchall()
        }
        self.assertTrue(set(result["installed_tables"]).issubset(names))

    def test_missing_foreign_keys_fails_closed(self):
        db = self.base_db(prepared=False)
        db.execute("BEGIN IMMEDIATE")
        with self.assertRaisesRegex(bootstrap.CognitionBootstrapError, "FOREIGN_KEYS_REQUIRED"):
            bootstrap.install_cognition_schema(db)
        self.assertTrue(db.in_transaction)
        db.rollback()

    def test_foreign_keys_must_be_enabled_before_transaction(self):
        db = sqlite3.connect(":memory:")
        db.execute("BEGIN IMMEDIATE")
        with self.assertRaisesRegex(
            bootstrap.CognitionBootstrapError,
            "FOREIGN_KEY_BOOTSTRAP_MUST_PRECEDE_TRANSACTION",
        ):
            bootstrap.prepare_connection(db)
        db.rollback()

    def test_install_requires_caller_owned_transaction(self):
        db = self.base_db()
        self.assertFalse(db.in_transaction)
        with self.assertRaisesRegex(
            bootstrap.CognitionBootstrapError,
            "CALLER_BOOTSTRAP_TRANSACTION_REQUIRED",
        ):
            bootstrap.install_cognition_schema(db)


if __name__ == "__main__":
    unittest.main()
