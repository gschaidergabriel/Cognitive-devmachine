import json
import tempfile
import unittest
from pathlib import Path

import sys
ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import free_lane_provenance as provenance


class NvidiaFreeEntitlement870Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.artifacts = root / "artifacts"
        self.admission = root / "admission.json"
        self.economic = root / "economic.json"
        self.admission.write_text(
            json.dumps(
                {
                    "schema": provenance.ADMISSION_SCHEMA,
                    "authority_epoch": "8.70",
                    "mode": "FREE_ONLY",
                    "providers": {"nvidia": {"admitted": True, "cost_class": "FREE"}},
                }
            ),
            encoding="utf-8",
        )
        self.economic.write_text(
            json.dumps(
                {
                    "schema": provenance.PROVENANCE_SCHEMA,
                    "authority_epoch": "8.70",
                    "mode": "FREE_ONLY",
                    "providers": {
                        "nvidia": {
                            "allowed_endpoint_host": "integrate.api.nvidia.com",
                            "evidence_kind": "NVIDIA_HOSTED_NIM_DEVELOPER_FREE_PROTOTYPING",
                            "source": "provider-docs",
                            "credential_plan_needed": True,
                            "credential_plan_proof": "credential-bound Developer Program/free hosted-NIM entitlement",
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        self.old_admission = provenance.ADMISSION_PATH
        self.old_economic = provenance.PROVENANCE_PATH
        provenance.ADMISSION_PATH = self.admission
        provenance.PROVENANCE_PATH = self.economic
        self.addCleanup(setattr, provenance, "ADMISSION_PATH", self.old_admission)
        self.addCleanup(setattr, provenance, "PROVENANCE_PATH", self.old_economic)

    def test_generic_nvidia_docs_do_not_admit_concrete_credential(self) -> None:
        result = provenance.lane_evidence(
            "nvidia",
            "fp123",
            "meta/model",
            "https://integrate.api.nvidia.com/v1/chat/completions",
            artifacts=self.artifacts,
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "NVIDIA_CREDENTIAL_FREE_ENTITLEMENT_NOT_BOUND")

    def test_typed_provider_free_label_still_cannot_bypass_entitlement_binding(self) -> None:
        result = provenance.current_lane_binding(
            "nvidia",
            "fp123",
            "meta/model",
            "https://integrate.api.nvidia.com/v1/chat/completions",
            artifacts=self.artifacts,
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "NVIDIA_CREDENTIAL_FREE_ENTITLEMENT_NOT_BOUND")


if __name__ == "__main__":
    unittest.main()
