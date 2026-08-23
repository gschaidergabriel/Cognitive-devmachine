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

    def call(self, **overrides):
        args = dict(
            db=object(),
            entity_generation=7,
            invocation=self.invocation(),
            compiled={"canonical_state_hash": h("state"), "packet_hash": h("source-packet")},
            prompt={"system": "SYS", "user": "USR"},
            inference={"kind": "claude_code", "model": "candidate"},
            target_engine_class="CLAUDE_CODE",
            jspace_mode="COMPILED_EXTERNAL",
            expected_activation_digest=h("activation"),
            profile_id="p1",
            profile_hash=h("profile"),
            origin="go",
            active_turn_module=Active,
            capsule_module=Capsule,
            packet_module=Packet,
        )
        args.update(overrides)
        return sut.build_pre_inference_admission(**args)

    def test_success_is_pre_inference_candidate_only(self):
        out = self.call()
        self.assertTrue(out["ok"])
        self.assertEqual(out["schema"], sut.ADMISSION_SCHEMA)
        self.assertEqual(out["admission_receipt"]["authority"], "CANDIDATE_INFERENCE_ONLY")
        self.assertFalse(out["admission_receipt"]["real_effect_executed"])
        self.assertNotIn("ucf_runtime_receipt_digest", out)
        self.assertEqual(out["generation"], 7)
        self.assertEqual(
            out["cognition_invocation_digest"],
            sut._sha256_obj({"schema": sut.INVOCATION_SCHEMA, **self.invocation()}),
        )

    def test_downstream_context_changes_packet_and_admission_identity(self):
        a = self.call(prompt={"system": "SYS", "user": "USR-A"})
        b = self.call(prompt={"system": "SYS", "user": "USR-B"})
        self.assertNotEqual(a["inference_packet_digest"], b["inference_packet_digest"])
        self.assertNotEqual(a["cognitive_fabric_receipt_digest"], b["cognitive_fabric_receipt_digest"])

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


if __name__ == "__main__":
    unittest.main()
