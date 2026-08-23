#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import pipeline_cognitive_fabric_admission_v1 as admission


def digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


BOOT_FIELDS = (
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


def make_prepare() -> dict:
    task = "exact semantic turn"
    value = {
        "ok": True,
        "entity_generation": 7,
        "causal_turn_id": "ct:test:g7:a1",
        "task_text": task,
        "task_sha256": hashlib.sha256(task.encode("utf-8")).hexdigest(),
        "turn_binding_digest": digest("turn-binding"),
        "boot_binding_digest": digest("boot-binding"),
        "workspace_digest": digest("workspace"),
        "activation_digest": digest("activation"),
        "selected_workspace_slots": ["slot:alpha"],
        "contradiction_state": "NONE",
        "required_zero_mode": "WORKSPACE_BOUND",
        "turn_provenance_refs": ["test:turn"],
        "boot_provenance_refs": ["test:boot"],
        "activation_provenance_refs": ["test:activation"],
        "authority": {
            "durable_state": "MiniUnifiedDB",
            "candidate_only": True,
            "direct_truth_authority": False,
            "direct_effect_authority": False,
        },
    }
    for field in BOOT_FIELDS:
        value[field] = digest("object:" + field)
    return value


class ActiveTurnStub:
    prepare = make_prepare()

    @classmethod
    def resolve_active_prepare(cls, db, *, entity_generation, expected_activation_digest=None):
        assert entity_generation == cls.prepare["entity_generation"]
        if expected_activation_digest is not None:
            assert expected_activation_digest == cls.prepare["activation_digest"]
        return dict(cls.prepare)


class SemanticStub:
    version_overrides: dict[str, str] = {}
    digest_overrides: dict[str, str] = {}
    turn_binding_override: str | None = None

    @classmethod
    def reset(cls):
        cls.version_overrides = {}
        cls.digest_overrides = {}
        cls.turn_binding_override = None

    @classmethod
    def resolve_prepare_bundle(
        cls,
        db,
        *,
        entity_generation,
        causal_turn_id,
        task_text,
        expected_turn_binding_digest=None,
    ):
        p = ActiveTurnStub.prepare
        assert entity_generation == 7
        assert causal_turn_id == p["causal_turn_id"]
        assert task_text == p["task_text"]
        assert expected_turn_binding_digest == p["turn_binding_digest"]
        objects = {}
        for field in BOOT_FIELDS:
            objects[field] = {
                "object_kind": "TEST_" + field.upper(),
                "object_version": cls.version_overrides.get(field, "v1"),
                "object_digest": cls.digest_overrides.get(field, p[field]),
                "payload_digest": digest("payload:" + field + ":" + cls.version_overrides.get(field, "v1")),
                "admission_receipt_digest": digest("object-admission:" + field + ":" + cls.version_overrides.get(field, "v1")),
                "admitted_generation": 7,
            }
        return {
            "ok": True,
            "schema": "MINIUNIFIEDDB_COGNITION_SEMANTIC_RESOLUTION/v1",
            "entity_generation": 7,
            "causal_turn_id": p["causal_turn_id"],
            "turn_binding_digest": cls.turn_binding_override or p["turn_binding_digest"],
            "boot_binding_digest": p["boot_binding_digest"],
            "workspace_digest": p["workspace_digest"],
            "objects": objects,
        }


class CapabilityStub:
    @staticmethod
    def resolve_bound_route(profile, prepare, *, expected_generation):
        return {
            "ok": True,
            "authority": "ROUTING_ONLY_BOUND_TO_CANONICAL_PREPARE",
            "route_digest": digest("route"),
            "entity_generation": expected_generation,
            "causal_turn_id": prepare["causal_turn_id"],
            "turn_binding_digest": prepare["turn_binding_digest"],
            "boot_binding_digest": prepare["boot_binding_digest"],
            "workspace_digest": prepare["workspace_digest"],
            "target_engine_class": "BUNDLED_LOCAL_08B",
            "ucf_engine_class": "local_08b",
            "jspace_mode": "LOCAL_OBSERVE_ONLY",
            "capability_binding_digest": digest("cap-binding"),
            "capability_receipt_digest": digest("cap-receipt"),
            "profile_id": "test-profile",
            "profile_hash": digest("profile"),
            "capability_evidence_kind": "BUNDLED_MANIFEST",
            "adapter_version": "test-adapter/v1",
        }


class CapsuleStub:
    @staticmethod
    def compile_workspace_capsule(**kwargs):
        return {
            "schema": "ZERO_WORKSPACE_CAPSULE/v1",
            "mode": "WORKSPACE_BOUND",
            "capsule_digest": digest("capsule"),
        }


class PacketStub:
    @staticmethod
    def compile_packet(capsule, **kwargs):
        return {
            "schema": "ZERO_INFERENCE_PACKET/v2",
            "packet_digest": digest("inference-packet"),
            "admitted_context_digest": digest("admitted-context"),
        }


def call_admission():
    compiled = {
        "canonical_state_hash": digest("canonical"),
        "packet_hash": digest("source-packet"),
    }
    prompt = {
        "system": "system",
        "user": json.dumps(
            {
                "CANONICAL_STATE_HASH": compiled["canonical_state_hash"],
                "PACKET_HASH": compiled["packet_hash"],
            },
            sort_keys=True,
        ),
    }
    p = ActiveTurnStub.prepare
    invocation = {
        "expected_generation": 7,
        "causal_turn_id": p["causal_turn_id"],
        "task_text": p["task_text"],
        "turn_binding_digest": p["turn_binding_digest"],
    }
    profile = {"inference": {"kind": "mock", "model": "candidate"}}
    return admission.build_pre_inference_admission(
        object(),
        entity_generation=7,
        invocation=invocation,
        compiled=compiled,
        prompt=prompt,
        profile=profile,
        active_turn_module=ActiveTurnStub,
        semantic_resolution_module=SemanticStub,
        capability_module=CapabilityStub,
        capsule_module=CapsuleStub,
        packet_module=PacketStub,
        origin="test:semantic-binding",
    )


class CognitiveFabricSemanticBindingTests(unittest.TestCase):
    def setUp(self):
        SemanticStub.reset()

    def test_exact_versions_are_bound_into_admission_receipt(self):
        result = call_admission()
        self.assertTrue(result["ok"])
        self.assertEqual(
            result["semantic_binding_digest"],
            result["admission_receipt"]["semantic_binding_digest"],
        )
        self.assertEqual(result["semantic_binding"]["objects"]["jspace_profile_digest"]["object_version"], "v1")
        self.assertEqual(result["admission_receipt"]["authority"], "CANDIDATE_INFERENCE_ONLY")
        self.assertFalse(result["admission_receipt"]["real_effect_executed"])

    def test_version_change_changes_admission_identity_without_changing_packet_identity(self):
        baseline = call_admission()
        SemanticStub.version_overrides = {"jspace_profile_digest": "v2"}
        changed = call_admission()
        self.assertEqual(baseline["inference_packet_digest"], changed["inference_packet_digest"])
        self.assertNotEqual(baseline["semantic_binding_digest"], changed["semantic_binding_digest"])
        self.assertNotEqual(
            baseline["cognitive_fabric_receipt_digest"],
            changed["cognitive_fabric_receipt_digest"],
        )

    def test_semantic_object_digest_drift_fails_closed(self):
        SemanticStub.digest_overrides = {"policy_authority_digest": digest("wrong-policy")}
        with self.assertRaisesRegex(
            admission.CognitiveFabricAdmissionError,
            "SEMANTIC_OBJECT_DIGEST_DRIFT:policy_authority_digest",
        ):
            call_admission()

    def test_semantic_turn_binding_drift_fails_closed(self):
        SemanticStub.turn_binding_override = digest("other-turn-binding")
        with self.assertRaisesRegex(
            admission.CognitiveFabricAdmissionError,
            "SEMANTIC_TURN_BINDING_DRIFT",
        ):
            call_admission()

    def test_ambiguous_version_error_stops_before_capability_and_packet(self):
        class AmbiguousSemantic:
            @staticmethod
            def resolve_prepare_bundle(*args, **kwargs):
                raise ValueError("COGNITION_OBJECT_VERSION_AMBIGUOUS:JSPACE_PROFILE")

        compiled = {
            "canonical_state_hash": digest("canonical"),
            "packet_hash": digest("source-packet"),
        }
        prompt = {
            "system": "system",
            "user": json.dumps(
                {
                    "CANONICAL_STATE_HASH": compiled["canonical_state_hash"],
                    "PACKET_HASH": compiled["packet_hash"],
                },
                sort_keys=True,
            ),
        }
        p = ActiveTurnStub.prepare
        with self.assertRaisesRegex(ValueError, "COGNITION_OBJECT_VERSION_AMBIGUOUS:JSPACE_PROFILE"):
            admission.build_pre_inference_admission(
                object(),
                entity_generation=7,
                invocation={
                    "expected_generation": 7,
                    "causal_turn_id": p["causal_turn_id"],
                    "task_text": p["task_text"],
                    "turn_binding_digest": p["turn_binding_digest"],
                },
                compiled=compiled,
                prompt=prompt,
                profile={"inference": {"kind": "mock"}},
                active_turn_module=ActiveTurnStub,
                semantic_resolution_module=AmbiguousSemantic,
                capability_module=CapabilityStub,
                capsule_module=CapsuleStub,
                packet_module=PacketStub,
            )


if __name__ == "__main__":
    unittest.main()
