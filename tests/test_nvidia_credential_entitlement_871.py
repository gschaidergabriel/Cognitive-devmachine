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


class NvidiaCredentialEntitlement871Tests(unittest.TestCase):
    provider = "nvidia"
    fp = "credential-fingerprint"
    model = "nvidia/nemotron-mini-4b-instruct"
    endpoint = "https://integrate.api.nvidia.com/v1/chat/completions"

    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)
        self.economic = self.root / "economic.json"
        self.admission = self.root / "admission.json"
        self.artifacts = self.root / "artifacts"
        self.admission.write_text(json.dumps({
            "schema": provenance.ADMISSION_SCHEMA,
            "authority_epoch": "8.71",
            "mode": "FREE_ONLY",
            "providers": {"nvidia": {"admitted": True, "cost_class": "FREE"}},
        }), encoding="utf-8")

    def tearDown(self):
        self.td.cleanup()

    def entitlement(self, **changes):
        now = dt.datetime.now(dt.timezone.utc)
        row = {
            "schema": provenance.NVIDIA_ENTITLEMENT_SCHEMA,
            "provider": "nvidia",
            "credential_fingerprint": self.fp,
            "endpoint_host": "integrate.api.nvidia.com",
            "provider_side_zero_cost_confirmed": True,
            "evidence_ref": "provider-admin:nvidia-developer-program",
            "entitlement_evidence_digest": "a" * 64,
            "observed_at": (now - dt.timedelta(minutes=5)).isoformat(),
            "valid_until": (now + dt.timedelta(minutes=25)).isoformat(),
            "account_scope": "developer-program",
            "allowed_models": [self.model],
        }
        row.update(changes)
        return row

    def write_economic(self, entitlement=None, *, legacy_allowlist=None):
        nvidia = {
            "allowed_endpoint_host": "integrate.api.nvidia.com",
            "evidence_kind": "NVIDIA_HOSTED_NIM_DEVELOPER_FREE_PROTOTYPING",
            "source": "provider:nvidia-nim",
            "credential_plan_needed": True,
            "credential_entitlements": {},
            "max_entitlement_age_seconds": 3600,
            "scope": "hosted NIM prototyping only",
        }
        if entitlement is not None:
            nvidia["credential_entitlements"][self.fp] = entitlement
        if legacy_allowlist is not None:
            nvidia["admitted_credential_fingerprints"] = legacy_allowlist
        self.economic.write_text(json.dumps({
            "schema": provenance.PROVENANCE_SCHEMA,
            "authority_epoch": "8.71",
            "mode": "FREE_ONLY",
            "providers": {"nvidia": nvidia},
        }), encoding="utf-8")

    def evidence(self):
        with mock.patch.object(provenance, "PROVENANCE_PATH", self.economic):
            return provenance.lane_evidence(
                self.provider, self.fp, self.model, self.endpoint, artifacts=self.artifacts
            )

    def test_unbound_credential_fails_closed(self):
        self.write_economic()
        ev = self.evidence()
        self.assertFalse(ev["ok"])
        self.assertEqual(ev["reason"], "NVIDIA_CREDENTIAL_DEVELOPER_FREE_ENTITLEMENT_NOT_BOUND")

    def test_legacy_fingerprint_allowlist_is_not_entitlement_authority(self):
        self.write_economic(legacy_allowlist=[self.fp])
        ev = self.evidence()
        self.assertFalse(ev["ok"])

    def test_fresh_exact_provider_side_entitlement_admits(self):
        self.write_economic(self.entitlement())
        ev = self.evidence()
        self.assertTrue(ev["ok"])
        binding = ev["credential_binding"]
        self.assertEqual(binding["credential_fingerprint"], self.fp)
        self.assertEqual(binding["model_or_route"], self.model)
        self.assertEqual(binding["entitlement_evidence_digest"], "a" * 64)

    def test_expired_or_stale_entitlement_fails_closed(self):
        now = dt.datetime.now(dt.timezone.utc)
        expired = self.entitlement(
            observed_at=(now - dt.timedelta(hours=2)).isoformat(),
            valid_until=(now - dt.timedelta(hours=1)).isoformat(),
        )
        self.write_economic(expired)
        self.assertFalse(self.evidence()["ok"])

        stale = self.entitlement(
            observed_at=(now - dt.timedelta(hours=2)).isoformat(),
            valid_until=(now + dt.timedelta(hours=2)).isoformat(),
        )
        self.write_economic(stale)
        self.assertFalse(self.evidence()["ok"])

    def test_bad_evidence_digest_and_model_expansion_fail_closed(self):
        self.write_economic(self.entitlement(entitlement_evidence_digest="not-a-sha"))
        self.assertFalse(self.evidence()["ok"])
        self.write_economic(self.entitlement(allowed_models=["nvidia/other-model"]))
        self.assertFalse(self.evidence()["ok"])

    def test_current_lane_binding_carries_exact_entitlement_and_authority_digests(self):
        self.write_economic(self.entitlement())
        with (
            mock.patch.object(provenance, "PROVENANCE_PATH", self.economic),
            mock.patch.object(provenance, "ADMISSION_PATH", self.admission),
        ):
            binding = provenance.current_lane_binding(
                self.provider, self.fp, self.model, self.endpoint, artifacts=self.artifacts
            )
        self.assertTrue(binding["ok"])
        self.assertEqual(len(binding["admission_digest"]), 64)
        self.assertEqual(len(binding["economic_provenance_digest"]), 64)
        self.assertEqual(
            binding["evidence"]["credential_binding"]["schema"],
            provenance.NVIDIA_ENTITLEMENT_SCHEMA,
        )


if __name__ == "__main__":
    unittest.main()
