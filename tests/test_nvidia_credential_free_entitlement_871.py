from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
import sys
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import free_lane_provenance as provenance
import nvidia_free_entitlement as nvidia


class NvidiaCredentialFreeEntitlement871Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.artifacts = root / "artifacts"
        self.admission = root / "FREE_PROVIDER_ADMISSION.json"
        self.economic = root / "FREE_LANE_ECONOMIC_PROVENANCE.json"
        self.entitlements = root / "NVIDIA_CREDENTIAL_FREE_ENTITLEMENTS.json"
        self.admission.write_text(
            json.dumps(
                {
                    "schema": provenance.ADMISSION_SCHEMA,
                    "authority_epoch": "8.71",
                    "mode": "FREE_ONLY",
                    "providers": {
                        "nvidia": {"admitted": True, "cost_class": "FREE"}
                    },
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        self.economic.write_text(
            json.dumps(
                {
                    "schema": provenance.PROVENANCE_SCHEMA,
                    "authority_epoch": "8.71",
                    "mode": "FREE_ONLY",
                    "providers": {
                        "nvidia": {
                            "allowed_endpoint_host": nvidia.NVIDIA_HOST,
                            "evidence_kind": "NVIDIA_HOSTED_NIM_DEVELOPER_FREE_PROTOTYPING",
                            "source": "provider-global-docs-are-not-credential-proof",
                            "admitted_credential_fingerprints": ["legacy-fp-must-not-self-admit"],
                        }
                    },
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        self._write_entitlements([])
        self.old_admission = provenance.ADMISSION_PATH
        self.old_economic = provenance.PROVENANCE_PATH
        self.old_entitlements = provenance.NVIDIA_ENTITLEMENT_PATH
        provenance.ADMISSION_PATH = self.admission
        provenance.PROVENANCE_PATH = self.economic
        provenance.NVIDIA_ENTITLEMENT_PATH = self.entitlements

    def tearDown(self) -> None:
        provenance.ADMISSION_PATH = self.old_admission
        provenance.PROVENANCE_PATH = self.old_economic
        provenance.NVIDIA_ENTITLEMENT_PATH = self.old_entitlements
        self.tmp.cleanup()

    def _write_entitlements(self, receipts: list[dict]) -> None:
        self.entitlements.write_text(
            json.dumps(
                {
                    "schema": nvidia.SET_SCHEMA,
                    "authority_epoch": "8.71",
                    "mode": "FREE_ONLY",
                    "provider": "nvidia",
                    "endpoint_host": nvidia.NVIDIA_HOST,
                    "receipts": receipts,
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )

    def _admission_digest(self) -> str:
        return hashlib.sha256(self.admission.read_bytes()).hexdigest()

    def _receipt(self, fingerprint: str = "fp-bound") -> dict:
        evidence = {
            "observation_kind": "NVIDIA_ACCOUNT_CONSOLE_FREE_ENTITLEMENT",
            "entitlement_class": nvidia.ENTITLEMENT_CLASS,
            "provider_subject_ref": "sha256:provider-subject-ref",
            "source_locator": "nvidia-account-console:developer-program",
            "provider_observed_at": "2026-08-24T13:00:00Z",
        }
        return {
            "schema": nvidia.RECEIPT_SCHEMA,
            "source_commit_and_tree": {"commit": "a" * 40, "tree": "b" * 40},
            "credential_fingerprint": fingerprint,
            "provider": "nvidia",
            "endpoint_host": nvidia.NVIDIA_HOST,
            "provider_side_developer_program_or_free_hosted_nim_entitlement_evidence": evidence,
            "entitlement_observed_at": "2026-08-24T13:00:00Z",
            "entitlement_evidence_digest": nvidia._digest(evidence),
            "typed_admission_epoch": "8.71",
            "typed_admission_digest": self._admission_digest(),
        }

    def _binding(self, fingerprint: str) -> dict:
        return provenance.current_lane_binding(
            "nvidia",
            fingerprint,
            "nvidia/model",
            "https://integrate.api.nvidia.com/v1/chat/completions",
            artifacts=self.artifacts,
        )

    def test_provider_global_or_legacy_fingerprint_label_cannot_self_admit(self) -> None:
        result = self._binding("legacy-fp-must-not-self-admit")
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "NVIDIA_CREDENTIAL_FREE_ENTITLEMENT_NOT_BOUND")

    def test_exact_bound_credential_receipt_admits(self) -> None:
        self._write_entitlements([self._receipt()])
        result = self._binding("fp-bound")
        self.assertTrue(result["ok"])
        evidence = result["evidence"]
        self.assertEqual(evidence["kind"], nvidia.RECEIPT_SCHEMA)
        self.assertEqual(evidence["credential_fingerprint"], "fp-bound")
        self.assertEqual(
            evidence["provider_observation"]["entitlement_class"],
            nvidia.ENTITLEMENT_CLASS,
        )

    def test_unbound_fingerprint_fails_closed(self) -> None:
        self._write_entitlements([self._receipt()])
        result = self._binding("fp-other")
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "NVIDIA_CREDENTIAL_FREE_ENTITLEMENT_NOT_BOUND")

    def test_admission_digest_drift_invalidates_receipt(self) -> None:
        self._write_entitlements([self._receipt()])
        obj = json.loads(self.admission.read_text(encoding="utf-8"))
        obj["revision_note"] = "same epoch but different exact admission bytes"
        self.admission.write_text(json.dumps(obj, sort_keys=True), encoding="utf-8")
        result = self._binding("fp-bound")
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "NVIDIA_CREDENTIAL_ENTITLEMENT_RECEIPT_INVALID_OR_STALE")

    def test_evidence_digest_tamper_invalidates_receipt(self) -> None:
        receipt = self._receipt()
        receipt["provider_side_developer_program_or_free_hosted_nim_entitlement_evidence"][
            "source_locator"
        ] = "tampered-after-digest"
        self._write_entitlements([receipt])
        result = self._binding("fp-bound")
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "NVIDIA_CREDENTIAL_ENTITLEMENT_RECEIPT_INVALID_OR_STALE")

    def test_wrong_endpoint_fails_before_entitlement_use(self) -> None:
        self._write_entitlements([self._receipt()])
        result = provenance.current_lane_binding(
            "nvidia",
            "fp-bound",
            "nvidia/model",
            "https://example.com/v1/chat/completions",
            artifacts=self.artifacts,
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "ENDPOINT_NOT_ZERO_COST_BOUND")


if __name__ == "__main__":
    unittest.main()
