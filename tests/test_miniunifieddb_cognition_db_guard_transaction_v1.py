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

import miniunifieddb_cognition_db_guards_v1 as guards
import miniunifieddb_cognition_store_v1 as store


class CognitionDBGuardTransactionV1Tests(unittest.TestCase):
    def test_schema_and_guards_stay_inside_caller_begin_immediate(self) -> None:
        db = sqlite3.connect(":memory:")
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("CREATE TABLE entity_state(id INTEGER PRIMARY KEY, generation INTEGER NOT NULL)")
        db.execute("INSERT INTO entity_state(id,generation) VALUES(1,7)")
        db.commit()

        db.execute("BEGIN IMMEDIATE")
        self.assertTrue(db.in_transaction)
        store.install_schema(db)
        self.assertTrue(db.in_transaction)
        status = guards.install_guards(db)
        self.assertTrue(status["ok"])
        self.assertTrue(status["transaction_preserving_installer"])
        self.assertTrue(db.in_transaction)
        self.assertEqual(status["trigger_count"], 11)

        db.rollback()
        self.assertFalse(db.in_transaction)
        tables = {
            row[0]
            for row in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'mini_cognition_%'"
            )
        }
        triggers = {
            row[0]
            for row in db.execute(
                "SELECT name FROM sqlite_master WHERE type='trigger' AND name LIKE 'mini_cognition_%'"
            )
        }
        self.assertEqual(tables, set())
        self.assertEqual(triggers, set())
        db.close()


if __name__ == "__main__":
    unittest.main()
