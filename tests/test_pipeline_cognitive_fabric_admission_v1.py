import hashlib
import json
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import pipeline_cognitive_fabric_admission_v1 as sut


def h(label):
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


class Capsule:
    @staticmethod
    def compile_workspace_capsule(**kw):
        return {"mode": "WORKSPACE_BOUND", "capsule_digest": h(json.dumps(kw, sort_keys=True))}


class Packet:
    @staticmethod
    def compile_packet(capsule, *, target_engine_class, jspace_mode, inference, system, user):
        context = {"inference": inference, "system": system, "user": user}
        admitted = h(json.dumps(context, sort_keys=True))
        doc = {
            "schema": "ZERO_INFERENCE_PACKET/v2",
            "capsule": capsule["capsule_digest"],
            "target": target_engine_class,
            "jspace": jspace_mode,
            "admitted_context_digest": admitted,
        }
        doc["packet_digest"] = h(json.dumps(doc, sort_keys=True))
        return doc


class Capability:
    route_digest = h("bound-route")
    authority = "ROUTING_ONLY_BOUND_TO_CANONICAL_PREPARE"

    @classmethod
    def resolve_bound_route(cls, profile, prepare, *, expected_generation):
        snapshot = profile.get("_runtime_profile_snapshot")
        if not isinstance(snapshot, dict):
            raise ValueError("PROFILE_SNAPSHOT_MISSING")
        binding = profile.get("inference", {}).get("capability_binding")
        if not isinstance(binding, dict):
            raise ValueError("INFERENCE_CAPABILITY_BINDING_REQUIRED")
        if prepare.get("entity_generation") != expected_generation:
            raise ValueError("STALE_GENERATION")
        return {
            "ok": True,
            "schema": "MINI_INFERENCE_BOUND_ROUTE/v1",
            "entity_generation": expected_generation,
            "causal_turn_id": prepare["causal_turn_id"],
            "turn_binding_digest": prepare["turn_binding_digest"],
            "boot_binding_digest": prepare["boot_binding_digest"],
            "workspace_digest": prepare["workspace_digest"],
            "profile_id": snapshot["profile_id"],
            "profile_hash": snapshot["profile_hash"],
            "capability_binding_digest": binding["binding_digest"],
            "capability_receipt_digest": binding["capability_receipt_digest"],
            "capability_evidence_kind": binding["capability_evidence_kind"],
            "adapter_version": binding["adapter_version"],
            "target_engine_class": binding["engine_class"],
            "ucf_engine_class": "claude_code",
            "jspace_mode": binding["jspace_mode"],
            "route_digest": cls.route_digest,
            "authority": cls.authority,
        }


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
    def profile(**inference_overrides):
        inference = {
            "kind": "json_chat",
            "model": "candidate",
            "capability_binding": {
                "binding_digest": h("capability-binding"),
                "capability_receipt_digest": h("capability-receipt"),
                "capability_evidence_kind": "STATIC_CONSERVATIVE",
                "adapter_version": "claude-code/v1",
                "engine_class": "CLAUDE_CODE",
                "jspace_mode": "COMPILED_EXTERNAL",
            },
        }
        inference.update(inference_overrides)
        return {
            "profile_id": "p1",
            "_runtime_profile_snapshot": {
                "profile_id": "p1",
                "profile_hash": h("profile"),
            },
            "inference": inference,
        }

    @staticmethod
    def prompt(*, state_hash=None, packet_hash=None, payload="USR"):
        state_hash = state_hash or h("state")
        packet_hash = packet_hash or h("source-packet")
        return {
            "system": "SYS",
            "user": json.dumps(
                {
                    "CANONICAL_STATE_HASH": state_hash,
                    "PACKET_HASH": packet_hash,
                    "payload": payload,
                },
                sort_keys=True,
            ),
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
            origin="go",
            active_turn_module=Active,
            capsule_module=Capsule,
            packet_module=Packet,
            capability_module=Capability,
        )
        args.update(overrides)
        return sut.build_pre_inference_admission(**args)

    def test_success_is_bound_route_candidate_only(self):
        out = self.call()
        self.assertTrue(out["ok"])
        self.assertEqual(out["schema"], sut.ADMISSION_SCHEMA)
        self.assertEqual(out["admission_receipt"]["authority"], "CANDIDATE_INFERENCE_ONLY")
        self.assertFalse(out["admission_receipt"]["real_effect_executed"])
        self.assertNotIn("ucf_runtime_receipt_digest", out)
        self.assertEqual(out["generation"], 7)
        self.assertEqual(out["target_engine_class"], "CLAUDE_CODE")
        self.assertEqual(out["jspace_mode"], "COMPILED_EXTERNAL")
        self.assertEqual(out["capability_route_digest"], h("bound-route"))
        self.assertEqual(out["capability_binding_digest"], h("capability-binding"))
        self.assertEqual(
            out["cognition_invocation_digest"],
            sut._sha256_obj({"schema": sut.INVOCATION_SCHEMA, **self.invocation()}),
        )

    def test_downstream_context_changes_packet_and_admission_identity(self):
        a = self.call(prompt=self.prompt(payload="USR-A"))
        b = self.call(prompt=self.prompt(payload="USR-B"))
        self.assertNotEqual(a["inference_packet_digest"], b["inference_packet_digest"])
        self.assertNotEqual(a["cognitive_fabric_receipt_digest"], b["cognitive_fabric_receipt_digest"])

    def test_bound_route_digest_changes_admission_identity(self):
        class OtherCapability(Capability):
            route_digest = h("bound-route-other")

        a = self.call()
        b = self.call(capability_module=OtherCapability)
        self.assertNotEqual(a["capability_route_digest"], b["capability_route_digest"])
        self.assertNotEqual(a["cognitive_fabric_receipt_digest"], b["cognitive_fabric_receipt_digest"])

    def test_bound_route_authority_escalation_fails_closed(self):
        class BadCapability(Capability):
            authority = "TRUTH_AUTHORITY"

        with self.assertRaisesRegex(sut.CognitiveFabricAdmissionError, "CAPABILITY_AUTHORITY_ESCALATION"):
            self.call(capability_module=BadCapability)

    def test_bound_route_turn_drift_fails_closed(self):
        class BadCapability(Capability):
            @classmethod
            def resolve_bound_route(cls, profile, prepare, *, expected_generation):
                out = super().resolve_bound_route(profile, prepare, expected_generation=expected_generation)
                out["causal_turn_id"] = "other-turn"
                return out

        with self.assertRaisesRegex(sut.CognitiveFabricAdmissionError, "BOUND_ROUTE_TURN_DRIFT"):
            self.call(capability_module=BadCapability)

    def test_prompt_compiled_identity_mismatch_fails_closed(self):
        with self.assertRaisesRegex(sut.CognitiveFabricAdmissionError, "PROMPT_COMPILED_IDENTITY_MISMATCH"):
            self.call(prompt=self.prompt(packet_hash=h("wrong-packet")))

    def test_placeholder_compiled_digest_fails_closed(self):
        with self.assertRaisesRegex(sut.CognitiveFabricAdmissionError, "PLACEHOLDER_REJECTED"):
            self.call(compiled={"canonical_state_hash": "0" * 64, "packet_hash": h("packet")})

    def test_wrong_activation_digest_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "ACTIVE_TURN_DIGEST_MISMATCH"):
            self.call(expected_activation_digest=h("wrong"))

    def test_prepare_authority_escalation_fails_closed(self):
        class BadActive(Active):
            @staticmethod
            def resolve_active_prepare(*args, **kwargs):
                out = Active.resolve_active_prepare(*args, **kwargs)
                out["authority"] = dict(out["authority"])
                out["authority"]["direct_truth_authority"] = True
                return out

        with self.assertRaisesRegex(sut.CognitiveFabricAdmissionError, "PREPARE_AUTHORITY_ESCALATION"):
            self.call(active_turn_module=BadActive)

    def test_task_text_hash_drift_fails_closed(self):
        class BadActive(Active):
            @staticmethod
            def resolve_active_prepare(*args, **kwargs):
                out = Active.resolve_active_prepare(*args, **kwargs)
                out["task_sha256"] = h("other task")
                return out

        with self.assertRaisesRegex(sut.CognitiveFabricAdmissionError, "TASK_BINDING_MISMATCH"):
            self.call(active_turn_module=BadActive)

    def test_selector_stale_generation_fails_closed(self):
        with self.assertRaisesRegex(sut.CognitiveFabricAdmissionError, "COGNITION_INVOCATION_STALE_GENERATION"):
            self.call(invocation=self.invocation(expected_generation=6))

    def test_selector_turn_mismatch_fails_closed(self):
        with self.assertRaisesRegex(sut.CognitiveFabricAdmissionError, "COGNITION_INVOCATION_CAUSAL_TURN_MISMATCH"):
            self.call(invocation=self.invocation(causal_turn_id="turn-other"))

    def test_selector_task_mismatch_fails_closed(self):
        with self.assertRaisesRegex(sut.CognitiveFabricAdmissionError, "COGNITION_INVOCATION_TASK_MISMATCH"):
            self.call(invocation=self.invocation(task_text="other task"))

    def test_selector_binding_digest_mismatch_fails_closed(self):
        with self.assertRaisesRegex(sut.CognitiveFabricAdmissionError, "COGNITION_INVOCATION_TURN_BINDING_MISMATCH"):
            self.call(invocation=self.invocation(turn_binding_digest=h("other-binding")))

    def test_selector_cannot_smuggle_cognition_authority(self):
        poisoned = self.invocation()
        poisoned["zero_identity_digest"] = h("caller-zero")
        with self.assertRaisesRegex(sut.CognitiveFabricAdmissionError, "COGNITION_INVOCATION_FIELDS_MISMATCH"):
            self.call(invocation=poisoned)

    def test_caller_route_parameters_are_not_part_of_api(self):
        with self.assertRaises(TypeError):
            self.call(target_engine_class="BUNDLED_LOCAL_08B")

    def test_profile_provider_metadata_cannot_override_bound_route(self):
        profile = self.profile(kind="local_exec", model="FULL_LOCAL_LATENT_SUPER_HOOKABLE")
        out = self.call(profile=profile)
        self.assertEqual(out["target_engine_class"], "CLAUDE_CODE")
        self.assertEqual(out["jspace_mode"], "COMPILED_EXTERNAL")

    def test_missing_profile_capability_binding_fails_closed(self):
        profile = self.profile()
        del profile["inference"]["capability_binding"]
        with self.assertRaisesRegex(ValueError, "INFERENCE_CAPABILITY_BINDING_REQUIRED"):
            self.call(profile=profile)


if __name__ == "__main__":
    unittest.main()
