#!/usr/bin/env python3
from __future__ import annotations

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


class FreeLaneProvenance870Tests(unittest.TestCase):
    def make_provenance(self, nvidia_entitlements: dict | None = None):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        path = root / "economic.json"
        payload = {
            "schema": "ENTITYOS_HCU_FREE_LANE_ECONOMIC_PROVENANCE/v1",
            "authority_epoch": "8.70",
            "mode": "FREE_ONLY",
            "providers": {
                "openrouter": {
                    "allowed_endpoint_host": "openrouter.ai",
                    "allowed_routes": ["openrouter/free"],
                    "evidence_kind": "EXACT_ROUTE_ZERO_PRICE",
                    "source": "provider:openrouter-free-route",
                    "credential_plan_needed": False,
                },
                "nvidia": {
                    "allowed_endpoint_host": "integrate.api.nvidia.com",
                    "evidence_kind": "NVIDIA_HOSTED_NIM_DEVELOPER_FREE_PROTOTYPING",
                    "source": "provider:nvidia-nim",
                    "credential_plan_needed": True,
                    "credential_entitlements": nvidia_entitlements or {},
                    "scope": "hosted NIM prototyping only",
                },
            },
        }
        path.write_text(json.dumps(payload), encoding="utf-8")
        return td, path

    def test_nvidia_provider_wide_statement_does_not_admit_unbound_credential(self):
        td, path = self.make_provenance()
        try:
            with mock.patch.object(provenance, "PROVENANCE_PATH", path):
                evidence = provenance.lane_evidence(
                    "nvidia",
                    "abc123credential",
                    "nvidia/nemotron-mini-4b-instruct",
                    "https://integrate.api.nvidia.com/v1/chat/completions",
                    artifacts=Path(td.name),
                )
            self.assertFalse(evidence["ok"])
            self.assertEqual(
                evidence["reason"], "NVIDIA_CREDENTIAL_FREE_ENTITLEMENT_NOT_BOUND"
            )
        finally:
            td.cleanup()

    def test_nvidia_other_credential_binding_cannot_authorize_request(self):
        td, path = self.make_provenance(
            {
                "different-fingerprint": {
                    "provider_side_zero_cost_confirmed": True,
                    "evidence_ref": "provider-admin:evidence-1",
                    "observed_at": "2026-08-24T13:00:00Z",
                    "allowed_models": ["nvidia/nemotron-mini-4b-instruct"],
                }
            }
        )
        try:
            with mock.patch.object(provenance, "PROVENANCE_PATH", path):
                evidence = provenance.lane_evidence(
                    "nvidia",
                    "requested-fingerprint",
                    "nvidia/nemotron-mini-4b-instruct",
                    "https://integrate.api.nvidia.com/v1/chat/completions",
                    artifacts=Path(td.name),
                )
            self.assertFalse(evidence["ok"])
        finally:
            td.cleanup()

    def test_nvidia_exact_credential_and_model_binding_admits(self):
        fp = "exact-fingerprint"
        model = "nvidia/nemotron-mini-4b-instruct"
        td, path = self.make_provenance(
            {
                fp: {
                    "provider_side_zero_cost_confirmed": True,
                    "evidence_ref": "provider-admin:evidence-2",
                    "observed_at": "2026-08-24T13:05:00Z",
                    "account_scope": "developer-program",
                    "allowed_models": [model],
                }
            }
        )
        try:
            with mock.patch.object(provenance, "PROVENANCE_PATH", path):
                evidence = provenance.lane_evidence(
                    "nvidia",
                    fp,
                    model,
                    "https://integrate.api.nvidia.com/v1/chat/completions",
                    artifacts=Path(td.name),
                )
            self.assertTrue(evidence["ok"])
            self.assertEqual(
                evidence["assertion"],
                "EXACT_NVIDIA_CREDENTIAL_BOUND_TO_PROVIDER_SIDE_FREE_NIM_ENTITLEMENT",
            )
            self.assertEqual(evidence["credential_binding"]["model_or_route"], model)
        finally:
            td.cleanup()

    def test_nvidia_exact_credential_cannot_expand_beyond_bound_model(self):
        fp = "exact-fingerprint"
        td, path = self.make_provenance(
            {
                fp: {
                    "provider_side_zero_cost_confirmed": True,
                    "evidence_ref": "provider-admin:evidence-3",
                    "observed_at": "2026-08-24T13:10:00Z",
                    "allowed_models": ["nvidia/nemotron-mini-4b-instruct"],
                }
            }
        )
        try:
            with mock.patch.object(provenance, "PROVENANCE_PATH", path):
                evidence = provenance.lane_evidence(
                    "nvidia",
                    fp,
                    "nvidia/other-model",
                    "https://integrate.api.nvidia.com/v1/chat/completions",
                    artifacts=Path(td.name),
                )
            self.assertFalse(evidence["ok"])
        finally:
            td.cleanup()

    def test_openrouter_explicit_zero_price_route_remains_route_bound(self):
        td, path = self.make_provenance()
        try:
            with mock.patch.object(provenance, "PROVENANCE_PATH", path):
                allowed = provenance.lane_evidence(
                    "openrouter",
                    "any-fingerprint",
                    "openrouter/free",
                    "https://openrouter.ai/api/v1/chat/completions",
                    artifacts=Path(td.name),
                )
                blocked = provenance.lane_evidence(
                    "openrouter",
                    "any-fingerprint",
                    "paid/model",
                    "https://openrouter.ai/api/v1/chat/completions",
                    artifacts=Path(td.name),
                )
            self.assertTrue(allowed["ok"])
            self.assertFalse(blocked["ok"])
            self.assertEqual(
                blocked["reason"], "OPENROUTER_ROUTE_NOT_EXPLICIT_ZERO_PRICE"
            )
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
