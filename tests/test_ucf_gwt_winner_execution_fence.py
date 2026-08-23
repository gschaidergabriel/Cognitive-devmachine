import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE_SPEC = importlib.util.spec_from_file_location(
    "ucf_base_tests", ROOT / "tests" / "test_unified_cognitive_fabric_receipt_v1.py"
)
base = importlib.util.module_from_spec(BASE_SPEC)
assert BASE_SPEC.loader is not None
BASE_SPEC.loader.exec_module(base)


class GwtWinnerExecutionFenceTests(unittest.TestCase):
    def test_executed_inference_without_gwt_winner_fails_closed(self):
        receipt = base.valid_receipt()
        receipt["workspace"]["gwt_winners"] = []
        base.redigest(receipt)

        with self.assertRaisesRegex(
            base.ucf.ReceiptError,
            "EXECUTED_INFERENCE_REQUIRES_GWT_WINNER",
        ):
            base.ucf.validate(receipt)

    def test_nonexecuted_blocked_path_may_have_no_gwt_winner(self):
        receipt = base.blocked_nonfree(base.valid_receipt())
        receipt["workspace"]["gwt_winners"] = []
        base.redigest(receipt)

        self.assertTrue(base.ucf.validate(receipt)["ok"])


if __name__ == "__main__":
    unittest.main()
