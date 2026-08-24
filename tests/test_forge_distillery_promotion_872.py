from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import promote_forge_distillery_runtime_gate as promotion


class PromotionSourceGuards872(unittest.TestCase):
    def test_wrong_source_sha_is_rejected(self):
        result = {
            "schema": promotion.PASS_SCHEMA,
            "pass": True,
            "status": promotion.PASS_STATUS,
            "source_sha": "1" * 40,
        }
        with self.assertRaises(promotion.PromotionError):
            promotion.validate_gate_result(result, "2" * 40)

    def test_non_pass_receipt_is_rejected(self):
        result = {
            "schema": promotion.PASS_SCHEMA,
            "pass": False,
            "status": "FAIL_RUNTIME_GATE",
            "source_sha": "1" * 40,
        }
        with self.assertRaises(promotion.PromotionError):
            promotion.validate_gate_result(result, "1" * 40)


if __name__ == "__main__":
    unittest.main()
