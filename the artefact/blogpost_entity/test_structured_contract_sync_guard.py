#!/usr/bin/env python3
import importlib.util
import pathlib
import unittest

MODULE_PATH = pathlib.Path(__file__).resolve().with_name("check_structured_contract_sync.py")
spec = importlib.util.spec_from_file_location("guard", MODULE_PATH)
guard = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(guard)


CONNECTED = '''
class ProfilePipelineRuntime:
    def __init__(self):
        self.allowed_effects = {
            "pipeline_profile_read",
            "pipeline_cognitive_fabric_admit",
            "inference_generate",
            "pipeline_cognitive_fabric_finalize",
        }
    def effect(self, kind, payload=None):
        dispatch = {
            "pipeline_profile_read": self._pipeline_profile_read,
            "pipeline_cognitive_fabric_admit": self._pipeline_cognitive_fabric_admit,
            "inference_generate": self._inference_generate,
            "pipeline_cognitive_fabric_finalize": self._pipeline_cognitive_fabric_finalize,
        }
        return dispatch[kind](payload or {})
    def _pipeline_profile_read(self, payload): return {"ok": True}
    def _pipeline_cognitive_fabric_admit(self, payload): return {"ok": True}
    def _inference_generate(self, payload):
        packet = payload["inference_packet_digest"]
        admission = payload["cognitive_fabric_admission_receipt_digest"]
        if not packet or not admission:
            return {"ok": False}
        return {"ok": True}
    def _pipeline_cognitive_fabric_finalize(self, payload):
        admitted = payload["admitted"]
        generated = payload["generated"]
        gated = payload["gated"]
        committed = payload["committed"]
        material = [admitted, generated, gated, committed]
        return {"ok": bool(material), "ucf_runtime_receipt_digest": "derived-by-real-validator"}
'''


class StructuredContractSyncGuardTests(unittest.TestCase):
    def test_comment_only_effect_names_do_not_count_as_support(self):
        poisoned = '''
class ProfilePipelineRuntime:
    """pipeline_profile_read pipeline_cognitive_fabric_admit inference_generate pipeline_cognitive_fabric_finalize"""
    def __init__(self):
        self.allowed_effects = {"legacy_only"}
    def effect(self, kind, payload=None):
        return {"ok": False}
    def _pipeline_profile_read(self, payload): return {"ok": True}
    def _pipeline_cognitive_fabric_admit(self, payload): return {"ok": True}
    def _inference_generate(self, payload): return {"ok": True}
    def _pipeline_cognitive_fabric_finalize(self, payload): return {"ok": True}
'''
        report = guard.runtime_effect_contract(poisoned)
        self.assertFalse(report["converged"])
        self.assertEqual(
            report["required_effect_bindings"],
            {
                "pipeline_profile_read": False,
                "pipeline_cognitive_fabric_admit": False,
                "inference_generate": False,
                "pipeline_cognitive_fabric_finalize": False,
            },
        )

    def test_real_allowed_dispatch_handler_binding_with_downstream_identity_counts(self):
        report = guard.runtime_effect_contract(CONNECTED)
        self.assertTrue(all(report["required_effect_bindings"].values()))
        downstream = report["downstream_identity"]
        self.assertTrue(downstream["inference_identity_bound"])
        self.assertTrue(downstream["finalizer_terminal_ancestry_bound"])
        self.assertTrue(downstream["finalizer_exposes_distinct_digest"])
        self.assertEqual(downstream["finalizer_forbidden_self_calls"], [])
        self.assertTrue(downstream["semantic_floor"])
        self.assertTrue(report["converged"])

    def test_names_bound_but_downstream_admission_identity_dropped_stays_closed(self):
        disconnected = '''
class ProfilePipelineRuntime:
    def __init__(self):
        self.allowed_effects = {
            "pipeline_profile_read", "pipeline_cognitive_fabric_admit",
            "inference_generate", "pipeline_cognitive_fabric_finalize",
        }
    def effect(self, kind, payload=None):
        dispatch = {
            "pipeline_profile_read": self._pipeline_profile_read,
            "pipeline_cognitive_fabric_admit": self._pipeline_cognitive_fabric_admit,
            "inference_generate": self._inference_generate,
            "pipeline_cognitive_fabric_finalize": self._pipeline_cognitive_fabric_finalize,
        }
        return dispatch[kind](payload or {})
    def _pipeline_profile_read(self, payload): return {"ok": True}
    def _pipeline_cognitive_fabric_admit(self, payload): return {"ok": True}
    def _inference_generate(self, payload):
        return {"ok": True}
    def _pipeline_cognitive_fabric_finalize(self, payload):
        admitted = payload["admitted"]
        generated = payload["generated"]
        gated = payload["gated"]
        committed = payload["committed"]
        return {"ok": bool([admitted, generated, gated, committed]),
                "ucf_runtime_receipt_digest": "fake"}
'''
        report = guard.runtime_effect_contract(disconnected)
        self.assertTrue(all(report["required_effect_bindings"].values()))
        self.assertFalse(report["downstream_identity"]["inference_identity_bound"])
        self.assertFalse(report["downstream_identity"]["semantic_floor"])
        self.assertFalse(report["converged"])

    def test_finalizer_must_bind_terminal_ancestry_and_expose_final_digest(self):
        disconnected = CONNECTED.replace(
            '''    def _pipeline_cognitive_fabric_finalize(self, payload):\n        admitted = payload["admitted"]\n        generated = payload["generated"]\n        gated = payload["gated"]\n        committed = payload["committed"]\n        material = [admitted, generated, gated, committed]\n        return {"ok": bool(material), "ucf_runtime_receipt_digest": "derived-by-real-validator"}\n''',
            '''    def _pipeline_cognitive_fabric_finalize(self, payload):\n        return {"ok": True}\n''',
        )
        report = guard.runtime_effect_contract(disconnected)
        self.assertFalse(report["downstream_identity"]["finalizer_terminal_ancestry_bound"])
        self.assertFalse(report["downstream_identity"]["finalizer_exposes_distinct_digest"])
        self.assertFalse(report["converged"])

    def test_finalizer_cannot_execute_second_commit_or_effect(self):
        poisoned = CONNECTED.replace(
            '        material = [admitted, generated, gated, committed]\n',
            '        material = [admitted, generated, gated, committed]\n        self._pipeline_commit({})\n        self.effect("anything", {})\n',
        )
        report = guard.runtime_effect_contract(poisoned)
        self.assertEqual(
            report["downstream_identity"]["finalizer_forbidden_self_calls"],
            ["_pipeline_commit", "effect"],
        )
        self.assertFalse(report["converged"])

    def test_missing_pre_admission_handler_keeps_gate_closed(self):
        bypass = CONNECTED.replace(
            '            "pipeline_cognitive_fabric_admit",\n', ''
        ).replace(
            '            "pipeline_cognitive_fabric_admit": self._pipeline_cognitive_fabric_admit,\n', ''
        ).replace(
            '    def _pipeline_cognitive_fabric_admit(self, payload): return {"ok": True}\n', ''
        )
        report = guard.runtime_effect_contract(bypass)
        self.assertFalse(report["required_effect_bindings"]["pipeline_cognitive_fabric_admit"])
        self.assertFalse(report["converged"])

    def test_missing_post_turn_finalizer_keeps_gate_closed(self):
        premature = CONNECTED.replace(
            '            "pipeline_cognitive_fabric_finalize",\n', ''
        ).replace(
            '            "pipeline_cognitive_fabric_finalize": self._pipeline_cognitive_fabric_finalize,\n', ''
        )
        start = premature.find('    def _pipeline_cognitive_fabric_finalize')
        if start != -1:
            premature = premature[:start]
        report = guard.runtime_effect_contract(premature)
        self.assertFalse(report["required_effect_bindings"]["pipeline_cognitive_fabric_finalize"])
        self.assertFalse(report["converged"])

    def test_legacy_effect_in_dispatch_keeps_gate_closed(self):
        mixed = CONNECTED.replace(
            '            "pipeline_cognitive_fabric_finalize",\n',
            '            "pipeline_cognitive_fabric_finalize",\n            "profile_load",\n',
        ).replace(
            '            "pipeline_cognitive_fabric_finalize": self._pipeline_cognitive_fabric_finalize,\n',
            '            "pipeline_cognitive_fabric_finalize": self._pipeline_cognitive_fabric_finalize,\n            "profile_load": self._profile_load,\n',
        ) + '    def _profile_load(self, payload): return {"ok": True}\n'
        report = guard.runtime_effect_contract(mixed)
        self.assertFalse(report["legacy_effects_absent"])
        self.assertFalse(report["converged"])


if __name__ == "__main__":
    unittest.main()
