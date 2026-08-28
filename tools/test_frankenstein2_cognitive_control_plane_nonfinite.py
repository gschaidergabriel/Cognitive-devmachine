#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from frankenstein2_cognitive_control_plane_v1 import CognitiveControlPlane, ControlError


class CognitiveControlPlaneNonFiniteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.td = tempfile.TemporaryDirectory()
        self.db = Path(self.td.name) / "unified.sqlite"
        self.control = CognitiveControlPlane(self.db)

    def tearDown(self) -> None:
        self.td.cleanup()

    def _assert_rejected_without_state_change(self, *, name: str, value: object, expected_error: str) -> None:
        before = self.control.snapshot()
        patch = self.control.build_patch(
            patch_id=f"nonfinite-{name}-{repr(value)}",
            writer="unit-test",
            writer_kind="EXPERIMENT",
            reason="fail closed on non-finite numeric control",
            changes={name: value},
            base=before,
        )
        with self.assertRaisesRegex(ControlError, expected_error):
            self.control.apply_patch(patch)
        after = self.control.snapshot()
        self.assertEqual(after.snapshot_digest, before.snapshot_digest)
        self.assertEqual(after.control_epoch, before.control_epoch)
        self.assertEqual(after.values[name].version, before.values[name].version)
        self.assertEqual(self.control.revision_rows(), ())

    def test_float_controls_reject_nan_and_infinities_atomically(self) -> None:
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value):
                self._assert_rejected_without_state_change(
                    name="grid.workspace_ignition_threshold",
                    value=value,
                    expected_error=r"NON_FINITE_NUMBER:grid\.workspace_ignition_threshold",
                )

    def test_integer_controls_reject_nan_and_infinities_as_typed_control_errors(self) -> None:
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value):
                self._assert_rejected_without_state_change(
                    name="reflection.max_rounds",
                    value=value,
                    expected_error=r"NON_FINITE_NUMBER:reflection\.max_rounds",
                )


if __name__ == "__main__":
    unittest.main()
