#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import free_provider_admission_v1 as admission
import run_24h_entityos_swarm as driver


class FreeProviderAdmissionBoundaryV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_path = admission.DEFAULT_ADMISSION_PATH
        self.saved_env = {
            key: os.environ.get(key)
            for key in (
                "GROQ_API_KEY", "GROQ_API_KEYS", "GROQ_SWARM_MODELS",
                "MISTRAL_API_KEY", "MISTRAL_API_KEYS", "MISTRAL_SWARM_MODELS",
                "NVIDIA_API_KEY", "NVIDIA_API_KEYS", "NVIDIA_SWARM_MODELS",
                "NGC_API_KEY", "NVIDIA_NIM_API_KEY",
                "CLAY_FREE_ONLY_ATTESTED", "CLAY_GROQ_FREE_ATTESTED",
                "CLAY_MISTRAL_FREE_ATTESTED", "CLAY_NVIDIA_FREE_ATTESTED",
            )
        }
        for key in self.saved_env:
            os.environ.pop(key, None)

    def tearDown(self) -> None:
        admission.DEFAULT_ADMISSION_PATH = self.original_path
        for key, value in self.saved_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def write_admission(
        self,
        provider: str = "groq",
        *,
        cost_class: str = "UNKNOWN",
        admitted: bool = False,
        secret_lookup_allowed: bool = False,
        network_io_allowed: bool = False,
    ) -> Path:
        payload = {
            "schema": admission.SCHEMA,
            "authority_epoch": "8.67",
            "product": admission.PRODUCT,
            "compute_architecture": admission.ARCHITECTURE,
            "mode": admission.MODE,
            "providers": {
                name: {
                    "admitted": False,
                    "cost_class": "UNKNOWN",
                    "admission_id": None,
                    "secret_lookup_allowed": False,
                    "network_io_allowed": False,
                }
                for name in admission.PROVIDERS
            },
        }
        payload["providers"][provider].update({
            "admitted": admitted,
            "cost_class": cost_class,
            "admission_id": f"test:{provider}:free" if admitted else None,
            "secret_lookup_allowed": secret_lookup_allowed,
            "network_io_allowed": network_io_allowed,
        })
        fd = tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False)
        with fd:
            json.dump(payload, fd)
        return Path(fd.name)

    def activate(self, path: Path) -> None:
        admission.DEFAULT_ADMISSION_PATH = path

    def test_unknown_paid_subscription_fail_closed(self) -> None:
        for cost in ("UNKNOWN", "PAID", "SUBSCRIPTION"):
            with self.subTest(cost=cost):
                self.activate(self.write_admission(cost_class=cost))
                decision = admission.provider_decision("groq")
                self.assertFalse(decision["admitted"])
                self.assertFalse(decision["secret_lookup_allowed"])
                self.assertFalse(decision["network_io_allowed"])

    def test_free_requires_explicit_admission_and_capability_flags(self) -> None:
        self.activate(self.write_admission(
            cost_class="FREE",
            admitted=True,
            secret_lookup_allowed=False,
            network_io_allowed=True,
        ))
        self.assertFalse(admission.provider_is_free("groq"))

        self.activate(self.write_admission(
            cost_class="FREE",
            admitted=True,
            secret_lookup_allowed=True,
            network_io_allowed=True,
        ))
        self.assertTrue(admission.provider_is_free("groq"))

    def test_environment_attestation_cannot_self_grant_unknown_provider(self) -> None:
        self.activate(self.write_admission(cost_class="UNKNOWN"))
        os.environ["CLAY_FREE_ONLY_ATTESTED"] = "1"
        os.environ["CLAY_GROQ_FREE_ATTESTED"] = "1"
        os.environ["GROQ_API_KEY"] = "SECRET_TRIPWIRE"
        driver.reset_boundary_audit()

        admitted = driver.sync_attestation_from_typed_admission()
        with mock.patch.object(driver, "fetch_catalog", side_effect=AssertionError("network attempted")):
            report = driver.discover_and_export(0.01)

        self.assertEqual(admitted, [])
        self.assertEqual(driver.BOUNDARY_AUDIT["secret_lookup_count"], 0)
        self.assertEqual(driver.BOUNDARY_AUDIT["network_attempt_count"], 0)
        self.assertEqual(report["groq"]["keys"], "NOT_READ")
        self.assertNotIn("CLAY_FREE_ONLY_ATTESTED", os.environ)
        self.assertNotIn("CLAY_GROQ_FREE_ATTESTED", os.environ)

    def test_paid_and_subscription_read_zero_secrets_and_make_zero_network_attempts(self) -> None:
        for cost in ("PAID", "SUBSCRIPTION"):
            with self.subTest(cost=cost):
                self.activate(self.write_admission(cost_class=cost))
                os.environ["GROQ_API_KEY"] = "SECRET_TRIPWIRE"
                driver.reset_boundary_audit()
                driver.sync_attestation_from_typed_admission()
                with mock.patch.object(driver, "fetch_catalog", side_effect=AssertionError("network attempted")):
                    report = driver.discover_and_export(0.01)
                self.assertEqual(driver.BOUNDARY_AUDIT["secret_lookup_count"], 0)
                self.assertEqual(driver.BOUNDARY_AUDIT["network_attempt_count"], 0)
                self.assertEqual(report["groq"]["keys"], "NOT_READ")

    def test_typed_free_reads_key_only_after_admission(self) -> None:
        self.activate(self.write_admission(
            cost_class="FREE",
            admitted=True,
            secret_lookup_allowed=True,
            network_io_allowed=True,
        ))
        os.environ["GROQ_API_KEY"] = "SECRET_ALLOWED_AFTER_TYPED_FREE"
        os.environ["GROQ_SWARM_MODELS"] = "test/model"
        driver.reset_boundary_audit()

        admitted = driver.sync_attestation_from_typed_admission()
        report = driver.discover_and_export(0.01)

        self.assertEqual(admitted, ["groq"])
        self.assertEqual(driver.BOUNDARY_AUDIT["secret_lookup_count"], 1)
        self.assertEqual(driver.BOUNDARY_AUDIT["network_attempt_count"], 0)
        self.assertEqual(report["groq"]["keys"], 1)
        self.assertEqual(report["groq"]["source"], "environment_override")

    def test_typed_free_catalog_attempt_is_counted_after_secret_read(self) -> None:
        self.activate(self.write_admission(
            cost_class="FREE",
            admitted=True,
            secret_lookup_allowed=True,
            network_io_allowed=True,
        ))
        os.environ["GROQ_API_KEY"] = "SECRET_ALLOWED_AFTER_TYPED_FREE"
        driver.reset_boundary_audit()
        driver.sync_attestation_from_typed_admission()

        with mock.patch.object(driver, "fetch_catalog", return_value=[]):
            report = driver.discover_and_export(0.01)

        self.assertEqual(driver.BOUNDARY_AUDIT["secret_lookup_count"], 1)
        self.assertEqual(driver.BOUNDARY_AUDIT["network_attempt_count"], 1)
        self.assertEqual(report["groq"]["source"], "controller_fallback")

    def test_supervisor_does_not_source_legacy_mixed_secret_files(self) -> None:
        source = (TOOLS / "run_24h_entityos_swarm_supervisor.sh").read_text(encoding="utf-8")
        self.assertNotIn("research_entity/private/API_TOKENS.env", source)
        self.assertNotIn("load_all_secret_sources", source)
        self.assertIn("provider_free_admitted", source)
        self.assertIn("load_provider_secret_sources", source)
        self.assertIn("TYPED_COST_CLASS_FREE_BEFORE_SECRET_LOOKUP_AND_NETWORK_IO", source)


if __name__ == "__main__":
    unittest.main()
