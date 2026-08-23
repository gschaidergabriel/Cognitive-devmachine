from __future__ import annotations

import copy
import hashlib
import unittest

import mini_cognitive_fabric_admission_v1 as admission


def h(tag: str) -> str:
    return hashlib.sha256(tag.encode()).hexdigest()


def binding() -> dict:
    return {
        "ok": True, "entity_generation": 7, "causal_turn_id": "turn-7",
        "activation_digest": h("activation"), "turn_binding_digest": h("turn-binding"),
        "boot_binding_digest": h("boot-binding"), "task_text": "task",
        "task_sha256": hashlib.sha256(b"task").hexdigest(), "workspace_digest": h("workspace"),
        "selected_workspace_slots": ["slot-a"], "contradiction_state": "RESOLVED",
        "activation_provenance_refs": ["activation:7"], "turn_provenance_refs": ["turn:7"],
        "boot_provenance_refs": ["boot:7"], "required_zero_mode": "COGNITIVE_MODULE_ON",
        "zero_identity_digest": h("zero"), "grf_digest": h("grf"),
        "hyperposition_digest": h("hyper"), "local_model_digest": h("model"),
        "jspace_profile_digest": h("jspace"), "jacobian_lens_digest": h("lens"),
        "workspace_calibration_digest": h("calibration"), "policy_authority_digest": h("policy"),
    }


def profile() -> dict:
    return {
        "profile_id": "p",
        "_runtime_profile_snapshot": {"profile_id": "p", "profile_hash": h("profile")},
        "inference": {"kind": "mock", "model": "m", "nested": {"temperature": 0.2},
                      "capability_binding": {"opaque": "canonical-binder-owned"}},
    }


def resolve_active(_db, **kwargs):
    assert kwargs == {"entity_generation": 7}
    return binding()


def resolve_capability(_profile):
    return {
        "ok": True, "binding_digest": h("cap-binding"),
        "capability_receipt_digest": h("cap-receipt"), "adapter_version": "adaptive/v1",
        "target_engine_class": "ADAPTIVE_BACKEND", "ucf_engine_class": "adaptive_backend",
        "jspace_mode": "COMPILED_EXTERNAL", "profile_id": "p", "profile_hash": h("profile"),
    }


def capsule(**kwargs):
    assert kwargs["entity_generation"] == 7
    assert kwargs["causal_turn_id"] == "turn-7"
    assert kwargs["task_text"] == "task"
    return {"mode": "WORKSPACE_BOUND", "capsule_digest": h("capsule")}


def packet(_capsule, *, target_engine_class, jspace_mode, inference, system, user):
    return {"packet_digest": admission.sha256_obj({
        "target": target_engine_class, "mode": jspace_mode,
        "inference": inference, "system": system, "user": user,
    })}


class AdmissionTests(unittest.TestCase):
    def call(self, **overrides):
        args = dict(
            db=None, profile=profile(), previous={"generation": 7},
            compiled={"canonical_state_hash": h("canonical"), "packet_hash": h("source-packet")},
            prompt={"system": "system", "user": "user"}, resolve_active_prepare=resolve_active,
            resolve_capability=resolve_capability, compile_workspace_capsule=capsule, compile_packet=packet,
        )
        args.update(overrides)
        return admission.prepare_admission(**args)

    def test_active_turn_plus_capability_binding_compiles_candidate_admission(self):
        out = self.call()
        self.assertTrue(out["ok"])
        self.assertEqual(out["admission_receipt"]["activation_digest"], h("activation"))
        self.assertEqual(out["admission_receipt"]["capability_binding_digest"], h("cap-binding"))
        self.assertEqual(out["admission_receipt"]["authority"], "CANDIDATE_INFERENCE_ONLY")
        self.assertEqual(out["cognitive_fabric_receipt_digest"], admission.sha256_obj(out["admission_receipt"]))

    def test_active_prepare_generation_drift_fails_closed(self):
        bad = binding(); bad["entity_generation"] = 6
        with self.assertRaisesRegex(admission.AdmissionError, "ACTIVE_PREPARE_GENERATION_MISMATCH"):
            self.call(resolve_active_prepare=lambda *_a, **_k: bad)

    def test_active_task_hash_drift_fails_closed(self):
        bad = binding(); bad["task_sha256"] = h("wrong-task")
        with self.assertRaisesRegex(admission.AdmissionError, "ACTIVE_TASK_BINDING_MISMATCH"):
            self.call(resolve_active_prepare=lambda *_a, **_k: bad)

    def test_capability_profile_snapshot_drift_fails_closed(self):
        bad = resolve_capability(profile()); bad["profile_hash"] = h("other-profile")
        with self.assertRaisesRegex(admission.AdmissionError, "CAPABILITY_PROFILE_HASH_DRIFT"):
            self.call(resolve_capability=lambda _p: bad)

    def test_post_admission_mutable_alias_poison_is_contained(self):
        p = profile()
        original = copy.deepcopy(p["inference"])
        out = self.call(profile=p)
        packet_digest_before = out["inference_packet_digest"]
        p["inference"]["nested"]["temperature"] = 9.9
        p["inference"]["model"] = "mutated"
        self.assertEqual(out["inference"], original)
        self.assertEqual(out["inference_packet_digest"], packet_digest_before)
        self.assertNotEqual(out["inference"], p["inference"])


if __name__ == "__main__":
    unittest.main()
