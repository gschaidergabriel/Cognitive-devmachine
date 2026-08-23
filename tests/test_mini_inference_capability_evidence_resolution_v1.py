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

import mini_inference_capability_binding_v1 as cap
import miniunifieddb_cognition_store_v1 as store


def h(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


class LocalCapabilityEvidenceTests(unittest.TestCase):
    def make_prepare(self):
        db = sqlite3.connect(":memory:")
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("CREATE TABLE entity_state(id INTEGER PRIMARY KEY, generation INTEGER NOT NULL)")
        db.execute("INSERT INTO entity_state(id,generation) VALUES(1,7)")
        store.install_schema(db)
        values: dict[str, str] = {}
        admission_receipts: dict[str, str] = {}
        for field_name, object_kind in store.BOOT_FIELD_KINDS.items():
            digest = h("bytes:" + field_name)
            receipt = h("admit:" + field_name)
            values[field_name] = digest
            admission_receipts[field_name] = receipt
            store.register_object(
                db,
                object_kind=object_kind,
                object_version="v1",
                object_digest=digest,
                digest_basis="EXTERNAL_BYTES",
                payload={
                    "field": field_name,
                    "classification": "TEST_FIXTURE_ONLY",
                    "semantic_marker": "v1:" + field_name,
                },
                provenance_refs=["test:object:" + field_name],
            )
            store.admit_object(
                db,
                object_kind=object_kind,
                object_version="v1",
                object_digest=digest,
                entity_generation=7,
                admission_receipt_digest=receipt,
            )
        boot = store.admit_boot_binding(
            db,
            entity_generation=7,
            provenance_refs=["test:boot:g7"],
            **values,
        )
        turn = store.bind_turn(
            db,
            entity_generation=7,
            causal_turn_id="ct:test:7",
            boot_binding_digest=boot["binding_digest"],
            task_text="exact task text",
            workspace_digest=h("workspace:g7"),
            selected_workspace_slots=["slot:alpha"],
            contradiction_state="NONE",
            provenance_refs=["test:turn:g7"],
            required_zero_mode="WORKSPACE_BOUND",
        )
        prepare = store.resolve_prepare_binding(
            db,
            entity_generation=7,
            causal_turn_id="ct:test:7",
            task_text="exact task text",
        )
        prepare["task_text"] = "exact task text"
        self.assertEqual(prepare["turn_binding_digest"], turn["binding_digest"])
        return db, prepare, admission_receipts

    @staticmethod
    def local_profile(receipt: str, *, evidence_kind: str = "BUNDLED_MANIFEST"):
        binding = cap.compile_binding(
            binding_id="bundled-08b-local-v1",
            engine_class="BUNDLED_LOCAL_08B",
            jspace_mode="FULL_LOCAL_LATENT",
            local_activation_access=True,
            external_hidden_state_claimed=False,
            provider_observability_claim_supported=True,
            adapter_version="bundled-local/v1",
            capability_evidence_kind=evidence_kind,
            capability_receipt_digest=receipt,
            provenance_refs=["profile:test", "policy:free-only"],
        )
        return {
            "schema": "clay-pipeline-profile/v2",
            "profile_id": "test",
            "inference": {"kind": "local_exec", "capability_binding": binding},
            "_runtime_profile_snapshot": {
                "profile_id": "test",
                "profile_hash": h("profile"),
            },
        }

    def test_random_valid_sha_cannot_authorize_full_local_latent(self):
        db, prepare, _ = self.make_prepare()
        with self.assertRaisesRegex(
            cap.CapabilityBindingError,
            "CAPABILITY_RECEIPT_NOT_CURRENT_BUNDLED_MANIFEST_ADMISSION",
        ):
            cap.resolve_bound_route(
                self.local_profile(h("random-but-valid-sha256")),
                prepare,
                expected_generation=7,
                db=db,
            )

    def test_current_manifest_admission_cross_binds_complete_ancestry(self):
        db, prepare, receipts = self.make_prepare()
        out = cap.resolve_bound_route(
            self.local_profile(receipts["bundled_manifest_digest"]),
            prepare,
            expected_generation=7,
            db=db,
        )
        self.assertTrue(out["ok"])
        self.assertEqual(out["target_engine_class"], "BUNDLED_LOCAL_08B")
        self.assertEqual(out["jspace_mode"], "FULL_LOCAL_LATENT")
        evidence = out["capability_evidence_resolution"]
        self.assertEqual(evidence["schema"], cap.CAPABILITY_EVIDENCE_SCHEMA)
        self.assertEqual(evidence["entity_generation"], 7)
        self.assertEqual(
            evidence["capability_receipt_digest"], receipts["bundled_manifest_digest"]
        )
        self.assertEqual(set(evidence["ancestry"]), set(cap.PREPARE_DIGEST_FIELDS))
        self.assertEqual(
            evidence["ancestry"]["policy_authority_digest"]["object_digest"],
            prepare["policy_authority_digest"],
        )
        self.assertEqual(
            out["capability_evidence_resolution_digest"], evidence["resolution_digest"]
        )

    def test_local_route_without_canonical_db_fails_closed(self):
        _, prepare, receipts = self.make_prepare()
        with self.assertRaisesRegex(
            cap.CapabilityBindingError, "LOCAL_CAPABILITY_EVIDENCE_DB_REQUIRED"
        ):
            cap.resolve_bound_route(
                self.local_profile(receipts["bundled_manifest_digest"]),
                prepare,
                expected_generation=7,
            )

    def test_runtime_probe_cannot_use_untyped_digest(self):
        db, prepare, _ = self.make_prepare()
        with self.assertRaisesRegex(
            cap.CapabilityBindingError, "RUNTIME_PROBE_TYPED_EVIDENCE_REQUIRED"
        ):
            cap.resolve_bound_route(
                self.local_profile(h("opaque-probe-receipt"), evidence_kind="RUNTIME_PROBE"),
                prepare,
                expected_generation=7,
                db=db,
            )


if __name__ == "__main__":
    unittest.main()
