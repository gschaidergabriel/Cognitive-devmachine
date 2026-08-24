from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from free_lane_provenance import _lane_evidence_from_provenance


class NvidiaCredentialBinding871Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.artifacts_ctx = tempfile.TemporaryDirectory()
        self.artifacts = Path(self.artifacts_ctx.name)
        self.base = {
            "providers": {
                "nvidia": {
                    "allowed_endpoint_host": "integrate.api.nvidia.com",
                    "evidence_kind": "EXACT_DEVELOPER_API_CREDENTIAL_PLUS_FREE_HOSTED_NIM_ENDPOINT",
                    "sources": ["https://developer.nvidia.com/nim"],
                    "scope": "NVIDIA-hosted API Catalog/NIM prototyping endpoint only",
                }
            }
        }

    def tearDown(self) -> None:
        self.artifacts_ctx.cleanup()

    def evidence(self, provenance: dict, fingerprint: str = "fp-test") -> dict:
        return _lane_evidence_from_provenance(
            provenance,
            "nvidia",
            fingerprint,
            "nvidia/test-model",
            "https://integrate.api.nvidia.com/v1/chat/completions",
            artifacts=self.artifacts,
        )

    def test_unbound_credential_fails_closed(self) -> None:
        result = self.evidence(self.base)
        self.assertFalse(result["ok"])
        self.assertEqual(
            result["reason"],
            "NVIDIA_CREDENTIAL_DEVELOPER_FREE_ENTITLEMENT_NOT_BOUND",
        )

    def test_empty_allowed_list_fails_closed(self) -> None:
        provenance = {
            "providers": {
                "nvidia": {
                    **self.base["providers"]["nvidia"],
                    "allowed_credential_fingerprints": [],
                }
            }
        }
        self.assertFalse(self.evidence(provenance)["ok"])

    def test_different_allowed_fingerprint_does_not_authorize(self) -> None:
        provenance = {
            "providers": {
                "nvidia": {
                    **self.base["providers"]["nvidia"],
                    "allowed_credential_fingerprints": ["fp-other"],
                }
            }
        }
        self.assertFalse(self.evidence(provenance, "fp-test")["ok"])

    def test_exact_allowed_fingerprint_can_authorize_hosted_nim_lane(self) -> None:
        provenance = {
            "providers": {
                "nvidia": {
                    **self.base["providers"]["nvidia"],
                    "allowed_credential_fingerprints": ["fp-test"],
                    "credential_binding_observation": "provider-side developer-program evidence",
                }
            }
        }
        result = self.evidence(provenance)
        self.assertTrue(result["ok"])
        self.assertEqual(result["credential_fingerprint"], "fp-test")
        self.assertEqual(
            result["assertion"],
            "BOUND_CREDENTIAL_NVIDIA_DEVELOPER_FREE_NIM_PROTOTYPING_ONLY",
        )
        self.assertEqual(
            result["credential_binding_observation"],
            "provider-side developer-program evidence",
        )

    def test_legacy_admitted_field_cannot_silently_authorize(self) -> None:
        provenance = {
            "providers": {
                "nvidia": {
                    **self.base["providers"]["nvidia"],
                    "admitted_credential_fingerprints": ["fp-test"],
                }
            }
        }
        result = self.evidence(provenance)
        self.assertFalse(result["ok"])
        self.assertEqual(
            result["reason"],
            "NVIDIA_CREDENTIAL_DEVELOPER_FREE_ENTITLEMENT_NOT_BOUND",
        )

    def test_wrong_endpoint_still_fails_even_for_bound_credential(self) -> None:
        provenance = {
            "providers": {
                "nvidia": {
                    **self.base["providers"]["nvidia"],
                    "allowed_credential_fingerprints": ["fp-test"],
                }
            }
        }
        result = _lane_evidence_from_provenance(
            provenance,
            "nvidia",
            "fp-test",
            "nvidia/test-model",
            "https://example.invalid/v1/chat/completions",
            artifacts=self.artifacts,
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "ENDPOINT_NOT_ZERO_COST_BOUND")


if __name__ == "__main__":
    unittest.main()
