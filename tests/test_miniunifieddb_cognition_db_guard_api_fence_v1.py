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

import miniunifieddb_cognition_db_guards_v1 as guards
import miniunifieddb_cognition_store_v1 as store


class CognitionDBGuardAPIFenceV1Tests(unittest.TestCase):
    @staticmethod
    def digest(label: str) -> str:
        return hashlib.sha256(label.encode("utf-8")).hexdigest()

    def test_store_api_cannot_reuse_prior_generation_admissions_when_guards_installed(self) -> None:
        db = sqlite3.connect(":memory:")
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("CREATE TABLE entity_state(id INTEGER PRIMARY KEY, generation INTEGER NOT NULL)")
        db.execute("INSERT INTO entity_state(id,generation) VALUES(1,7)")
        db.commit()
        store.install_schema(db)
        guards.install_guards(db)

        values: dict[str, str] = {}
        for field_name, kind in store.BOOT_FIELD_KINDS.items():
            digest = self.digest(field_name)
            values[field_name] = digest
            store.register_object(
                db,
                object_kind=kind,
                object_version="v1",
                object_digest=digest,
                digest_basis="EXTERNAL_BYTES",
                payload={"identity": field_name, "classification": "TEST_FIXTURE_ONLY"},
                provenance_refs=["test:" + field_name],
            )
            store.admit_object(
                db,
                object_kind=kind,
                object_version="v1",
                object_digest=digest,
                entity_generation=7,
                admission_receipt_digest=self.digest("receipt:" + field_name),
            )
        db.commit()

        # Current store source still accepts <= generation while resolving an admission.
        # The DB guard must therefore be the final enforcement boundary until that source
        # check is separately tightened.
        db.execute("UPDATE entity_state SET generation=8 WHERE id=1")
        db.commit()

        with self.assertRaisesRegex(sqlite3.DatabaseError, "COGNITION_BOOT_OBJECT_NOT_ADMITTED"):
            store.admit_boot_binding(
                db,
                entity_generation=8,
                provenance_refs=["test:boot-generation-8"],
                **values,
            )

        rows = db.execute(
            "SELECT COUNT(*) FROM mini_cognition_boot_bindings WHERE entity_generation=8"
        ).fetchone()[0]
        self.assertEqual(rows, 0)
        db.close()


if __name__ == "__main__":
    unittest.main()
