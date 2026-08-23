#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import miniunifieddb_active_turn_v1 as active


def sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class FakeStore:
    wrong_binding = False

    @classmethod
    def resolve_prepare_binding(
        cls, db, *, entity_generation: int, causal_turn_id: str, task_text: str
    ):
        row = db.execute(
            """SELECT binding_digest,task_sha256
                 FROM mini_cognition_turn_bindings
                WHERE entity_generation=? AND causal_turn_id=?""",
            (entity_generation, causal_turn_id),
        ).fetchone()
        binding = "wrong-binding" if cls.wrong_binding else row[0]
        return {
            "ok": True,
            "entity_generation": entity_generation,
            "causal_turn_id": causal_turn_id,
            "turn_binding_digest": binding,
            "task_sha256": row[1],
            "workspace_digest": sha("workspace"),
            "selected_workspace_slots": ["slot-a"],
            "required_zero_mode": "ACTIVE",
            "zero_identity_digest": sha("zero"),
            "grf_digest": sha("grf"),
        }


class ActiveTurnTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.execute(
            "CREATE TABLE entity_state(id INTEGER PRIMARY KEY,generation INTEGER NOT NULL)"
        )
        self.db.execute("INSERT INTO entity_state VALUES(1,3)")
        self.db.execute(
            """CREATE TABLE mini_cognition_turn_bindings(
                 entity_generation INTEGER NOT NULL,
                 causal_turn_id TEXT NOT NULL,
                 binding_digest TEXT NOT NULL,
                 task_sha256 TEXT NOT NULL,
                 PRIMARY KEY(entity_generation,causal_turn_id))"""
        )
        self.task = "produce one evidence-bound candidate"
        self.task_sha = sha(self.task)
        self.binding = sha("turn-binding")
        self.db.execute(
            "INSERT INTO mini_cognition_turn_bindings VALUES(?,?,?,?)",
            (3, "turn-3-a", self.binding, self.task_sha),
        )
        active.install_schema(self.db)

    def activate(self):
        return active.activate_bound_turn(
            self.db,
            entity_generation=3,
            causal_turn_id="turn-3-a",
            task_text=self.task,
            expected_turn_binding_digest=self.binding,
            provenance_refs=["test:bound-turn"],
        )

    def test_schema_refuses_database_without_existing_turn_store(self):
        db = sqlite3.connect(":memory:")
        db.execute(
            "CREATE TABLE entity_state(id INTEGER PRIMARY KEY,generation INTEGER NOT NULL)"
        )
        db.execute("INSERT INTO entity_state VALUES(1,0)")
        with self.assertRaisesRegex(
            active.ActiveTurnError, "COGNITION_TURN_BINDING_STORE_REQUIRED"
        ):
            active.install_schema(db)

    def test_exact_activation_and_prepare_resolution(self):
        activated = self.activate()
        resolved = active.resolve_active_prepare(
            self.db,
            entity_generation=3,
            expected_activation_digest=activated["activation_digest"],
            store_module=FakeStore,
        )
        self.assertEqual(resolved["causal_turn_id"], "turn-3-a")
        self.assertEqual(resolved["task_text"], self.task)
        self.assertEqual(resolved["turn_binding_digest"], self.binding)
        self.assertEqual(resolved["activation_digest"], activated["activation_digest"])

    def test_prepare_resolution_works_under_query_only(self):
        activated = self.activate()
        self.db.execute("PRAGMA query_only=ON")
        resolved = active.resolve_active_prepare(
            self.db,
            entity_generation=3,
            expected_activation_digest=activated["activation_digest"],
            store_module=FakeStore,
        )
        self.assertEqual(resolved["causal_turn_id"], "turn-3-a")
        self.assertEqual(resolved["task_text"], self.task)

    def test_prepare_resolution_does_not_install_missing_schema(self):
        db = sqlite3.connect(":memory:")
        db.execute(
            "CREATE TABLE entity_state(id INTEGER PRIMARY KEY,generation INTEGER NOT NULL)"
        )
        db.execute("INSERT INTO entity_state VALUES(1,3)")
        db.execute(
            """CREATE TABLE mini_cognition_turn_bindings(
                 entity_generation INTEGER NOT NULL,
                 causal_turn_id TEXT NOT NULL,
                 binding_digest TEXT NOT NULL,
                 task_sha256 TEXT NOT NULL,
                 PRIMARY KEY(entity_generation,causal_turn_id))"""
        )
        with self.assertRaisesRegex(active.ActiveTurnError, "ACTIVE_TURN_SCHEMA_REQUIRED"):
            active.resolve_active_prepare(db, entity_generation=3, store_module=FakeStore)
        created = db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='mini_cognition_active_turns'"
        ).fetchone()
        self.assertIsNone(created)

    def test_task_text_must_match_preexisting_bound_hash(self):
        with self.assertRaisesRegex(active.ActiveTurnError, "TURN_TASK_BINDING_MISMATCH"):
            active.activate_bound_turn(
                self.db,
                entity_generation=3,
                causal_turn_id="turn-3-a",
                task_text="different task",
                expected_turn_binding_digest=self.binding,
                provenance_refs=["test:mismatch"],
            )

    def test_stale_generation_cannot_activate(self):
        with self.assertRaisesRegex(active.ActiveTurnError, "STALE_GENERATION"):
            active.activate_bound_turn(
                self.db,
                entity_generation=2,
                causal_turn_id="turn-3-a",
                task_text=self.task,
                expected_turn_binding_digest=self.binding,
                provenance_refs=["test:stale"],
            )

    def test_second_active_turn_in_same_generation_conflicts(self):
        self.activate()
        task2 = "other task"
        binding2 = sha("turn-binding-2")
        self.db.execute(
            "INSERT INTO mini_cognition_turn_bindings VALUES(?,?,?,?)",
            (3, "turn-3-b", binding2, sha(task2)),
        )
        with self.assertRaisesRegex(
            active.ActiveTurnError, "ACTIVE_TURN_GENERATION_CONFLICT"
        ):
            active.activate_bound_turn(
                self.db,
                entity_generation=3,
                causal_turn_id="turn-3-b",
                task_text=task2,
                expected_turn_binding_digest=binding2,
                provenance_refs=["test:other"],
            )

    def test_post_activation_task_text_tamper_fails(self):
        self.activate()
        self.db.execute(
            "UPDATE mini_cognition_active_turns SET task_text='poison' WHERE entity_generation=3"
        )
        with self.assertRaisesRegex(
            active.ActiveTurnError, "ACTIVE_TASK_TEXT_HASH_MISMATCH"
        ):
            active.resolve_active_prepare(
                self.db, entity_generation=3, store_module=FakeStore
            )

    def test_store_resolver_must_return_same_binding(self):
        self.activate()
        FakeStore.wrong_binding = True
        try:
            with self.assertRaisesRegex(
                active.ActiveTurnError, "PREPARE_TURN_BINDING_MISMATCH"
            ):
                active.resolve_active_prepare(
                    self.db, entity_generation=3, store_module=FakeStore
                )
        finally:
            FakeStore.wrong_binding = False


if __name__ == "__main__":
    unittest.main()
