#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools/trigger1_openrouter_runtime_identity.py"


def load_module():
    spec = importlib.util.spec_from_file_location("trigger1_openrouter_runtime_identity", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def payload(provider="ProviderA", model="qwen/qwen3-0.6b-04-28:free", attempt=1, pipeline=None):
    return {
        "openrouter_metadata": {
            "requested": "qwen/qwen3-0.6b-04-28:free",
            "strategy": "direct",
            "region": "iad",
            "attempt": attempt,
            "is_byok": False,
            "endpoints": {
                "total": 1,
                "available": [
                    {"provider": provider, "model": model, "selected": True}
                ],
            },
            "pipeline": [] if pipeline is None else pipeline,
        }
    }


class RuntimeRouteIdentityTests(unittest.TestCase):
    def setUp(self):
        self.mod = load_module()

    def test_extracts_selected_route_and_keeps_quantization_unknown(self):
        result = self.mod.extract_runtime_route_identity(payload())
        self.assertEqual("ProviderA", result["selected_provider"])
        self.assertEqual("qwen/qwen3-0.6b-04-28:free", result["selected_model"])
        self.assertEqual(1, result["attempt"])
        self.assertEqual(64, len(result["route_identity_sha256"]))
        self.assertEqual("UNKNOWN_NOT_ATTESTED_BY_ROUTER_METADATA", result["quantization"])
        self.assertFalse(result["exact_model_weight_bytes_attested"])

    def test_missing_metadata_fails_closed(self):
        with self.assertRaisesRegex(
            self.mod.RuntimeRouteIdentityError,
            "OPENROUTER_METADATA_REQUIRED",
        ):
            self.mod.extract_runtime_route_identity({})

    def test_retry_or_fallback_attempt_fails_closed(self):
        with self.assertRaisesRegex(
            self.mod.RuntimeRouteIdentityError,
            "FIRST_ATTEMPT_ROUTE_REQUIRED",
        ):
            self.mod.extract_runtime_route_identity(payload(attempt=2))

    def test_two_selected_endpoints_fail_closed(self):
        p = payload()
        p["openrouter_metadata"]["endpoints"]["available"].append(
            {"provider": "ProviderB", "model": "same", "selected": True}
        )
        with self.assertRaisesRegex(
            self.mod.RuntimeRouteIdentityError,
            "EXACTLY_ONE_SELECTED_ENDPOINT_REQUIRED",
        ):
            self.mod.extract_runtime_route_identity(p)

    def test_six_controls_same_route_pass_route_component_only(self):
        identity = self.mod.extract_runtime_route_identity(payload())
        rows = []
        for seed, control in enumerate(self.mod.REQUIRED_CONTROLS, start=1):
            rows.append({
                "status": "SUCCESS",
                "control": control,
                "seed": seed,
                "observation": {"runtime_route_identity": identity},
            })
        result = self.mod.validate_control_family_runtime_identity(rows)
        self.assertTrue(result["stable_selected_route"])
        self.assertEqual(1, result["unique_route_identities"])
        self.assertEqual([], result["failures"])
        self.assertFalse(result["exact_model_weight_bytes_attested"])

    def test_provider_change_across_controls_is_rejected(self):
        a = self.mod.extract_runtime_route_identity(payload(provider="ProviderA"))
        b = self.mod.extract_runtime_route_identity(payload(provider="ProviderB"))
        rows = []
        for seed, control in enumerate(self.mod.REQUIRED_CONTROLS, start=1):
            rows.append({
                "status": "SUCCESS",
                "control": control,
                "seed": seed,
                "observation": {"runtime_route_identity": b if control == "+VECTOR" else a},
            })
        result = self.mod.validate_control_family_runtime_identity(rows)
        self.assertFalse(result["stable_selected_route"])
        self.assertEqual(2, result["unique_route_identities"])
        self.assertIn("RUNTIME_ROUTE_IDENTITY_CHANGED_ACROSS_CONTROLS", result["failures"])

    def test_missing_control_is_rejected(self):
        identity = self.mod.extract_runtime_route_identity(payload())
        rows = []
        for seed, control in enumerate(self.mod.REQUIRED_CONTROLS[:-1], start=1):
            rows.append({
                "status": "SUCCESS",
                "control": control,
                "seed": seed,
                "observation": {"runtime_route_identity": identity},
            })
        result = self.mod.validate_control_family_runtime_identity(rows)
        self.assertFalse(result["stable_selected_route"])
        self.assertTrue(any(x.startswith("MISSING_CONTROLS:") for x in result["failures"]))


if __name__ == "__main__":
    unittest.main()
