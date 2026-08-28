#!/usr/bin/env python3
from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import mini_causal_turn_allocation_v1 as allocator


class CausalTurnRetryTransactionV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "mini.db"
        self.db = sqlite3.connect(self.db_path)
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute(
            "CREATE TABLE entity_state(id INTEGER PRIMARY KEY, generation INTEGER NOT NULL)"
        )
        self.db.execute("INSERT INTO entity_state(id,generation) VALUES(1,7)")
        # allocator.install_schema only requires the canonical turn-binding table to exist;
        # the mocked bind path below writes a deliberately small visibility marker into it.
        self.db.execute(
            """CREATE TABLE mini_cognition_turn_bindings(
                 entity_generation INTEGER NOT NULL,
                 causal_turn_id TEXT NOT NULL,
                 marker TEXT NOT NULL,
                 PRIMARY KEY(entity_generation,causal_turn_id))"""
        )
        allocator.install_schema(self.db)
        self.db.execute(
            """INSERT INTO mini_cognition_turn_allocations(
                 schema,entity_generation,causal_turn_id,allocated_at)
               VALUES(?,?,?,?)""",
            (allocator.SCHEMA, 7, "ct1:g7:a1", "2026-08-23T00:00:00Z"),
        )
        self.db.commit()

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    @staticmethod
    def _args(causal_turn_id: str) -> dict:
        return {
            "entity_generation": 7,
            "causal_turn_id": causal_turn_id,
            "boot_binding_digest": "ab" * 32,
            "task_text": "retry transaction visibility",
            "workspace_digest": "cd" * 32,
            "selected_workspace_slots": ["slot-a"],
            "contradiction_state": "UNRESOLVED",
            "provenance_refs": ["test:retry-transaction"],
            "required_zero_mode": "ACTIVE",
        }

    @staticmethod
    def _mock_bind(db: sqlite3.Connection, **kwargs) -> dict:
        db.execute(
            "INSERT INTO mini_cognition_turn_bindings VALUES(?,?,?)",
            (kwargs["entity_generation"], kwargs["causal_turn_id"], "BOUND"),
        )
        return {
            "ok": True,
            "idempotent": False,
            "binding_digest": "ef" * 32,
        }

    def test_standalone_retry_commits_before_success_is_returned(self) -> None:
        with patch.object(allocator.cognition_store, "bind_turn", side_effect=self._mock_bind):
            result = allocator.bind_existing_turn(self.db, **self._args("ct1:g7:a1"))
        self.assertTrue(result["ok"])
        self.assertFalse(self.db.in_transaction)

        observer = sqlite3.connect(self.db_path)
        try:
            row = observer.execute(
                "SELECT marker FROM mini_cognition_turn_bindings WHERE entity_generation=7 AND causal_turn_id=?",
                ("ct1:g7:a1",),
            ).fetchone()
            self.assertEqual(row, ("BOUND",))
        finally:
            observer.close()

    def test_caller_owned_retry_uses_savepoint_and_obeys_outer_rollback(self) -> None:
        self.db.execute(
            """INSERT INTO mini_cognition_turn_allocations(
                 schema,entity_generation,causal_turn_id,allocated_at)
               VALUES(?,?,?,?)""",
            (allocator.SCHEMA, 7, "ct1:g7:a2", "2026-08-23T00:00:01Z"),
        )
        self.db.commit()

        self.db.execute("BEGIN IMMEDIATE")
        with patch.object(allocator.cognition_store, "bind_turn", side_effect=self._mock_bind):
            result = allocator.bind_existing_turn(self.db, **self._args("ct1:g7:a2"))
        self.assertTrue(result["ok"])
        self.assertTrue(self.db.in_transaction)
        self.assertEqual(
            self.db.execute(
                "SELECT marker FROM mini_cognition_turn_bindings WHERE entity_generation=7 AND causal_turn_id=?",
                ("ct1:g7:a2",),
            ).fetchone(),
            ("BOUND",),
        )
        self.db.rollback()

        observer = sqlite3.connect(self.db_path)
        try:
            row = observer.execute(
                "SELECT marker FROM mini_cognition_turn_bindings WHERE entity_generation=7 AND causal_turn_id=?",
                ("ct1:g7:a2",),
            ).fetchone()
            self.assertIsNone(row)
        finally:
            observer.close()


if __name__ == "__main__":
    unittest.main()
