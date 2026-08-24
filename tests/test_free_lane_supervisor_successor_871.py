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

import free_lane_provenance as provenance


class FreeLaneSupervisorSuccessor871Tests(unittest.TestCase):
    EPOCH = "8.71"

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.root = root
        self.artifacts = root / "artifacts"
        self.admission = root / "FREE_PROVIDER_ADMISSION.json"
        self.economic = root / "FREE_LANE_ECONOMIC_PROVENANCE.json"
        self.supervisor_dir = root / "research_entity/claycode/autonomous"
        self.supervisor_dir.mkdir(parents=True)
        self.inbox = self.supervisor_dir / "SUPERVISOR_INBOX.json"
        self.steering = self.supervisor_dir / "SUPERVISOR_STEERING_8_71.json"

        evidence = {
            "sources": ["fixture"],
            "provider_statement": "fixture free entitlement",
            "credential_binding_observation": "fixture-bound credential",
            "scope": "fixture hosted NIM only",
        }
        self.admission.write_text(
            json.dumps(
                {
                    "schema": provenance.ADMISSION_SCHEMA,
                    "authority_epoch": self.EPOCH,
                    "mode": "FREE_ONLY",
                    "providers": {
                        "openrouter": {"admitted": True, "cost_class": "FREE"},
                        "nvidia": {"admitted": True, "cost_class": "FREE"},
                    },
                }
            ),
            encoding="utf-8",
        )
        self.economic.write_text(
            json.dumps(
                {
                    "schema": provenance.PROVENANCE_SCHEMA,
                    "authority_epoch": self.EPOCH,
                    "mode": "FREE_ONLY",
                    "providers": {
                        "openrouter": {
                            "allowed_endpoint_host": "openrouter.ai",
                            "allowed_routes": ["openrouter/free"],
                            "evidence_kind": "EXACT_ROUTE_ZERO_PRICE",
                            "source": "fixture",
                        },
                        "nvidia": {
                            "allowed_endpoint_host": "integrate.api.nvidia.com",
                            "admitted_credential_fingerprints": ["nvidia-fp"],
                            "evidence_kind": "EXACT_DEVELOPER_API_CREDENTIAL_PLUS_FREE_HOSTED_NIM_ENDPOINT",
                            "source": "fixture",
                            "scope": "fixture hosted NIM only",
                            "credential_entitlement_evidence": {
                                "nvidia-fp": {
                                    "entitlement_observed_at": "2026-08-24",
                                    "entitlement_observed_at_precision": "day",
                                    "provider_side_developer_program_or_free_hosted_nim_entitlement_evidence": evidence,
                                    "entitlement_evidence_digest": provenance._canonical_json_digest(evidence),
                                }
                            },
                        },
                    },
                }
            ),
            encoding="utf-8",
        )
        self.inbox.write_text(
            json.dumps(
                {
                    "schema_version": self.EPOCH,
                    "steering": "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_71.json",
                }
            ),
            encoding="utf-8",
        )
        self._write_steering()

        self.old_root = provenance.ROOT
        self.old_admission = provenance.ADMISSION_PATH
        self.old_provenance = provenance.PROVENANCE_PATH
        self.old_inbox = provenance.SUPERVISOR_INBOX_PATH
        provenance.ROOT = root
        provenance.ADMISSION_PATH = self.admission
        provenance.PROVENANCE_PATH = self.economic
        provenance.SUPERVISOR_INBOX_PATH = self.inbox

    def tearDown(self) -> None:
        provenance.ROOT = self.old_root
        provenance.ADMISSION_PATH = self.old_admission
        provenance.PROVENANCE_PATH = self.old_provenance
        provenance.SUPERVISOR_INBOX_PATH = self.old_inbox
        self.tmp.cleanup()

    def _write_steering(self, *, state: str | None = None, contingents=None) -> None:
        free_only = {
            "enabled": True,
            "no_paid_fallback": True,
            "together_forbidden": True,
            "owner_authorized_free_contingents": contingents or ["openrouter", "nvidia"],
        }
        if state is not None:
            free_only["execution_state"] = state
        self.steering.write_text(
            json.dumps(
                {
                    "schema_version": self.EPOCH,
                    "active_program": "ENTITYOS_HCU",
                    "product": "EntityOS",
                    "integrated_cognition_compute_architecture": "HCU",
                    "free_only": free_only,
                }
            ),
            encoding="utf-8",
        )

    def _openrouter(self) -> dict:
        return provenance.current_lane_binding(
            "openrouter",
            "fp",
            "openrouter/free",
            "https://openrouter.ai/api/v1/chat/completions",
            artifacts=self.artifacts,
        )

    def test_positive_binding_contains_supervisor_digests(self) -> None:
        binding = self._openrouter()
        self.assertTrue(binding["ok"])
        self.assertEqual(binding["supervisor_epoch"], self.EPOCH)
        self.assertEqual(len(binding["supervisor_inbox_digest"]), 64)
        self.assertEqual(len(binding["supervisor_steering_digest"]), 64)

    def test_stale_lane_files_after_supervisor_epoch_advance_fail_closed(self) -> None:
        newer = self.supervisor_dir / "SUPERVISOR_STEERING_8_72.json"
        newer.write_text(
            json.dumps(
                {
                    "schema_version": "8.72",
                    "active_program": "ENTITYOS_HCU",
                    "product": "EntityOS",
                    "integrated_cognition_compute_architecture": "HCU",
                    "free_only": {
                        "enabled": True,
                        "no_paid_fallback": True,
                        "together_forbidden": True,
                        "owner_authorized_free_contingents": ["openrouter"],
                    },
                }
            ),
            encoding="utf-8",
        )
        self.inbox.write_text(
            json.dumps(
                {
                    "schema_version": "8.72",
                    "steering": "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_72.json",
                }
            ),
            encoding="utf-8",
        )
        binding = self._openrouter()
        self.assertFalse(binding["ok"])
        self.assertEqual(binding["reason"], "FREE_LANE_SUPERVISOR_EPOCH_MISMATCH")

    def test_supervisor_quarantine_fails_before_lane_admission(self) -> None:
        self._write_steering(state="RUNTIME_QUARANTINED")
        binding = self._openrouter()
        self.assertFalse(binding["ok"])
        self.assertEqual(binding["reason"], "FREE_LANE_AUTHORITY_SNAPSHOT_INVALID")
        self.assertIn("SUPERVISOR_EXTERNAL_PROVIDER_EXECUTION_NOT_AUTHORIZED", binding["detail"])

    def test_provider_removed_from_current_supervisor_fails_closed(self) -> None:
        self._write_steering(contingents=["nvidia"])
        binding = self._openrouter()
        self.assertFalse(binding["ok"])
        self.assertEqual(binding["reason"], "PROVIDER_NOT_AUTHORIZED_BY_CURRENT_SUPERVISOR")

    def test_supervisor_mutation_invalidates_cached_binding(self) -> None:
        binding = self._openrouter()
        self.assertTrue(binding["ok"])
        self._write_steering(contingents=["openrouter", "nvidia", "groq"])
        self.assertFalse(provenance.binding_still_current(binding))

    def test_nvidia_still_requires_digest_bound_entitlement(self) -> None:
        binding = provenance.current_lane_binding(
            "nvidia",
            "nvidia-fp",
            "fixture/model",
            "https://integrate.api.nvidia.com/v1/chat/completions",
            artifacts=self.artifacts,
        )
        self.assertTrue(binding["ok"])
        receipt = binding["evidence"]["credential_entitlement_receipt"]
        self.assertEqual(receipt["schema"], provenance.NVIDIA_ENTITLEMENT_SCHEMA)
        self.assertEqual(receipt["credential_fingerprint"], "nvidia-fp")

        obj = json.loads(self.economic.read_text(encoding="utf-8"))
        obj["providers"]["nvidia"]["credential_entitlement_evidence"]["nvidia-fp"][
            "provider_side_developer_program_or_free_hosted_nim_entitlement_evidence"
        ]["scope"] = "tampered"
        self.economic.write_text(json.dumps(obj), encoding="utf-8")
        denied = provenance.current_lane_binding(
            "nvidia",
            "nvidia-fp",
            "fixture/model",
            "https://integrate.api.nvidia.com/v1/chat/completions",
            artifacts=self.artifacts,
        )
        self.assertFalse(denied["ok"])
        self.assertEqual(
            denied["reason"],
            "NVIDIA_CREDENTIAL_FREE_ENTITLEMENT_EVIDENCE_NOT_BOUND",
        )


if __name__ == "__main__":
    unittest.main()
