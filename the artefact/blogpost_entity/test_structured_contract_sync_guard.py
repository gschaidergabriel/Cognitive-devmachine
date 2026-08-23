#!/usr/bin/env python3
import importlib.util
import pathlib
import unittest

MODULE_PATH = pathlib.Path(__file__).resolve().with_name("check_structured_contract_sync.py")
spec = importlib.util.spec_from_file_location("guard", MODULE_PATH)
guard = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(guard)


class StructuredContractSyncGuardTests(unittest.TestCase):
    def test_comment_only_effect_names_do_not_count_as_support(self):
        poisoned = '''
class ProfilePipelineRuntime:
    """pipeline_profile_read pipeline_cognitive_fabric_admit inference_generate"""
    def __init__(self):
        self.allowed_effects = {"legacy_only"}
    def effect(self, kind, payload=None):
        # Required effect names below are intentionally dead text.
        return {"ok": False}
    def _pipeline_profile_read(self, payload):
        return {"ok": True}
    def _pipeline_cognitive_fabric_admit(self, payload):
        return {"ok": True}
    def _inference_generate(self, payload):
        return {"ok": True}
'''
        report = guard.runtime_effect_contract(poisoned)
        self.assertFalse(report["converged"])
        self.assertEqual(
            report["required_effect_bindings"],
            {
                "pipeline_profile_read": False,
                "pipeline_cognitive_fabric_admit": False,
                "inference_generate": False,
            },
        )

    def test_name_bound_but_semantically_empty_handler_stays_closed(self):
        bound_stub = '''
class ProfilePipelineRuntime:
    def __init__(self):
        self.allowed_effects = {
            "pipeline_profile_read",
            "pipeline_cognitive_fabric_admit",
            "inference_generate",
        }
    def effect(self, kind, payload=None):
        dispatch = {
            "pipeline_profile_read": self._pipeline_profile_read,
            "pipeline_cognitive_fabric_admit": self._pipeline_cognitive_fabric_admit,
            "inference_generate": self._inference_generate,
        }
        return dispatch[kind](payload or {})
    def _pipeline_profile_read(self, payload):
        return {"ok": True}
    def _pipeline_cognitive_fabric_admit(self, payload):
        profile = payload.get("profile", {})
        return {
            "ok": True,
            "inference": profile.get("inference", {}),
            "system": "",
            "user": "",
            "inference_packet_digest": "0" * 64,
            "cognitive_fabric_receipt_digest": "f" * 64,
        }
    def _inference_generate(self, payload):
        return {"ok": True}
'''
        report = guard.runtime_effect_contract(bound_stub)
        self.assertTrue(all(report["required_effect_bindings"].values()))
        self.assertFalse(report["cognitive_fabric_handler"]["semantic_floor"])
        self.assertEqual(
            report["cognitive_fabric_handler"]["placeholder_digest_constructs"],
            ["repeat:0", "repeat:f"],
        )
        self.assertFalse(report["converged"])

    def test_real_chain_shaped_handler_counts_at_source_guard_scope(self):
        shaped = '''
class ProfilePipelineRuntime:
    def __init__(self):
        self.allowed_effects = {
            "pipeline_profile_read",
            "pipeline_cognitive_fabric_admit",
            "inference_generate",
        }
    def effect(self, kind, payload=None):
        dispatch = {
            "pipeline_profile_read": self._pipeline_profile_read,
            "pipeline_cognitive_fabric_admit": self._pipeline_cognitive_fabric_admit,
            "inference_generate": self._inference_generate,
        }
        return dispatch[kind](payload or {})
    def _pipeline_profile_read(self, payload):
        return {"ok": True}
    def _pipeline_cognitive_fabric_admit(self, payload):
        previous = payload["previous"]
        data = payload["data"]
        compiled = data["compiled"]
        prompt = data["prompt"]
        with self._read_only_db(payload["entity_db"]) as db:
            cognition = db.execute("SELECT 1").fetchone()
        capsule = compile_workspace_capsule(
            entity_generation=previous["generation"],
            causal_turn_id=compiled["packet_hash"],
            task_text=prompt["user"],
            zero_identity_digest=cognition["zero_identity_digest"],
            grf_digest=cognition["grf_digest"],
            hyperposition_digest=cognition["hyperposition_digest"],
            local_model_digest=cognition["local_model_digest"],
            jacobian_lens_digest=cognition["jacobian_lens_digest"],
            workspace_digest=cognition["workspace_digest"],
            selected_workspace_slots=cognition["selected_workspace_slots"],
            contradiction_state=cognition["contradiction_state"],
            provenance_refs=cognition["provenance_refs"],
            required_zero_mode=cognition["required_zero_mode"],
        )
        packet = compile_packet(capsule, target_engine_class="ADAPTIVE_BACKEND", jspace_mode="PLAIN_COMPATIBILITY")
        receipt_digest = _sha256_text(
            packet["packet_digest"] + compiled["canonical_state_hash"] + compiled["packet_hash"]
        )
        return {
            "ok": True,
            "inference": payload["profile"]["inference"],
            "system": prompt["system"],
            "user": prompt["user"],
            "inference_packet_digest": packet["packet_digest"],
            "cognitive_fabric_receipt_digest": receipt_digest,
        }
    def _read_only_db(self, path):
        return path
    def _inference_generate(self, payload):
        return {"ok": True}
'''
        report = guard.runtime_effect_contract(shaped)
        self.assertTrue(all(report["required_effect_bindings"].values()))
        fabric = report["cognitive_fabric_handler"]
        self.assertTrue(fabric["miniunifieddb_read_only"])
        self.assertTrue(fabric["workspace_capsule_compiler"])
        self.assertTrue(fabric["inference_packet_compiler"])
        self.assertTrue(fabric["required_identity_keys_present"])
        self.assertTrue(fabric["digest_construction"])
        self.assertEqual(fabric["placeholder_digest_constructs"], [])
        self.assertEqual(fabric["forbidden_self_calls"], [])
        self.assertTrue(fabric["semantic_floor"])
        self.assertTrue(report["converged"])

    def test_missing_cognitive_fabric_handler_keeps_gate_closed(self):
        bypass = '''
class ProfilePipelineRuntime:
    def __init__(self):
        self.allowed_effects = {"pipeline_profile_read", "inference_generate"}
    def effect(self, kind, payload=None):
        dispatch = {
            "pipeline_profile_read": self._pipeline_profile_read,
            "inference_generate": self._inference_generate,
        }
        return dispatch[kind](payload or {})
    def _pipeline_profile_read(self, payload): return {"ok": True}
    def _inference_generate(self, payload): return {"ok": True}
'''
        report = guard.runtime_effect_contract(bypass)
        self.assertFalse(report["required_effect_bindings"]["pipeline_cognitive_fabric_admit"])
        self.assertFalse(report["cognitive_fabric_handler"]["semantic_floor"])
        self.assertFalse(report["converged"])

    def test_admission_time_inference_or_commit_keeps_gate_closed(self):
        poisoned = '''
class ProfilePipelineRuntime:
    def __init__(self):
        self.allowed_effects = {"pipeline_profile_read", "pipeline_cognitive_fabric_admit", "inference_generate"}
    def effect(self, kind, payload=None):
        dispatch = {
            "pipeline_profile_read": self._pipeline_profile_read,
            "pipeline_cognitive_fabric_admit": self._pipeline_cognitive_fabric_admit,
            "inference_generate": self._inference_generate,
        }
        return dispatch[kind](payload or {})
    def _pipeline_profile_read(self, payload): return {"ok": True}
    def _pipeline_cognitive_fabric_admit(self, payload):
        previous = payload["previous"]
        data = payload["data"]
        compiled = data["compiled"]
        prompt = data["prompt"]
        with self._read_only_db(payload["entity_db"]): pass
        capsule = compile_workspace_capsule(entity_generation=previous["generation"])
        packet = compile_packet(capsule)
        receipt = _sha256_text(compiled["canonical_state_hash"] + compiled["packet_hash"])
        self._inference_generate({})
        self._pipeline_commit({})
        return {"inference_packet_digest": packet["packet_digest"], "cognitive_fabric_receipt_digest": receipt}
    def _read_only_db(self, path): return path
    def _inference_generate(self, payload): return {"ok": True}
    def _pipeline_commit(self, payload): return {"ok": True}
'''
        report = guard.runtime_effect_contract(poisoned)
        self.assertEqual(
            report["cognitive_fabric_handler"]["forbidden_self_calls"],
            ["_inference_generate", "_pipeline_commit"],
        )
        self.assertFalse(report["cognitive_fabric_handler"]["semantic_floor"])
        self.assertFalse(report["converged"])

    def test_legacy_effect_in_dispatch_keeps_gate_closed(self):
        mixed = '''
class ProfilePipelineRuntime:
    def __init__(self):
        self.allowed_effects = {
            "pipeline_profile_read",
            "pipeline_cognitive_fabric_admit",
            "inference_generate",
            "profile_load",
        }
    def effect(self, kind, payload=None):
        dispatch = {
            "pipeline_profile_read": self._pipeline_profile_read,
            "pipeline_cognitive_fabric_admit": self._pipeline_cognitive_fabric_admit,
            "inference_generate": self._inference_generate,
            "profile_load": self._profile_load,
        }
        return dispatch[kind](payload or {})
    def _pipeline_profile_read(self, payload): return {"ok": True}
    def _pipeline_cognitive_fabric_admit(self, payload): return {"ok": True}
    def _inference_generate(self, payload): return {"ok": True}
    def _profile_load(self, payload): return {"ok": True}
'''
        report = guard.runtime_effect_contract(mixed)
        self.assertFalse(report["legacy_effects_absent"])
        self.assertFalse(report["converged"])


if __name__ == "__main__":
    unittest.main()
