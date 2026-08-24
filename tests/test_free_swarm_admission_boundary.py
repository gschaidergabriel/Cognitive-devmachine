from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import free_provider_admission as admission
import run_free_go_swarm as base

COUNTERS = {"secret": 0, "network": 0}
TEST_BINDING = (
    "8.TEST",
    "research_entity/claycode/autonomous/SUPERVISOR_STEERING_TEST.json",
)
SYNTHETIC_EVIDENCE_SHA256 = hashlib.sha256(
    b"synthetic-local-free-provider-admission-boundary-evidence"
).hexdigest()


def load_driver():
    spec = importlib.util.spec_from_file_location(
        "entityos_swarm_driver_under_test", TOOLS / "run_24h_entityos_swarm.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def free_evidence(provider: str) -> dict:
    return {
        "evidence_ref": f"synthetic-test-fixture:{provider}",
        "checked_at": "TEST_ONLY",
        "claim": "ZERO_MONETARY_COST_FOR_BOUND_PROVIDER_SCOPE",
        "scope": provider,
        "evidence_sha256": SYNTHETIC_EVIDENCE_SHA256,
    }


def provider_item(provider: str, cost_class: str = "FREE") -> dict:
    cost_class = cost_class.upper()
    item = {
        "cost_class": cost_class,
        "admitted": cost_class == "FREE",
    }
    if cost_class == "FREE":
        item["cost_evidence"] = free_evidence(provider)
    return item


def admission_document(
    *,
    binding: tuple[str, str],
    cost_class: str = "FREE",
    missing: str | None = None,
    source: str = admission.CONTROL_PLANE,
    free_only: bool = True,
) -> dict:
    providers = {
        provider: provider_item(provider, cost_class)
        for provider in admission.KNOWN_PROVIDERS
    }
    if missing:
        providers.pop(missing)
    return {
        "schema": admission.SCHEMA,
        "source": source,
        "free_only": free_only,
        "authority_epoch": binding[0],
        "supervisor_steering": binding[1],
        "providers": providers,
    }


class ProviderAdmissionValidatorTests(unittest.TestCase):
    def good(self):
        return admission_document(binding=TEST_BINDING)

    def test_all_free_pass(self):
        self.assertEqual(
            admission.validate_admission(
                self.good(), supervisor_binding=TEST_BINDING
            ),
            admission.KNOWN_PROVIDERS,
        )

    def test_missing_provider_denied_when_all_required(self):
        obj = admission_document(binding=TEST_BINDING, missing="nvidia")
        with self.assertRaisesRegex(ValueError, "provider_missing:nvidia"):
            admission.validate_admission(
                obj, require_all=True, supervisor_binding=TEST_BINDING
            )

    def test_unknown_paid_subscription_denied_per_provider(self):
        for cost_class in ("UNKNOWN", "PAID", "SUBSCRIPTION"):
            with self.subTest(cost_class=cost_class):
                obj = self.good()
                obj["providers"]["groq"] = provider_item("groq", cost_class)
                allowed, reason = admission.provider_decision(
                    obj, "groq", supervisor_binding=TEST_BINDING
                )
                self.assertFalse(allowed)
                self.assertIn(cost_class, reason)

    def test_environment_attestation_cannot_be_source(self):
        obj = self.good()
        obj["source"] = "ENV_ATTESTATION"
        with self.assertRaisesRegex(ValueError, "admission_wrong_source"):
            admission.validate_admission(
                obj, supervisor_binding=TEST_BINDING
            )

    def test_stale_authority_epoch_denied(self):
        obj = self.good()
        obj["authority_epoch"] = "8.STALE"
        with self.assertRaisesRegex(ValueError, "stale_or_wrong_authority_epoch"):
            admission.validate_admission(
                obj, supervisor_binding=TEST_BINDING
            )

    def test_free_without_evidence_denied(self):
        obj = self.good()
        obj["providers"]["groq"].pop("cost_evidence")
        with self.assertRaisesRegex(ValueError, "provider_free_evidence_missing:groq"):
            admission.provider_decision(
                obj, "groq", supervisor_binding=TEST_BINDING
            )


class DriverTripwireTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "admission.json"
        self.binding = admission.active_supervisor_binding()
        COUNTERS["secret"] = 0
        COUNTERS["network"] = 0

        self.saved_base_collect_keys = base.collect_keys
        self.saved_base_request_chat = base.request_chat

        def counted_collect_keys(spec):
            COUNTERS["secret"] += 1
            return []

        # The driver captures this as its post-admission collector when imported.
        base.collect_keys = counted_collect_keys
        self.driver = load_driver()

        self.saved_driver_require_provider = self.driver.require_provider_admitted
        self.saved_driver_admitted_providers = self.driver.admitted_providers_from_path
        self.driver.require_provider_admitted = (
            lambda provider, **_kwargs: admission.require_provider_admitted(
                provider, path=self.path
            )
        )
        self.driver.admitted_providers_from_path = (
            lambda *_args, **_kwargs: admission.admitted_providers_from_path(self.path)
        )

        self.original_urlopen = self.driver.urllib.request.urlopen

        def counted_urlopen(*args, **kwargs):
            COUNTERS["network"] += 1
            raise urllib.error.URLError("network_tripwire")

        self.driver.urllib.request.urlopen = counted_urlopen

    def tearDown(self):
        self.driver.urllib.request.urlopen = self.original_urlopen
        self.driver.require_provider_admitted = self.saved_driver_require_provider
        self.driver.admitted_providers_from_path = self.saved_driver_admitted_providers
        base.collect_keys = self.saved_base_collect_keys
        base.request_chat = self.saved_base_request_chat
        self.tmp.cleanup()
        for name in (
            "CLAY_PROVIDER_ADMISSION_FILE",
            "CLAY_FREE_ONLY_ATTESTED",
            "CLAY_GROQ_FREE_ATTESTED",
            "CLAY_MISTRAL_FREE_ATTESTED",
            "CLAY_NVIDIA_FREE_ATTESTED",
        ):
            os.environ.pop(name, None)

    def args(self):
        return argparse.Namespace(
            hours=0.01,
            max_tokens=1,
            context_chars=100,
            timeout=0.01,
            drain_seconds=0,
            output_dir="",
            inventory_only=True,
        )

    def write(
        self,
        *,
        cost_class: str = "FREE",
        missing: str | None = None,
        source: str = admission.CONTROL_PLANE,
        free_only: bool = True,
        stale_authority: bool = False,
    ) -> None:
        payload = admission_document(
            binding=self.binding,
            cost_class=cost_class,
            missing=missing,
            source=source,
            free_only=free_only,
        )
        if stale_authority:
            payload["authority_epoch"] = "8.STALE"
        self.path.write_text(
            json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )

    def assert_globally_denied_before_secret_or_network(self):
        rc = asyncio.run(self.driver.main(self.args()))
        self.assertIn(rc, (3, 4))
        self.assertEqual(COUNTERS, {"secret": 0, "network": 0})

    def test_missing_canonical_test_admission_has_zero_secret_and_network_attempts(self):
        self.assert_globally_denied_before_secret_or_network()

    def test_all_nonfree_classes_have_zero_secret_and_network_attempts(self):
        for cost_class in ("UNKNOWN", "PAID", "SUBSCRIPTION"):
            with self.subTest(cost_class=cost_class):
                COUNTERS["secret"] = COUNTERS["network"] = 0
                self.write(cost_class=cost_class)
                self.assert_globally_denied_before_secret_or_network()

    def test_wrong_source_has_zero_secret_and_network_attempts(self):
        self.write(source="ENV_ATTESTATION")
        self.assert_globally_denied_before_secret_or_network()

    def test_stale_authority_has_zero_secret_and_network_attempts(self):
        self.write(stale_authority=True)
        self.assert_globally_denied_before_secret_or_network()

    def test_all_free_reaches_secret_stage_only_after_admission(self):
        self.write()
        rc = asyncio.run(self.driver.main(self.args()))
        self.assertEqual(rc, 0)
        self.assertEqual(COUNTERS["secret"], len(base.PROVIDERS))
        self.assertEqual(COUNTERS["network"], 0)
        self.assertEqual(os.environ["CLAY_FREE_ONLY_ATTESTED"], "1")

    def test_network_tripwire_is_live_only_after_free_admission(self):
        def keys_present(spec):
            COUNTERS["secret"] += 1
            return [f"synthetic-{spec.name}-key"]

        self.driver._ORIGINAL_COLLECT_KEYS = keys_present
        self.write()
        rc = asyncio.run(self.driver.main(self.args()))
        self.assertEqual(rc, 0)
        self.assertEqual(COUNTERS["secret"], len(base.PROVIDERS))
        self.assertEqual(COUNTERS["network"], len(base.PROVIDERS))

    def test_missing_provider_is_blocked_without_touching_its_secret_or_network(self):
        self.write(missing="nvidia")
        nvidia = next(spec for spec in base.PROVIDERS if spec.name == "nvidia")
        COUNTERS["secret"] = COUNTERS["network"] = 0

        self.assertEqual(self.driver.base.collect_keys(nvidia), [])
        self.assertEqual(COUNTERS["secret"], 0)

        with self.assertRaises(admission.ProviderAdmissionError):
            self.driver.fetch_catalog(
                "nvidia", self.driver.CATALOGS["nvidia"], "synthetic-never-key", 0.01
            )
        self.assertEqual(COUNTERS["network"], 0)


class SupervisorSourceFenceTests(unittest.TestCase):
    def test_shell_syntax_and_presecret_ordering(self):
        path = TOOLS / "run_24h_entityos_swarm_supervisor.sh"
        subprocess.run(["bash", "-n", str(path)], check=True)
        text = path.read_text(encoding="utf-8")
        loop = text.index("while (( $(date +%s) < DEADLINE ))")
        gate = text.index("typed_free_admission_ready", loop)
        secret = text.index("load_admitted_provider_secret_sources", loop)
        self.assertLess(gate, secret)

    def test_broad_catch_all_secret_files_are_not_sourced(self):
        text = (TOOLS / "run_24h_entityos_swarm_supervisor.sh").read_text(encoding="utf-8")
        self.assertNotIn("research_entity/private/API_TOKENS.env", text)
        self.assertNotIn("/run/secrets/clay_provider.env", text)
        self.assertNotIn("/artifacts/.clay_provider.env", text)

    def test_production_driver_does_not_take_admission_path_from_environment(self):
        text = (TOOLS / "run_24h_entityos_swarm.py").read_text(encoding="utf-8")
        self.assertNotIn("CLAY_PROVIDER_ADMISSION_FILE", text)


if __name__ == "__main__":
    unittest.main()
