#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools/trigger1_openrouter_qwen06_route_bound_execute.py"


def load_module():
    spec = importlib.util.spec_from_file_location("trigger1_openrouter_qwen06_route_bound_execute", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def payload(*, provider="ProviderA", system_fingerprint="fp-A", is_byok=False, pipeline=None):
    return {
        "id": "gen-fixture",
        "model": "qwen/qwen3-0.6b-04-28:free",
        "system_fingerprint": system_fingerprint,
        "choices": [{"message": {"content": "A"}, "finish_reason": "stop"}],
        "openrouter_metadata": {
            "requested": "qwen/qwen3-0.6b-04-28:free",
            "strategy": "direct",
            "region": "iad",
            "attempt": 1,
            "is_byok": is_byok,
            "endpoints": {"total": 1, "available": [{"provider": provider, "model": "qwen/qwen3-0.6b-04-28:free", "selected": True}]},
            "pipeline": [] if pipeline is None else pipeline,
        },
    }


def successful_rows(mod, *, provider="ProviderA", system_fingerprint="fp-A"):
    observation = mod.extract_observation_route_bound(payload(provider=provider, system_fingerprint=system_fingerprint))
    rows = []
    for seed in (2718, 3141):
        for control in mod.base.CONTROLS:
            rows.append({"status": "SUCCESS", "control": control, "seed": seed, "score": 1.0 if control == "+VECTOR" else 0.0, "binding_stable_after_call": True, "observation": observation})
    return rows


class RouteBoundExecutorTests(unittest.TestCase):
    def setUp(self):
        self.mod = load_module()

    def test_provider_call_enables_router_metadata_header(self):
        response = mock.MagicMock()
        response.__enter__.return_value = response
        response.status = 200
        response.headers.items.return_value = []
        response.read.return_value = b'{"choices":[]}'
        slot = mock.MagicMock()
        slot.return_value.__enter__.return_value = None
        slot.return_value.__exit__.return_value = None
        captured = {}
        def fake_urlopen(req, timeout):
            captured["headers"] = {k.lower(): v for k, v in req.header_items()}
            return response
        with mock.patch.object(self.mod.base, "quota_slot", slot), mock.patch.object(self.mod.base, "quota_observe"), mock.patch.object(self.mod.base.urllib.request, "urlopen", side_effect=fake_urlopen):
            status, _, _ = self.mod.provider_call_with_router_metadata("secret", {"model": "x"}, owner="o")
        self.assertEqual(200, status)
        self.assertEqual("enabled", captured["headers"]["x-openrouter-metadata"])

    def test_good_payload_has_execution_runtime_identity(self):
        obs = self.mod.extract_observation_route_bound(payload())
        self.assertNotIn("runtime_identity_error", obs)
        self.assertEqual("ProviderA", obs["runtime_route_identity"]["selected_provider"])
        self.assertEqual("fp-A", obs["execution_runtime_identity"]["system_fingerprint"])

    def test_missing_system_fingerprint_fails_closed(self):
        obs = self.mod.extract_observation_route_bound(payload(system_fingerprint=""))
        self.assertEqual("SYSTEM_FINGERPRINT_REQUIRED", obs["runtime_identity_error"])

    def test_byok_route_fails_closed(self):
        obs = self.mod.extract_observation_route_bound(payload(is_byok=True))
        self.assertEqual("BYOK_ROUTE_FORBIDDEN_FREE_ONLY", obs["runtime_identity_error"])

    def test_material_pipeline_fails_closed(self):
        obs = self.mod.extract_observation_route_bound(payload(pipeline=[{"type": "response-healing"}]))
        self.assertEqual("MATERIAL_ROUTER_PIPELINE_FORBIDDEN_FOR_CAUSAL_ATTRIBUTION", obs["runtime_identity_error"])

    def test_runtime_change_across_batch_is_rejected(self):
        rows = successful_rows(self.mod)
        rows[-1]["observation"] = self.mod.extract_observation_route_bound(payload(provider="ProviderB", system_fingerprint="fp-B"))
        result = self.mod.validate_execution_runtime_family(rows)
        self.assertFalse(result["stable_execution_runtime"])
        self.assertEqual(2, result["unique_execution_runtime_identities"])

    def test_full_six_control_holdout_same_runtime_passes_identity_only(self):
        result = self.mod.validate_execution_runtime_family(successful_rows(self.mod))
        self.assertTrue(result["stable_execution_runtime"])
        self.assertEqual(1, result["unique_execution_runtime_identities"])
        self.assertFalse(result["exact_model_weight_bytes_attested"])

    def test_positive_base_verdict_is_demoted_without_runtime_identity(self):
        calibration = [
            {"status":"SUCCESS","control":"+VECTOR","seed":1701,"gain":4.0,"score":2.0,"binding_stable_after_call":True,"observation":{"first_token":"A"}},
            {"status":"SUCCESS","control":"SIGN_FLIP","seed":1701,"gain":4.0,"score":-2.0,"binding_stable_after_call":True,"observation":{"first_token":"B"}},
        ]
        holdout = []
        for seed in (2718, 3141):
            for control in self.mod.base.CONTROLS:
                score = 3.0 if control == "+VECTOR" else (-2.0 if control == "SIGN_FLIP" else 0.0)
                token = "A" if control == "+VECTOR" else "B"
                if control in ("BASELINE", "NULL_VECTOR"):
                    token = "C"
                holdout.append({"status":"SUCCESS","control":control,"seed":seed,"gain":4.0,"score":score,"binding_stable_after_call":True,"observation":{"first_token":token}})
        verdict = self.mod.adjudicate_route_bound(calibration, holdout, 4.0)
        self.assertTrue(verdict["pre_runtime_identity_pass"])
        self.assertFalse(verdict["pass"])
        self.assertEqual("RUNTIME_IDENTITY_UNRESOLVED", verdict["classification"])


if __name__ == "__main__":
    unittest.main()
