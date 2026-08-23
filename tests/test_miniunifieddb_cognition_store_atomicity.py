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

import miniunifieddb_cognition_store_v1 as store


class CognitionStoreAtomicityTests(unittest.TestCase):
    def test_install_schema_preserves_caller_transaction_and_rollback(self):
        db = sqlite3.connect(":memory:")
        db.execute(
            "CREATE TABLE entity_state(id INTEGER PRIMARY KEY, generation INTEGER NOT NULL)"
        )
        db.execute("INSERT INTO entity_state(id,generation) VALUES(1,3)")
        db.commit()

        db.execute("BEGIN IMMEDIATE")
        store.install_schema(db)
        self.assertTrue(db.in_transaction)
        db.rollback()

        names = {
            row[0]
            for row in db.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name LIKE 'mini_cognition_%'"
            )
        }
        self.assertEqual(names, set())


if __name__ == "__main__":
    unittest.main()
