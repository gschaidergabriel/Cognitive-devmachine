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

import free_swarm_provider_admission as admission
import run_free_go_swarm as base
import run_24h_entityos_swarm as entityos


class FreeSwarmProviderAdmissionTests(unittest.TestCase):
    NOW = dt.datetime(2026, 8, 24, 10, 0, tzinfo=dt.timezone.utc)

    def make_tree(self, cost_class="UNKNOWN", evidence_status="NOT_VERIFIED_FOR_CURRENT_ACCOUNT_AND_ENDPOINT_SCOPE", *, valid_until="2026-08-25T10:00:00Z", endpoint=None, active=True):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        sup = root / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
        sup.parent.mkdir(parents=True, exist_ok=True)
        sup.write_text(json.dumps({
            "schema_version": "8.67",
            "active_program": "ENTITYOS_HCU",
            "product": "EntityOS",
            "integrated_cognition_compute_architecture": "HCU",
            "free_only": {
                "enabled": True,
                "provider_execution_requires_typed_explicit_free_classification": True,
                "environment_attestation_flag_alone_is_not_provider_admission": True,
                "admission_boundary": admission.EXPECTED_BOUNDARY,
            },
        }), encoding="utf-8")
        ctl = root / "research_entity/claycode/autonomous/FREE_SWARM_PROVIDER_ADMISSION.json"
        ctl.write_text(json.dumps({
            "schema": admission.EXPECTED_SCHEMA,
            "authority_epoch": "8.67",
            "mode": "FREE_ONLY",
            "product": "EntityOS",
            "compute_architecture": "HCU",
            "status": admission.POSITIVE_CONTROL_STATUS if active else "FAIL_CLOSED_NO_PROVIDER_ADMITTED",
            "admission_boundary": admission.EXPECTED_BOUNDARY,
            "providers": {
                "groq": {
                    "cost_class": cost_class,
                    "endpoints": [endpoint or "https://api.groq.com/openai/v1/chat/completions"],
                    "cost_evidence": {
                        "status": evidence_status,
                        "checked_at": "2026-08-24T09:00:00Z",
                        "valid_until": valid_until,
                        "sources": ["https://example.invalid/authoritative-account-cost-evidence"],
                        "scope": "CURRENT_CONNECTED_ACCOUNT_AND_DECLARED_ENDPOINTS",
                    },
                    "secret_sources": ["research_entity/private/GROQ_API.env"],
                }
            },
        }), encoding="utf-8")
        return td, root

    def test_missing_unknown_paid_subscription_are_rejected(self):
        for cost_class in ("UNKNOWN", "PAID", "SUBSCRIPTION"):
            with self.subTest(cost_class=cost_class):
                td, root = self.make_tree(cost_class=cost_class)
                self.addCleanup(td.cleanup)
                self.assertFalse(admission.provider_is_explicit_free(
                    "groq", "https://api.groq.com/openai/v1/chat/completions", root=root, now=self.NOW))
                self.assertEqual(admission.admitted_provider_names(root=root, now=self.NOW), [])
                self.assertEqual(admission.admitted_secret_sources(root=root, now=self.NOW), [])

    def test_positive_record_cannot_activate_while_control_status_is_fail_closed(self):
        td, root = self.make_tree(cost_class="FREE", evidence_status="VERIFIED_ZERO_MONETARY_COST", active=False)
        self.addCleanup(td.cleanup)
        self.assertFalse(admission.provider_is_explicit_free(
            "groq", "https://api.groq.com/openai/v1/chat/completions", root=root, now=self.NOW))
        self.assertEqual(admission.admitted_secret_sources(root=root, now=self.NOW), [])

    def test_exact_free_current_evidence_admits_exact_endpoint_only(self):
        td, root = self.make_tree(cost_class="FREE", evidence_status="VERIFIED_ZERO_MONETARY_COST")
        self.addCleanup(td.cleanup)
        self.assertTrue(admission.provider_is_explicit_free(
            "groq", "https://api.groq.com/openai/v1/chat/completions", root=root, now=self.NOW))
        self.assertFalse(admission.provider_is_explicit_free(
            "groq", "https://api.groq.com/openai/v1/models", root=root, now=self.NOW))
        self.assertEqual(admission.admitted_provider_names(root=root, now=self.NOW), ["groq"])
        sources = admission.admitted_secret_sources(root=root, now=self.NOW)
        self.assertEqual(sources, [("groq", str(root / "research_entity/private/GROQ_API.env"))])

    def test_free_record_without_canonical_chat_endpoint_cannot_unlock_secret_source(self):
        td, root = self.make_tree(
            cost_class="FREE", evidence_status="VERIFIED_ZERO_MONETARY_COST",
            endpoint="https://api.groq.com/openai/v1/models")
        self.addCleanup(td.cleanup)
        self.assertEqual(admission.admitted_provider_names(root=root, now=self.NOW), [])
        self.assertEqual(admission.admitted_secret_sources(root=root, now=self.NOW), [])

    def test_stale_free_evidence_returns_to_fail_closed(self):
        td, root = self.make_tree(
            cost_class="FREE", evidence_status="VERIFIED_ZERO_MONETARY_COST",
            valid_until="2026-08-24T09:30:00Z")
        self.addCleanup(td.cleanup)
        self.assertFalse(admission.provider_is_explicit_free(
            "groq", "https://api.groq.com/openai/v1/chat/completions", root=root, now=self.NOW))

    def test_authority_epoch_drift_fails_closed(self):
        td, root = self.make_tree(cost_class="FREE", evidence_status="VERIFIED_ZERO_MONETARY_COST")
        self.addCleanup(td.cleanup)
        path = root / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
        doc = json.loads(path.read_text(encoding="utf-8")); doc["schema_version"] = "8.68"
        path.write_text(json.dumps(doc), encoding="utf-8")
        with self.assertRaisesRegex(admission.ProviderAdmissionError, "AUTHORITY_EPOCH_DRIFT"):
            admission.provider_is_explicit_free(
                "groq", "https://api.groq.com/openai/v1/chat/completions", root=root, now=self.NOW)

    def test_blocked_collect_keys_never_reads_provider_environment(self):
        spec = base.PROVIDERS[0]
        with mock.patch.object(base, "provider_network_admitted", return_value=False), \
             mock.patch.object(base.os, "getenv", side_effect=AssertionError("secret lookup fired")):
            self.assertEqual(base.collect_keys(spec), [])

    def test_direct_chat_network_path_rechecks_typed_admission(self):
        spec = base.PROVIDERS[0]
        with mock.patch.object(base, "provider_network_admitted", return_value=False), \
             mock.patch.object(base.urllib.request, "urlopen", side_effect=AssertionError("socket fired")):
            with self.assertRaisesRegex(admission.ProviderAdmissionError, "PROVIDER_NETWORK_NOT_ADMITTED"):
                base.request_chat(spec, "synthetic-key", "synthetic-model", "prompt", 1, 0.01)

    def test_direct_catalog_network_path_rechecks_typed_admission(self):
        spec = base.PROVIDERS[0]
        with mock.patch.object(base, "provider_network_admitted", return_value=False), \
             mock.patch.object(entityos.urllib.request, "urlopen", side_effect=AssertionError("socket fired")):
            self.assertEqual(entityos.fetch_catalog(spec, entityos.CATALOGS[spec.name], "synthetic-key", 0.01), [])

    def test_supervisor_no_longer_sources_untyped_shared_secret_files(self):
        text = (TOOLS / "run_24h_entityos_swarm_supervisor.sh").read_text(encoding="utf-8")
        for forbidden in (
            "/run/secrets/clay_provider.env",
            "/artifacts/.clay_provider.env",
            "/cache/clay_provider.env",
            "$ROOT/.clay_provider.env",
            "$ROOT/research_entity/private/API_TOKENS.env",
            "load_all_secret_sources",
            "attest_free_only",
        ):
            self.assertNotIn(forbidden, text)
        self.assertIn("refresh_typed_free_admission", text)
        self.assertIn("secret-sources", text)

    def test_current_repository_control_is_fail_closed_until_real_free_evidence_exists(self):
        self.assertEqual(admission.admitted_provider_names(root=ROOT, now=self.NOW), [])
        self.assertEqual(admission.admitted_secret_sources(root=ROOT, now=self.NOW), [])


if __name__ == "__main__":
    unittest.main()
