from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import mini_cognitive_fabric_admission_v1 as sut


def h(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def invocation(**changes):
    value = {
        "expected_generation": 7,
        "causal_turn_id": "turn-7",
        "task_text": "exact task",
        "turn_binding_digest": h("turn-binding"),
    }
    value.update(changes)
    return value


def active_binding(**changes):
    task = "exact task"
    value = {
        "ok": True,
        "entity_generation": 7,
        "causal_turn_id": "turn-7",
        "task_text": task,
        "task_sha256": h(task),
        "activation_digest": h("activation"),
        "turn_binding_digest": h("turn-binding"),
        "boot_binding_digest": h("boot-binding"),
        "workspace_digest": h("workspace"),
        "zero_identity_digest": h("zero"),
        "grf_digest": h("grf"),
        "hyperposition_digest": h("hyperposition"),
        "local_model_digest": h("model"),
        "jacobian_lens_digest": h("lens"),
        "selected_workspace_slots": ["slot:a"],
        "contradiction_state": "NONE",
        "required_zero_mode": "NORMAL",
        "activation_provenance_refs": ["active:r1"],
        "turn_provenance_refs": ["turn:r1"],
        "boot_provenance_refs": ["boot:r1"],
        "authority": {
            "durable_state": "MiniUnifiedDB",
            "candidate_only": True,
            "direct_truth_authority": False,
            "direct_effect_authority": False,
        },
    }
    value.update(changes)
    return value


def fixtures():
    state_hash = h("state")
    packet_hash = h("packet")
    profile = {
        "_runtime_profile_snapshot": {
            "profile_id": "p1",
            "profile_hash": h("profile"),
        },
        "inference": {
            "kind": "local_exec",
            "provider": "descriptive-only",
            "model": "descriptive-only",
            "capability_binding": {"opaque": True},
        },
    }
    previous = {"generation": 7}
    compiled = {"canonical_state_hash": state_hash, "packet_hash": packet_hash}
    prompt = {
        "system": "SYS",
        "user": json.dumps(
            {
                "CANONICAL_STATE_HASH": state_hash,
                "PACKET_HASH": packet_hash,
                "payload": "candidate",
            },
            sort_keys=True,
        ),
    }
    return profile, previous, compiled, prompt


class Fakes:
    binding = active_binding()
    packet_call = None

    @classmethod
    def active(cls, db, *, entity_generation, expected_activation_digest=None):
        return dict(cls.binding)

    @classmethod
    def route(cls, profile, binding, *, expected_generation):
        return {
            "ok": True,
            "schema": "MINI_INFERENCE_BOUND_ROUTE/v1",
            "entity_generation": expected_generation,
            "causal_turn_id": binding["causal_turn_id"],
            "turn_binding_digest": binding["turn_binding_digest"],
            "profile_id": profile["_runtime_profile_snapshot"]["profile_id"],
            "profile_hash": profile["_runtime_profile_snapshot"]["profile_hash"],
            "capability_binding_digest": h("capability-binding"),
            "capability_receipt_digest": h("capability-receipt"),
            "target_engine_class": "BUNDLED_LOCAL_08B",
            "jspace_mode": "FULL_LOCAL_LATENT",
            "route_digest": h("route"),
            "authority": "ROUTING_ONLY_BOUND_TO_CANONICAL_PREPARE",
        }

    @staticmethod
    def capsule(**kwargs):
        return {
            "schema": "ZERO_WORKSPACE_CAPSULE/v1",
            "mode": "WORKSPACE_BOUND",
            "capsule_digest": h(json.dumps(kwargs, sort_keys=True)),
        }

    @classmethod
    def packet(cls, capsule, *, target_engine_class, jspace_mode, inference, system, user):
        cls.packet_call = {
            "target_engine_class": target_engine_class,
            "jspace_mode": jspace_mode,
            "inference": inference,
            "system": system,
            "user": user,
        }
        material = json.dumps(cls.packet_call, sort_keys=True)
        return {
            "schema": "ZERO_INFERENCE_PACKET/v2",
            "packet_digest": h("packet:" + material),
            "admitted_context_digest": h("context:" + material),
        }


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        Fakes.binding = active_binding()
        Fakes.packet_call = None

    def call(self, *, invocation_value=None, route=None, active=None, **changes):
        profile, previous, compiled, prompt = fixtures()
        profile = changes.pop("profile", profile)
        previous = changes.pop("previous", previous)
        compiled = changes.pop("compiled", compiled)
        prompt = changes.pop("prompt", prompt)
        return sut.prepare_admission(
            object(),
            profile=profile,
            previous=previous,
            invocation=invocation_value or invocation(),
            compiled=compiled,
            prompt=prompt,
            resolve_active_prepare=active or Fakes.active,
            resolve_bound_route=route or Fakes.route,
            compile_workspace_capsule=Fakes.capsule,
            compile_packet=Fakes.packet,
            **changes,
        )

    def test_exact_path_is_candidate_only_and_bound(self):
        result = self.call()
        self.assertTrue(result["ok"])
        self.assertEqual(result["schema"], sut.ADMISSION_SCHEMA)
        self.assertEqual(Fakes.packet_call["target_engine_class"], "BUNDLED_LOCAL_08B")
        self.assertEqual(Fakes.packet_call["jspace_mode"], "FULL_LOCAL_LATENT")
        receipt = result["admission_receipt"]
        self.assertEqual(receipt["authority"], "CANDIDATE_INFERENCE_ONLY")
        self.assertFalse(receipt["real_effect_executed"])
        self.assertEqual(receipt["bound_route_digest"], h("route"))
        self.assertIn("cognition_invocation_digest", receipt)
        self.assertNotIn("ucf_runtime_receipt_digest", result)

    def test_selector_must_match_active_turn(self):
        with self.assertRaisesRegex(sut.AdmissionError, "COGNITION_INVOCATION_CAUSAL_TURN_MISMATCH"):
            self.call(invocation_value=invocation(causal_turn_id="other"))
        self.assertIsNone(Fakes.packet_call)

    def test_selector_cannot_smuggle_cognition_authority(self):
        poisoned = invocation()
        poisoned["jspace_profile_digest"] = h("caller-jspace")
        with self.assertRaisesRegex(sut.AdmissionError, "COGNITION_INVOCATION_FIELDS_MISMATCH"):
            self.call(invocation_value=poisoned)
        self.assertIsNone(Fakes.packet_call)

    def test_bound_route_must_match_active_turn(self):
        def bad_route(profile, binding, *, expected_generation):
            out = Fakes.route(profile, binding, expected_generation=expected_generation)
            out["causal_turn_id"] = "other"
            return out

        with self.assertRaisesRegex(sut.AdmissionError, "BOUND_ROUTE_TURN_MISMATCH"):
            self.call(route=bad_route)
        self.assertIsNone(Fakes.packet_call)

    def test_bound_route_authority_cannot_escalate(self):
        def bad_route(profile, binding, *, expected_generation):
            out = Fakes.route(profile, binding, expected_generation=expected_generation)
            out["authority"] = "MODEL_DECIDES"
            return out

        with self.assertRaisesRegex(sut.AdmissionError, "BOUND_ROUTE_AUTHORITY_ESCALATION"):
            self.call(route=bad_route)
        self.assertIsNone(Fakes.packet_call)

    def test_prompt_must_bind_compiled_hashes(self):
        profile, previous, compiled, prompt = fixtures()
        doc = json.loads(prompt["user"])
        doc["PACKET_HASH"] = h("other")
        prompt["user"] = json.dumps(doc, sort_keys=True)
        with self.assertRaisesRegex(sut.AdmissionError, "PROMPT_COMPILED_IDENTITY_MISMATCH"):
            self.call(profile=profile, previous=previous, compiled=compiled, prompt=prompt)
        self.assertIsNone(Fakes.packet_call)

    def test_active_prepare_authority_cannot_escalate(self):
        Fakes.binding = active_binding(
            authority={
                "durable_state": "MiniUnifiedDB",
                "candidate_only": False,
                "direct_truth_authority": True,
                "direct_effect_authority": False,
            }
        )
        with self.assertRaisesRegex(sut.AdmissionError, "ACTIVE_PREPARE_AUTHORITY_ESCALATION"):
            self.call()
        self.assertIsNone(Fakes.packet_call)

    def test_admitted_inference_is_deep_copy(self):
        profile, previous, compiled, prompt = fixtures()
        result = self.call(profile=profile, previous=previous, compiled=compiled, prompt=prompt)
        profile["inference"]["model"] = "mutated-after-admission"
        self.assertEqual(result["inference"]["model"], "descriptive-only")
        self.assertEqual(Fakes.packet_call["inference"]["model"], "descriptive-only")


if __name__ == "__main__":
    unittest.main()
