from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import free_lane_provenance as provenance


class FreeLaneSupervisorBinding871Tests(unittest.TestCase):
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
        self.admission.write_text(
            json.dumps(
                {
                    "schema": provenance.ADMISSION_SCHEMA,
                    "authority_epoch": self.EPOCH,
                    "mode": "FREE_ONLY",
                    "providers": {
                        "openrouter": {"admitted": True, "cost_class": "FREE"}
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
                        }
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

    def _write_steering(
        self,
        *,
        execution_state: str | None = None,
        contingents: list[str] | None = None,
    ) -> None:
        free_only = {
            "enabled": True,
            "no_paid_fallback": True,
            "owner_authorized_free_contingents": contingents
            if contingents is not None
            else ["openrouter"],
        }
        if execution_state is not None:
            free_only["execution_state"] = execution_state
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

    def _binding(self) -> dict:
        return provenance.current_lane_binding(
            "openrouter",
            "fixture-fp",
            "openrouter/free",
            "https://openrouter.ai/api/v1/chat/completions",
            artifacts=self.artifacts,
        )

    def test_positive_binding_carries_exact_supervisor_digests(self) -> None:
        binding = self._binding()
        self.assertTrue(binding["ok"])
        self.assertEqual(binding["supervisor_epoch"], self.EPOCH)
        self.assertEqual(len(binding["supervisor_inbox_digest"]), 64)
        self.assertEqual(len(binding["supervisor_steering_digest"]), 64)
        self.assertTrue(provenance.binding_still_current(binding))

    def test_future_supervisor_epoch_rejects_stale_admission_and_provenance(self) -> None:
        self.assertTrue(self._binding()["ok"])
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
        binding = self._binding()
        self.assertFalse(binding["ok"])
        self.assertEqual(binding["reason"], "FREE_LANE_SUPERVISOR_EPOCH_MISMATCH")

    def test_supervisor_quarantine_rejects_before_lane_evidence_can_authorize(self) -> None:
        self.assertTrue(self._binding()["ok"])
        self._write_steering(execution_state="RUNTIME_QUARANTINED")
        binding = self._binding()
        self.assertFalse(binding["ok"])
        self.assertEqual(binding["reason"], "FREE_LANE_AUTHORITY_SNAPSHOT_INVALID")
        self.assertIn(
            "SUPERVISOR_EXTERNAL_PROVIDER_EXECUTION_NOT_AUTHORIZED",
            binding["detail"],
        )

    def test_provider_removed_from_supervisor_contingents_fails_closed(self) -> None:
        self.assertTrue(self._binding()["ok"])
        self._write_steering(contingents=["groq"])
        binding = self._binding()
        self.assertFalse(binding["ok"])
        self.assertEqual(
            binding["reason"], "PROVIDER_NOT_AUTHORIZED_BY_CURRENT_SUPERVISOR"
        )

    def test_steering_mutation_invalidates_existing_binding(self) -> None:
        binding = self._binding()
        self.assertTrue(binding["ok"])
        self._write_steering(contingents=["openrouter", "groq"])
        self.assertFalse(provenance.binding_still_current(binding))

    def test_execution_receipt_preserves_supervisor_identity(self) -> None:
        binding = self._binding()
        receipt = provenance.emit_execution_receipt(
            provider="openrouter",
            credential_fingerprint="fixture-fp",
            model_or_route="openrouter/free",
            endpoint="https://openrouter.ai/api/v1/chat/completions",
            binding=binding,
            request_id="fixture-request",
            usage={},
            http_status=200,
            result_digest="fixture-result-digest",
            source_commit_and_tree={"commit": "fixture", "tree": "fixture"},
            binding_stable_after_call=True,
            artifacts=self.artifacts,
        )
        self.assertEqual(receipt["supervisor_epoch"], self.EPOCH)
        self.assertEqual(
            receipt["supervisor_inbox_digest"], binding["supervisor_inbox_digest"]
        )
        self.assertEqual(
            receipt["supervisor_steering_digest"], binding["supervisor_steering_digest"]
        )


if __name__ == "__main__":
    unittest.main()
