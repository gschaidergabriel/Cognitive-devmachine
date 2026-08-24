from __future__ import annotations

import importlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import free_provider_admission as admission
import run_free_go_swarm as base


class CanonicalAdmissionTests(unittest.TestCase):
    def test_canonical_registry_binds_active_supervisor_and_admits_zero(self):
        payload = admission.load_provider_admission()
        inbox = json.loads(admission.SUPERVISOR_INBOX_PATH.read_text(encoding="utf-8"))
        self.assertEqual(payload["authority_epoch"], str(inbox["schema_version"]))
        self.assertEqual(payload["supervisor_steering"], inbox["steering"])
        self.assertEqual(admission.admitted_provider_names(payload), ())

    def test_all_credential_bearing_distillery_and_swarm_providers_are_covered(self):
        self.assertEqual(
            admission.ALLOWED_PROVIDERS,
            frozenset({"groq", "mistral", "nvidia", "openrouter", "tavily", "exa"}),
        )

    def test_stale_supervisor_epoch_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            inbox_path = Path(td) / "inbox.json"
            inbox_path.write_text(json.dumps({
                "schema_version": "8.66",
                "steering": "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_66.json",
            }), encoding="utf-8")
            with self.assertRaisesRegex(admission.ProviderAdmissionError, "AUTHORITY_EPOCH_MISMATCH"):
                admission.load_provider_admission(admission.ADMISSION_PATH, supervisor_inbox_path=inbox_path)

    def test_nonfree_record_cannot_self_admit(self):
        payload = json.loads(admission.ADMISSION_PATH.read_text(encoding="utf-8"))
        payload["providers"]["groq"]["admitted"] = True
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "admission.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(admission.ProviderAdmissionError, "NONFREE_CANNOT_BE_ADMITTED"):
                admission.load_provider_admission(path)

    def test_candidate_free_document_cannot_self_grant_runtime_authority(self):
        payload = json.loads(admission.ADMISSION_PATH.read_text(encoding="utf-8"))
        payload["providers"]["groq"].update({"cost_class": "FREE", "admitted": True})
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "admission.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            loaded = admission.load_provider_admission(path)
            self.assertEqual(loaded["providers"]["groq"]["cost_class"], "FREE")
            self.assertTrue(loaded["providers"]["groq"]["admitted"])
            self.assertFalse(admission.provider_is_admitted_free("groq", loaded))
            self.assertFalse(admission.provider_is_admitted_free("mistral", loaded))


class PreSecretTripwireTests(unittest.TestCase):
    def test_legacy_controller_collect_keys_never_reads_env_for_unadmitted_provider(self):
        canonical = admission.load_provider_admission()
        spec = next(spec for spec in base.PROVIDERS if spec.name == "groq")
        original_getenv = base.os.getenv
        original_environ = base.os.environ

        class NoRead(dict):
            def items(self):
                raise AssertionError("provider environment enumeration before FREE admission")
            def __getitem__(self, key):
                raise AssertionError("provider environment value read before FREE admission")

        def no_getenv(*args, **kwargs):
            raise AssertionError("provider environment value read before FREE admission")

        try:
            base.os.getenv = no_getenv
            base.os.environ = NoRead()
            self.assertEqual(base.collect_keys(spec, canonical), [])
        finally:
            base.os.getenv = original_getenv
            base.os.environ = original_environ

    def test_driver_catalog_does_not_open_socket_for_unadmitted_provider(self):
        driver = importlib.import_module("run_24h_entityos_swarm")
        original = driver.urllib.request.urlopen
        calls = []

        def tripwire(*args, **kwargs):
            calls.append((args, kwargs))
            raise AssertionError("network opened before FREE admission")

        try:
            driver.urllib.request.urlopen = tripwire
            self.assertEqual(driver.fetch_catalog("groq", "https://example.invalid", "synthetic", 0.01), [])
            self.assertEqual(calls, [])
        finally:
            driver.urllib.request.urlopen = original

    def test_distillery_entry_blocks_secret_and_network_before_underlying_calls(self):
        entry = importlib.import_module("run_research_distillery_entry")
        secret_calls = []
        network_calls = []
        original_secret = entry._original_get_secret
        original_request = entry._original_request_json

        def secret_tripwire(*args, **kwargs):
            secret_calls.append((args, kwargs))
            raise AssertionError("secret lookup crossed typed admission")

        def network_tripwire(*args, **kwargs):
            network_calls.append((args, kwargs))
            raise AssertionError("provider network crossed typed admission")

        try:
            entry._original_get_secret = secret_tripwire
            entry._original_request_json = network_tripwire
            self.assertEqual(entry.d.get_secret("OPENROUTER_API_KEY", required=False), "")
            status, headers, body = entry.d.request_json(
                "openrouter", "tripwire", "https://example.invalid", key="synthetic"
            )
            self.assertEqual(status, 0)
            self.assertEqual(headers, {})
            self.assertIn("TYPED_FREE_PROVIDER_ADMISSION_REQUIRED", body["error"])
            self.assertEqual(secret_calls, [])
            self.assertEqual(network_calls, [])
        finally:
            entry._original_get_secret = original_secret
            entry._original_request_json = original_request


class SupervisorSourceFenceTests(unittest.TestCase):
    def test_shell_syntax_and_no_catchall_secrets(self):
        path = TOOLS / "run_24h_entityos_swarm_supervisor.sh"
        subprocess.run(["bash", "-n", str(path)], check=True)
        text = path.read_text(encoding="utf-8")
        self.assertNotIn("/run/secrets/clay_provider.env", text)
        self.assertNotIn("/artifacts/.clay_provider.env", text)
        self.assertNotIn("research_entity/private/API_TOKENS.env", text)
        self.assertNotIn("load_all_secret_sources", text)

    def test_loop_gates_before_provider_secret_source(self):
        text = (TOOLS / "run_24h_entityos_swarm_supervisor.sh").read_text(encoding="utf-8")
        loop = text.index("while (( $(date +%s) < DEADLINE ))")
        gate = text.index("typed_admitted_providers", loop)
        source = text.index("load_provider_secret_sources", loop)
        self.assertLess(gate, source)
        self.assertIn("provider_is_still_admitted", text[source - 500:source])


if __name__ == "__main__":
    unittest.main()
