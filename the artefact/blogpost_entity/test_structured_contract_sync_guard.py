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
    """pipeline_profile_read inference_generate"""
    def __init__(self):
        self.allowed_effects = {"legacy_only"}
    def effect(self, kind, payload=None):
        # "pipeline_profile_read" and "inference_generate" are intentionally dead text.
        return {"ok": False}
    def _pipeline_profile_read(self, payload):
        return {"ok": True}
    def _inference_generate(self, payload):
        return {"ok": True}
'''
        report = guard.runtime_effect_contract(poisoned)
        self.assertFalse(report["converged"])
        self.assertEqual(
            report["required_effect_bindings"],
            {"pipeline_profile_read": False, "inference_generate": False},
        )

    def test_real_allowed_dispatch_handler_binding_counts(self):
        bound = '''
class ProfilePipelineRuntime:
    def __init__(self):
        self.allowed_effects = {"pipeline_profile_read", "inference_generate"}
    def effect(self, kind, payload=None):
        dispatch = {
            "pipeline_profile_read": self._pipeline_profile_read,
            "inference_generate": self._inference_generate,
        }
        return dispatch[kind](payload or {})
    def _pipeline_profile_read(self, payload):
        return {"ok": True}
    def _inference_generate(self, payload):
        return {"ok": True}
'''
        report = guard.runtime_effect_contract(bound)
        self.assertTrue(report["converged"])

    def test_legacy_effect_in_dispatch_keeps_gate_closed(self):
        mixed = '''
class ProfilePipelineRuntime:
    def __init__(self):
        self.allowed_effects = {"pipeline_profile_read", "inference_generate", "profile_load"}
    def effect(self, kind, payload=None):
        dispatch = {
            "pipeline_profile_read": self._pipeline_profile_read,
            "inference_generate": self._inference_generate,
            "profile_load": self._profile_load,
        }
        return dispatch[kind](payload or {})
    def _pipeline_profile_read(self, payload): return {"ok": True}
    def _inference_generate(self, payload): return {"ok": True}
    def _profile_load(self, payload): return {"ok": True}
'''
        report = guard.runtime_effect_contract(mixed)
        self.assertFalse(report["legacy_effects_absent"])
        self.assertFalse(report["converged"])

    def test_ucf_ordering_bypass_poison_fails_closed(self):
        # Unusual discriminator for this GO: UCF is present and the inference map names
        # an admitted envelope, but the only UCF phase occurs after inference. Presence-
        # only checking would false-green; causal ordering must fail closed.
        poisoned = '''
module clay.entity_pipeline
fn run(entity_db:String, source_db:String, secret_file:String)->Map {
  let prompt = phase("pipeline_build_prompt",entity_db,source_db,map_new(),map_new(),map_new())
  let admitted = map_new()
  let infer = map_new()
  map_set(infer,"inference",admitted.inference)
  map_set(infer,"system",admitted.system)
  map_set(infer,"user",admitted.user)
  map_set(infer,"inference_packet_digest",admitted.inference_packet_digest)
  map_set(infer,"cognitive_fabric_receipt_digest",admitted.cognitive_fabric_receipt_digest)
  let generated = effect("inference_generate",infer)
  let too_late = phase("pipeline_cognitive_fabric_admit",entity_db,source_db,map_new(),map_new(),map_new())
  return generated
}
'''
        report = guard.clay_cognitive_path_contract(poisoned)
        self.assertTrue(report["single_cognitive_fabric_admission"])
        self.assertTrue(report["inference_uses_admitted_envelope"])
        self.assertFalse(report["ordered_prompt_ucf_inference"])
        self.assertFalse(report["converged"])

    def test_prompt_ucf_inference_order_with_admitted_envelope_converges(self):
        bound = '''
module clay.entity_pipeline
fn run(entity_db:String, source_db:String, secret_file:String)->Map {
  let prompt = phase("pipeline_build_prompt",entity_db,source_db,map_new(),map_new(),map_new())
  let admitted = phase("pipeline_cognitive_fabric_admit",entity_db,source_db,map_new(),map_new(),map_new())
  let infer = map_new()
  map_set(infer,"inference",admitted.inference)
  map_set(infer,"system",admitted.system)
  map_set(infer,"user",admitted.user)
  map_set(infer,"inference_packet_digest",admitted.inference_packet_digest)
  map_set(infer,"cognitive_fabric_receipt_digest",admitted.cognitive_fabric_receipt_digest)
  let generated = effect("inference_generate",infer)
  return generated
}
'''
        report = guard.clay_cognitive_path_contract(bound)
        self.assertEqual(
            report["call_sequence"],
            ["pipeline_build_prompt", "pipeline_cognitive_fabric_admit", "inference_generate"],
        )
        self.assertTrue(report["converged"])

    def test_raw_profile_or_prompt_inference_bypass_is_rejected(self):
        bypassed = '''
module clay.entity_pipeline
fn run(entity_db:String, source_db:String, secret_file:String)->Map {
  let prompt = phase("pipeline_build_prompt",entity_db,source_db,map_new(),map_new(),map_new())
  let admitted = phase("pipeline_cognitive_fabric_admit",entity_db,source_db,map_new(),map_new(),map_new())
  let infer = map_new()
  map_set(infer,"inference",profile.inference)
  map_set(infer,"system",prompt.system)
  map_set(infer,"user",prompt.user)
  map_set(infer,"inference_packet_digest",admitted.inference_packet_digest)
  map_set(infer,"cognitive_fabric_receipt_digest",admitted.cognitive_fabric_receipt_digest)
  let generated = effect("inference_generate",infer)
  return generated
}
'''
        report = guard.clay_cognitive_path_contract(bypassed)
        self.assertTrue(report["ordered_prompt_ucf_inference"])
        self.assertFalse(report["raw_prompt_profile_bypass_absent"])
        self.assertFalse(report["converged"])


if __name__ == "__main__":
    unittest.main()
