from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from tools import free_lane_provenance as lane


class FreeLaneSecretLookupBinding870Tests(unittest.TestCase):
    def setUp(self):
        self.td=tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        root=Path(self.td.name)
        self.admission=root/"admission.json"
        self.provenance=root/"provenance.json"
        self.admission.write_text(json.dumps({
            "schema":lane.ADMISSION_SCHEMA,
            "authority_epoch":"8.70",
            "mode":"FREE_ONLY",
            "providers":{
                "openrouter":{"admitted":True,"cost_class":"FREE"},
                "nvidia":{"admitted":True,"cost_class":"FREE"},
                "groq":{"admitted":True,"cost_class":"FREE"},
                "mistral":{"admitted":True,"cost_class":"FREE"},
            },
        }),encoding="utf-8")
        self.provenance.write_text(json.dumps({
            "schema":lane.PROVENANCE_SCHEMA,
            "authority_epoch":"8.70",
            "mode":"FREE_ONLY",
            "providers":{
                "openrouter":{
                    "allowed_endpoint_host":"openrouter.ai",
                    "allowed_routes":["openrouter/free"],
                    "evidence_kind":"EXACT_ROUTE_ZERO_PRICE",
                },
                "nvidia":{
                    "allowed_endpoint_host":"integrate.api.nvidia.com",
                    "evidence_kind":"NVIDIA_HOSTED_NIM_DEVELOPER_FREE_PROTOTYPING",
                },
                "groq":{
                    "allowed_endpoint_host":"api.groq.com",
                    "evidence_kind":"CREDENTIAL_FINGERPRINT_PLUS_PROVIDER_RATE_HEADER_MATCH",
                    "free_plan_models":{"openai/gpt-oss-20b":{"requests_per_day":1000,"tokens_per_minute":8000}},
                },
                "mistral":{
                    "allowed_endpoint_host":"api.mistral.ai",
                    "evidence_kind":"PROVIDER_SIDE_FREE_MODE_REQUIRED",
                    "default":"FAIL_CLOSED_UNTIL_BOUND",
                },
            },
        }),encoding="utf-8")
        self.patches=[
            mock.patch.object(lane,"ADMISSION_PATH",self.admission),
            mock.patch.object(lane,"PROVENANCE_PATH",self.provenance),
        ]
        for p in self.patches:
            p.start(); self.addCleanup(p.stop)

    def test_openrouter_only_explicit_free_route_can_reach_secret_lookup(self):
        ok=lane.route_secret_lookup_binding(
            "openrouter","openrouter/free","https://openrouter.ai/api/v1/chat/completions"
        )
        blocked=lane.route_secret_lookup_binding(
            "openrouter","some/paid-model","https://openrouter.ai/api/v1/chat/completions"
        )
        self.assertTrue(ok["ok"])
        self.assertEqual(ok["scope"],"SECRET_LOOKUP_ONLY_NOT_PROVIDER_EXECUTION")
        self.assertFalse(blocked["ok"])
        self.assertEqual(blocked["reason"],"OPENROUTER_ROUTE_NOT_EXPLICIT_ZERO_PRICE")

    def test_groq_known_free_plan_model_can_reach_secret_lookup_but_not_execution_without_fingerprint_evidence(self):
        pre=lane.route_secret_lookup_binding(
            "groq","openai/gpt-oss-20b","https://api.groq.com/openai/v1/chat/completions"
        )
        self.assertTrue(pre["ok"])
        with tempfile.TemporaryDirectory() as artifacts:
            bound=lane.current_lane_binding(
                "groq","unobserved-fp","openai/gpt-oss-20b",
                "https://api.groq.com/openai/v1/chat/completions",
                artifacts=Path(artifacts),
            )
        self.assertFalse(bound["ok"])
        self.assertEqual(bound["reason"],"GROQ_CREDENTIAL_FREE_PLAN_HEADERS_NOT_OBSERVED")

    def test_mistral_and_wrong_endpoint_block_before_secret_lookup(self):
        mistral=lane.route_secret_lookup_binding(
            "mistral","mistral-small-latest","https://api.mistral.ai/v1/chat/completions"
        )
        wrong=lane.route_secret_lookup_binding(
            "openrouter","openrouter/free","https://example.com/v1/chat/completions"
        )
        self.assertFalse(mistral["ok"])
        self.assertEqual(mistral["reason"],"MISTRAL_PROVIDER_SIDE_FREE_MODE_NOT_BOUND")
        self.assertFalse(wrong["ok"])
        self.assertEqual(wrong["reason"],"ENDPOINT_NOT_ZERO_COST_BOUND")


if __name__=="__main__":
    unittest.main()
