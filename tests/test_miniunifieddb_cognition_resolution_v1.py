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

import miniunifieddb_cognition_resolution_v1 as resolver
import miniunifieddb_cognition_store_v1 as store


class CognitionSemanticResolutionTests(unittest.TestCase):
    @staticmethod
    def digest(label: str) -> str:
        return hashlib.sha256(label.encode("utf-8")).hexdigest()

    def make_bound_turn(self):
        db = sqlite3.connect(":memory:")
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("CREATE TABLE entity_state(id INTEGER PRIMARY KEY, generation INTEGER NOT NULL)")
        db.execute("INSERT INTO entity_state(id,generation) VALUES(1,7)")
        store.install_schema(db)
        values: dict[str, str] = {}
        for field_name, object_kind in store.BOOT_FIELD_KINDS.items():
            digest = self.digest("bytes:" + field_name)
            values[field_name] = digest
            store.register_object(
                db,
                object_kind=object_kind,
                object_version="v1",
                object_digest=digest,
                digest_basis="EXTERNAL_BYTES",
                payload={"field": field_name, "semantic_marker": "v1:" + field_name, "classification": "TEST_FIXTURE_ONLY"},
                provenance_refs=["test:object:" + field_name],
            )
            store.admit_object(
                db,
                object_kind=object_kind,
                object_version="v1",
                object_digest=digest,
                entity_generation=7,
                admission_receipt_digest=self.digest("admit:v1:" + field_name),
            )
        boot = store.admit_boot_binding(db, entity_generation=7, provenance_refs=["test:boot:g7"], **values)
        turn = store.bind_turn(
            db,
            entity_generation=7,
            causal_turn_id="ct:test:7",
            boot_binding_digest=boot["binding_digest"],
            task_text="exact task text",
            workspace_digest=self.digest("workspace:g7"),
            selected_workspace_slots=["slot:alpha"],
            contradiction_state="NONE",
            provenance_refs=["test:turn:g7"],
            required_zero_mode="WORKSPACE_BOUND",
        )
        return db, values, turn

    def test_resolves_exact_live_turn_and_versioned_payloads(self):
        db, values, turn = self.make_bound_turn()
        resolved = resolver.resolve_prepare_bundle(
            db,
            entity_generation=7,
            causal_turn_id="ct:test:7",
            task_text="exact task text",
            expected_turn_binding_digest=turn["binding_digest"],
        )
        self.assertTrue(resolved["ok"])
        self.assertEqual(resolved["turn_binding_digest"], turn["binding_digest"])
        self.assertEqual(set(resolved["objects"]), set(store.BOOT_FIELD_KINDS))
        for field_name, obj in resolved["objects"].items():
            self.assertEqual(obj["object_digest"], values[field_name])
            self.assertEqual(obj["object_version"], "v1")
            self.assertEqual(obj["admitted_generation"], 7)
            self.assertEqual(obj["payload"]["semantic_marker"], "v1:" + field_name)

    def test_same_digest_two_admitted_versions_fails_closed(self):
        db, values, turn = self.make_bound_turn()
        field_name = "jspace_profile_digest"
        object_kind = store.BOOT_FIELD_KINDS[field_name]
        digest = values[field_name]
        store.register_object(
            db,
            object_kind=object_kind,
            object_version="v2",
            object_digest=digest,
            digest_basis="EXTERNAL_BYTES",
            payload={"field": field_name, "semantic_marker": "v2:DIFFERENT_SEMANTICS", "classification": "TEST_FIXTURE_ONLY"},
            provenance_refs=["test:object:jspace:v2"],
        )
        store.admit_object(
            db,
            object_kind=object_kind,
            object_version="v2",
            object_digest=digest,
            entity_generation=7,
            admission_receipt_digest=self.digest("admit:v2:jspace"),
        )
        base = store.resolve_prepare_binding(db, entity_generation=7, causal_turn_id="ct:test:7", task_text="exact task text")
        self.assertEqual(base["turn_binding_digest"], turn["binding_digest"])
        with self.assertRaisesRegex(resolver.CognitionResolutionError, "COGNITION_OBJECT_VERSION_AMBIGUOUS:JSPACE_PROFILE"):
            resolver.resolve_prepare_bundle(
                db,
                entity_generation=7,
                causal_turn_id="ct:test:7",
                task_text="exact task text",
                expected_turn_binding_digest=turn["binding_digest"],
            )

    def test_unadmitted_second_version_does_not_create_ambiguity(self):
        db, values, turn = self.make_bound_turn()
        field_name = "policy_authority_digest"
        object_kind = store.BOOT_FIELD_KINDS[field_name]
        digest = values[field_name]
        store.register_object(
            db,
            object_kind=object_kind,
            object_version="v2",
            object_digest=digest,
            digest_basis="EXTERNAL_BYTES",
            payload={"semantic_marker": "registered-not-admitted"},
            provenance_refs=["test:policy:v2"],
        )
        resolved = resolver.resolve_prepare_bundle(
            db,
            entity_generation=7,
            causal_turn_id="ct:test:7",
            task_text="exact task text",
            expected_turn_binding_digest=turn["binding_digest"],
        )
        self.assertEqual(resolved["objects"][field_name]["object_version"], "v1")

    def test_expected_turn_binding_digest_is_a_hard_selector_fence(self):
        db, _, _ = self.make_bound_turn()
        with self.assertRaisesRegex(resolver.CognitionResolutionError, "TURN_BINDING_DIGEST_MISMATCH"):
            resolver.resolve_prepare_bundle(
                db,
                entity_generation=7,
                causal_turn_id="ct:test:7",
                task_text="exact task text",
                expected_turn_binding_digest=self.digest("different-turn-binding"),
            )

    def test_payload_row_tamper_fails_before_semantic_use(self):
        db, values, turn = self.make_bound_turn()
        digest = values["policy_authority_digest"]
        db.execute(
            """UPDATE mini_cognition_objects SET payload_json=?
                 WHERE object_kind='POLICY_AUTHORITY' AND object_version='v1' AND object_digest=?""",
            ('{"tampered":true}', digest),
        )
        with self.assertRaisesRegex(resolver.CognitionResolutionError, "OBJECT_PAYLOAD_DIGEST_MISMATCH"):
            resolver.resolve_prepare_bundle(
                db,
                entity_generation=7,
                causal_turn_id="ct:test:7",
                task_text="exact task text",
                expected_turn_binding_digest=turn["binding_digest"],
            )


if __name__ == "__main__":
    unittest.main()
