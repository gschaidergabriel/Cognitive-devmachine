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


class CognitionGenerationFenceTests(unittest.TestCase):
    @staticmethod
    def digest(label: str) -> str:
        return hashlib.sha256(label.encode("utf-8")).hexdigest()

    def test_prior_generation_object_admission_cannot_authorize_new_boot_binding(self):
        db = sqlite3.connect(":memory:")
        db.execute("PRAGMA foreign_keys=ON")
        db.execute(
            "CREATE TABLE entity_state(id INTEGER PRIMARY KEY, generation INTEGER NOT NULL)"
        )
        db.execute("INSERT INTO entity_state(id,generation) VALUES(1,3)")
        store.install_schema(db)

        values: dict[str, str] = {}
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
                entity_generation=3,
                admission_receipt_digest=self.digest("receipt:g3:" + field_name),
            )

        db.execute("UPDATE entity_state SET generation=4 WHERE id=1")

        with self.assertRaisesRegex(
            store.CognitionStoreError,
            "COGNITION_OBJECT_NOT_ADMITTED",
        ):
            store.admit_boot_binding(
                db,
                entity_generation=4,
                provenance_refs=["test:boot:g4"],
                **values,
            )


if __name__ == "__main__":
    unittest.main()
