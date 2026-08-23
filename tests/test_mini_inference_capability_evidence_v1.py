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

import mini_inference_capability_evidence_v1 as sut


def h(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


FIELDS = (
    "zero_identity_digest",
    "grf_digest",
    "hyperposition_digest",
    "bundled_manifest_digest",
    "local_model_digest",
    "tokenizer_digest",
    "jspace_profile_digest",
    "jacobian_lens_digest",
    "workspace_calibration_digest",
    "boot_source_lock_digest",
    "policy_authority_digest",
)


def prepare() -> dict:
    out = {
        "ok": True,
        "entity_generation": 7,
        "causal_turn_id": "turn-7-a",
        "task_text": "measure first",
        "turn_binding_digest": h("turn-binding"),
        "boot_binding_digest": h("boot-binding"),
    }
    for field in FIELDS:
        out[field] = h(field)
    return out


def capability(*, receipt: str | None = None, kind: str = "BUNDLED_MANIFEST") -> dict:
    return {
        "binding_digest": h("capability-binding"),
        "capability_evidence_kind": kind,
        "capability_receipt_digest": receipt or h("manifest-admission"),
    }


class SemanticResolver:
    @staticmethod
    def resolve_prepare_bundle(
        db,
        *,
        entity_generation,
        causal_turn_id,
        task_text,
        expected_turn_binding_digest,
    ):
        p = prepare()
        objects = {
            field: {
                "object_digest": p[field],
                "admitted_generation": entity_generation,
                "admission_receipt_digest": (
                    h("manifest-admission") if field == "bundled_manifest_digest" else h("receipt:" + field)
                ),
            }
            for field in FIELDS
        }
        return {
            "ok": True,
            "entity_generation": entity_generation,
            "causal_turn_id": causal_turn_id,
            "turn_binding_digest": expected_turn_binding_digest,
            "boot_binding_digest": p["boot_binding_digest"],
            "objects": objects,
            "authority": {
                "durable_state": "MiniUnifiedDB",
                "routing_only": True,
                "candidate_configuration_only": True,
                "direct_truth_authority": False,
                "direct_effect_authority": False,
            },
        }


class CapabilityEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")

    def tearDown(self):
        self.db.close()

    def resolve(self, *, cap=None, prep=None, resolver=SemanticResolver):
        return sut.resolve_capability_evidence(
            self.db,
            capability=cap or capability(),
            prepare=prep or prepare(),
            expected_generation=7,
            semantic_resolver=resolver,
        )

    def test_manifest_receipt_binds_exact_live_cognition_ancestry(self):
        out = self.resolve()
        self.assertTrue(out["ok"])
        self.assertEqual(out["schema"], sut.SCHEMA)
        self.assertEqual(out["capability_receipt_digest"], h("manifest-admission"))
        self.assertEqual(out["cognition"]["local_model_digest"], h("local_model_digest"))
        self.assertEqual(len(out["evidence_binding_digest"]), 64)
        self.assertFalse(out["direct_truth_authority"])
        self.assertFalse(out["direct_effect_authority"])

    def test_random_valid_sha256_labeled_manifest_cannot_authorize_local_route(self):
        # The one unusual discriminator for this GO: a syntactically perfect but causally
        # unrelated receipt digest must not become local-latent authority merely by label.
        with self.assertRaisesRegex(
            sut.CapabilityEvidenceError,
            "CAPABILITY_RECEIPT_NOT_CURRENT_BUNDLED_MANIFEST_ADMISSION",
        ):
            self.resolve(cap=capability(receipt=h("random-but-valid-sha256")))

    def test_runtime_probe_stays_closed_without_typed_miniunifieddb_receipt(self):
        with self.assertRaisesRegex(
            sut.CapabilityEvidenceError,
            "RUNTIME_PROBE_TYPED_EVIDENCE_NOT_ADMITTED",
        ):
            self.resolve(cap=capability(kind="RUNTIME_PROBE"))

    def test_object_digest_drift_fails_closed(self):
        class DriftResolver(SemanticResolver):
            @staticmethod
            def resolve_prepare_bundle(*args, **kwargs):
                out = SemanticResolver.resolve_prepare_bundle(*args, **kwargs)
                out["objects"]["tokenizer_digest"]["object_digest"] = h("other-tokenizer")
                return out

        with self.assertRaisesRegex(
            sut.CapabilityEvidenceError,
            "SEMANTIC_OBJECT_DIGEST_DRIFT:tokenizer_digest",
        ):
            self.resolve(resolver=DriftResolver)

    def test_stale_prepare_generation_fails_closed(self):
        p = prepare()
        p["entity_generation"] = 6
        with self.assertRaisesRegex(sut.CapabilityEvidenceError, "STALE_GENERATION"):
            self.resolve(prep=p)

    def test_semantic_authority_escalation_fails_closed(self):
        class BadAuthorityResolver(SemanticResolver):
            @staticmethod
            def resolve_prepare_bundle(*args, **kwargs):
                out = SemanticResolver.resolve_prepare_bundle(*args, **kwargs)
                out["authority"]["direct_truth_authority"] = True
                return out

        with self.assertRaisesRegex(
            sut.CapabilityEvidenceError,
            "SEMANTIC_BUNDLE_AUTHORITY_ESCALATION",
        ):
            self.resolve(resolver=BadAuthorityResolver)


if __name__ == "__main__":
    unittest.main()
