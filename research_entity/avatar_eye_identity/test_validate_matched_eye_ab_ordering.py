#!/usr/bin/env python3
"""Regression fence for matched-eye virtual-time ordering.

The real-host failure on 2026-09-12 showed that a finite virtual-time budget
applied before runtime readiness can freeze the shadow before readyState reaches
complete. Keep virtual-time freezing strictly downstream of readiness and
special-expression activation.
"""
from pathlib import Path
import unittest


class MatchedEyeVirtualTimeOrderingTest(unittest.TestCase):
    def test_virtual_time_is_not_budgeted_before_readiness(self) -> None:
        source = (Path(__file__).with_name("validate_matched_eye_ab.py")).read_text()
        self.assertNotIn('"policy": "advance"', source)

        ready = source.index("ready = False")
        special = source.index("sonderausdruckZeigen", ready)
        active = source.index('cdp.eval("_sonderLaeuft===true")', special)
        pause = source.index('"policy": "pause"', active)

        self.assertLess(ready, special)
        self.assertLess(special, active)
        self.assertLess(active, pause)

    def test_acceptance_thresholds_remain_present(self) -> None:
        source = (Path(__file__).with_name("validate_matched_eye_ab.py")).read_text()
        for marker in (
            '"virtual_time_frozen_stable"',
            '"eye_delta_present"',
            '"eye_delta_fraction_below_2pct"',
            '"eye_delta_fraction_above_noise"',
            '"edge_energy_ratio_below_1_35"',
            '"canonical_route_retained"',
            '"live_source_unchanged"',
        ):
            self.assertIn(marker, source)


if __name__ == "__main__":
    unittest.main()
