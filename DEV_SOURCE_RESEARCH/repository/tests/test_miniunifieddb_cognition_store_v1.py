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

import miniunifieddb_cognition_store_v1 as store


class CognitionStoreV1Tests(unittest.TestCase):
    def make_db(self, generation: int = 3) -> sqlite3.Connection:
        db = sqlite3.connect(":memory:")
        db.execute("PRAGMA foreign_keys=ON")
        db.execute(
            "CREATE TABLE entity_state(id INTEGER PRIMARY KEY, generation INTEGER NOT NULL)"
        )
        db.execute("INSERT INTO entity_state(id,generation) VALUES(1,?)", (generation,))
        store.install_schema(db)
        return db

    @staticmethod
    def digest(label: str) -> str:
        return hashlib.sha256(label.encode("utf-8")).hexdigest()

    def register_and_admit_boot_objects(self, db: sqlite3.Connection, generation: int = 3):
        values = {}
        for field_name, object_kind in store.BOOT_FIELD_KINDS.items():
            digest = self.digest(field_name)
            values[field_name] = digest
            store.register_object(
                db,
                object_kind=object_kind,
                object_version="v1",
                object_digest=digest,
                digest_basis="EXTERNAL_BYTES",
                payload={"identity": field_name, "classification": "TEST_FIXTURE_ONLY"},
                provenance_refs=["test:" + field_name],
            )
            store.admit_object(
                db,
                object_kind=object_kind,
                object_version="v1",
                object_digest=digest,
                entity_generation=generation,
                admission_receipt_digest=self.digest("receipt:" + field_name),
            )
        return values

    def admit_boot(self, db: sqlite3.Connection, generation: int = 3):
        values = self.register_and_admit_boot_objects(db, generation)
        result = store.admit_boot_binding(
            db,
            entity_generation=generation,
            provenance_refs=["test:boot"],
            **values,
        )
        return values, result["binding_digest"]

    def test_canonical_json_object_digest_must_match_payload(self):
        db = self.make_db()
        with self.assertRaisesRegex(store.CognitionStoreError, "OBJECT_DIGEST_PAYLOAD_MISMATCH"):
            store.register_object(
                db,
                object_kind="ZERO_IDENTITY",
                object_version="v1",
                object_digest=self.digest("wrong"),
                digest_basis="CANONICAL_JSON",
                payload={"identity": "ZERO"},
                provenance_refs=["test:zero"],
            )

    def test_boot_binding_requires_every_referenced_object_to_be_admitted(self):
        db = self.make_db()
        values = self.register_and_admit_boot_objects(db)
        db.execute(
            "DELETE FROM mini_cognition_object_admissions WHERE object_kind='JACOBIAN_LENS_PROFILE'"
        )
        with self.assertRaisesRegex(
            store.CognitionStoreError,
            "COGNITION_OBJECT_NOT_ADMITTED:JACOBIAN_LENS_PROFILE",
        ):
            store.admit_boot_binding(
                db,
                entity_generation=3,
                provenance_refs=["test:boot"],
                **values,
            )

    def test_stale_generation_cannot_admit_or_bind(self):
        db = self.make_db(generation=4)
        digest = self.digest("zero")
        store.register_object(
            db,
            object_kind="ZERO_IDENTITY",
            object_version="v1",
            object_digest=digest,
            digest_basis="EXTERNAL_BYTES",
            payload={"identity": "ZERO"},
            provenance_refs=["test:zero"],
        )
        with self.assertRaisesRegex(store.CognitionStoreError, "STALE_GENERATION"):
            store.admit_object(
                db,
                object_kind="ZERO_IDENTITY",
                object_version="v1",
                object_digest=digest,
                entity_generation=3,
                admission_receipt_digest=self.digest("receipt"),
            )

    def test_turn_binding_is_idempotent_but_conflicting_rebind_fails(self):
        db = self.make_db()
        _, boot_digest = self.admit_boot(db)
        first = store.bind_turn(
            db,
            entity_generation=3,
            causal_turn_id="turn-1",
            boot_binding_digest=boot_digest,
            task_text="explain state",
            workspace_digest=self.digest("workspace-a"),
            selected_workspace_slots=["slot-a"],
            contradiction_state="NONE",
            provenance_refs=["test:workspace"],
            required_zero_mode="ACTIVE",
        )
        second = store.bind_turn(
            db,
            entity_generation=3,
            causal_turn_id="turn-1",
            boot_binding_digest=boot_digest,
            task_text="explain state",
            workspace_digest=self.digest("workspace-a"),
            selected_workspace_slots=["slot-a"],
            contradiction_state="NONE",
            provenance_refs=["test:workspace"],
            required_zero_mode="ACTIVE",
        )
        self.assertEqual(first["binding_digest"], second["binding_digest"])
        self.assertTrue(second["idempotent"])

        with self.assertRaisesRegex(store.CognitionStoreError, "TURN_BINDING_CONFLICT"):
            store.bind_turn(
                db,
                entity_generation=3,
                causal_turn_id="turn-1",
                boot_binding_digest=boot_digest,
                task_text="explain state",
                workspace_digest=self.digest("workspace-b"),
                selected_workspace_slots=["slot-b"],
                contradiction_state="NONE",
                provenance_refs=["test:workspace"],
                required_zero_mode="ACTIVE",
            )

    def test_resolve_prepare_binding_cross_binds_task_boot_and_workspace(self):
        db = self.make_db()
        values, boot_digest = self.admit_boot(db)
        turn = store.bind_turn(
            db,
            entity_generation=3,
            causal_turn_id="turn-2",
            boot_binding_digest=boot_digest,
            task_text="run bounded reasoning",
            workspace_digest=self.digest("workspace-current"),
            selected_workspace_slots=["slot-1", "slot-2"],
            contradiction_state="UNRESOLVED",
            provenance_refs=["test:turn"],
            required_zero_mode="ACTIVE",
        )
        resolved = store.resolve_prepare_binding(
            db,
            entity_generation=3,
            causal_turn_id="turn-2",
            task_text="run bounded reasoning",
        )
        self.assertEqual(resolved["turn_binding_digest"], turn["binding_digest"])
        self.assertEqual(resolved["boot_binding_digest"], boot_digest)
        self.assertEqual(resolved["zero_identity_digest"], values["zero_identity_digest"])
        self.assertEqual(resolved["workspace_digest"], self.digest("workspace-current"))
        self.assertFalse(resolved["authority"]["direct_truth_authority"])
        self.assertFalse(resolved["authority"]["direct_effect_authority"])

        with self.assertRaisesRegex(store.CognitionStoreError, "TURN_TASK_BINDING_MISMATCH"):
            store.resolve_prepare_binding(
                db,
                entity_generation=3,
                causal_turn_id="turn-2",
                task_text="different task",
            )


if __name__ == "__main__":
    unittest.main()
