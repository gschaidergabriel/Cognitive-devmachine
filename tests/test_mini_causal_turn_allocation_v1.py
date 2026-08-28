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

import mini_causal_turn_allocation_v1 as allocator
import miniunifieddb_cognition_store_v1 as store


class CausalTurnAllocationV1Tests(unittest.TestCase):
    @staticmethod
    def digest(label: str) -> str:
        return hashlib.sha256(label.encode("utf-8")).hexdigest()

    def setUp(self) -> None:
        self.db = sqlite3.connect(":memory:")
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("CREATE TABLE entity_state(id INTEGER PRIMARY KEY, generation INTEGER NOT NULL)")
        self.db.execute("INSERT INTO entity_state(id,generation) VALUES(1,7)")
        self.db.commit()
        store.install_schema(self.db)
        allocator.install_schema(self.db)
        self.db.commit()

        boot_values: dict[str, str] = {}
        for field_name, object_kind in store.BOOT_FIELD_KINDS.items():
            digest = self.digest(field_name)
            boot_values[field_name] = digest
            store.register_object(
                self.db,
                object_kind=object_kind,
                object_version="v1",
                object_digest=digest,
                digest_basis="EXTERNAL_BYTES",
                payload={"fixture": field_name},
                provenance_refs=["test:" + field_name],
            )
            store.admit_object(
                self.db,
                object_kind=object_kind,
                object_version="v1",
                object_digest=digest,
                entity_generation=7,
                admission_receipt_digest=self.digest("receipt:" + field_name),
            )
        self.boot = store.admit_boot_binding(
            self.db,
            entity_generation=7,
            provenance_refs=["test:boot"],
            **boot_values,
        )
        self.db.commit()

    def tearDown(self) -> None:
        self.db.close()

    def args(self) -> dict:
        return {
            "entity_generation": 7,
            "boot_binding_digest": self.boot["binding_digest"],
            "task_text": "byte-identical task",
            "workspace_digest": self.digest("workspace"),
            "selected_workspace_slots": ["slot-a", "slot-b"],
            "contradiction_state": "UNRESOLVED",
            "provenance_refs": ["source:a", "source:b"],
            "required_zero_mode": "ACTIVE",
        }

    def test_two_identical_turns_get_distinct_event_ids(self) -> None:
        first = allocator.allocate_and_bind_turn(self.db, **self.args())
        second = allocator.allocate_and_bind_turn(self.db, **self.args())
        self.assertNotEqual(first["causal_turn_id"], second["causal_turn_id"])
        self.assertTrue(first["causal_turn_id"].startswith("ct1:g7:a"))
        allocation_count = self.db.execute(
            "SELECT COUNT(*) FROM mini_cognition_turn_allocations"
        ).fetchone()[0]
        binding_count = self.db.execute(
            "SELECT COUNT(*) FROM mini_cognition_turn_bindings"
        ).fetchone()[0]
        self.assertEqual(allocation_count, 2)
        self.assertEqual(binding_count, 2)

    def test_explicit_retry_reuses_existing_id_without_new_allocation(self) -> None:
        first = allocator.allocate_and_bind_turn(self.db, **self.args())
        retry = allocator.bind_existing_turn(
            self.db, causal_turn_id=first["causal_turn_id"], **self.args()
        )
        self.assertEqual(first["causal_turn_id"], retry["causal_turn_id"])
        self.assertFalse(retry["new_causal_event"])
        self.assertTrue(retry["idempotent"])
        self.assertEqual(
            self.db.execute("SELECT COUNT(*) FROM mini_cognition_turn_allocations").fetchone()[0],
            1,
        )
        self.assertEqual(
            self.db.execute("SELECT COUNT(*) FROM mini_cognition_turn_bindings").fetchone()[0],
            1,
        )

    def test_retry_cannot_launder_changed_material_through_old_id(self) -> None:
        first = allocator.allocate_and_bind_turn(self.db, **self.args())
        changed = self.args()
        changed["task_text"] = "changed task"
        with self.assertRaisesRegex(store.CognitionStoreError, "TURN_BINDING_CONFLICT"):
            allocator.bind_existing_turn(
                self.db, causal_turn_id=first["causal_turn_id"], **changed
            )

    def test_failed_binding_rolls_back_allocation(self) -> None:
        poisoned = self.args()
        poisoned["workspace_digest"] = "0" * 64
        with self.assertRaises(store.CognitionStoreError):
            allocator.allocate_and_bind_turn(self.db, **poisoned)
        self.assertEqual(
            self.db.execute("SELECT COUNT(*) FROM mini_cognition_turn_allocations").fetchone()[0],
            0,
        )
        self.assertEqual(
            self.db.execute("SELECT COUNT(*) FROM mini_cognition_turn_bindings").fetchone()[0],
            0,
        )

    def test_stale_generation_cannot_allocate(self) -> None:
        self.db.execute("UPDATE entity_state SET generation=8 WHERE id=1")
        self.db.commit()
        with self.assertRaisesRegex(allocator.CausalTurnAllocationError, "STALE_GENERATION"):
            allocator.allocate_and_bind_turn(self.db, **self.args())
        self.assertEqual(
            self.db.execute("SELECT COUNT(*) FROM mini_cognition_turn_allocations").fetchone()[0],
            0,
        )

    def test_caller_transaction_rollback_removes_allocation_and_binding(self) -> None:
        self.db.execute("BEGIN IMMEDIATE")
        result = allocator.allocate_and_bind_turn(self.db, **self.args())
        self.assertTrue(result["new_causal_event"])
        self.assertEqual(
            self.db.execute("SELECT COUNT(*) FROM mini_cognition_turn_allocations").fetchone()[0],
            1,
        )
        self.db.rollback()
        self.assertEqual(
            self.db.execute("SELECT COUNT(*) FROM mini_cognition_turn_allocations").fetchone()[0],
            0,
        )
        self.assertEqual(
            self.db.execute("SELECT COUNT(*) FROM mini_cognition_turn_bindings").fetchone()[0],
            0,
        )


if __name__ == "__main__":
    unittest.main()
