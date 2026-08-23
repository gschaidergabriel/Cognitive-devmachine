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
    """pipeline_profile_read pipeline_cognitive_fabric_prepare inference_generate pipeline_cognitive_fabric_finalize"""
    def __init__(self):
        self.allowed_effects = {"legacy_only"}
    def effect(self, kind, payload=None):
        return {"ok": False}
    def _pipeline_profile_read(self, payload): return {"ok": True}
    def _pipeline_cognitive_fabric_prepare(self, payload): return {"ok": True}
    def _inference_generate(self, payload): return {"ok": True}
    def _pipeline_cognitive_fabric_finalize(self, payload): return {"ok": True}
'''
        report = guard.runtime_effect_contract(poisoned)
        self.assertFalse(report["converged"])
        self.assertEqual(
            report["required_effect_bindings"],
            {
                "pipeline_profile_read": False,
                "pipeline_cognitive_fabric_prepare": False,
                "inference_generate": False,
                "pipeline_cognitive_fabric_finalize": False,
            },
        )

    def test_real_temporal_effect_bindings_count(self):
        bound = '''
class ProfilePipelineRuntime:
    def __init__(self):
        self.allowed_effects = {
            "pipeline_profile_read",
            "pipeline_cognitive_fabric_prepare",
            "inference_generate",
            "pipeline_cognitive_fabric_finalize",
        }
    def effect(self, kind, payload=None):
        dispatch = {
            "pipeline_profile_read": self._pipeline_profile_read,
            "pipeline_cognitive_fabric_prepare": self._pipeline_cognitive_fabric_prepare,
            "inference_generate": self._inference_generate,
            "pipeline_cognitive_fabric_finalize": self._pipeline_cognitive_fabric_finalize,
        }
        return dispatch[kind](payload or {})
    def _pipeline_profile_read(self, payload): return {"ok": True}
    def _pipeline_cognitive_fabric_prepare(self, payload): return {"ok": True}
    def _inference_generate(self, payload): return {"ok": True}
    def _pipeline_cognitive_fabric_finalize(self, payload): return {"ok": True}
'''
        report = guard.runtime_effect_contract(bound)
        self.assertTrue(report["converged"])

    def test_missing_finalize_keeps_gate_closed(self):
        bypass = '''
class ProfilePipelineRuntime:
    def __init__(self):
        self.allowed_effects = {
            "pipeline_profile_read",
            "pipeline_cognitive_fabric_prepare",
            "inference_generate",
        }
    def effect(self, kind, payload=None):
        dispatch = {
            "pipeline_profile_read": self._pipeline_profile_read,
            "pipeline_cognitive_fabric_prepare": self._pipeline_cognitive_fabric_prepare,
            "inference_generate": self._inference_generate,
        }
        return dispatch[kind](payload or {})
    def _pipeline_profile_read(self, payload): return {"ok": True}
    def _pipeline_cognitive_fabric_prepare(self, payload): return {"ok": True}
    def _inference_generate(self, payload): return {"ok": True}
'''
        report = guard.runtime_effect_contract(bypass)
        self.assertFalse(report["required_effect_bindings"]["pipeline_cognitive_fabric_finalize"])
        self.assertFalse(report["converged"])

    def test_legacy_one_phase_admit_keeps_gate_closed(self):
        mixed = '''
class ProfilePipelineRuntime:
    def __init__(self):
        self.allowed_effects = {
            "pipeline_profile_read",
            "pipeline_cognitive_fabric_prepare",
            "inference_generate",
            "pipeline_cognitive_fabric_finalize",
            "pipeline_cognitive_fabric_admit",
        }
    def effect(self, kind, payload=None):
        dispatch = {
            "pipeline_profile_read": self._pipeline_profile_read,
            "pipeline_cognitive_fabric_prepare": self._pipeline_cognitive_fabric_prepare,
            "inference_generate": self._inference_generate,
            "pipeline_cognitive_fabric_finalize": self._pipeline_cognitive_fabric_finalize,
            "pipeline_cognitive_fabric_admit": self._pipeline_cognitive_fabric_admit,
        }
        return dispatch[kind](payload or {})
    def _pipeline_profile_read(self, payload): return {"ok": True}
    def _pipeline_cognitive_fabric_prepare(self, payload): return {"ok": True}
    def _inference_generate(self, payload): return {"ok": True}
    def _pipeline_cognitive_fabric_finalize(self, payload): return {"ok": True}
    def _pipeline_cognitive_fabric_admit(self, payload): return {"ok": True}
'''
        report = guard.runtime_effect_contract(mixed)
        self.assertFalse(report["legacy_effects_absent"])
        self.assertFalse(report["converged"])


if __name__ == "__main__":
    unittest.main()
