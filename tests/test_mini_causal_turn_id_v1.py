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

import mini_causal_turn_id_v1 as causal
import miniunifieddb_cognition_store_v1 as store


class CausalTurnIdV1Tests(unittest.TestCase):
    @staticmethod
    def digest(label: str) -> str:
        return hashlib.sha256(label.encode("utf-8")).hexdigest()

    def args(self) -> dict:
        return {
            "entity_generation": 7,
            "boot_binding_digest": self.digest("boot"),
            "task_text": "exact pipeline task",
            "workspace_digest": self.digest("workspace"),
            "selected_workspace_slots": ["slot-a", "slot-b"],
            "contradiction_state": "UNRESOLVED",
            "provenance_refs": ["source:a", "source:b"],
            "required_zero_mode": "ACTIVE",
        }

    def make_bound_db(self) -> tuple[sqlite3.Connection, dict]:
        db = sqlite3.connect(":memory:")
        db.execute("CREATE TABLE entity_state(id INTEGER PRIMARY KEY, generation INTEGER NOT NULL)")
        db.execute("INSERT INTO entity_state(id,generation) VALUES(1,7)")
        store.install_schema(db)
        boot_values = {}
        for field_name, object_kind in store.BOOT_FIELD_KINDS.items():
            digest = self.digest(field_name)
            boot_values[field_name] = digest
            store.register_object(
                db,
                object_kind=object_kind,
                object_version="v1",
                object_digest=digest,
                digest_basis="EXTERNAL_BYTES",
                payload={"fixture": field_name},
                provenance_refs=["test:" + field_name],
            )
            store.admit_object(
                db,
                object_kind=object_kind,
                object_version="v1",
                object_digest=digest,
                entity_generation=7,
                admission_receipt_digest=self.digest("receipt:" + field_name),
            )
        boot = store.admit_boot_binding(
            db,
            entity_generation=7,
            provenance_refs=["test:boot"],
            **boot_values,
        )
        args = self.args()
        args["boot_binding_digest"] = boot["binding_digest"]
        return db, args

    def test_same_complete_material_is_same_retry_identity(self):
        first = causal.derive_causal_turn_id(**self.args())
        second = causal.derive_causal_turn_id(**self.args())
        self.assertEqual(first, second)
        self.assertTrue(first.startswith("ct1:"))

    def test_task_or_workspace_change_cannot_reuse_identity(self):
        base = causal.derive_causal_turn_id(**self.args())
        task_changed = self.args()
        task_changed["task_text"] = "different task"
        workspace_changed = self.args()
        workspace_changed["workspace_digest"] = self.digest("other-workspace")
        self.assertNotEqual(base, causal.derive_causal_turn_id(**task_changed))
        self.assertNotEqual(base, causal.derive_causal_turn_id(**workspace_changed))

    def test_generation_or_boot_change_cannot_reuse_identity(self):
        base = causal.derive_causal_turn_id(**self.args())
        generation_changed = self.args()
        generation_changed["entity_generation"] = 8
        boot_changed = self.args()
        boot_changed["boot_binding_digest"] = self.digest("different-boot")
        self.assertNotEqual(base, causal.derive_causal_turn_id(**generation_changed))
        self.assertNotEqual(base, causal.derive_causal_turn_id(**boot_changed))

    def test_placeholder_digest_fails_closed(self):
        poisoned = self.args()
        poisoned["workspace_digest"] = "0" * 64
        with self.assertRaisesRegex(causal.CausalTurnError, "PLACEHOLDER_REJECTED"):
            causal.derive_causal_turn_id(**poisoned)

    def test_binding_delegates_to_same_miniunifieddb_and_is_idempotent(self):
        db, args = self.make_bound_db()
        first = causal.bind_derived_turn(db, **args)
        second = causal.bind_derived_turn(db, **args)
        self.assertEqual(first["causal_turn_id"], second["causal_turn_id"])
        self.assertTrue(second["idempotent"])
        count = db.execute("SELECT COUNT(*) FROM mini_cognition_turn_bindings").fetchone()[0]
        self.assertEqual(count, 1)

    def test_resolve_cross_checks_exact_bound_material(self):
        db, args = self.make_bound_db()
        bound = causal.bind_derived_turn(db, **args)
        resolved = causal.resolve_derived_prepare_binding(db, **args)
        self.assertEqual(resolved["causal_turn_id"], bound["causal_turn_id"])
        poisoned = dict(args)
        poisoned["selected_workspace_slots"] = ["slot-b", "slot-a"]
        with self.assertRaises(store.CognitionStoreError):
            causal.resolve_derived_prepare_binding(db, **poisoned)


if __name__ == "__main__":
    unittest.main()
