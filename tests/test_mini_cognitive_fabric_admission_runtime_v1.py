from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("admission", ROOT / "tools" / "mini_cognitive_fabric_admission_runtime_v1.py")
assert spec is not None and spec.loader is not None
admission = importlib.util.module_from_spec(spec)
spec.loader.exec_module(admission)


def h(label: str) -> str:
    return hashlib.sha256(label.encode()).hexdigest()


class Active:
    @staticmethod
    def resolve_active_prepare(db, *, entity_generation, store_module):
        return {
            "ok": True,
            "entity_generation": entity_generation,
            "causal_turn_id": "turn-7",
            "task_text": "exact task",
            "turn_binding_digest": h("turn-binding"),
            "boot_binding_digest": h("boot-binding"),
            "activation_digest": h("activation"),
            "zero_identity_digest": h("zero"),
            "grf_digest": h("grf"),
            "hyperposition_digest": h("hyper"),
            "local_model_digest": h("model"),
            "jspace_profile_digest": h("jspace"),
            "jacobian_lens_digest": h("lens"),
            "workspace_calibration_digest": h("cal"),
            "workspace_digest": h("workspace"),
            "selected_workspace_slots": ["slot-a"],
            "contradiction_state": "NONE",
            "provenance_refs": ["turn:test"],
            "required_zero_mode": "NORMAL",
        }


class Store:
    pass


class Capability:
    @staticmethod
    def resolve_from_profile(profile):
        return {
            "ok": True,
            "target_engine_class": "ADAPTIVE_BACKEND",
            "ucf_engine_class": "adaptive_backend",
            "jspace_mode": "COMPILED_EXTERNAL",
            "binding_digest": h("cap-binding"),
            "capability_receipt_digest": h("cap-receipt"),
        }


class Capsule:
    @staticmethod
    def compile_workspace_capsule(**kw):
        return {"mode": "WORKSPACE_BOUND", "capsule_digest": h("capsule"), **kw}


class Packet:
    @staticmethod
    def compile_packet(capsule, *, target_engine_class, jspace_mode, inference, system, user):
        basis = {"capsule": capsule["capsule_digest"], "target": target_engine_class, "mode": jspace_mode,
                 "inference": inference, "system": system, "user": user}
        return {"packet_digest": admission.sha256_obj(basis), "basis": basis}

    @staticmethod
    def validate(packet, capsule, *, inference, system, user, require_context):
        expected = Packet.compile_packet(capsule, target_engine_class=packet["basis"]["target"],
                                         jspace_mode=packet["basis"]["mode"], inference=inference,
                                         system=system, user=user)
        if expected["packet_digest"] != packet["packet_digest"] or not require_context:
            raise ValueError("PACKET_CONTEXT_MISMATCH")
        return {"ok": True}


MODULES = {"active": Active, "store": Store, "capability": Capability, "capsule": Capsule, "packet": Packet}


def profile():
    return {
        "inference": {"kind": "mock", "capability_binding": {"schema": "bound"}},
        "_runtime_profile_snapshot": {"profile_id": "p", "profile_hash": h("profile")},
    }


def data():
    state = h("state")
    packet = h("source-packet")
    return {
        "compiled": {"ok": True, "canonical_state_hash": state, "packet_hash": packet},
        "prompt": {"ok": True, "system": "system", "user": json.dumps({"CANONICAL_STATE_HASH": state, "PACKET_HASH": packet})},
        "invocation": {"expected_generation": 7, "causal_turn_id": "turn-7", "task_text": "exact task", "turn_binding_digest": h("turn-binding")},
    }


class AdmissionTests(unittest.TestCase):
    def test_exact_selector_active_capability_capsule_packet_chain(self):
        out = admission.admit(object(), profile=profile(), previous={"generation": 7}, data=data(), modules=MODULES)
        self.assertTrue(out["ok"])
        self.assertEqual(out["schema"], admission.SCHEMA)
        self.assertEqual(out["authority"], "CANDIDATE_INFERENCE_ONLY")
        self.assertFalse(out["admission_receipt"]["admission_effect_executed"])
        self.assertNotIn("candidate_result_digest", out["admission_receipt"])
        self.assertNotIn("canonical_write_committed", out["admission_receipt"])

    def test_selector_task_drift_fails_before_packet(self):
        bad = data(); bad["invocation"]["task_text"] = "other"
        with self.assertRaisesRegex(admission.AdmissionError, "INVOCATION_TASK_TEXT_MISMATCH"):
            admission.admit(object(), profile=profile(), previous={"generation": 7}, data=bad, modules=MODULES)

    def test_selector_stale_generation_fails_closed(self):
        bad = data(); bad["invocation"]["expected_generation"] = 6
        with self.assertRaisesRegex(admission.AdmissionError, "INVOCATION_STALE_GENERATION"):
            admission.admit(object(), profile=profile(), previous={"generation": 7}, data=bad, modules=MODULES)

    def test_prompt_compiled_identity_drift_fails_closed(self):
        bad = data(); payload = json.loads(bad["prompt"]["user"]); payload["PACKET_HASH"] = h("wrong"); bad["prompt"]["user"] = json.dumps(payload)
        with self.assertRaisesRegex(admission.AdmissionError, "PROMPT_PACKET_HASH_MISMATCH"):
            admission.admit(object(), profile=profile(), previous={"generation": 7}, data=bad, modules=MODULES)

    def test_abstained_capsule_cannot_reach_inference_packet(self):
        class AbstainCapsule(Capsule):
            @staticmethod
            def compile_workspace_capsule(**kw):
                return {"mode": "ABSTAINED", "capsule_digest": h("abstain")}
        mods = dict(MODULES); mods["capsule"] = AbstainCapsule
        with self.assertRaisesRegex(admission.AdmissionError, "ABSTAINED_CAPSULE_NOT_EXECUTABLE"):
            admission.admit(object(), profile=profile(), previous={"generation": 7}, data=data(), modules=mods)


if __name__ == "__main__":
    unittest.main()
