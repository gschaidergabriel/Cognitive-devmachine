import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import miniunifieddb_cognition_store_v1 as store


GENERATION = 7
TASK = "integrity-bound task"
TURN_ID = "turn-integrity-1"


def digest(text: str) -> str:
    return store.sha256_text(text)


def build_bound_db() -> tuple[sqlite3.Connection, dict[str, str], str]:
    db = sqlite3.connect(":memory:")
    db.execute(
        """CREATE TABLE entity_state(
             id INTEGER PRIMARY KEY CHECK(id=1),
             generation INTEGER NOT NULL)"""
    )
    db.execute("INSERT INTO entity_state(id,generation) VALUES(1,?)", (GENERATION,))
    store.install_schema(db)
    db.commit()

    field_digests: dict[str, str] = {}
    for field_name, object_kind in store.BOOT_FIELD_KINDS.items():
        payload = {"kind": object_kind, "fixture": field_name, "version": 1}
        object_digest = store.sha256_obj(payload)
        store.register_object(
            db,
            object_kind=object_kind,
            object_version="v1",
            object_digest=object_digest,
            digest_basis="CANONICAL_JSON",
            payload=payload,
            provenance_refs=[f"fixture:{field_name}"],
        )
        store.admit_object(
            db,
            object_kind=object_kind,
            object_version="v1",
            object_digest=object_digest,
            entity_generation=GENERATION,
            admission_receipt_digest=digest(f"admit:{field_name}"),
        )
        field_digests[field_name] = object_digest

    boot = store.admit_boot_binding(
        db,
        entity_generation=GENERATION,
        **field_digests,
        provenance_refs=["fixture:boot"],
    )
    workspace_digest = digest("workspace:v1")
    store.bind_turn(
        db,
        entity_generation=GENERATION,
        causal_turn_id=TURN_ID,
        boot_binding_digest=boot["binding_digest"],
        task_text=TASK,
        workspace_digest=workspace_digest,
        selected_workspace_slots=["slot:a", "slot:b"],
        contradiction_state="CLEAR",
        provenance_refs=["fixture:turn"],
        required_zero_mode="BOUND",
    )
    db.commit()
    return db, field_digests, boot["binding_digest"]


class CognitionReadIntegrityTests(unittest.TestCase):
    def test_valid_binding_resolves(self):
        db, field_digests, boot_digest = build_bound_db()
        resolved = store.resolve_prepare_binding(
            db,
            entity_generation=GENERATION,
            causal_turn_id=TURN_ID,
            task_text=TASK,
        )
        self.assertTrue(resolved["ok"])
        self.assertEqual(boot_digest, resolved["boot_binding_digest"])
        self.assertEqual(field_digests["zero_identity_digest"], resolved["zero_identity_digest"])

    def test_workspace_digest_tamper_fails_closed(self):
        db, _, _ = build_bound_db()
        db.execute(
            """UPDATE mini_cognition_turn_bindings
               SET workspace_digest=?
               WHERE entity_generation=? AND causal_turn_id=?""",
            (digest("workspace:tampered"), GENERATION, TURN_ID),
        )
        db.commit()
        with self.assertRaisesRegex(store.CognitionStoreError, "TURN_BINDING_DIGEST_MISMATCH"):
            store.resolve_prepare_binding(
                db,
                entity_generation=GENERATION,
                causal_turn_id=TURN_ID,
                task_text=TASK,
            )

    def test_zero_identity_digest_tamper_fails_closed(self):
        db, _, boot_digest = build_bound_db()
        db.execute(
            """UPDATE mini_cognition_boot_bindings
               SET zero_identity_digest=?
               WHERE binding_digest=?""",
            (digest("zero:tampered"), boot_digest),
        )
        db.commit()
        with self.assertRaisesRegex(store.CognitionStoreError, "BOOT_BINDING_DIGEST_MISMATCH"):
            store.resolve_prepare_binding(
                db,
                entity_generation=GENERATION,
                causal_turn_id=TURN_ID,
                task_text=TASK,
            )

    def test_noncanonical_slots_json_fails_before_digest_use(self):
        db, _, _ = build_bound_db()
        db.execute(
            """UPDATE mini_cognition_turn_bindings
               SET selected_workspace_slots_json=?
               WHERE entity_generation=? AND causal_turn_id=?""",
            ('[ "slot:a", "slot:b" ]', GENERATION, TURN_ID),
        )
        db.commit()
        with self.assertRaisesRegex(store.CognitionStoreError, "NONCANONICAL_JSON"):
            store.resolve_prepare_binding(
                db,
                entity_generation=GENERATION,
                causal_turn_id=TURN_ID,
                task_text=TASK,
            )


if __name__ == "__main__":
    unittest.main()
