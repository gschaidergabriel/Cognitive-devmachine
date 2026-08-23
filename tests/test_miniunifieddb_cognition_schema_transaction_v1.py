#!/usr/bin/env python3
from __future__ import annotations
import sqlite3
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1] if '__file__' in globals() else Path('/tmp')
if str(ROOT / 'tools') not in sys.path:
    sys.path.insert(0, str(ROOT / 'tools'))
if '/tmp' not in sys.path:
    sys.path.insert(0, '/tmp')
import miniunifieddb_cognition_store_v1 as store

class CognitionSchemaTransactionTests(unittest.TestCase):
    def test_install_schema_preserves_caller_owned_transaction(self):
        db = sqlite3.connect(':memory:')
        db.execute('CREATE TABLE entity_state(id INTEGER PRIMARY KEY, generation INTEGER NOT NULL)')
        db.execute('INSERT INTO entity_state(id,generation) VALUES(1,3)')
        db.commit()
        db.execute('BEGIN IMMEDIATE')
        db.execute('UPDATE entity_state SET generation=4 WHERE id=1')
        self.assertTrue(db.in_transaction)
        store.install_schema(db)
        self.assertTrue(db.in_transaction)
        db.rollback()
        self.assertEqual(db.execute('SELECT generation FROM entity_state WHERE id=1').fetchone()[0], 3)

if __name__ == '__main__':
    unittest.main()
