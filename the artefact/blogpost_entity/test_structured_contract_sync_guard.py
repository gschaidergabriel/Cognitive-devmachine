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
        # Required names are intentionally dead text.
        return {"ok": False}
    def _pipeline_profile_read(self, payload): return {"ok": True}
    def _pipeline_cognitive_fabric_admit(self, payload): return {"ok": True}
    def _inference_generate(self, payload): return {"ok": True}
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

    def test_real_allowed_dispatch_handler_binding_counts(self):
        bound = '''
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
    def _pipeline_profile_read(self, payload): return {"ok": True}
    def _pipeline_cognitive_fabric_admit(self, payload): return {"ok": True}
    def _inference_generate(self, payload): return {"ok": True}
'''
        report = guard.runtime_effect_contract(bound)
        self.assertTrue(report["converged"])

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

    @staticmethod
    def causal_clay(inference_lines: str) -> str:
        return f'''
fn run(entity_db:String, source_db:String, secret_file:String)->Map {{
  let prompt = phase("pipeline_build_prompt",entity_db,source_db,profile,previous,compiled)
  let cognition_data = map_new()
  map_set(cognition_data,"compiled",compiled)
  map_set(cognition_data,"prompt",prompt)
  let admitted = phase("pipeline_cognitive_fabric_admit",entity_db,source_db,profile,previous,cognition_data)
  let infer = map_new()
  {inference_lines}
  let generated = effect("inference_generate",infer)
  map_set(gate_data,"cognitive_fabric",admitted)
  map_set(commit_data,"cognitive_fabric",admitted)
  return generated
}}
'''

    def test_cognitive_fabric_sidecar_with_raw_prompt_bypass_fails(self):
        source = self.causal_clay('''
map_set(infer,"inference",profile.inference)
map_set(infer,"system",prompt.system)
map_set(infer,"user",prompt.user)
map_set(infer,"inference_packet_digest",admitted.inference_packet_digest)
map_set(infer,"cognitive_fabric_receipt_digest",admitted.cognitive_fabric_receipt_digest)
''')
        report = guard.clay_cognitive_contract(source)
        self.assertTrue(report["ordered_prompt_fabric_inference"])
        self.assertFalse(report["raw_prompt_profile_inference_bypass_absent"])
        self.assertFalse(report["causal_source_wiring"])

    def test_cognitive_fabric_after_inference_fails_ordering(self):
        source = self.causal_clay('''
map_set(infer,"inference",admitted.inference)
map_set(infer,"system",admitted.system)
map_set(infer,"user",admitted.user)
map_set(infer,"inference_packet_digest",admitted.inference_packet_digest)
map_set(infer,"cognitive_fabric_receipt_digest",admitted.cognitive_fabric_receipt_digest)
''')
        source = source.replace(
            'let admitted = phase("pipeline_cognitive_fabric_admit",entity_db,source_db,profile,previous,cognition_data)',
            'let admitted = map_new()',
        ).replace(
            'let generated = effect("inference_generate",infer)',
            'let generated = effect("inference_generate",infer)\n  let late = phase("pipeline_cognitive_fabric_admit",entity_db,source_db,profile,previous,cognition_data)',
        )
        report = guard.clay_cognitive_contract(source)
        self.assertFalse(report["ordered_prompt_fabric_inference"])
        self.assertFalse(report["causal_source_wiring"])

    def test_admitted_fabric_envelope_is_causal(self):
        source = self.causal_clay('''
map_set(infer,"inference",admitted.inference)
map_set(infer,"system",admitted.system)
map_set(infer,"user",admitted.user)
map_set(infer,"inference_packet_digest",admitted.inference_packet_digest)
map_set(infer,"cognitive_fabric_receipt_digest",admitted.cognitive_fabric_receipt_digest)
''')
        report = guard.clay_cognitive_contract(source)
        self.assertTrue(report["causal_source_wiring"])

    def test_current_canonical_clay_has_causal_fabric_wiring(self):
        source = MODULE_PATH.with_name("BLOGPOST_ENTITY.clay").read_text(encoding="utf-8")
        report = guard.clay_cognitive_contract(source)
        self.assertTrue(report["causal_source_wiring"])


if __name__ == "__main__":
    unittest.main()
