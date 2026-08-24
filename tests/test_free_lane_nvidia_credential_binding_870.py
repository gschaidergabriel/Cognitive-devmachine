from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from free_lane_provenance import (
    NVIDIA_ENTITLEMENT_SCHEMA,
    _lane_evidence_from_provenance,
)


def digest(value: object) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class NvidiaCredentialBinding870Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.artifacts_ctx = tempfile.TemporaryDirectory()
        self.artifacts = Path(self.artifacts_ctx.name)
        self.base_record = {
            "allowed_endpoint_host": "integrate.api.nvidia.com",
            "evidence_kind": "NVIDIA_HOSTED_NIM_DEVELOPER_FREE_PROTOTYPING",
            "source": "https://developer.nvidia.com/nim",
            "scope": "NVIDIA-hosted API Catalog/NIM prototyping endpoint only",
            "credential_plan_needed": True,
            "credential_entitlements": {},
        }

    def tearDown(self) -> None:
        self.artifacts_ctx.cleanup()

    def provenance(self, entitlements: dict | None = None) -> dict:
        return {
            "providers": {
                "nvidia": {
                    **self.base_record,
                    "credential_entitlements": entitlements or {},
                }
            }
        }

    def entitlement(
        self,
        *,
        model: str = "nvidia/test-model",
        confirmed: bool = True,
        evidence: dict | None = None,
    ) -> dict:
        provider_evidence = evidence or {
            "provider": "NVIDIA",
            "credential_fingerprint": "fp-test",
            "endpoint_host": "integrate.api.nvidia.com",
            "evidence_ref": "provider-admin:developer-program-membership",
            "account_scope": "developer-program",
            "free_hosted_nim_prototyping": True,
        }
        return {
            "provider_side_zero_cost_confirmed": confirmed,
            "entitlement_observed_at": "2026-08-24T13:50:00Z",
            "provider_side_developer_program_or_free_hosted_nim_entitlement_evidence": provider_evidence,
            "entitlement_evidence_digest": digest(provider_evidence),
            "allowed_models": [model],
        }

    def evidence(
        self,
        provenance: dict,
        fingerprint: str = "fp-test",
        model: str = "nvidia/test-model",
        endpoint: str = "https://integrate.api.nvidia.com/v1/chat/completions",
    ) -> dict:
        return _lane_evidence_from_provenance(
            provenance,
            "nvidia",
            fingerprint,
            model,
            endpoint,
            artifacts=self.artifacts,
        )

    def test_unbound_credential_fails_closed(self) -> None:
        result = self.evidence(self.provenance())
        self.assertFalse(result["ok"])
        self.assertEqual(
            result["reason"],
            "NVIDIA_CREDENTIAL_FREE_ENTITLEMENT_RECEIPT_NOT_BOUND",
        )

    def test_legacy_fingerprint_allowlist_no_longer_grants_entitlement(self) -> None:
        provenance = self.provenance()
        provenance["providers"]["nvidia"]["admitted_credential_fingerprints"] = ["fp-test"]
        self.assertFalse(self.evidence(provenance)["ok"])

    def test_different_credential_entitlement_does_not_authorize(self) -> None:
        other = self.entitlement(
            evidence={
                "provider": "NVIDIA",
                "credential_fingerprint": "fp-other",
                "endpoint_host": "integrate.api.nvidia.com",
                "evidence_ref": "provider-admin:developer-program-membership",
                "account_scope": "developer-program",
                "free_hosted_nim_prototyping": True,
            }
        )
        provenance = self.provenance({"fp-other": other})
        self.assertFalse(self.evidence(provenance, "fp-test")["ok"])

    def test_transplanted_provider_evidence_for_other_fingerprint_fails(self) -> None:
        provider_evidence = {
            "provider": "NVIDIA",
            "credential_fingerprint": "fp-other",
            "endpoint_host": "integrate.api.nvidia.com",
            "account_scope": "developer-program",
            "free_hosted_nim_prototyping": True,
        }
        provenance = self.provenance(
            {"fp-test": self.entitlement(evidence=provider_evidence)}
        )
        self.assertFalse(
            self.evidence(provenance, "fp-test")["ok"],
            "provider-side entitlement evidence for a different credential fingerprint must not be transplantable under another outer entitlement key",
        )

    def test_nested_provider_and_endpoint_identity_must_match(self) -> None:
        mismatches = (
            {
                "provider": "OTHER",
                "credential_fingerprint": "fp-test",
                "endpoint_host": "integrate.api.nvidia.com",
                "account_scope": "developer-program",
                "free_hosted_nim_prototyping": True,
            },
            {
                "provider": "NVIDIA",
                "credential_fingerprint": "fp-test",
                "endpoint_host": "example.invalid",
                "account_scope": "developer-program",
                "free_hosted_nim_prototyping": True,
            },
        )
        for provider_evidence in mismatches:
            with self.subTest(provider_evidence=provider_evidence):
                provenance = self.provenance(
                    {"fp-test": self.entitlement(evidence=provider_evidence)}
                )
                self.assertFalse(self.evidence(provenance, "fp-test")["ok"])

    def test_exact_credential_and_model_entitlement_authorizes(self) -> None:
        provenance = self.provenance({"fp-test": self.entitlement()})
        result = self.evidence(provenance)
        self.assertTrue(result["ok"])
        self.assertEqual(result["assertion"], "EXACT_NVIDIA_CREDENTIAL_MODEL_FREE_ENTITLEMENT_BOUND")
        receipt = result["credential_entitlement_receipt"]
        self.assertEqual(receipt["schema"], NVIDIA_ENTITLEMENT_SCHEMA)
        self.assertEqual(receipt["credential_fingerprint"], "fp-test")
        self.assertEqual(receipt["provider"], "nvidia")
        self.assertEqual(receipt["endpoint_host"], "integrate.api.nvidia.com")
        self.assertEqual(receipt["model_or_route"], "nvidia/test-model")
        self.assertEqual(
            receipt["entitlement_evidence_digest"],
            self.entitlement()["entitlement_evidence_digest"],
        )

    def test_exact_credential_cannot_expand_to_unlisted_model(self) -> None:
        provenance = self.provenance({"fp-test": self.entitlement(model="nvidia/model-a")})
        self.assertFalse(self.evidence(provenance, model="nvidia/model-b")["ok"])

    def test_missing_or_false_provider_side_confirmation_fails(self) -> None:
        for row in (
            self.entitlement(confirmed=False),
            {k: v for k, v in self.entitlement().items() if k != "provider_side_zero_cost_confirmed"},
        ):
            with self.subTest(row=row):
                self.assertFalse(self.evidence(self.provenance({"fp-test": row}))["ok"])

    def test_missing_evidence_or_observation_fails(self) -> None:
        required = (
            "entitlement_observed_at",
            "provider_side_developer_program_or_free_hosted_nim_entitlement_evidence",
            "entitlement_evidence_digest",
            "allowed_models",
        )
        for field in required:
            row = self.entitlement()
            del row[field]
            with self.subTest(field=field):
                self.assertFalse(self.evidence(self.provenance({"fp-test": row}))["ok"])

    def test_tampered_entitlement_evidence_digest_fails(self) -> None:
        row = self.entitlement()
        row["provider_side_developer_program_or_free_hosted_nim_entitlement_evidence"][
            "account_scope"
        ] = "changed-after-digest"
        self.assertFalse(self.evidence(self.provenance({"fp-test": row}))["ok"])

    def test_wrong_endpoint_still_fails_for_bound_entitlement(self) -> None:
        provenance = self.provenance({"fp-test": self.entitlement()})
        result = self.evidence(provenance, endpoint="https://example.invalid/v1/chat/completions")
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "ENDPOINT_NOT_ZERO_COST_BOUND")


if __name__ == "__main__":
    unittest.main()
