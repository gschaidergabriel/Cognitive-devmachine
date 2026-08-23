from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import pipeline_cognitive_fabric_admission_v1 as sut


def h(label: str) -> str:
    return hashlib.sha256(label.encode()).hexdigest()


class Active:
    @staticmethod
    def resolve_active_prepare(db, *, entity_generation, expected_activation_digest=None):
        out = {
            "ok": True,
            "entity_generation": entity_generation,
            "causal_turn_id": "turn-1",
            "task_text": "measure first",
            "task_sha256": h("measure first"),
            "activation_digest": h("activation"),
            "turn_binding_digest": h("turn-binding"),
            "boot_binding_digest": h("boot-binding"),
            "workspace_digest": h("workspace"),
            "zero_identity_digest": h("zero"),
            "grf_digest": h("grf"),
            "hyperposition_digest": h("hyperposition"),
            "bundled_manifest_digest": h("manifest"),
            "local_model_digest": h("model"),
            "tokenizer_digest": h("tokenizer"),
            "jspace_profile_digest": h("jspace"),
            "jacobian_lens_digest": h("lens"),
            "workspace_calibration_digest": h("calibration"),
            "boot_source_lock_digest": h("source-lock"),
            "policy_authority_digest": h("policy"),
            "selected_workspace_slots": ["slot:a"],
            "contradiction_state": "NONE",
            "required_zero_mode": "NORMAL",
            "turn_provenance_refs": ["turn:r1"],
            "boot_provenance_refs": ["boot:r1"],
            "activation_provenance_refs": ["active:r1"],
            "authority": {
                "durable_state": "MiniUnifiedDB",
                "candidate_only": True,
                "direct_truth_authority": False,
                "direct_effect_authority": False,
            },
        }
        if expected_activation_digest is not None and expected_activation_digest != out["activation_digest"]:
            raise ValueError("ACTIVE_TURN_DIGEST_MISMATCH")
        return out


class Capability:
    @staticmethod
    def resolve_bound_route(profile, prepare, *, expected_generation):
        assert prepare["entity_generation"] == expected_generation
        snap = profile["_runtime_profile_snapshot"]
        return {
            "ok": True,
            "schema": "MINI_INFERENCE_BOUND_ROUTE/v1",
            "entity_generation": expected_generation,
            "causal_turn_id": prepare["causal_turn_id"],
            "turn_binding_digest": prepare["turn_binding_digest"],
            "boot_binding_digest": prepare["boot_binding_digest"],
            "workspace_digest": prepare["workspace_digest"],
            "profile_id": snap["profile_id"],
            "profile_hash": snap["profile_hash"],
            "capability_binding_digest": h("capability-binding"),
            "capability_receipt_digest": h("capability-receipt"),
            "target_engine_class": "CLAUDE_CODE",
            "ucf_engine_class": "claude_code",
            "jspace_mode": "COMPILED_EXTERNAL",
            "cognition": {name: prepare[name] for name in (
                "zero_identity_digest", "grf_digest", "hyperposition_digest",
                "bundled_manifest_digest", "local_model_digest", "tokenizer_digest",
                "jspace_profile_digest", "jacobian_lens_digest", "workspace_calibration_digest",
                "boot_source_lock_digest", "policy_authority_digest",
            )},
            "route_digest": h("bound-route"),
            "local_activation_access": False,
            "external_hidden_state_claimed": False,
            "provider_observability_claim_supported": True,
            "adapter_version": "claude-code/v1",
            "capability_evidence_kind": "STATIC_CONSERVATIVE",
            "authority": "ROUTING_ONLY_BOUND_TO_CANONICAL_PREPARE",
        }


class Capsule:
    @staticmethod
    def compile_workspace_capsule(**kw):
        return {"mode": "WORKSPACE_BOUND", "capsule_digest": h(json.dumps(kw, sort_keys=True))}


class Packet:
    @staticmethod
    def context_digests(inference, system, user):
        cfg = sut.sha256_obj(dict(inference))
        system_digest = hashlib.sha256(system.encode()).hexdigest()
        user_digest = hashlib.sha256(user.encode()).hexdigest()
        return {
            "inference_config_digest": cfg,
            "system_context_digest": system_digest,
            "user_context_digest": user_digest,
            "admitted_context_digest": sut.sha256_obj({
                "inference_config_digest": cfg,
                "system_context_digest": system_digest,
                "user_context_digest": user_digest,
            }),
        }

    @classmethod
    def compile_packet(cls, capsule, *, target_engine_class, jspace_mode, inference, system, user):
        context = cls.context_digests(inference, system, user)
        doc = {
            "schema": "ZERO_INFERENCE_PACKET/v2",
            "capsule": capsule["capsule_digest"],
            "target": target_engine_class,
            "jspace": jspace_mode,
            **context,
        }
        doc["packet_digest"] = sut.sha256_obj(doc)
        return doc


class AdmissionTests(unittest.TestCase):
    @staticmethod
    def invocation(**overrides):
        value = {
            "expected_generation": 7,
            "causal_turn_id": "turn-1",
            "task_text": "measure first",
            "turn_binding_digest": h("turn-binding"),
        }
        value.update(overrides)
        return value

    @staticmethod
    def profile():
        return {
            "profile_id": "p1",
            "_runtime_profile_snapshot": {"profile_id": "p1", "profile_hash": h("profile")},
            "inference": {"kind": "mock", "model": "candidate", "nested": {"temperature": 0.2}},
        }

    @staticmethod
    def prompt(payload="USR"):
        return {
            "system": "SYS",
            "user": json.dumps({
                "CANONICAL_STATE_HASH": h("state"),
                "PACKET_HASH": h("source-packet"),
                "payload": payload,
            }, sort_keys=True),
        }

    def call(self, **overrides):
        args = dict(
            db=object(),
            entity_generation=7,
            invocation=self.invocation(),
            compiled={"canonical_state_hash": h("state"), "packet_hash": h("source-packet")},
            prompt=self.prompt(),
            profile=self.profile(),
            expected_activation_digest=h("activation"),
            origin="test",
            active_turn_module=Active,
            capsule_module=Capsule,
            packet_module=Packet,
            capability_module=Capability,
        )
        args.update(overrides)
        return sut.build_pre_inference_admission(**args)

    def test_exact_bound_route_builds_candidate_only_admission(self):
        out = self.call()
        self.assertTrue(out["ok"])
        self.assertEqual(out["admission_receipt"]["authority"], "CANDIDATE_INFERENCE_ONLY")
        self.assertEqual(out["admission_receipt"]["bound_route_digest"], h("bound-route"))
        self.assertEqual(out["cognitive_fabric_receipt_digest"], sut.sha256_obj(out["admission_receipt"]))
        self.assertFalse(out["admission_receipt"]["real_effect_executed"])

    def test_selector_task_mismatch_fails_closed(self):
        with self.assertRaisesRegex(sut.CognitiveFabricAdmissionError, "COGNITION_INVOCATION_TASK_MISMATCH"):
            self.call(invocation=self.invocation(task_text="other"))

    def test_prompt_identity_mismatch_fails_before_packet(self):
        bad = self.prompt()
        bad["user"] = json.dumps({"CANONICAL_STATE_HASH": h("state"), "PACKET_HASH": h("wrong")})
        with self.assertRaisesRegex(sut.CognitiveFabricAdmissionError, "PROMPT_COMPILED_IDENTITY_MISMATCH"):
            self.call(prompt=bad)

    def test_bound_route_turn_drift_fails_closed(self):
        class BadCapability(Capability):
            @staticmethod
            def resolve_bound_route(profile, prepare, *, expected_generation):
                out = Capability.resolve_bound_route(profile, prepare, expected_generation=expected_generation)
                out["turn_binding_digest"] = h("other")
                return out
        with self.assertRaisesRegex(sut.CognitiveFabricAdmissionError, "BOUND_ROUTE_TURN_MISMATCH"):
            self.call(capability_module=BadCapability)

    def test_post_admission_profile_mutation_does_not_change_admitted_inference(self):
        profile = self.profile()
        out = self.call(profile=profile)
        frozen = copy.deepcopy(out["inference"])
        profile["inference"]["nested"]["temperature"] = 9.9
        self.assertEqual(out["inference"], frozen)
        self.assertNotEqual(out["inference"], profile["inference"])

    def test_downstream_exact_context_revalidates(self):
        out = self.call()
        verified = sut.validate_downstream_context(
            admission_receipt=out["admission_receipt"],
            admission_receipt_digest=out["cognitive_fabric_receipt_digest"],
            inference_packet_digest=out["inference_packet_digest"],
            admitted_context_digest=out["admitted_context_digest"],
            inference=out["inference"],
            system=out["system"],
            user=out["user"],
            packet_module=Packet,
        )
        self.assertEqual(verified["inference_packet_digest"], out["inference_packet_digest"])

    def test_downstream_context_swap_fails_closed(self):
        out = self.call()
        with self.assertRaisesRegex(sut.CognitiveFabricAdmissionError, "DOWNSTREAM_CONTEXT_BINDING_MISMATCH"):
            sut.validate_downstream_context(
                admission_receipt=out["admission_receipt"],
                admission_receipt_digest=out["cognitive_fabric_receipt_digest"],
                inference_packet_digest=out["inference_packet_digest"],
                admitted_context_digest=out["admitted_context_digest"],
                inference=out["inference"],
                system=out["system"],
                user=out["user"] + " MUTATED",
                packet_module=Packet,
            )

    def test_admission_receipt_tamper_fails_closed(self):
        out = self.call()
        tampered = copy.deepcopy(out["admission_receipt"])
        tampered["jspace_mode"] = "PLAIN_COMPATIBILITY"
        with self.assertRaisesRegex(sut.CognitiveFabricAdmissionError, "ADMISSION_RECEIPT_DIGEST_MISMATCH"):
            sut.validate_downstream_context(
                admission_receipt=tampered,
                admission_receipt_digest=out["cognitive_fabric_receipt_digest"],
                inference_packet_digest=out["inference_packet_digest"],
                admitted_context_digest=out["admitted_context_digest"],
                inference=out["inference"],
                system=out["system"],
                user=out["user"],
                packet_module=Packet,
            )


if __name__ == "__main__":
    unittest.main()
