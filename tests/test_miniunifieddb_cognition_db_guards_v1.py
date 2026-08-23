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


class CognitionDBGuardV1Tests(unittest.TestCase):
    @staticmethod
    def digest(label: str) -> str:
        return hashlib.sha256(label.encode("utf-8")).hexdigest()

    def make_db(self, generation: int = 7) -> sqlite3.Connection:
        db = sqlite3.connect(":memory:")
        db.execute("PRAGMA foreign_keys=ON")
        db.execute(
            "CREATE TABLE entity_state(id INTEGER PRIMARY KEY, generation INTEGER NOT NULL)"
        )
        db.execute("INSERT INTO entity_state(id,generation) VALUES(1,?)", (generation,))
        db.commit()
        store.install_schema(db)
        guards.install_guards(db)
        return db

    def register(self, db: sqlite3.Connection, kind: str, label: str) -> str:
        digest = self.digest(label)
        store.register_object(
            db,
            object_kind=kind,
            object_version="v1",
            object_digest=digest,
            digest_basis="EXTERNAL_BYTES",
            payload={"identity": label, "classification": "TEST_FIXTURE_ONLY"},
            provenance_refs=["test:" + label],
        )
        return digest

    def complete_boot(self, db: sqlite3.Connection, generation: int = 7) -> str:
        values: dict[str, str] = {}
        for field_name, kind in store.BOOT_FIELD_KINDS.items():
            digest = self.register(db, kind, field_name)
            values[field_name] = digest
            store.admit_object(
                db,
                object_kind=kind,
                object_version="v1",
                object_digest=digest,
                entity_generation=generation,
                admission_receipt_digest=self.digest("receipt:" + field_name),
            )
        result = store.admit_boot_binding(
            db,
            entity_generation=generation,
            provenance_refs=["test:boot"],
            **values,
        )
        return str(result["binding_digest"])

    def test_guards_add_no_second_table_or_store(self) -> None:
        db = sqlite3.connect(":memory:")
        db.execute("CREATE TABLE entity_state(id INTEGER PRIMARY KEY, generation INTEGER NOT NULL)")
        db.execute("INSERT INTO entity_state(id,generation) VALUES(1,7)")
        db.commit()
        store.install_schema(db)
        before = {
            row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        status = guards.install_guards(db)
        after = {
            row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        self.assertEqual(before, after)
        self.assertTrue(status["ok"])
        self.assertEqual(status["trigger_count"], 11)
        self.assertFalse(status["creates_tables"])
        db.close()

    def test_post_check_stale_admission_insert_fails_inside_sqlite(self) -> None:
        """Models generation advancing after an application check but before its INSERT."""
        db = self.make_db(generation=8)
        digest = self.register(db, "ZERO_IDENTITY", "zero")
        db.commit()
        with self.assertRaisesRegex(sqlite3.DatabaseError, "COGNITION_STALE_GENERATION"):
            db.execute(
                """INSERT INTO mini_cognition_object_admissions(
                     object_kind,object_version,object_digest,admitted_generation,
                     admission_receipt_digest,admitted_at)
                   VALUES(?,?,?,?,?,?)""",
                ("ZERO_IDENTITY", "v1", digest, 7, self.digest("receipt"), "t"),
            )
        self.assertEqual(
            db.execute("SELECT COUNT(*) FROM mini_cognition_object_admissions").fetchone()[0],
            0,
        )
        db.close()

    def test_current_generation_direct_admission_can_pass_guard(self) -> None:
        db = self.make_db(generation=8)
        digest = self.register(db, "ZERO_IDENTITY", "zero")
        db.execute(
            """INSERT INTO mini_cognition_object_admissions(
                 object_kind,object_version,object_digest,admitted_generation,
                 admission_receipt_digest,admitted_at)
               VALUES(?,?,?,?,?,?)""",
            ("ZERO_IDENTITY", "v1", digest, 8, self.digest("receipt"), "t"),
        )
        self.assertEqual(
            db.execute("SELECT admitted_generation FROM mini_cognition_object_admissions").fetchone()[0],
            8,
        )
        db.close()

    def test_direct_boot_insert_cannot_bypass_object_admission(self) -> None:
        db = self.make_db(generation=7)
        values = {field: self.digest(field) for field in store.BOOT_FIELD_KINDS}
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
                    self.digest("boot"),
                    store.BOOT_BINDING_SCHEMA,
                    7,
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
        db.close()

    def test_direct_turn_insert_rejects_stale_boot_generation(self) -> None:
        db = self.make_db(generation=7)
        boot_digest = self.complete_boot(db, generation=7)
        db.commit()
        db.execute("UPDATE entity_state SET generation=8 WHERE id=1")
        db.commit()
        with self.assertRaisesRegex(
            sqlite3.DatabaseError,
            "COGNITION_TURN_BOOT_BINDING_STALE_OR_MISSING",
        ):
            db.execute(
                """INSERT INTO mini_cognition_turn_bindings(
                     entity_generation,causal_turn_id,binding_digest,schema,boot_binding_digest,
                     task_sha256,workspace_digest,selected_workspace_slots_json,
                     contradiction_state,provenance_refs_json,required_zero_mode,created_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    8,
                    "turn-8",
                    self.digest("turn-8"),
                    store.TURN_BINDING_SCHEMA,
                    boot_digest,
                    self.digest("task"),
                    self.digest("workspace"),
                    "[]",
                    "NONE",
                    "[]",
                    "ACTIVE",
                    "t",
                ),
            )
        db.close()

    def test_direct_stale_boot_and_turn_inserts_fail_on_live_generation(self) -> None:
        db = self.make_db(generation=8)
        stale_boot_values = [self.digest("x" + str(i)) for i in range(11)]
        with self.assertRaisesRegex(sqlite3.DatabaseError, "COGNITION_STALE_GENERATION"):
            db.execute(
                """INSERT INTO mini_cognition_boot_bindings(
                     binding_digest,schema,entity_generation,zero_identity_digest,grf_digest,
                     hyperposition_digest,bundled_manifest_digest,local_model_digest,
                     tokenizer_digest,jspace_profile_digest,jacobian_lens_digest,
                     workspace_calibration_digest,boot_source_lock_digest,policy_authority_digest,
                     provenance_refs_json,created_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    self.digest("boot"), store.BOOT_BINDING_SCHEMA, 7,
                    *stale_boot_values, "[]", "t",
                ),
            )
        with self.assertRaisesRegex(sqlite3.DatabaseError, "COGNITION_STALE_GENERATION"):
            db.execute(
                """INSERT INTO mini_cognition_turn_bindings(
                     entity_generation,causal_turn_id,binding_digest,schema,boot_binding_digest,
                     task_sha256,workspace_digest,selected_workspace_slots_json,
                     contradiction_state,provenance_refs_json,required_zero_mode,created_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    7, "turn-7", self.digest("turn-7"), store.TURN_BINDING_SCHEMA,
                    self.digest("boot-7"), self.digest("task"), self.digest("workspace"),
                    "[]", "NONE", "[]", "ACTIVE", "t",
                ),
            )
        db.close()

    def test_cognition_tables_are_append_only_when_guards_installed(self) -> None:
        db = self.make_db(generation=7)
        boot_digest = self.complete_boot(db, generation=7)
        store.bind_turn(
            db,
            entity_generation=7,
            causal_turn_id="turn-7",
            boot_binding_digest=boot_digest,
            task_text="task",
            workspace_digest=self.digest("workspace"),
            selected_workspace_slots=["slot-a"],
            contradiction_state="NONE",
            provenance_refs=["test:turn"],
            required_zero_mode="ACTIVE",
        )
        db.commit()

        mutations = [
            "UPDATE mini_cognition_objects SET created_at='x'",
            "DELETE FROM mini_cognition_objects",
            "UPDATE mini_cognition_object_admissions SET admitted_at='x'",
            "DELETE FROM mini_cognition_object_admissions",
            "UPDATE mini_cognition_boot_bindings SET created_at='x'",
            "DELETE FROM mini_cognition_boot_bindings",
            "UPDATE mini_cognition_turn_bindings SET created_at='x'",
            "DELETE FROM mini_cognition_turn_bindings",
        ]
        for sql in mutations:
            with self.subTest(sql=sql):
                with self.assertRaisesRegex(sqlite3.DatabaseError, "IMMUTABLE"):
                    db.execute(sql)
                db.rollback()
        db.close()


if __name__ == "__main__":
    unittest.main()
