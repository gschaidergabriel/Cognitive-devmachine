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


class CognitionReadIntegrityV1Tests(unittest.TestCase):
    @staticmethod
    def digest(label: str) -> str:
        return hashlib.sha256(label.encode("utf-8")).hexdigest()

    def populated(self) -> sqlite3.Connection:
        db = sqlite3.connect(":memory:")
        db.execute("CREATE TABLE entity_state(id INTEGER PRIMARY KEY, generation INTEGER NOT NULL)")
        db.execute("INSERT INTO entity_state(id,generation) VALUES(1,7)")
        store.install_schema(db)

        values: dict[str, str] = {}
        for field_name, object_kind in store.BOOT_FIELD_KINDS.items():
            value = self.digest(field_name)
            values[field_name] = value
            store.register_object(
                db,
                object_kind=object_kind,
                object_version="v1",
                object_digest=value,
                digest_basis="EXTERNAL_BYTES",
                payload={"identity": field_name, "scope": "READ_INTEGRITY_TEST"},
                provenance_refs=["test:" + field_name],
            )
            store.admit_object(
                db,
                object_kind=object_kind,
                object_version="v1",
                object_digest=value,
                entity_generation=7,
                admission_receipt_digest=self.digest("admit:" + field_name),
            )

        boot = store.admit_boot_binding(
            db,
            entity_generation=7,
            provenance_refs=["test:boot"],
            **values,
        )
        store.bind_turn(
            db,
            entity_generation=7,
            causal_turn_id="turn-read-integrity",
            boot_binding_digest=boot["binding_digest"],
            task_text="bounded cognition",
            workspace_digest=self.digest("workspace"),
            selected_workspace_slots=["slot-a", "slot-b"],
            contradiction_state="UNRESOLVED",
            provenance_refs=["test:turn"],
            required_zero_mode="ACTIVE",
        )
        return db

    def resolve(self, db: sqlite3.Connection):
        return store.resolve_prepare_binding(
            db,
            entity_generation=7,
            causal_turn_id="turn-read-integrity",
            task_text="bounded cognition",
        )

    def test_exact_persisted_bindings_resolve(self):
        resolved = self.resolve(self.populated())
        self.assertTrue(resolved["ok"])
        self.assertEqual(resolved["selected_workspace_slots"], ["slot-a", "slot-b"])
        self.assertEqual(resolved["authority"]["durable_state"], "MiniUnifiedDB")

    def test_workspace_digest_tamper_fails_closed(self):
        db = self.populated()
        db.execute(
            "UPDATE mini_cognition_turn_bindings SET workspace_digest=? WHERE causal_turn_id=?",
            (self.digest("workspace-poison"), "turn-read-integrity"),
        )
        with self.assertRaisesRegex(store.CognitionStoreError, "TURN_BINDING_DIGEST_MISMATCH"):
            self.resolve(db)

    def test_zero_identity_digest_tamper_fails_closed(self):
        db = self.populated()
        db.execute(
            "UPDATE mini_cognition_boot_bindings SET zero_identity_digest=? WHERE entity_generation=7",
            (self.digest("zero-poison"),),
        )
        with self.assertRaisesRegex(store.CognitionStoreError, "COGNITION_OBJECT_NOT_ADMITTED:ZERO_IDENTITY|BOOT_BINDING_DIGEST_MISMATCH"):
            self.resolve(db)

    def test_turn_slot_json_noncanonical_fails_closed(self):
        db = self.populated()
        db.execute(
            "UPDATE mini_cognition_turn_bindings SET selected_workspace_slots_json=? WHERE causal_turn_id=?",
            ('["slot-a", "slot-b"]', "turn-read-integrity"),
        )
        with self.assertRaisesRegex(store.CognitionStoreError, "selected_workspace_slots:NONCANONICAL_JSON"):
            self.resolve(db)

    def test_turn_provenance_malformed_json_fails_closed(self):
        db = self.populated()
        db.execute(
            "UPDATE mini_cognition_turn_bindings SET provenance_refs_json=? WHERE causal_turn_id=?",
            ('["test:turn"', "turn-read-integrity"),
        )
        with self.assertRaisesRegex(store.CognitionStoreError, "turn_provenance_refs:MALFORMED_JSON"):
            self.resolve(db)

    def test_boot_provenance_noncanonical_fails_closed(self):
        db = self.populated()
        db.execute(
            "UPDATE mini_cognition_boot_bindings SET provenance_refs_json=? WHERE entity_generation=7",
            ('[ "test:boot" ]',),
        )
        with self.assertRaisesRegex(store.CognitionStoreError, "boot_provenance_refs:NONCANONICAL_JSON"):
            self.resolve(db)

    def test_binding_schema_tamper_fails_closed(self):
        db = self.populated()
        db.execute(
            "UPDATE mini_cognition_turn_bindings SET schema='MINIUNIFIEDDB_COGNITION_TURN_BINDING/v0' WHERE causal_turn_id=?",
            ("turn-read-integrity",),
        )
        with self.assertRaisesRegex(store.CognitionStoreError, "TURN_BINDING_SCHEMA_MISMATCH"):
            self.resolve(db)


if __name__ == "__main__":
    unittest.main()
