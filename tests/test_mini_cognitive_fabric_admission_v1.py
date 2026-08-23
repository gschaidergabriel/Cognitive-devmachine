#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import mini_entity_cognitive_fabric_admission_v1 as admission
import miniunifieddb_cognition_store_v1 as store


def digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


class FakeRuntime:
    def __init__(self, root: Path):
        self.root = root
        self.provider_override = lambda request: {"ok": True}
        self._cognitive_admissions: dict[str, dict] = {}

    def _db(self, value: str) -> sqlite3.Connection:
        return sqlite3.connect(value)

    def _read_only_db(self, value: str) -> sqlite3.Connection:
        return sqlite3.connect(f"file:{Path(value).as_posix()}?mode=ro", uri=True)

    def _pipeline_build_prompt(self, p: dict) -> dict:
        compiled = p["data"]
        return {
            "ok": True,
            "system": "SYSTEM:" + compiled["canonical_state_hash"],
            "user": "USER:" + compiled["packet_hash"],
        }


class CognitiveBindingIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.entity_db = self.root / "entity.db"
        db = sqlite3.connect(self.entity_db)
        db.execute(
            "CREATE TABLE entity_state(id INTEGER PRIMARY KEY,generation INTEGER NOT NULL)"
        )
        db.execute("INSERT INTO entity_state(id,generation) VALUES(1,0)")
        db.commit()
        db.execute("BEGIN IMMEDIATE")
        store.install_schema(db)
        self.assertTrue(db.in_transaction)
        db.commit()
        db.close()

    def tearDown(self):
        self.tmp.cleanup()

    def _admit_boot(self) -> str:
        db = sqlite3.connect(self.entity_db)
        values = {}
        for field_name, object_kind in store.BOOT_FIELD_KINDS.items():
            value = digest("object:" + field_name)
            values[field_name] = value
            store.register_object(
                db,
                object_kind=object_kind,
                object_version="test-v1",
                object_digest=value,
                digest_basis="EXTERNAL_BYTES",
                payload={"fixture": field_name, "authority": "TEST_ONLY"},
                provenance_refs=["test:" + field_name],
            )
            store.admit_object(
                db,
                object_kind=object_kind,
                object_version="test-v1",
                object_digest=value,
                entity_generation=0,
                admission_receipt_digest=digest("receipt:" + field_name),
            )
        boot = store.admit_boot_binding(
            db,
            entity_generation=0,
            provenance_refs=["test:boot"],
            **values,
        )
        db.commit()
        db.close()
        return boot["binding_digest"]

    def _runtime_material(self):
        runtime = FakeRuntime(self.root)
        profile = {
            "inference": {"kind": "mock", "model": "fixture"},
            "_runtime_profile_snapshot": {
                "profile_id": "fixture-profile",
                "profile_hash": digest("fixture-profile"),
            },
        }
        previous = {"generation": 0}
        compiled = {
            "canonical_state_hash": digest("canonical"),
            "packet_hash": digest("packet"),
        }
        prompt = runtime._pipeline_build_prompt(
            {"profile": profile, "previous": previous, "data": compiled}
        )
        return runtime, profile, previous, compiled, prompt

    def _bind_turn(self):
        boot_digest = self._admit_boot()
        runtime, profile, previous, compiled, prompt = self._runtime_material()
        turn = admission.derive_turn_identity(profile, previous, compiled, prompt)
        db = sqlite3.connect(self.entity_db)
        bound = store.bind_turn(
            db,
            entity_generation=0,
            causal_turn_id=turn["causal_turn_id"],
            boot_binding_digest=boot_digest,
            task_text=turn["task_text"],
            workspace_digest=digest("workspace"),
            selected_workspace_slots=["slot:falsifier"],
            contradiction_state="UNRESOLVED",
            provenance_refs=["test:turn"],
            required_zero_mode="DISCRIMINATE",
        )
        db.commit()
        db.close()
        return runtime, profile, previous, compiled, prompt, bound

    def test_transactional_schema_install_does_not_implicitly_commit(self):
        db = sqlite3.connect(":memory:")
        db.execute(
            "CREATE TABLE entity_state(id INTEGER PRIMARY KEY,generation INTEGER NOT NULL)"
        )
        db.execute("INSERT INTO entity_state VALUES(1,0)")
        db.commit()
        db.execute("BEGIN IMMEDIATE")
        store.install_schema(db)
        self.assertTrue(db.in_transaction)
        db.rollback()
        names = {
            row[0]
            for row in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'mini_cognition_%'"
            )
        }
        self.assertEqual(names, set())
        db.close()

    def test_unusual_workspace_row_tamper_with_old_digest_fails_closed(self):
        _, profile, previous, compiled, prompt, _ = self._bind_turn()
        turn = admission.derive_turn_identity(profile, previous, compiled, prompt)
        db = sqlite3.connect(self.entity_db)
        db.execute(
            """UPDATE mini_cognition_turn_bindings
                  SET workspace_digest=?
                WHERE entity_generation=0 AND causal_turn_id=?""",
            (digest("workspace-tampered"), turn["causal_turn_id"]),
        )
        db.commit()
        with self.assertRaisesRegex(
            store.CognitionStoreError, "TURN_BINDING_DIGEST_MISMATCH"
        ):
            store.resolve_prepare_binding(
                db,
                entity_generation=0,
                causal_turn_id=turn["causal_turn_id"],
                task_text=turn["task_text"],
            )
        db.close()

    def test_admission_binds_exact_context_and_is_single_use(self):
        runtime, profile, previous, compiled, prompt, _ = self._bind_turn()
        admitted = admission.admit(
            runtime,
            {
                "entity_db": str(self.entity_db),
                "profile": profile,
                "previous": previous,
                "data": {"compiled": compiled, "prompt": prompt},
            },
        )
        request = {
            "inference": admitted["inference"],
            "system": admitted["system"],
            "user": admitted["user"],
            "inference_packet_digest": admitted["inference_packet_digest"],
            "cognitive_fabric_receipt_digest": admitted[
                "cognitive_fabric_receipt_digest"
            ],
        }
        self.assertEqual(
            admission.require_inference_admission(runtime, request)["causal_turn_id"],
            admitted["causal_turn_id"],
        )
        with self.assertRaisesRegex(
            admission.CognitiveFabricAdmissionError,
            "COGNITIVE_ADMISSION_ALREADY_USED",
        ):
            admission.require_inference_admission(runtime, request)

    def test_prompt_context_mutation_cannot_reuse_registered_admission(self):
        runtime, profile, previous, compiled, prompt, _ = self._bind_turn()
        admitted = admission.admit(
            runtime,
            {
                "entity_db": str(self.entity_db),
                "profile": profile,
                "previous": previous,
                "data": {"compiled": compiled, "prompt": prompt},
            },
        )
        request = {
            "inference": admitted["inference"],
            "system": admitted["system"],
            "user": admitted["user"] + " MUTATED",
            "inference_packet_digest": admitted["inference_packet_digest"],
            "cognitive_fabric_receipt_digest": admitted[
                "cognitive_fabric_receipt_digest"
            ],
        }
        with self.assertRaisesRegex(
            admission.CognitiveFabricAdmissionError,
            "DOWNSTREAM_USER_CONTEXT_MISMATCH",
        ):
            admission.require_inference_admission(runtime, request)

    def test_commit_rechecks_live_binding_integrity(self):
        runtime, profile, previous, compiled, prompt, _ = self._bind_turn()
        admitted = admission.admit(
            runtime,
            {
                "entity_db": str(self.entity_db),
                "profile": profile,
                "previous": previous,
                "data": {"compiled": compiled, "prompt": prompt},
            },
        )
        request = {
            "inference": admitted["inference"],
            "system": admitted["system"],
            "user": admitted["user"],
            "inference_packet_digest": admitted["inference_packet_digest"],
            "cognitive_fabric_receipt_digest": admitted[
                "cognitive_fabric_receipt_digest"
            ],
        }
        admission.require_inference_admission(runtime, request)
        generated = admission.attach_generated(
            runtime,
            request,
            {"ok": True, "payload": {"candidate": True}, "provider_kind": "mock"},
        )
        envelope = {
            "profile": profile,
            "previous": previous,
            "data": {
                "compiled": compiled,
                "generated": generated,
                "cognitive_fabric": admitted,
            },
        }
        admission.validate_gate(runtime, envelope)

        db = sqlite3.connect(self.entity_db)
        admission.validate_commit(runtime, envelope, db)
        db.execute(
            "UPDATE mini_cognition_turn_bindings SET workspace_digest=?",
            (digest("late-tamper"),),
        )
        db.commit()
        with self.assertRaisesRegex(
            store.CognitionStoreError, "TURN_BINDING_DIGEST_MISMATCH"
        ):
            admission.validate_commit(runtime, envelope, db)
        db.close()


if __name__ == "__main__":
    unittest.main()
