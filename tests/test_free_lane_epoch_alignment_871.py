#!/usr/bin/env python3
"""Fail-closed regression for the supervisor-8.71 FREE lane control-plane epoch.

No provider secrets are read and no network calls are made.  The test proves that
successor-dynamic provider admission is loadable again after the 8.71 supervisor
advance while the stricter NVIDIA credential-entitlement requirement remains
closed until an exact fingerprint is explicitly admitted.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import free_lane_provenance as lanes
import free_provider_admission as admission


class FreeLaneEpochAlignment871Tests(unittest.TestCase):
    def test_current_control_plane_epochs_are_aligned(self) -> None:
        inbox = json.loads((ROOT / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json").read_text())
        provider = json.loads((ROOT / "research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json").read_text())
        economic = json.loads((ROOT / "governance/FREE_LANE_ECONOMIC_PROVENANCE_2026-08-24.json").read_text())
        self.assertEqual(inbox["schema_version"], "8.71")
        self.assertEqual(provider["authority_epoch"], inbox["schema_version"])
        self.assertEqual(economic["authority_epoch"], inbox["schema_version"])

    def test_successor_dynamic_provider_admission_loads(self) -> None:
        payload = admission.load_provider_admission()
        self.assertEqual(payload["authority_epoch"], "8.71")
        self.assertEqual(payload["mode"], "FREE_ONLY")
        self.assertTrue(admission.provider_is_admitted_free("openrouter"))

    def test_openrouter_exact_free_route_remains_admitted(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            binding = lanes.current_lane_binding(
                "openrouter",
                "synthetic-nonsecret-fingerprint",
                "openrouter/free",
                "https://openrouter.ai/api/v1/chat/completions",
                artifacts=Path(td),
            )
        self.assertTrue(binding.get("ok"), binding)
        self.assertEqual(binding.get("admission_epoch"), "8.71")

    def test_openrouter_unlisted_route_still_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            binding = lanes.current_lane_binding(
                "openrouter",
                "synthetic-nonsecret-fingerprint",
                "some-paid-or-unknown-route",
                "https://openrouter.ai/api/v1/chat/completions",
                artifacts=Path(td),
            )
        self.assertFalse(binding.get("ok"))
        self.assertEqual(binding.get("reason"), "OPENROUTER_ROUTE_NOT_EXPLICIT_ZERO_PRICE")

    def test_unbound_nvidia_credential_stays_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            binding = lanes.current_lane_binding(
                "nvidia",
                "synthetic-unbound-fingerprint",
                "nvidia/nemotron-3-super-120b-a12b",
                "https://integrate.api.nvidia.com/v1/chat/completions",
                artifacts=Path(td),
            )
        self.assertFalse(binding.get("ok"))
        self.assertEqual(
            binding.get("reason"),
            "NVIDIA_CREDENTIAL_DEVELOPER_FREE_ENTITLEMENT_NOT_BOUND",
        )

    def test_mistral_remains_fail_closed_without_free_mode_binding(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            binding = lanes.current_lane_binding(
                "mistral",
                "synthetic-nonsecret-fingerprint",
                "mistral-small-latest",
                "https://api.mistral.ai/v1/chat/completions",
                artifacts=Path(td),
            )
        self.assertFalse(binding.get("ok"))
        self.assertEqual(binding.get("reason"), "MISTRAL_PROVIDER_SIDE_FREE_MODE_NOT_BOUND")


if __name__ == "__main__":
    unittest.main()
