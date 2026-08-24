from __future__ import annotations

from pathlib import Path
import unittest


WORKFLOW = Path('.github/workflows/trigger1-v2-local-fastpath-selfhosted.yml')
FUSED = 'CLAY_TRIGGER1_LOCAL_QWEN06_INTERMEDIATE_CONTRASTIVE/v1'
SUPERSEDED = 'CLAY_TRIGGER1_LOCAL_QWEN06_MIDLAYER_CAUSAL_EXPERIMENT/v1'


class Trigger1LeaseReceiptBindingWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = WORKFLOW.read_text(encoding='utf-8')

    def test_blocked_fallbacks_use_effective_fused_experiment_schema(self) -> None:
        self.assertIn(FUSED, self.text)
        self.assertNotIn(SUPERSEDED, self.text)

    def test_runtime_receipt_persists_admitted_atomic_lease_identity(self) -> None:
        required = [
            "'atomic_lease':{",
            "'trigger_key':os.environ.get('TRIGGER1_TRIGGER_KEY')",
            "'claim_path':os.environ.get('TRIGGER1_CLAIM_PATH')",
            "'claim_sha256':os.environ.get('TRIGGER1_CLAIM_SHA256')",
            "'claimant_organ':os.environ.get('TRIGGER1_CLAIMANT_ORGAN')",
            "'experiment_name':os.environ.get('TRIGGER1_EXPERIMENT_NAME')",
        ]
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, self.text)

    def test_result_sidecar_hash_binds_runtime_receipt_bytes(self) -> None:
        required = [
            "runtime_receipt_sha256=hashlib.sha256(receipt_path.read_bytes()).hexdigest() if runtime_receipt_present else None",
            "'runtime_receipt_present_in_checkout':runtime_receipt_present",
            "'runtime_receipt_sha256':runtime_receipt_sha256",
            "'runtime_receipt_lease_matches_claim':runtime_receipt_lease_matches",
        ]
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, self.text)

    def test_pass_fails_closed_when_receipt_lease_binding_is_missing_or_mismatched(self) -> None:
        self.assertIn("if classification == 'PASS' and not runtime_receipt_lease_matches:", self.text)
        self.assertIn("classification='BLOCKED'", self.text)


if __name__ == '__main__':
    unittest.main()
