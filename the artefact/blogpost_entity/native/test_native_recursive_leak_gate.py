from __future__ import annotations

import unittest

from test_native_semantic_gate import NativeSemanticGateTests


class NativeRecursiveLeakGateTests(unittest.TestCase):
    """Regression-only checks for the already-fused recursive persisted-output leak scan."""

    @classmethod
    def setUpClass(cls) -> None:
        NativeSemanticGateTests.setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        NativeSemanticGateTests.tearDownClass()

    def reject(self, payload: dict, reason: str) -> None:
        helper = NativeSemanticGateTests(methodName="test_configured_leak_pattern_rejected")
        entity, source = helper.prepare(payload)
        run = helper.command("run", str(entity), str(source), check=False)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("ERROR:" + reason, run.stderr)
        helper.assert_no_commit(entity, source)

    def test_leak_pattern_rejected_in_continuity_leaf(self) -> None:
        payload = NativeSemanticGateTests.valid_payload()
        payload["continuity"] = "private-table continuity must not persist"
        self.reject(payload, "LEAK_PATTERN_NO_COMMIT")

    def test_leak_pattern_rejected_in_nested_hypothesis_leaf(self) -> None:
        payload = NativeSemanticGateTests.valid_payload()
        payload["hypotheses"] = [{"candidate": {"note": "FORBIDDEN_TOKEN"}}]
        self.reject(payload, "LEAK_PATTERN_NO_COMMIT")
