#!/usr/bin/env python3
"""Deterministic regression for the Supervisor-8.78 raw-generation backpressure patch.

This test is source-only. It performs no provider/network calls and grants no runtime,
HCU, J-Space, training, or whole-product credit.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


PATCHER = Path(__file__).with_name("apply_go878_raw_generation_backpressure.py")
spec = importlib.util.spec_from_file_location("go878_backpressure", PATCHER)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


BASE = """#!/usr/bin/env bash
set -Eeuo pipefail
start_6000(){
  echo start
}
while true; do
  reconcile_6000_admission
  start_6000
  refresh_root_results
done
"""


class RawGenerationBackpressurePatchTests(unittest.TestCase):
    def test_patch_inserts_fail_closed_gate_and_control_loop(self) -> None:
        out = mod.patch(BASE)
        self.assertEqual(out.count("CLAY_SWARM_RAW_GENERATION_BACKPRESSURE/v1"), 1)
        self.assertIn("raw_generation_allowed(){", out)
        self.assertIn("'action':'PAUSE_RAW_GENERATION_FAIL_CLOSED'", out)
        self.assertIn("pressure=ready+implementation+pending", out)
        self.assertIn("allowed=pressure < threshold", out)
        self.assertIn(
            "reconcile_6000_admission\n  if raw_generation_allowed; then\n    start_6000\n  else\n    stop_6000\n  fi\n  refresh_root_results",
            out,
        )

    def test_second_application_fails_closed(self) -> None:
        once = mod.patch(BASE)
        with self.assertRaisesRegex(SystemExit, "RAW_GENERATION_BACKPRESSURE_ALREADY_PRESENT"):
            mod.patch(once)

    def test_ambiguous_insert_marker_fails_closed(self) -> None:
        ambiguous = BASE.replace("while true; do", "start_6000(){\n}\nwhile true; do")
        with self.assertRaisesRegex(SystemExit, "PATCH_MARKER_INSERT_GATE_COUNT_2"):
            mod.patch(ambiguous)

    def test_ambiguous_control_loop_marker_fails_closed(self) -> None:
        duplicated = BASE + "\n  reconcile_6000_admission\n  start_6000\n  refresh_root_results\n"
        with self.assertRaisesRegex(SystemExit, "PATCH_MARKER_CONTROL_LOOP_GATE_COUNT_2"):
            mod.patch(duplicated)


if __name__ == "__main__":
    unittest.main()
