from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import sys

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import free_lane_provenance as provenance


class CanonicalUncertainProviderFence871Tests(unittest.TestCase):
    def test_nvidia_known_fingerprint_stays_fail_closed_without_account_bound_entitlement(self) -> None:
        result = provenance.lane_evidence(
            "nvidia",
            "e498d9744e",
            "nvidia/test-model",
            "https://integrate.api.nvidia.com/v1/chat/completions",
        )
        self.assertFalse(result["ok"])
        self.assertEqual(
            result["reason"],
            "NVIDIA_CREDENTIAL_FREE_ENTITLEMENT_EVIDENCE_NOT_BOUND",
        )

    def test_groq_free_like_headers_cannot_authorize_canonical_lane(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            artifacts = Path(td)
            workers = artifacts / "run" / "workers.jsonl"
            workers.parent.mkdir(parents=True)
            workers.write_text(
                json.dumps(
                    {
                        "provider": "groq",
                        "key_fp": "fp-free-like",
                        "model": "openai/gpt-oss-120b",
                        "rate": {
                            "x-ratelimit-limit-requests": "1000",
                            "x-ratelimit-limit-tokens": "8000",
                        },
                        "http_status": 200,
                        "ts": "historical",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            result = provenance.lane_evidence(
                "groq",
                "fp-free-like",
                "openai/gpt-oss-120b",
                "https://api.groq.com/openai/v1/chat/completions",
                artifacts=artifacts,
            )
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "GROQ_MODEL_NOT_BOUND_TO_DOCUMENTED_FREE_LIMITS")

    def test_openrouter_explicit_zero_price_route_remains_available(self) -> None:
        result = provenance.lane_evidence(
            "openrouter",
            "nonsecret-fingerprint",
            "openrouter/free",
            "https://openrouter.ai/api/v1/chat/completions",
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["assertion"], "EXACT_ROUTE_ZERO_PROMPT_AND_COMPLETION_PRICE")

    def test_mistral_remains_fail_closed(self) -> None:
        result = provenance.lane_evidence(
            "mistral",
            "nonsecret-fingerprint",
            "mistral/test-model",
            "https://api.mistral.ai/v1/chat/completions",
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "MISTRAL_PROVIDER_SIDE_FREE_MODE_NOT_BOUND")


if __name__ == "__main__":
    unittest.main()
