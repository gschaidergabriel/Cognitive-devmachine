import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "free_lane_provenance.py"
spec = importlib.util.spec_from_file_location("free_lane_provenance", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


class FreeLaneProvenance870Tests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.root = Path(self.td.name)
        self.prov = self.root / "provenance.json"
        self.prov.write_text(
            json.dumps(
                {
                    "providers": {
                        "openrouter": {
                            "allowed_endpoint_host": "openrouter.ai",
                            "allowed_routes": ["openrouter/free"],
                            "evidence_kind": "EXACT_ROUTE_ZERO_PRICE",
                            "source": "provider-route-evidence",
                            "credential_plan_needed": False,
                        },
                        "nvidia": {
                            "allowed_endpoint_host": "integrate.api.nvidia.com",
                            "evidence_kind": "NVIDIA_HOSTED_NIM_DEVELOPER_FREE_PROTOTYPING",
                            "source": "provider-docs",
                            "credential_plan_needed": True,
                            "credential_plan_proof": "credential-bound Developer Program/free hosted-NIM entitlement",
                        },
                        "groq": {
                            "allowed_endpoint_host": "api.groq.com",
                            "evidence_kind": "CREDENTIAL_FINGERPRINT_PLUS_PROVIDER_RATE_HEADER_MATCH",
                            "source": "provider-rate-limits",
                            "free_plan_models": {
                                "model-a": {"requests_per_day": 1000, "tokens_per_minute": 8000}
                            },
                            "credential_plan_needed": True,
                        },
                        "mistral": {
                            "allowed_endpoint_host": "api.mistral.ai",
                            "evidence_kind": "PROVIDER_SIDE_FREE_MODE_REQUIRED",
                            "source": "provider-subscriptions",
                            "credential_plan_needed": True,
                        },
                    }
                }
            ),
            encoding="utf-8",
        )
        self.old_prov = mod.PROVENANCE_PATH
        mod.PROVENANCE_PATH = self.prov
        self.addCleanup(setattr, mod, "PROVENANCE_PATH", self.old_prov)

    def test_nvidia_fails_closed_without_credential_entitlement_binding(self):
        evidence = mod.lane_evidence(
            "nvidia",
            "fp123",
            "meta/llama",
            "https://integrate.api.nvidia.com/v1/chat/completions",
            artifacts=self.root / "artifacts",
        )
        self.assertFalse(evidence["ok"])
        self.assertEqual(evidence["reason"], "NVIDIA_CREDENTIAL_FREE_ENTITLEMENT_NOT_BOUND")

    def test_openrouter_exact_zero_price_route_remains_admitted(self):
        evidence = mod.lane_evidence(
            "openrouter",
            "fp123",
            "openrouter/free",
            "https://openrouter.ai/api/v1/chat/completions",
            artifacts=self.root / "artifacts",
        )
        self.assertTrue(evidence["ok"])
        self.assertEqual(evidence["assertion"], "EXACT_ROUTE_ZERO_PROMPT_AND_COMPLETION_PRICE")

    def test_openrouter_nonfree_route_fails_closed(self):
        evidence = mod.lane_evidence(
            "openrouter",
            "fp123",
            "some/paid-route",
            "https://openrouter.ai/api/v1/chat/completions",
            artifacts=self.root / "artifacts",
        )
        self.assertFalse(evidence["ok"])
        self.assertEqual(evidence["reason"], "OPENROUTER_ROUTE_NOT_EXPLICIT_ZERO_PRICE")

    def test_wrong_endpoint_fails_before_provider_specific_logic(self):
        evidence = mod.lane_evidence(
            "nvidia",
            "fp123",
            "meta/llama",
            "https://example.com/v1/chat/completions",
            artifacts=self.root / "artifacts",
        )
        self.assertFalse(evidence["ok"])
        self.assertEqual(evidence["reason"], "ENDPOINT_NOT_ZERO_COST_BOUND")

    def test_groq_without_same_credential_rate_evidence_fails_closed(self):
        evidence = mod.lane_evidence(
            "groq",
            "fp123",
            "model-a",
            "https://api.groq.com/openai/v1/chat/completions",
            artifacts=self.root / "artifacts",
        )
        self.assertFalse(evidence["ok"])
        self.assertEqual(evidence["reason"], "GROQ_CREDENTIAL_FREE_PLAN_HEADERS_NOT_OBSERVED")

    def test_mistral_without_provider_side_free_mode_binding_fails_closed(self):
        evidence = mod.lane_evidence(
            "mistral",
            "fp123",
            "model-a",
            "https://api.mistral.ai/v1/chat/completions",
            artifacts=self.root / "artifacts",
        )
        self.assertFalse(evidence["ok"])
        self.assertEqual(evidence["reason"], "MISTRAL_PROVIDER_SIDE_FREE_MODE_NOT_BOUND")


if __name__ == "__main__":
    unittest.main()
