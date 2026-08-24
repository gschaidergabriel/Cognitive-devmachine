from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "trigger1-v2-local-fastpath-selfhosted.yml"


class Trigger1LeaseRuntimeReceiptBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = WORKFLOW.read_text(encoding="utf-8")
        cls.persist = cls.text.split(
            "      - name: Persist sanitized exact-source result\n", 1
        )[1].split(
            "      - name: Finalize canonical unusual-experiment lease result\n", 1
        )[0]
        cls.finalize = cls.text.split(
            "      - name: Finalize canonical unusual-experiment lease result\n", 1
        )[1]

    def test_runtime_receipt_binds_admitted_atomic_lease(self) -> None:
        self.assertIn("'schema':'CLAY_TRIGGER1_V2_SELFHOSTED_RUNTIME_RECEIPT/v1'", self.persist)
        self.assertIn("'atomic_lease':{", self.persist)
        for env_name in (
            "TRIGGER1_TRIGGER_KEY",
            "TRIGGER1_CLAIM_PATH",
            "TRIGGER1_CLAIM_SHA256",
            "TRIGGER1_CLAIMANT_ORGAN",
            "TRIGGER1_EXPERIMENT_NAME",
        ):
            self.assertIn(f"os.environ['{env_name}']", self.persist)

    def test_result_hash_binds_runtime_receipt_bytes_when_present(self) -> None:
        self.assertIn("runtime_receipt_present=runtime_receipt_path.is_file()", self.finalize)
        self.assertIn("runtime_receipt_sha256=hashlib.sha256(raw).hexdigest()", self.finalize)
        self.assertIn("'runtime_receipt_present_in_checkout':runtime_receipt_present", self.finalize)
        self.assertIn("'runtime_receipt_sha256':runtime_receipt_sha256", self.finalize)

    def test_result_rejects_runtime_receipt_lease_mismatch(self) -> None:
        self.assertIn("expected_lease={", self.finalize)
        self.assertIn("receipt.get('atomic_lease') != expected_lease", self.finalize)
        self.assertIn("RUNTIME_RECEIPT_ATOMIC_LEASE_MISMATCH", self.finalize)

    def test_missing_receipt_is_explicit_not_silently_hashed(self) -> None:
        self.assertIn("runtime_receipt_sha256=None", self.finalize)
        self.assertIn("if runtime_receipt_present:", self.finalize)
        self.assertLess(
            self.finalize.index("if runtime_receipt_present:"),
            self.finalize.index("runtime_receipt_sha256=hashlib.sha256(raw).hexdigest()"),
        )


if __name__ == "__main__":
    unittest.main()
