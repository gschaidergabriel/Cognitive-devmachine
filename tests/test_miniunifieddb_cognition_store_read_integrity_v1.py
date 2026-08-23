from __future__ import annotations

import hashlib
import json
import sqlite3
import unittest

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import miniunifieddb_cognition_store_v1 as store


def h(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


BOOT_PAYLOADS = {
    "zero_identity_digest": ("ZERO_IDENTITY", {"identity": "ZERO"}),
    "grf_digest": ("GRF", {"framework": "GRF"}),
    "hyperposition_digest": ("HYPERPOSITION", {"mode": "set-valued"}),
    "bundled_manifest_digest": ("BUNDLED_MANIFEST", {"model": "fixture"}),
    "local_model_digest": ("LOCAL_MODEL_CHECKPOINT", {"checkpoint": "fixture"}),
    "tokenizer_digest": ("TOKENIZER", {"tokenizer": "fixture"}),
    "jspace_profile_digest": ("JSPACE_PROFILE", {"profile": "fixture"}),
    "jacobian_lens_digest": ("JACOBIAN_LENS_PROFILE", {"lens": "fixture"}),
    "workspace_calibration_digest": ("WORKSPACE_CALIBRATION", {"workspace": "fixture"}),
    "boot_source_lock_digest": ("BOOT_SOURCE_LOCK", {"source": "fixture"}),
    "policy_authority_digest": ("POLICY_AUTHORITY", {"policy": "FREE_ONLY"}),
}


class CognitionStoreReadIntegrityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = sqlite3.connect(":memory:")
        self.db.execute("CREATE TABLE entity_state(id INTEGER PRIMARY KEY, generation INTEGER NOT NULL)")
        self.db.execute("INSERT INTO entity_state VALUES(1,7)")
        store.install_schema(self.db)
        self.boot_fields: dict[str, str] = {}
        for index, (field, (kind, payload)) in enumerate(BOOT_PAYLOADS.items()):
            digest = store.sha256_obj(payload)
            self.boot_fields[field] = digest
            store.register_object(
                self.db,
                object_kind=kind,
                object_version="fixture-v1",
                object_digest=digest,
                digest_basis="CANONICAL_JSON",
                payload=payload,
                provenance_refs=[f"fixture:{kind}"],
            )
            store.admit_object(
                self.db,
                object_kind=kind,
                object_version="fixture-v1",
                object_digest=digest,
                entity_generation=7,
                admission_receipt_digest=h(f"admission-{index}-{kind}"),
            )
        boot = store.admit_boot_binding(
            self.db,
            entity_generation=7,
            provenance_refs=["fixture:boot"],
            **self.boot_fields,
        )
        self.boot_digest = boot["binding_digest"]
        turn = store.bind_turn(
            self.db,
            entity_generation=7,
            causal_turn_id="turn-7",
            boot_binding_digest=self.boot_digest,
            task_text="fixture task",
            workspace_digest=h("workspace"),
            selected_workspace_slots=["slot-a"],
            contradiction_state="UNKNOWN",
            provenance_refs=["fixture:turn"],
            required_zero_mode="PLAIN_COMPATIBILITY",
        )
        self.turn_digest = turn["binding_digest"]
        self.db.commit()

    def tearDown(self) -> None:
        self.db.close()

    def resolve(self):
        return store.resolve_prepare_binding(
            self.db,
            entity_generation=7,
            causal_turn_id="turn-7",
            task_text="fixture task",
        )

    def test_valid_binding_is_reconstructed_exactly(self):
        result = self.resolve()
        self.assertEqual(result["boot_binding_digest"], self.boot_digest)
        self.assertEqual(result["turn_binding_digest"], self.turn_digest)
        self.assertEqual(result["workspace_digest"], h("workspace"))

    def test_workspace_digest_tamper_fails_closed(self):
        self.db.execute(
            "UPDATE mini_cognition_turn_bindings SET workspace_digest=? WHERE entity_generation=7",
            (h("tampered-workspace"),),
        )
        self.db.commit()
        with self.assertRaisesRegex(store.CognitionStoreError, "TURN_BINDING_DIGEST_MISMATCH"):
            self.resolve()

    def test_zero_identity_tamper_fails_closed(self):
        self.db.execute(
            "UPDATE mini_cognition_boot_bindings SET zero_identity_digest=? WHERE entity_generation=7",
            (h("tampered-zero"),),
        )
        self.db.commit()
        with self.assertRaisesRegex(store.CognitionStoreError, "BOOT_BINDING_DIGEST_MISMATCH"):
            self.resolve()

    def test_malformed_slot_json_fails_before_binding_use(self):
        self.db.execute(
            "UPDATE mini_cognition_turn_bindings SET selected_workspace_slots_json='[bad' WHERE entity_generation=7"
        )
        self.db.commit()
        with self.assertRaisesRegex(store.CognitionStoreError, "selected_workspace_slots:MALFORMED_JSON"):
            self.resolve()

    def test_task_mismatch_remains_fail_closed(self):
        with self.assertRaisesRegex(store.CognitionStoreError, "TURN_TASK_BINDING_MISMATCH"):
            store.resolve_prepare_binding(
                self.db,
                entity_generation=7,
                causal_turn_id="turn-7",
                task_text="different task",
            )


if __name__ == "__main__":
    unittest.main()
