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
        self.provider_evidence = {
            "sources": [
                "https://developer.nvidia.com/nim",
                "https://docs.api.nvidia.com/nim/re/docs/api-quickstart",
                "https://build.nvidia.com/explore",
            ],
            "provider_statement": "Developer Program members get free hosted NIM prototyping access.",
            "credential_binding_observation": "Exact non-secret fingerprint came from the admitted Developer API credential inventory.",
            "scope": "NVIDIA-hosted NIM prototyping endpoint only",
        }
        self.base = {
            "providers": {
                "nvidia": {
                    "allowed_endpoint_host": "integrate.api.nvidia.com",
                    "evidence_kind": "EXACT_DEVELOPER_API_CREDENTIAL_PLUS_FREE_HOSTED_NIM_ENDPOINT",
                    "source": "https://docs.api.nvidia.com/nim/re/docs/api-quickstart",
                    "scope": "NVIDIA-hosted API Catalog/NIM prototyping endpoint only",
                    "admitted_credential_fingerprints": ["fp-test"],
                    "credential_entitlement_evidence": {
                        "fp-test": {
                            "entitlement_observed_at": "2026-08-24",
                            "entitlement_observed_at_precision": "day",
                            "provider_side_developer_program_or_free_hosted_nim_entitlement_evidence": self.provider_evidence,
                            "entitlement_evidence_digest": digest(self.provider_evidence),
                        }
                    },
                }
            }
        }

    def tearDown(self) -> None:
        self.artifacts_ctx.cleanup()

    def evidence(
        self,
        provenance: dict,
        fingerprint: str = "fp-test",
        endpoint: str = "https://integrate.api.nvidia.com/v1/chat/completions",
        model: str = "nvidia/test-model",
    ) -> dict:
        return _lane_evidence_from_provenance(
            provenance,
            "nvidia",
            fingerprint,
            model,
            endpoint,
            artifacts=self.artifacts,
        )

    def test_exact_bound_credential_with_digest_evidence_authorizes(self) -> None:
        result = self.evidence(self.base)
        self.assertTrue(result["ok"])
        self.assertEqual(
            result["assertion"],
            "BOUND_CREDENTIAL_NVIDIA_DEVELOPER_FREE_NIM_PROTOTYPING_WITH_DIGESTED_EVIDENCE",
        )
        receipt = result["credential_entitlement_receipt"]
        self.assertEqual(receipt["schema"], NVIDIA_ENTITLEMENT_SCHEMA)
        self.assertEqual(receipt["credential_fingerprint"], "fp-test")
        self.assertEqual(receipt["provider"], "nvidia")
        self.assertEqual(receipt["endpoint_host"], "integrate.api.nvidia.com")
        self.assertEqual(receipt["entitlement_evidence_digest"], digest(self.provider_evidence))
        self.assertEqual(result["model_or_route"], "nvidia/test-model")

    def test_unlisted_credential_fails_closed(self) -> None:
        result = self.evidence(self.base, fingerprint="fp-other")
        self.assertFalse(result["ok"])
        self.assertEqual(
            result["reason"],
            "NVIDIA_CREDENTIAL_FREE_ENTITLEMENT_EVIDENCE_NOT_BOUND",
        )

    def test_fingerprint_allowlist_alone_is_not_entitlement_proof(self) -> None:
        provenance = json.loads(json.dumps(self.base))
        provenance["providers"]["nvidia"]["credential_entitlement_evidence"] = {}
        self.assertFalse(self.evidence(provenance)["ok"])

    def test_entitlement_record_without_allowlist_cannot_self_admit(self) -> None:
        provenance = json.loads(json.dumps(self.base))
        provenance["providers"]["nvidia"]["admitted_credential_fingerprints"] = []
        self.assertFalse(self.evidence(provenance)["ok"])

    def test_other_credential_evidence_cannot_authorize(self) -> None:
        provenance = json.loads(json.dumps(self.base))
        row = provenance["providers"]["nvidia"]["credential_entitlement_evidence"].pop("fp-test")
        provenance["providers"]["nvidia"]["credential_entitlement_evidence"]["fp-other"] = row
        self.assertFalse(self.evidence(provenance)["ok"])

    def test_tampered_provider_evidence_digest_fails_closed(self) -> None:
        provenance = json.loads(json.dumps(self.base))
        evidence = provenance["providers"]["nvidia"]["credential_entitlement_evidence"]["fp-test"][
            "provider_side_developer_program_or_free_hosted_nim_entitlement_evidence"
        ]
        evidence["scope"] = "changed-after-digest"
        self.assertFalse(self.evidence(provenance)["ok"])

    def test_missing_required_entitlement_fields_fail_closed(self) -> None:
        for field in (
            "entitlement_observed_at",
            "entitlement_observed_at_precision",
            "provider_side_developer_program_or_free_hosted_nim_entitlement_evidence",
            "entitlement_evidence_digest",
        ):
            provenance = json.loads(json.dumps(self.base))
            del provenance["providers"]["nvidia"]["credential_entitlement_evidence"]["fp-test"][field]
            with self.subTest(field=field):
                self.assertFalse(self.evidence(provenance)["ok"])

    def test_wrong_endpoint_still_fails_even_for_bound_credential(self) -> None:
        result = self.evidence(
            self.base,
            endpoint="https://example.invalid/v1/chat/completions",
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "ENDPOINT_NOT_ZERO_COST_BOUND")


if __name__ == "__main__":
    unittest.main()
