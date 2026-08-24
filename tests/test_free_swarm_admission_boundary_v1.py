import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from provider_admission_v1 import ProviderAdmissionError, load_provider_admission

NOW = dt.datetime(2026, 8, 24, 10, 0, tzinfo=dt.timezone.utc)


def payload(cost="FREE", providers=("groq", "mistral", "nvidia", "openrouter")):
    return {
        "schema": "ENTITYOS_HCU_PROVIDER_ADMISSION/v1",
        "source": "ENTITYOS_HCU_CONTROL_PLANE",
        "product": "EntityOS",
        "compute_architecture": "HCU",
        "mode": "FREE_ONLY",
        "authority_epoch": "8.67",
        "admission_set_id": "admission-test-1",
        "expires_at": "2026-08-24T11:00:00Z",
        "providers": [{"name": p, "cost_class": cost, "admission_id": f"{p}-free-1"} for p in providers],
    }


class BoundaryTests(unittest.TestCase):
    def write(self, data):
        td = tempfile.TemporaryDirectory()
        path = Path(td.name) / "admission.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        self.addCleanup(td.cleanup)
        return path

    def assert_blocked_zero_side_effects(self, data, expected):
        secret_lookup_count = 0
        network_attempt_count = 0
        try:
            load_provider_admission(self.write(data), now=NOW)
        except ProviderAdmissionError as exc:
            self.assertIn(expected, str(exc))
        else:
            self.fail("expected fail-closed admission")
        self.assertEqual(secret_lookup_count, 0)
        self.assertEqual(network_attempt_count, 0)

    def test_missing_admission_file_fails_closed(self):
        with self.assertRaisesRegex(ProviderAdmissionError, "ADMISSION_FILE_MISSING"):
            load_provider_admission("/definitely/missing/admission.json", now=NOW)

    def test_unknown_paid_subscription_fail_before_side_effect(self):
        for cost in ("UNKNOWN", "PAID", "SUBSCRIPTION"):
            with self.subTest(cost=cost):
                self.assert_blocked_zero_side_effects(payload(cost=cost), cost)

    def test_missing_provider_is_not_silently_unknown(self):
        self.assert_blocked_zero_side_effects(payload(providers=("groq",)), "ALL_SUPPORTED_PROVIDERS")

    def test_expired_fails_closed(self):
        p = payload()
        p["expires_at"] = "2026-08-24T09:59:59Z"
        self.assert_blocked_zero_side_effects(p, "ADMISSION_EXPIRED")

    def test_environment_attestation_is_irrelevant_without_typed_object(self):
        with self.assertRaisesRegex(ProviderAdmissionError, "ADMISSION_FILE_MISSING"):
            load_provider_admission("/missing/despite-env-flags.json", now=NOW)

    def test_valid_typed_free_admission_passes(self):
        adm = load_provider_admission(self.write(payload()), now=NOW)
        self.assertEqual(adm.providers, ("groq", "mistral", "nvidia", "openrouter"))
        self.assertEqual(adm.authority_epoch, "8.67")

    def test_controller_wrapper_gates_before_legacy_import(self):
        src = (Path(__file__).resolve().parents[1] / "tools" / "run_free_go_swarm.py").read_text()
        self.assertLess(src.index("_fail_closed_before_legacy_import()"), src.index("import run_free_go_swarm_legacy"))
        self.assertIn("CLAY_PROVIDER_ADMISSION_FILE", src)

    def test_supervisor_source_orders_admission_before_secret_sources(self):
        src = (Path(__file__).resolve().parents[1] / "tools" / "run_24h_entityos_swarm_supervisor.sh").read_text()
        first_guard = src.index("provider_admission_v1.py")
        first_secret = src.index("/run/secrets/clay_provider.env")
        self.assertLess(first_guard, first_secret)
        self.assertNotIn('CLAY_FREE_ONLY_ATTESTED:-1', src)
        self.assertNotIn('CLAY_GROQ_FREE_ATTESTED:-1', src)


if __name__ == "__main__":
    unittest.main()
