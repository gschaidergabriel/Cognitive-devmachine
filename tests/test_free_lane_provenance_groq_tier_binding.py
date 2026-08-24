from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import free_lane_provenance as gate


MODEL = "openai/gpt-oss-120b"
ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
FP = "credential-a1"


def base_provenance(binding: dict | None = None) -> dict:
    return {
        "schema": gate.PROVENANCE_SCHEMA,
        "mode": "FREE_ONLY",
        "providers": {
            "groq": {
                "allowed_endpoint_host": "api.groq.com",
                "evidence_kind": "EXACT_CREDENTIAL_PROVIDER_SIDE_FREE_TIER_BINDING_PLUS_RATE_HEADER_CORROBORATION",
                "source": "provider-side-observation",
                "free_plan_models": {
                    MODEL: {"requests_per_day": 1000, "tokens_per_minute": 8000},
                },
                "credential_free_tier_bindings": ({FP: binding} if binding is not None else {}),
                "max_binding_age_seconds": 86400,
            }
        },
    }


def write_matching_headers(root: Path, fp: str = FP) -> None:
    run = root / "active-test"
    run.mkdir(parents=True, exist_ok=True)
    row = {
        "provider": "groq",
        "key_fp": fp,
        "model": MODEL,
        "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
        "http_status": 200,
        "rate": {
            "x-ratelimit-limit-requests": "1000",
            "x-ratelimit-limit-tokens": "8000",
        },
    }
    (run / "workers.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")


def valid_binding(**overrides) -> dict:
    value = {
        "tier": "FREE",
        "payg_enabled": False,
        "provider_account_or_project_fingerprint": "project-fingerprint-1234",
        "provider_observation_ref": "receipt:groq-free-tier-observation",
        "observed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    value.update(overrides)
    return value


class GroqEconomicBindingTests(unittest.TestCase):
    def evaluate(self, provenance: dict, *, fp: str = FP, with_headers: bool = True) -> dict:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            if with_headers:
                write_matching_headers(root, fp=fp)
            return gate._lane_evidence_from_provenance(
                provenance,
                "groq",
                fp,
                MODEL,
                ENDPOINT,
                artifacts=root,
            )

    def test_free_table_headers_without_provider_tier_binding_reject(self) -> None:
        result = self.evaluate(base_provenance())
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "GROQ_CREDENTIAL_FREE_TIER_NOT_BOUND")

    def test_developer_payg_with_free_like_headers_reject(self) -> None:
        result = self.evaluate(base_provenance(valid_binding(tier="DEVELOPER", payg_enabled=True)))
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "GROQ_BOUND_TIER_NOT_FREE")

    def test_binding_for_different_credential_rejects(self) -> None:
        prov = base_provenance()
        prov["providers"]["groq"]["credential_free_tier_bindings"] = {
            "different-fp": valid_binding()
        }
        result = self.evaluate(prov)
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "GROQ_CREDENTIAL_FREE_TIER_NOT_BOUND")

    def test_stale_provider_tier_observation_rejects(self) -> None:
        stale = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=2)).isoformat()
        result = self.evaluate(base_provenance(valid_binding(observed_at=stale)))
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "GROQ_FREE_TIER_OBSERVATION_STALE")

    def test_fresh_free_tier_binding_without_quota_corroboration_rejects(self) -> None:
        result = self.evaluate(base_provenance(valid_binding()), with_headers=False)
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "GROQ_FREE_TIER_QUOTA_CORROBORATION_NOT_OBSERVED")

    def test_fresh_free_tier_binding_plus_matching_quota_corroboration_accepts(self) -> None:
        result = self.evaluate(base_provenance(valid_binding()))
        self.assertTrue(result["ok"])
        self.assertEqual(result["assertion"], "BOUND_GROQ_FREE_TIER_ACCOUNT_PLUS_QUOTA_CORROBORATION")
        self.assertFalse(result["provider_quota_corroboration"]["economic_authority"])


if __name__ == "__main__":
    unittest.main()
