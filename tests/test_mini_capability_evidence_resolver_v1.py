from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import mini_capability_evidence_resolver_v1 as resolver


def d(label: str) -> str:
    return hashlib.sha256(label.encode()).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


class CapabilityEvidenceResolverTests(unittest.TestCase):
    def db(self):
        db = sqlite3.connect(":memory:")
        db.executescript(
            """
            CREATE TABLE entity_state(id INTEGER PRIMARY KEY, generation INTEGER NOT NULL);
            INSERT INTO entity_state VALUES(1,7);
            CREATE TABLE mini_cognition_objects(
              object_kind TEXT NOT NULL, object_version TEXT NOT NULL, object_digest TEXT NOT NULL,
              digest_basis TEXT NOT NULL, payload_json TEXT NOT NULL, payload_digest TEXT NOT NULL,
              provenance_refs_json TEXT NOT NULL, created_at TEXT NOT NULL,
              PRIMARY KEY(object_kind,object_version,object_digest));
            CREATE TABLE mini_cognition_object_admissions(
              object_kind TEXT NOT NULL, object_version TEXT NOT NULL, object_digest TEXT NOT NULL,
              admitted_generation INTEGER NOT NULL, admission_receipt_digest TEXT NOT NULL,
              admitted_at TEXT NOT NULL);
            CREATE TABLE mini_cognition_boot_bindings(
              binding_digest TEXT PRIMARY KEY, schema TEXT NOT NULL, entity_generation INTEGER NOT NULL,
              zero_identity_digest TEXT NOT NULL, grf_digest TEXT NOT NULL,
              hyperposition_digest TEXT NOT NULL, bundled_manifest_digest TEXT NOT NULL,
              local_model_digest TEXT NOT NULL, tokenizer_digest TEXT NOT NULL,
              jspace_profile_digest TEXT NOT NULL, jacobian_lens_digest TEXT NOT NULL,
              workspace_calibration_digest TEXT NOT NULL, boot_source_lock_digest TEXT NOT NULL,
              policy_authority_digest TEXT NOT NULL, provenance_refs_json TEXT NOT NULL,
              created_at TEXT NOT NULL);
            """
        )
        return db

    def fixture(self, *, evidence_kind="BUNDLED_MANIFEST", mode="FULL_LOCAL_LATENT"):
        db = self.db()
        payload = {"schema": "BUNDLED_MANIFEST/test", "model": "m"}
        payload_json = canonical(payload)
        manifest_digest = hashlib.sha256(payload_json.encode()).hexdigest()
        admission = d("manifest-admission")
        db.execute(
            "INSERT INTO mini_cognition_objects VALUES(?,?,?,?,?,?,?,?)",
            ("BUNDLED_MANIFEST", "v1", manifest_digest, "CANONICAL_JSON",
             payload_json, manifest_digest, canonical(["fixture"]), "now"),
        )
        db.execute(
            "INSERT INTO mini_cognition_object_admissions VALUES(?,?,?,?,?,?)",
            ("BUNDLED_MANIFEST", "v1", manifest_digest, 7, admission, "now"),
        )
        fields = {
            "zero_identity_digest": d("zero"),
            "grf_digest": d("grf"),
            "hyperposition_digest": d("hp"),
            "bundled_manifest_digest": manifest_digest,
            "local_model_digest": d("model"),
            "tokenizer_digest": d("tokenizer"),
            "jspace_profile_digest": d("jspace"),
            "jacobian_lens_digest": d("lens"),
            "workspace_calibration_digest": d("cal"),
            "boot_source_lock_digest": d("lock"),
            "policy_authority_digest": d("policy"),
        }
        boot_material = {
            "schema": "MINIUNIFIEDDB_COGNITION_BOOT_BINDING/v1",
            "entity_generation": 7,
            **fields,
            "provenance_refs": ["fixture:boot"],
        }
        boot_digest = hashlib.sha256(canonical(boot_material).encode()).hexdigest()
        db.execute(
            "INSERT INTO mini_cognition_boot_bindings VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (boot_digest, boot_material["schema"], 7, *(fields[name] for name in resolver._BOOT_FIELDS),
             canonical(["fixture:boot"]), "now"),
        )
        prepare = {
            "ok": True,
            "entity_generation": 7,
            "causal_turn_id": "turn-7",
            "turn_binding_digest": d("turn"),
            "boot_binding_digest": boot_digest,
            "workspace_digest": d("workspace"),
            **fields,
        }
        route = {
            "ok": True,
            "entity_generation": 7,
            "causal_turn_id": "turn-7",
            "turn_binding_digest": prepare["turn_binding_digest"],
            "boot_binding_digest": boot_digest,
            "workspace_digest": prepare["workspace_digest"],
            "cognition": dict(fields),
            "target_engine_class": "BUNDLED_LOCAL_08B" if mode in resolver.LOCAL_MODES else "CLAUDE_CODE",
            "jspace_mode": mode,
            "capability_evidence_kind": evidence_kind,
            "capability_receipt_digest": admission,
            "capability_binding_digest": d("binding"),
            "route_digest": d("route"),
            "local_activation_access": mode in resolver.LOCAL_MODES,
        }
        return db, prepare, route, admission, manifest_digest

    def test_exact_manifest_admission_authorizes_local_mode(self):
        db, prepare, route, _, manifest = self.fixture()
        out = resolver.resolve_bound_evidence(db, route=route, prepare=prepare, expected_generation=7)
        self.assertTrue(out["ok"])
        self.assertTrue(out["local_latent_authorized"])
        self.assertEqual(out["resolved_object"]["object_digest"], manifest)

    def test_random_valid_sha_cannot_authorize_bundled_manifest(self):
        db, prepare, route, _, _ = self.fixture()
        route["capability_receipt_digest"] = d("random-valid-but-unbound")
        with self.assertRaisesRegex(resolver.CapabilityEvidenceError, "CAPABILITY_RECEIPT_REFERENT_MISMATCH"):
            resolver.resolve_bound_evidence(db, route=route, prepare=prepare, expected_generation=7)

    def test_stale_generation_rejected(self):
        db, prepare, route, _, _ = self.fixture()
        db.execute("UPDATE entity_state SET generation=8 WHERE id=1")
        with self.assertRaisesRegex(resolver.CapabilityEvidenceError, "STALE_GENERATION"):
            resolver.resolve_bound_evidence(db, route=route, prepare=prepare, expected_generation=7)

    def test_boot_manifest_drift_rejected(self):
        db, prepare, route, _, _ = self.fixture()
        prepare["bundled_manifest_digest"] = d("other-manifest")
        with self.assertRaisesRegex(resolver.CapabilityEvidenceError, "BOOT_PREPARE_MISMATCH"):
            resolver.resolve_bound_evidence(db, route=route, prepare=prepare, expected_generation=7)

    def test_same_digest_multi_version_admission_is_ambiguous(self):
        db, prepare, route, admission, manifest = self.fixture()
        row = db.execute(
            "SELECT payload_json,payload_digest,provenance_refs_json FROM mini_cognition_objects "
            "WHERE object_kind='BUNDLED_MANIFEST' AND object_version='v1'"
        ).fetchone()
        db.execute(
            "INSERT INTO mini_cognition_objects VALUES(?,?,?,?,?,?,?,?)",
            ("BUNDLED_MANIFEST", "v2", manifest, "CANONICAL_JSON", row[0], row[1], row[2], "now"),
        )
        db.execute(
            "INSERT INTO mini_cognition_object_admissions VALUES(?,?,?,?,?,?)",
            ("BUNDLED_MANIFEST", "v2", manifest, 7, admission, "now"),
        )
        with self.assertRaisesRegex(resolver.CapabilityEvidenceError, "CAPABILITY_OBJECT_VERSION_AMBIGUOUS"):
            resolver.resolve_bound_evidence(db, route=route, prepare=prepare, expected_generation=7)

    def test_runtime_probe_local_mode_stays_blocked_without_typed_receipt(self):
        db, prepare, route, _, _ = self.fixture(evidence_kind="RUNTIME_PROBE")
        with self.assertRaisesRegex(resolver.CapabilityEvidenceError, "TYPED_RUNTIME_PROBE_RECEIPT_UNAVAILABLE"):
            resolver.resolve_bound_evidence(db, route=route, prepare=prepare, expected_generation=7)

    def test_external_mode_requires_no_local_capability_referent(self):
        db, prepare, route, _, _ = self.fixture(evidence_kind="STATIC_CONSERVATIVE", mode="COMPILED_EXTERNAL")
        route["capability_receipt_digest"] = d("static-profile-receipt")
        out = resolver.resolve_bound_evidence(db, route=route, prepare=prepare, expected_generation=7)
        self.assertTrue(out["ok"])
        self.assertFalse(out["local_latent_authorized"])
        self.assertEqual(out["status"], "LOCAL_CAPABILITY_NOT_REQUIRED")

    def test_manifest_payload_mutation_rejected(self):
        db, prepare, route, _, _ = self.fixture()
        db.execute(
            "UPDATE mini_cognition_objects SET payload_json=? WHERE object_kind='BUNDLED_MANIFEST'",
            (canonical({"schema": "BUNDLED_MANIFEST/test", "model": "mutated"}),),
        )
        with self.assertRaisesRegex(resolver.CapabilityEvidenceError, "BUNDLED_MANIFEST_PAYLOAD_DIGEST_MISMATCH"):
            resolver.resolve_bound_evidence(db, route=route, prepare=prepare, expected_generation=7)


if __name__ == "__main__":
    unittest.main()
