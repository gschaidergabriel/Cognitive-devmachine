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

import mini_cognitive_fabric_prepare_v1 as prepare


def digest_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def digest_obj(value) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def resolved_prepare(generation: int = 7):
    task = "exact bound task"
    return {
        "ok": True,
        "entity_generation": generation,
        "causal_turn_id": "turn-7",
        "task_text": task,
        "task_sha256": digest_text(task),
        "activation_digest": digest_text("activation"),
        "turn_binding_digest": digest_text("turn-binding"),
        "boot_binding_digest": digest_text("boot-binding"),
        "workspace_digest": digest_text("workspace"),
        "selected_workspace_slots": ["slot:observed:1", "slot:counter:1"],
        "contradiction_state": "OPEN",
        "required_zero_mode": "FULL",
        "zero_identity_digest": digest_text("zero"),
        "grf_digest": digest_text("grf"),
        "hyperposition_digest": digest_text("hyperposition"),
        "bundled_manifest_digest": digest_text("manifest"),
        "local_model_digest": digest_text("local-model"),
        "tokenizer_digest": digest_text("tokenizer"),
        "jspace_profile_digest": digest_text("jspace-profile"),
        "jacobian_lens_digest": digest_text("lens"),
        "workspace_calibration_digest": digest_text("workspace-calibration"),
        "boot_source_lock_digest": digest_text("boot-lock"),
        "policy_authority_digest": digest_text("policy"),
        "boot_provenance_refs": ["boot:receipt"],
        "turn_provenance_refs": ["turn:binding"],
        "activation_provenance_refs": ["turn:activation"],
        "authority": {
            "durable_state": "MiniUnifiedDB",
            "candidate_only": True,
            "direct_truth_authority": False,
            "direct_effect_authority": False,
        },
    }


def invocation(**updates):
    value = {
        "expected_generation": 7,
        "causal_turn_id": "turn-7",
        "task_text": "exact bound task",
        "turn_binding_digest": digest_text("turn-binding"),
    }
    value.update(updates)
    return value


class FakeActiveTurn:
    generation = 7
    last_expected_activation_digest = None

    @classmethod
    def resolve_active_prepare(
        cls, db, *, entity_generation, expected_activation_digest=None
    ):
        cls.last_expected_activation_digest = expected_activation_digest
        return resolved_prepare(cls.generation)


class FakeCapability:
    mode = "valid"

    @classmethod
    def resolve_from_profile(cls, profile):
        if cls.mode == "reject":
            raise ValueError("CAPABILITY_REJECT")
        snapshot = profile["_runtime_profile_snapshot"]
        out = {
            "ok": True,
            "profile_id": snapshot["profile_id"],
            "profile_hash": snapshot["profile_hash"],
            "binding_digest": digest_text("capability-binding"),
            "capability_receipt_digest": digest_text("capability-receipt"),
            "target_engine_class": "BUNDLED_LOCAL_08B",
            "jspace_mode": "FULL_LOCAL_LATENT",
            "authority": "ROUTING_ONLY_NO_TRUTH_STATE_EFFECT_AUTHORITY",
        }
        if cls.mode == "authority":
            out["authority"] = "MODEL_DECIDES"
        return out


class FakeCapsule:
    @staticmethod
    def compile_workspace_capsule(**kwargs):
        return {
            "schema": "ZERO_WORKSPACE_CAPSULE/v1",
            "capsule_digest": digest_obj(kwargs),
            "entity_generation": kwargs["entity_generation"],
            "causal_turn_id": kwargs["causal_turn_id"],
            "workspace_digest": kwargs["workspace_digest"],
        }


class FakePacket:
    last = None

    @classmethod
    def compile_packet(
        cls,
        capsule,
        *,
        target_engine_class,
        jspace_mode,
        inference,
        system,
        user,
    ):
        cls.last = {
            "capsule": capsule,
            "target_engine_class": target_engine_class,
            "jspace_mode": jspace_mode,
            "inference": inference,
            "system": system,
            "user": user,
        }
        context = {
            "inference": inference,
            "system": system,
            "user": user,
        }
        return {
            "schema": "ZERO_INFERENCE_PACKET/v2",
            "packet_digest": digest_obj({"capsule": capsule, "route": [target_engine_class, jspace_mode], **context}),
            "admitted_context_digest": digest_obj(context),
        }


def fixtures():
    canonical_hash = digest_text("canonical")
    packet_hash = digest_text("source-packet")
    compiled = {
        "canonical_state_hash": canonical_hash,
        "packet_hash": packet_hash,
    }
    prompt = {
        "system": "immutable system context",
        "user": json.dumps(
            {
                "CANONICAL_STATE_HASH": canonical_hash,
                "PACKET_HASH": packet_hash,
                "payload": "candidate context",
            },
            sort_keys=True,
        ),
    }
    profile = {
        "profile_id": "mini",
        "_runtime_profile_snapshot": {
            "profile_id": "mini",
            "profile_hash": digest_text("profile"),
        },
        "inference": {
            "kind": "local_exec",
            "provider": "descriptive-only",
            "model": "descriptive-only",
            "capability_binding": {"opaque_to_materializer": True},
        },
    }
    return compiled, prompt, profile


class MiniCognitiveFabricPrepareTests(unittest.TestCase):
    def setUp(self):
        FakeActiveTurn.generation = 7
        FakeActiveTurn.last_expected_activation_digest = None
        FakeCapability.mode = "valid"
        FakePacket.last = None
        self.db = sqlite3.connect(":memory:")

    def tearDown(self):
        self.db.close()

    def call(self, compiled, prompt, profile, **kwargs):
        return prepare.prepare_admission(
            self.db,
            previous_generation=7,
            invocation=invocation(),
            compiled=compiled,
            prompt=prompt,
            profile=profile,
            active_turn_module=FakeActiveTurn,
            capability_module=FakeCapability,
            capsule_module=FakeCapsule,
            packet_module=FakePacket,
            **kwargs,
        )

    def test_exact_bound_prepare_materializes_candidate_only_admission(self):
        compiled, prompt, profile = fixtures()
        expected_activation = digest_text("activation")
        result = self.call(
            compiled,
            prompt,
            profile,
            expected_activation_digest=expected_activation,
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["schema"], prepare.SCHEMA)
        self.assertEqual(result["generation"], 7)
        self.assertEqual(result["inference"], profile["inference"])
        self.assertEqual(FakeActiveTurn.last_expected_activation_digest, expected_activation)
        self.assertEqual(FakePacket.last["target_engine_class"], "BUNDLED_LOCAL_08B")
        self.assertEqual(FakePacket.last["jspace_mode"], "FULL_LOCAL_LATENT")
        receipt = result["audit"]["admission_receipt"]
        self.assertFalse(receipt["effect_executed"])
        self.assertEqual(receipt["authority"]["semantic_authority"], "CANDIDATE_INFERENCE_ONLY")
        self.assertFalse(receipt["authority"]["direct_truth_authority"])
        self.assertFalse(receipt["authority"]["direct_state_authority"])
        self.assertFalse(receipt["authority"]["direct_effect_authority"])
        self.assertEqual(receipt["capability_binding_digest"], digest_text("capability-binding"))
        self.assertIn("cognition_invocation_digest", receipt)

    def test_prompt_compiled_identity_mismatch_fails_closed(self):
        compiled, prompt, profile = fixtures()
        poisoned = json.loads(prompt["user"])
        poisoned["PACKET_HASH"] = digest_text("other-packet")
        prompt["user"] = json.dumps(poisoned, sort_keys=True)
        result = self.call(compiled, prompt, profile)
        self.assertFalse(result["ok"])
        self.assertIn("PROMPT_COMPILED_IDENTITY_MISMATCH", result["error"])
        self.assertIsNone(FakePacket.last)

    def test_capability_route_is_resolved_by_canonical_binder_not_provider_names(self):
        compiled, prompt, profile = fixtures()
        profile["inference"]["provider"] = "claims-full-local-latent"
        profile["inference"]["model"] = "claims-claude-and-local"
        result = self.call(compiled, prompt, profile)
        self.assertTrue(result["ok"])
        self.assertEqual(FakePacket.last["target_engine_class"], "BUNDLED_LOCAL_08B")
        self.assertEqual(FakePacket.last["jspace_mode"], "FULL_LOCAL_LATENT")

    def test_capability_rejection_fails_before_packet(self):
        compiled, prompt, profile = fixtures()
        FakeCapability.mode = "reject"
        result = self.call(compiled, prompt, profile)
        self.assertFalse(result["ok"])
        self.assertIn("CAPABILITY_BINDING_REJECTED", result["error"])
        self.assertIsNone(FakePacket.last)

    def test_capability_authority_escalation_fails_before_packet(self):
        compiled, prompt, profile = fixtures()
        FakeCapability.mode = "authority"
        result = self.call(compiled, prompt, profile)
        self.assertFalse(result["ok"])
        self.assertIn("CAPABILITY_AUTHORITY_ESCALATION", result["error"])
        self.assertIsNone(FakePacket.last)

    def test_selector_must_match_active_turn(self):
        compiled, prompt, profile = fixtures()
        result = self.call(
            compiled,
            prompt,
            profile,
            invocation=invocation(causal_turn_id="turn-other"),
        )
        self.assertFalse(result["ok"])
        self.assertIn("COGNITION_INVOCATION_CAUSAL_TURN_MISMATCH", result["error"])
        self.assertIsNone(FakePacket.last)

    def test_selector_cannot_smuggle_cognition_authority(self):
        compiled, prompt, profile = fixtures()
        bad = invocation()
        bad["zero_identity_digest"] = digest_text("caller-zero")
        result = self.call(compiled, prompt, profile, invocation=bad)
        self.assertFalse(result["ok"])
        self.assertIn("COGNITION_INVOCATION_FIELDS_MISMATCH", result["error"])
        self.assertIsNone(FakePacket.last)

    def test_active_prepare_generation_drift_fails_closed(self):
        compiled, prompt, profile = fixtures()
        FakeActiveTurn.generation = 8
        result = self.call(compiled, prompt, profile)
        self.assertFalse(result["ok"])
        self.assertIn("ACTIVE_PREPARE_GENERATION_MISMATCH", result["error"])
        self.assertIsNone(FakePacket.last)

    def test_prepare_authority_escalation_fails_closed(self):
        compiled, prompt, profile = fixtures()

        class BadActive(FakeActiveTurn):
            @classmethod
            def resolve_active_prepare(cls, *args, **kwargs):
                value = resolved_prepare(7)
                value["authority"] = dict(value["authority"])
                value["authority"]["direct_truth_authority"] = True
                return value

        result = self.call(compiled, prompt, profile, active_turn_module=BadActive)
        self.assertFalse(result["ok"])
        self.assertIn("PREPARE_AUTHORITY_ESCALATION", result["error"])
        self.assertIsNone(FakePacket.last)

    def test_placeholder_profile_identity_fails_closed(self):
        compiled, prompt, profile = fixtures()
        profile["_runtime_profile_snapshot"]["profile_hash"] = "0" * 64
        result = self.call(compiled, prompt, profile)
        self.assertFalse(result["ok"])
        self.assertIn("profile_hash:PLACEHOLDER_REJECTED", result["error"])
        self.assertIsNone(FakePacket.last)


if __name__ == "__main__":
    unittest.main()
