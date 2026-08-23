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

import mini_cognitive_fabric_prepare_v2 as mod


def d(label: str) -> str:
    return hashlib.sha256(label.encode()).hexdigest()


class Active:
    prepare = {
        "ok": True,
        "entity_generation": 7,
        "causal_turn_id": "ct1:g7:a3",
        "task_text": "summarize admitted evidence",
        "task_sha256": hashlib.sha256(b"summarize admitted evidence").hexdigest(),
        "activation_digest": d("activation"),
        "turn_binding_digest": d("turn"),
        "boot_binding_digest": d("boot"),
        "boot_provenance_refs": ["boot:r"],
        "turn_provenance_refs": ["turn:r"],
        "activation_provenance_refs": ["active:r"],
        "zero_identity_digest": d("zero"),
        "grf_digest": d("grf"),
        "hyperposition_digest": d("hyper"),
        "local_model_digest": d("model"),
        "jspace_profile_digest": d("jspace"),
        "jacobian_lens_digest": d("lens"),
        "workspace_calibration_digest": d("cal"),
        "policy_authority_digest": d("policy"),
        "workspace_digest": d("workspace"),
        "selected_workspace_slots": ["s1", "s2"],
        "contradiction_state": "UNKNOWN",
        "required_zero_mode": "TEXT_ONLY_BASELINE",
    }

    @classmethod
    def resolve_active_prepare(cls, db, *, entity_generation):
        if entity_generation != cls.prepare["entity_generation"]:
            raise ValueError("STALE_GENERATION")
        return dict(cls.prepare)


class Capability:
    @staticmethod
    def resolve_from_profile(profile):
        snapshot = profile["_runtime_profile_snapshot"]
        binding = profile["inference"].get("capability_binding")
        if not binding:
            raise ValueError("INFERENCE_CAPABILITY_BINDING_REQUIRED")
        return {
            "ok": True,
            "binding_digest": d("capability"),
            "target_engine_class": "CLAUDE_CODE",
            "ucf_engine_class": "claude_code",
            "jspace_mode": "COMPILED_EXTERNAL",
            "profile_id": snapshot["profile_id"],
            "profile_hash": snapshot["profile_hash"],
        }


class Capsule:
    @staticmethod
    def compile_workspace_capsule(**kwargs):
        return {"capsule_digest": d("capsule"), **kwargs}


class Packet:
    @staticmethod
    def compile_packet(capsule, *, target_engine_class, jspace_mode, inference, system, user):
        material = {
            "capsule": capsule["capsule_digest"],
            "target_engine_class": target_engine_class,
            "jspace_mode": jspace_mode,
            "inference": inference,
            "system": system,
            "user": user,
        }
        return {
            "packet_digest": hashlib.sha256(json.dumps(material, sort_keys=True).encode()).hexdigest(),
            "admitted_context_digest": d("context"),
        }


class PrepareV2Tests(unittest.TestCase):
    def base(self):
        compiled = {"canonical_state_hash": d("state"), "packet_hash": d("source-packet")}
        prompt = {
            "system": "system",
            "user": json.dumps({"CANONICAL_STATE_HASH": d("state"), "PACKET_HASH": d("source-packet")}),
        }
        profile = {
            "profile_id": "p1",
            "_runtime_profile_snapshot": {"profile_id": "p1", "profile_hash": d("profile")},
            "inference": {
                "kind": "mock",
                "model": "provider-name-must-not-authorize",
                "capability_binding": {"opaque": "validated by canonical binder"},
            },
        }
        invocation = {
            "expected_generation": 7,
            "causal_turn_id": "ct1:g7:a3",
            "task_text": "summarize admitted evidence",
            "turn_binding_digest": d("turn"),
        }
        return compiled, prompt, profile, invocation

    def call(self, *, compiled=None, prompt=None, profile=None, invocation=None, generation=7):
        b_compiled, b_prompt, b_profile, b_invocation = self.base()
        return mod.materialize_admission(
            object(),
            previous_generation=generation,
            compiled=compiled or b_compiled,
            prompt=prompt or b_prompt,
            profile=profile or b_profile,
            invocation=invocation or b_invocation,
            active_turn_module=Active,
            capability_module=Capability,
            capsule_module=Capsule,
            packet_module=Packet,
        )

    def test_candidate_only_exact_active_turn_and_capability_binding(self):
        out = self.call()
        self.assertTrue(out["ok"])
        self.assertEqual(out["causal_turn_id"], "ct1:g7:a3")
        receipt = out["audit"]["admission_receipt"]
        self.assertEqual(receipt["capability_binding_digest"], d("capability"))
        self.assertEqual(receipt["target_engine_class"], "CLAUDE_CODE")
        self.assertEqual(receipt["jspace_mode"], "COMPILED_EXTERNAL")
        self.assertEqual(receipt["authority"]["semantic_authority"], "CANDIDATE_INFERENCE_ONLY")
        self.assertFalse(receipt["authority"]["direct_truth_authority"])
        self.assertFalse(receipt["authority"]["direct_effect_authority"])

    def test_invocation_is_assertion_not_alternate_turn_selector(self):
        _, _, _, invocation = self.base()
        invocation["causal_turn_id"] = "ct1:g7:a999"
        with self.assertRaisesRegex(mod.PrepareError, "INVOCATION_ACTIVE_TURN_MISMATCH"):
            self.call(invocation=invocation)

    def test_invocation_task_or_binding_mismatch_fails(self):
        _, _, _, invocation = self.base()
        invocation["task_text"] = "other"
        with self.assertRaisesRegex(mod.PrepareError, "INVOCATION_ACTIVE_TASK_MISMATCH"):
            self.call(invocation=invocation)
        _, _, _, invocation = self.base()
        invocation["turn_binding_digest"] = d("other-turn")
        with self.assertRaisesRegex(mod.PrepareError, "INVOCATION_TURN_BINDING_MISMATCH"):
            self.call(invocation=invocation)

    def test_extra_invocation_authority_fields_fail(self):
        _, _, _, invocation = self.base()
        invocation["jspace_mode"] = "FULL_LOCAL_LATENT"
        with self.assertRaisesRegex(mod.PrepareError, "INVOCATION_FIELDS_MISMATCH"):
            self.call(invocation=invocation)

    def test_prompt_compiled_identity_drift_fails_before_packet(self):
        compiled, prompt, _, _ = self.base()
        prompt = dict(prompt)
        prompt["user"] = json.dumps({"CANONICAL_STATE_HASH": d("wrong"), "PACKET_HASH": compiled["packet_hash"]})
        with self.assertRaisesRegex(mod.PrepareError, "PROMPT_CANONICAL_STATE_HASH_MISMATCH"):
            self.call(compiled=compiled, prompt=prompt)

    def test_missing_capability_binding_cannot_fall_back_to_provider_name(self):
        _, _, profile, _ = self.base()
        profile = json.loads(json.dumps(profile))
        profile["inference"].pop("capability_binding")
        profile["inference"].update({"provider": "local", "model": "FULL_LOCAL_LATENT"})
        with self.assertRaisesRegex(ValueError, "INFERENCE_CAPABILITY_BINDING_REQUIRED"):
            self.call(profile=profile)

    def test_profile_snapshot_identity_mismatch_fails(self):
        _, _, profile, _ = self.base()
        profile = json.loads(json.dumps(profile))
        profile["profile_id"] = "other"
        with self.assertRaisesRegex(mod.PrepareError, "PROFILE_SNAPSHOT_ID_MISMATCH"):
            self.call(profile=profile)

    def test_generation_and_placeholder_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "STALE_GENERATION"):
            self.call(generation=8)
        compiled, _, _, _ = self.base()
        compiled["packet_hash"] = "0" * 64
        with self.assertRaisesRegex(mod.PrepareError, "PLACEHOLDER_REJECTED"):
            self.call(compiled=compiled)


if __name__ == "__main__":
    unittest.main()
