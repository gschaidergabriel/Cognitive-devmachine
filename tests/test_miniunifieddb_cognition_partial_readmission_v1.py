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


class CognitionPartialReadmissionTests(unittest.TestCase):
    @staticmethod
    def digest(label: str) -> str:
        return hashlib.sha256(label.encode("utf-8")).hexdigest()

    def test_one_fresh_object_cannot_launder_stale_remaining_boot_authority(self):
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
        fresh_field = "zero_identity_digest"
        store.admit_object(
            db,
            object_kind=store.BOOT_FIELD_KINDS[fresh_field],
            object_version="v1",
            object_digest=values[fresh_field],
            entity_generation=4,
            admission_receipt_digest=self.digest("receipt:g4:" + fresh_field),
        )

        with self.assertRaisesRegex(
            store.CognitionStoreError,
            "COGNITION_OBJECT_NOT_ADMITTED:GRF",
        ):
            store.admit_boot_binding(
                db,
                entity_generation=4,
                provenance_refs=["test:partial-readmission:g4"],
                **values,
            )
        db.close()


if __name__ == "__main__":
    unittest.main()
