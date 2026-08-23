import hashlib
import json
import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
import pipeline_cognitive_fabric_admission_v1 as sut


def h(label):
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
        for name in FIELDS:
            out[name] = h(name)
        if expected_activation_digest is not None and expected_activation_digest != out["activation_digest"]:
            raise ValueError("ACTIVE_TURN_DIGEST_MISMATCH")
        return out


class Semantic:
    version = "v1"
    authority = {
        "durable_state": "MiniUnifiedDB",
        "routing_only": True,
        "candidate_configuration_only": True,
        "direct_truth_authority": False,
        "direct_effect_authority": False,
    }
    mutate_field = None
    calls = 0

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
        cls.calls += 1
        objects = {}
        for name in FIELDS:
            object_digest = h(name)
            if cls.mutate_field == name:
                object_digest = h("drift:" + name)
            objects[name] = {
                "object_kind": name.upper(),
                "object_version": cls.version,
                "object_digest": object_digest,
                "payload_digest": h("payload:" + cls.version + ":" + name),
                "provenance_refs": ["semantic:" + cls.version + ":" + name],
                "admission_receipt_digest": h("admit:" + cls.version + ":" + name),
                "admitted_generation": entity_generation,
            }
        return {
            "ok": True,
            "schema": "MINIUNIFIEDDB_COGNITION_SEMANTIC_RESOLUTION/v1",
            "entity_generation": entity_generation,
            "causal_turn_id": causal_turn_id,
            "turn_binding_digest": expected_turn_binding_digest,
            "boot_binding_digest": h("boot-binding"),
            "task_sha256": h(task_text),
            "workspace_digest": h("workspace"),
            "objects": objects,
            "authority": dict(cls.authority),
        }


class AmbiguousSemantic:
    @staticmethod
    def resolve_prepare_bundle(*args, **kwargs):
        raise ValueError("COGNITION_OBJECT_VERSION_AMBIGUOUS:JSPACE_PROFILE")


class Capsule:
    calls = 0

    @classmethod
    def compile_workspace_capsule(cls, **kw):
        cls.calls += 1
        return {
            "mode": "WORKSPACE_BOUND",
            "capsule_digest": h(json.dumps(kw, sort_keys=True)),
        }


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
    @classmethod
    def resolve_bound_route(cls, profile, prepare, *, expected_generation):
        binding = profile["inference"]["capability_binding"]
        snapshot = profile["_runtime_profile_snapshot"]
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
            "route_digest": h("route"),
            "authority": "ROUTING_ONLY_BOUND_TO_CANONICAL_PREPARE",
        }


class SemanticBindingTests(unittest.TestCase):
    def setUp(self):
        Semantic.version = "v1"
        Semantic.mutate_field = None
        Semantic.authority = {
            "durable_state": "MiniUnifiedDB",
            "routing_only": True,
            "candidate_configuration_only": True,
            "direct_truth_authority": False,
            "direct_effect_authority": False,
        }
        Semantic.calls = 0
        Capsule.calls = 0

    @staticmethod
    def invocation():
        return {
            "expected_generation": 7,
            "causal_turn_id": "turn-1",
            "task_text": "measure first",
            "turn_binding_digest": h("turn-binding"),
        }

    @staticmethod
    def profile():
        return {
            "profile_id": "p1",
            "_runtime_profile_snapshot": {
                "profile_id": "p1",
                "profile_hash": h("profile"),
            },
            "inference": {
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
            },
        }

    @staticmethod
    def prompt():
        return {
            "system": "SYS",
            "user": json.dumps(
                {
                    "CANONICAL_STATE_HASH": h("state"),
                    "PACKET_HASH": h("source-packet"),
                    "payload": "USR",
                },
                sort_keys=True,
            ),
        }

    def call(self, **overrides):
        args = {
            "db": object(),
            "entity_generation": 7,
            "invocation": self.invocation(),
            "compiled": {
                "canonical_state_hash": h("state"),
                "packet_hash": h("source-packet"),
            },
            "prompt": self.prompt(),
            "profile": self.profile(),
            "expected_activation_digest": h("activation"),
            "origin": "go",
            "active_turn_module": Active,
            "semantic_module": Semantic,
            "capsule_module": Capsule,
            "packet_module": Packet,
            "capability_module": Capability,
        }
        args.update(overrides)
        return sut.build_pre_inference_admission(**args)

    def test_semantic_object_versions_are_bound_into_admission_identity(self):
        first = self.call()
        self.assertTrue(first["ok"])
        self.assertEqual(Semantic.calls, 1)
        self.assertIn("cognition_semantic_binding_digest", first)
        self.assertEqual(
            first["admission_receipt"]["cognition_semantic_binding_digest"],
            first["cognition_semantic_binding_digest"],
        )
        self.assertEqual(
            first["cognition_semantic_objects"]["jspace_profile_digest"]["object_version"],
            "v1",
        )

        Semantic.version = "v2"
        second = self.call()
        self.assertNotEqual(
            first["cognition_semantic_binding_digest"],
            second["cognition_semantic_binding_digest"],
        )
        self.assertNotEqual(
            first["cognitive_fabric_receipt_digest"],
            second["cognitive_fabric_receipt_digest"],
        )

    def test_semantic_object_digest_drift_fails_before_capsule(self):
        Semantic.mutate_field = "jspace_profile_digest"
        with self.assertRaisesRegex(
            sut.CognitiveFabricAdmissionError,
            "SEMANTIC_OBJECT_DIGEST_DRIFT:jspace_profile_digest",
        ):
            self.call()
        self.assertEqual(Capsule.calls, 0)

    def test_semantic_authority_escalation_fails_before_capsule(self):
        Semantic.authority = dict(Semantic.authority)
        Semantic.authority["direct_truth_authority"] = True
        with self.assertRaisesRegex(
            sut.CognitiveFabricAdmissionError,
            "SEMANTIC_AUTHORITY_ESCALATION",
        ):
            self.call()
        self.assertEqual(Capsule.calls, 0)

    def test_ambiguous_object_version_aborts_before_capsule_or_packet(self):
        with self.assertRaisesRegex(
            ValueError,
            "COGNITION_OBJECT_VERSION_AMBIGUOUS:JSPACE_PROFILE",
        ):
            self.call(semantic_module=AmbiguousSemantic)
        self.assertEqual(Capsule.calls, 0)


if __name__ == "__main__":
    unittest.main()
