#!/usr/bin/env python3
"""Successor-dynamic, no-secret/no-network FREE lane economic boundary tests.

These tests complement the older provider-admission boundary family. They bind
current supervisor/admission/economic-provenance epochs and exercise concrete
credential+route semantics without making provider calls or reading secret values.
They intentionally tolerate successor field-strengthening while preserving the
fail-closed behavior itself.
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
import free_provider_admission as provider_admission

INBOX = ROOT / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
ADMISSION = ROOT / "research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json"
ECONOMIC = ROOT / "governance/FREE_LANE_ECONOMIC_PROVENANCE_2026-08-24.json"


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"object required: {path}")
    return value


def nvidia_bound_lanes(record: dict) -> list[tuple[str, str]]:
    """Return non-secret fingerprint/model pairs across current/successor schemas."""
    out: list[tuple[str, str]] = []
    entitlements = record.get("credential_entitlements")
    if isinstance(entitlements, dict):
        for fingerprint, entitlement in entitlements.items():
            if not isinstance(entitlement, dict):
                continue
            models = entitlement.get("allowed_models") or []
            for model in models:
                if str(fingerprint).strip() and str(model).strip():
                    out.append((str(fingerprint).strip(), str(model).strip()))
        return out
    fingerprints = record.get("allowed_credential_fingerprints")
    if fingerprints is None:
        fingerprints = record.get("admitted_credential_fingerprints")
    if isinstance(fingerprints, list):
        for fingerprint in fingerprints:
            if str(fingerprint).strip():
                out.append((str(fingerprint).strip(), "nvidia/nemotron-3-super-120b-a12b"))
    return out


class FreeLaneEconomicBoundaryCurrentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.inbox = read_json(INBOX)
        self.admission = read_json(ADMISSION)
        self.economic = read_json(ECONOMIC)

    def binding(self, provider: str, fingerprint: str, route: str, endpoint: str) -> dict:
        with tempfile.TemporaryDirectory() as td:
            return lanes.current_lane_binding(
                provider,
                fingerprint,
                route,
                endpoint,
                artifacts=Path(td),
            )

    def test_supervisor_admission_and_economic_epochs_are_identical(self) -> None:
        epoch = str(self.inbox.get("schema_version") or "")
        self.assertTrue(epoch)
        self.assertEqual(self.admission.get("authority_epoch"), epoch)
        self.assertEqual(self.economic.get("authority_epoch"), epoch)
        loaded = provider_admission.load_provider_admission()
        self.assertEqual(loaded.get("authority_epoch"), epoch)
        self.assertEqual(loaded.get("mode"), "FREE_ONLY")

    def test_openrouter_only_explicit_zero_price_route_is_positive(self) -> None:
        providers = self.admission.get("providers") or {}
        record = providers.get("openrouter") or {}
        if record.get("admitted") is not True:
            self.skipTest("openrouter is not currently provider-level admitted")
        good = self.binding(
            "openrouter",
            "synthetic-nonsecret-fingerprint",
            "openrouter/free",
            "https://openrouter.ai/api/v1/chat/completions",
        )
        self.assertTrue(good.get("ok"), good)
        self.assertTrue(lanes.binding_still_current(good))
        bad = self.binding(
            "openrouter",
            "synthetic-nonsecret-fingerprint",
            "unknown-or-paid-route",
            "https://openrouter.ai/api/v1/chat/completions",
        )
        self.assertFalse(bad.get("ok"), bad)
        self.assertTrue(str(bad.get("reason") or "").startswith("OPENROUTER_"), bad)

    def test_unlisted_nvidia_credential_fails_closed(self) -> None:
        bad = self.binding(
            "nvidia",
            "ffffffffffffffff-unlisted-synthetic",
            "nvidia/nemotron-3-super-120b-a12b",
            "https://integrate.api.nvidia.com/v1/chat/completions",
        )
        self.assertFalse(bad.get("ok"), bad)
        self.assertTrue(str(bad.get("reason") or "").startswith("NVIDIA_"), bad)

    def test_every_currently_bound_nvidia_lane_is_exactly_scoped(self) -> None:
        record = ((self.economic.get("providers") or {}).get("nvidia") or {})
        for fingerprint, model in nvidia_bound_lanes(record):
            with self.subTest(fingerprint=fingerprint, model=model):
                good = self.binding(
                    "nvidia",
                    fingerprint,
                    model,
                    "https://integrate.api.nvidia.com/v1/chat/completions",
                )
                self.assertTrue(good.get("ok"), good)
                self.assertTrue(lanes.binding_still_current(good))
                wrong_host = self.binding(
                    "nvidia",
                    fingerprint,
                    model,
                    "https://example.invalid/v1/chat/completions",
                )
                self.assertFalse(wrong_host.get("ok"), wrong_host)
                self.assertEqual(wrong_host.get("reason"), "ENDPOINT_NOT_ZERO_COST_BOUND")

    def test_mistral_stays_fail_closed_until_provider_side_free_mode_is_bound(self) -> None:
        bad = self.binding(
            "mistral",
            "synthetic-nonsecret-fingerprint",
            "mistral-small-latest",
            "https://api.mistral.ai/v1/chat/completions",
        )
        self.assertFalse(bad.get("ok"), bad)
        self.assertTrue(str(bad.get("reason") or "").startswith("MISTRAL_"), bad)

    def test_groq_unknown_credential_has_no_free_lane_credit(self) -> None:
        bad = self.binding(
            "groq",
            "synthetic-never-observed-fingerprint",
            "openai/gpt-oss-120b",
            "https://api.groq.com/openai/v1/chat/completions",
        )
        self.assertFalse(bad.get("ok"), bad)
        self.assertTrue(str(bad.get("reason") or "").startswith("GROQ_"), bad)


if __name__ == "__main__":
    unittest.main()
