#!/usr/bin/env python3
from __future__ import annotations

import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import miniunifieddb_causal_turn_allocator_v1 as alloc


class CausalTurnAllocatorV1Tests(unittest.TestCase):
    def make_db(self, generation: int = 7) -> sqlite3.Connection:
        db = sqlite3.connect(":memory:")
        db.execute("CREATE TABLE entity_state(id INTEGER PRIMARY KEY,generation INTEGER NOT NULL)")
        db.execute("INSERT INTO entity_state VALUES(1,?)", (generation,))
        alloc.install_schema(db)
        return db

    def test_install_requires_existing_entity_state(self):
        db = sqlite3.connect(":memory:")
        with self.assertRaisesRegex(alloc.CausalTurnAllocationError, "ENTITY_STATE_UNAVAILABLE"):
            alloc.install_schema(db)

    def test_identical_context_allocates_distinct_causal_events(self):
        db = self.make_db()
        first = alloc.allocate_causal_turn(db, entity_generation=7, provenance_refs=["input:event"])
        second = alloc.allocate_causal_turn(db, entity_generation=7, provenance_refs=["input:event"])
        self.assertNotEqual(first["causal_turn_id"], second["causal_turn_id"])
        self.assertNotEqual(first["allocation_digest"], second["allocation_digest"])

    def test_resolve_is_generation_fenced(self):
        db = self.make_db()
        created = alloc.allocate_causal_turn(db, entity_generation=7, provenance_refs=["input:event"])
        resolved = alloc.resolve_allocation(db, causal_turn_id=created["causal_turn_id"], entity_generation=7)
        self.assertEqual(resolved["allocation_digest"], created["allocation_digest"])
        db.execute("UPDATE entity_state SET generation=8 WHERE id=1")
        with self.assertRaisesRegex(alloc.CausalTurnAllocationError, "STALE_GENERATION"):
            alloc.resolve_allocation(db, causal_turn_id=created["causal_turn_id"], entity_generation=7)

    def test_invalid_or_unknown_id_fails_closed(self):
        db = self.make_db()
        with self.assertRaisesRegex(alloc.CausalTurnAllocationError, "CAUSAL_TURN_ID_INVALID"):
            alloc.resolve_allocation(db, causal_turn_id="ct1:0", entity_generation=7)
        with self.assertRaisesRegex(alloc.CausalTurnAllocationError, "CAUSAL_TURN_ALLOCATION_UNAVAILABLE"):
            alloc.resolve_allocation(db, causal_turn_id="ct1:999", entity_generation=7)

    def test_allocation_rows_are_immutable(self):
        db = self.make_db()
        created = alloc.allocate_causal_turn(db, entity_generation=7, provenance_refs=["input:event"])
        with self.assertRaisesRegex(sqlite3.IntegrityError, "CAUSAL_TURN_ALLOCATION_IMMUTABLE"):
            db.execute("UPDATE mini_cognition_turn_allocations SET entity_generation=6 WHERE allocation_id=?",
                       (created["allocation_id"],))
        with self.assertRaisesRegex(sqlite3.IntegrityError, "CAUSAL_TURN_ALLOCATION_IMMUTABLE"):
            db.execute("DELETE FROM mini_cognition_turn_allocations WHERE allocation_id=?",
                       (created["allocation_id"],))

    def test_caller_owned_transaction_can_rollback_allocation(self):
        db = self.make_db()
        db.commit()
        db.execute("BEGIN IMMEDIATE")
        created = alloc.allocate_causal_turn(db, entity_generation=7, provenance_refs=["input:event"])
        db.rollback()
        count = db.execute("SELECT COUNT(*) FROM mini_cognition_turn_allocations").fetchone()[0]
        self.assertEqual(count, 0)
        with self.assertRaisesRegex(alloc.CausalTurnAllocationError, "CAUSAL_TURN_ALLOCATION_UNAVAILABLE"):
            alloc.resolve_allocation(db, causal_turn_id=created["causal_turn_id"], entity_generation=7)


if __name__ == "__main__":
    unittest.main()
