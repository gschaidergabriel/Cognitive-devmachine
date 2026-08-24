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


class CognitionDBGuardGenerationReuseV1Tests(unittest.TestCase):
    @staticmethod
    def digest(label: str) -> str:
        return hashlib.sha256(label.encode("utf-8")).hexdigest()

    def test_direct_boot_cannot_reuse_prior_generation_admissions(self) -> None:
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

        db.execute("UPDATE entity_state SET generation=8 WHERE id=1")
        db.commit()

        with self.assertRaisesRegex(
            sqlite3.DatabaseError,
            "COGNITION_BOOT_OBJECT_NOT_ADMITTED",
        ):
            db.execute(
                """INSERT INTO mini_cognition_boot_bindings(
                     binding_digest,schema,entity_generation,zero_identity_digest,grf_digest,
                     hyperposition_digest,bundled_manifest_digest,local_model_digest,
                     tokenizer_digest,jspace_profile_digest,jacobian_lens_digest,
                     workspace_calibration_digest,boot_source_lock_digest,policy_authority_digest,
                     provenance_refs_json,created_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    self.digest("boot-generation-8"),
                    store.BOOT_BINDING_SCHEMA,
                    8,
                    values["zero_identity_digest"],
                    values["grf_digest"],
                    values["hyperposition_digest"],
                    values["bundled_manifest_digest"],
                    values["local_model_digest"],
                    values["tokenizer_digest"],
                    values["jspace_profile_digest"],
                    values["jacobian_lens_digest"],
                    values["workspace_calibration_digest"],
                    values["boot_source_lock_digest"],
                    values["policy_authority_digest"],
                    "[]",
                    "t",
                ),
            )

        rows = db.execute(
            "SELECT COUNT(*) FROM mini_cognition_boot_bindings WHERE entity_generation=8"
        ).fetchone()[0]
        self.assertEqual(rows, 0)
        db.close()


if __name__ == "__main__":
    unittest.main()
