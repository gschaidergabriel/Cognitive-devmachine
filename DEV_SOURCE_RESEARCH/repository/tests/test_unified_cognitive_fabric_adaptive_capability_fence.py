import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

VALIDATOR_SPEC = importlib.util.spec_from_file_location(
    "ucf_validator", ROOT / "tools" / "validate_unified_cognitive_fabric_receipt_v1.py"
)
ucf = importlib.util.module_from_spec(VALIDATOR_SPEC)
assert VALIDATOR_SPEC.loader is not None
VALIDATOR_SPEC.loader.exec_module(ucf)

BASE_SPEC = importlib.util.spec_from_file_location(
    "ucf_base_tests", ROOT / "tests" / "test_unified_cognitive_fabric_receipt_v1.py"
)
base = importlib.util.module_from_spec(BASE_SPEC)
assert BASE_SPEC.loader is not None
BASE_SPEC.loader.exec_module(base)


class AdaptiveCapabilityFenceTests(unittest.TestCase):
    def adaptive_receipt(self, *, capability_match: bool):
        receipt = base.valid_receipt()
        receipt["inference"].update(
            engine_class="adaptive_backend",
            jspace_mode="PLAIN_COMPATIBILITY",
            local_activation_access=False,
            external_hidden_state_claimed=False,
            adapter_version="adaptive-backend/candidate-v1",
            adapter_capability_match=capability_match,
            provider_observability_claim_supported=True,
        )
        base.redigest(receipt)
        return receipt

    def test_adaptive_backend_capability_mismatch_is_rejected(self):
        receipt = self.adaptive_receipt(capability_match=False)
        with self.assertRaisesRegex(ucf.ReceiptError, "ADAPTER_CAPABILITY_MISMATCH"):
            ucf.validate(receipt)

    def test_adaptive_backend_matching_profile_remains_admitted(self):
        receipt = self.adaptive_receipt(capability_match=True)
        self.assertTrue(ucf.validate(receipt)["ok"])


if __name__ == "__main__":
    unittest.main()
