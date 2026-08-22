from __future__ import annotations

import unittest

from test_native_semantic_gate import NativeSemanticGateTests


class PersistedOutputLeakTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        NativeSemanticGateTests.setUpClass()
        cls.helper = NativeSemanticGateTests(methodName="test_configured_leak_pattern_rejected")

    @classmethod
    def tearDownClass(cls) -> None:
        NativeSemanticGateTests.tearDownClass()

    def reject(self, payload: dict, reason: str = "LEAK_PATTERN_NO_COMMIT") -> None:
        self.helper.reject(payload, reason)

    def test_continuity_string_leaf_is_scanned(self) -> None:
        payload = self.helper.valid_payload()
        payload["continuity"] = "retain FORBIDDEN_TOKEN here"
        self.reject(payload)

    def test_hypothesis_nested_string_leaf_is_scanned(self) -> None:
        payload = self.helper.valid_payload()
        payload["hypotheses"] = [{"candidate": {"text": "private-table must stay hidden"}}]
        self.reject(payload)

    def test_self_report_nested_string_leaf_is_scanned(self) -> None:
        payload = self.helper.valid_payload()
        payload["self_report"] = {"layers": [{"note": "FORBIDDEN_TOKEN"}]}
        self.reject(payload)

    def test_arbitrary_extra_persisted_string_leaf_is_scanned(self) -> None:
        payload = self.helper.valid_payload()
        payload["future_contract_extension"] = {"nested": ["safe", {"value": "private_table"}]}
        self.reject(payload)


if __name__ == "__main__":
    unittest.main(verbosity=2)
