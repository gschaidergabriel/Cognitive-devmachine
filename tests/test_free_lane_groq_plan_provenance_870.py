#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import free_lane_provenance as provenance


class GroqFreeTierProvenance870Tests(unittest.TestCase):
    model = "openai/gpt-oss-120b"
    endpoint = "https://api.groq.com/openai/v1/chat/completions"
    fp = "credential-fingerprint"

    def _times(self):
        now = dt.datetime.now(dt.timezone.utc)
        return (
            (now - dt.timedelta(minutes=5)).isoformat(),
            (now + dt.timedelta(minutes=25)).isoformat(),
        )

    def _fixture(self, entitlement=None, with_matching_headers=True):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        economic = root / "economic.json"
        provider = {
            "allowed_endpoint_host": "api.groq.com",
            "evidence_kind": "CREDENTIAL_FINGERPRINT_PLUS_PROVIDER_SIDE_FREE_TIER_BINDING",
            "source": "provider:groq-billing",
            "max_entitlement_age_seconds": 3600,
            "free_plan_models": {
                self.model: {"requests_per_day": 1000, "tokens_per_minute": 8000}
            },
            "credential_entitlements": {},
        }
        if entitlement is not None:
            provider["credential_entitlements"][self.fp] = entitlement
        economic.write_text(json.dumps({"providers": {"groq": provider}}), encoding="utf-8")
        artifacts = root / "artifacts"
        if with_matching_headers:
            workers = artifacts / "run" / "workers.jsonl"
            workers.parent.mkdir(parents=True)
            workers.write_text(json.dumps({
                "provider": "groq",
                "key_fp": self.fp,
                "model": self.model,
                "rate": {
                    "x-ratelimit-limit-requests": "1000",
                    "x-ratelimit-limit-tokens": "8000",
                },
                "http_status": 200,
                "ts": "historical",
            }) + "\n", encoding="utf-8")
        return td, economic, artifacts

    def test_free_like_rate_headers_alone_cannot_authorize(self):
        td, economic, artifacts = self._fixture()
        try:
            with mock.patch.object(provenance, "PROVENANCE_PATH", economic):
                ev = provenance.lane_evidence(
                    "groq", self.fp, self.model, self.endpoint, artifacts=artifacts
                )
            self.assertFalse(ev["ok"])
            self.assertEqual(ev["reason"], "GROQ_CREDENTIAL_FREE_TIER_NOT_BOUND")
        finally:
            td.cleanup()

    def test_exact_fresh_provider_side_free_tier_binding_authorizes(self):
        observed_at, valid_until = self._times()
        entitlement = {
            "provider_side_free_tier_confirmed": True,
            "tier": "FREE",
            "evidence_ref": "groq-console:org/project-free-tier",
            "observed_at": observed_at,
            "valid_until": valid_until,
            "account_scope": "project:hashed",
            "allowed_models": [self.model],
        }
        td, economic, artifacts = self._fixture(entitlement)
        try:
            with mock.patch.object(provenance, "PROVENANCE_PATH", economic):
                ev = provenance.lane_evidence(
                    "groq", self.fp, self.model, self.endpoint, artifacts=artifacts
                )
            self.assertTrue(ev["ok"])
            self.assertEqual(ev["credential_binding"]["tier"], "FREE")
            self.assertEqual(
                ev["assertion"],
                "EXACT_GROQ_CREDENTIAL_BOUND_TO_FRESH_PROVIDER_SIDE_FREE_TIER",
            )
            self.assertIsNotNone(ev["rate_limit_telemetry"])
        finally:
            td.cleanup()

    def test_developer_tier_binding_is_rejected_even_with_free_like_headers(self):
        observed_at, valid_until = self._times()
        entitlement = {
            "provider_side_free_tier_confirmed": True,
            "tier": "DEVELOPER",
            "evidence_ref": "groq-console:developer",
            "observed_at": observed_at,
            "valid_until": valid_until,
            "allowed_models": [self.model],
        }
        td, economic, artifacts = self._fixture(entitlement)
        try:
            with mock.patch.object(provenance, "PROVENANCE_PATH", economic):
                ev = provenance.lane_evidence(
                    "groq", self.fp, self.model, self.endpoint, artifacts=artifacts
                )
            self.assertFalse(ev["ok"])
        finally:
            td.cleanup()

    def test_expired_free_tier_binding_is_rejected(self):
        now = dt.datetime.now(dt.timezone.utc)
        entitlement = {
            "provider_side_free_tier_confirmed": True,
            "tier": "FREE",
            "evidence_ref": "groq-console:stale-free",
            "observed_at": (now - dt.timedelta(hours=2)).isoformat(),
            "valid_until": (now - dt.timedelta(hours=1)).isoformat(),
            "allowed_models": [self.model],
        }
        td, economic, artifacts = self._fixture(entitlement)
        try:
            with mock.patch.object(provenance, "PROVENANCE_PATH", economic):
                ev = provenance.lane_evidence(
                    "groq", self.fp, self.model, self.endpoint, artifacts=artifacts
                )
            self.assertFalse(ev["ok"])
        finally:
            td.cleanup()

    def test_entitlement_cannot_expand_to_unbound_model(self):
        observed_at, valid_until = self._times()
        entitlement = {
            "provider_side_free_tier_confirmed": True,
            "tier": "FREE",
            "evidence_ref": "groq-console:free",
            "observed_at": observed_at,
            "valid_until": valid_until,
            "allowed_models": ["openai/gpt-oss-20b"],
        }
        td, economic, artifacts = self._fixture(entitlement)
        try:
            with mock.patch.object(provenance, "PROVENANCE_PATH", economic):
                ev = provenance.lane_evidence(
                    "groq", self.fp, self.model, self.endpoint, artifacts=artifacts
                )
            self.assertFalse(ev["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
