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


class CognitionStoreReadIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.execute(
            "CREATE TABLE entity_state(id INTEGER PRIMARY KEY, generation INTEGER NOT NULL)"
        )
        self.db.execute("INSERT INTO entity_state(id,generation) VALUES(1,3)")
        store.install_schema(self.db)
        self.task_text = "run bounded reasoning"
        self.values = self._admit_boot_objects()
        self.boot = store.admit_boot_binding(
            self.db,
            entity_generation=3,
            provenance_refs=["test:boot"],
            **self.values,
        )
        self.turn = store.bind_turn(
            self.db,
            entity_generation=3,
            causal_turn_id="turn-read-integrity",
            boot_binding_digest=self.boot["binding_digest"],
            task_text=self.task_text,
            workspace_digest=self.digest("workspace-current"),
            selected_workspace_slots=["slot-a", "slot-b"],
            contradiction_state="UNRESOLVED",
            provenance_refs=["test:turn"],
            required_zero_mode="ACTIVE",
        )
        self.db.commit()

    def tearDown(self):
        self.db.close()

    @staticmethod
    def digest(label: str) -> str:
        return hashlib.sha256(label.encode("utf-8")).hexdigest()

    def _admit_boot_objects(self) -> dict[str, str]:
        values: dict[str, str] = {}
        for field_name, object_kind in store.BOOT_FIELD_KINDS.items():
            object_digest = self.digest(field_name)
            values[field_name] = object_digest
            store.register_object(
                self.db,
                object_kind=object_kind,
                object_version="v1",
                object_digest=object_digest,
                digest_basis="EXTERNAL_BYTES",
                payload={"identity": field_name, "classification": "TEST_FIXTURE_ONLY"},
                provenance_refs=["test:" + field_name],
            )
            store.admit_object(
                self.db,
                object_kind=object_kind,
                object_version="v1",
                object_digest=object_digest,
                entity_generation=3,
                admission_receipt_digest=self.digest("receipt:" + field_name),
            )
        return values

    def resolve(self):
        return store.resolve_prepare_binding(
            self.db,
            entity_generation=3,
            causal_turn_id="turn-read-integrity",
            task_text=self.task_text,
        )

    def test_valid_binding_roundtrip_still_resolves(self):
        resolved = self.resolve()
        self.assertEqual(resolved["turn_binding_digest"], self.turn["binding_digest"])
        self.assertEqual(resolved["boot_binding_digest"], self.boot["binding_digest"])
        self.assertEqual(resolved["workspace_digest"], self.digest("workspace-current"))

    def test_workspace_digest_tamper_with_old_turn_digest_fails_closed(self):
        self.db.execute(
            "UPDATE mini_cognition_turn_bindings SET workspace_digest=? WHERE causal_turn_id=?",
            (self.digest("workspace-poison"), "turn-read-integrity"),
        )
        self.db.commit()
        with self.assertRaisesRegex(store.CognitionStoreError, "TURN_BINDING_DIGEST_MISMATCH"):
            self.resolve()

    def test_zero_identity_tamper_with_old_boot_digest_fails_closed(self):
        self.db.execute(
            "UPDATE mini_cognition_boot_bindings SET zero_identity_digest=? WHERE binding_digest=?",
            (self.digest("zero-poison"), self.boot["binding_digest"]),
        )
        self.db.commit()
        with self.assertRaisesRegex(store.CognitionStoreError, "BOOT_BINDING_DIGEST_MISMATCH"):
            self.resolve()

    def test_turn_list_json_corruption_fails_closed(self):
        self.db.execute(
            "UPDATE mini_cognition_turn_bindings SET selected_workspace_slots_json='not-json' WHERE causal_turn_id=?",
            ("turn-read-integrity",),
        )
        self.db.commit()
        with self.assertRaisesRegex(store.CognitionStoreError, "TURN_BINDING_JSON_CORRUPT"):
            self.resolve()

    def test_boot_provenance_json_corruption_fails_closed(self):
        self.db.execute(
            "UPDATE mini_cognition_boot_bindings SET provenance_refs_json='not-json' WHERE binding_digest=?",
            (self.boot["binding_digest"],),
        )
        self.db.commit()
        with self.assertRaisesRegex(store.CognitionStoreError, "BOOT_BINDING_JSON_CORRUPT"):
            self.resolve()


if __name__ == "__main__":
    unittest.main()
