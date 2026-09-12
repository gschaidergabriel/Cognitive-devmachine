#!/usr/bin/env python3
from pathlib import Path
import unittest


class QuiescedMatchedEyeGateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.here = Path(__file__).resolve().parent
        self.src = (self.here / "validate_matched_eye_quiesced_ab.py").read_text()
        self.base = (self.here / "validate_matched_eye_ab.py").read_text()

    def test_quiesces_every_current_scheduler_plane(self) -> None:
        for marker in (
            'nativeRAF', 'nativeCAF', 'nativeST', 'nativeCT', 'nativeSI', 'nativeCI',
            'window.requestAnimationFrame = ()=>0',
            'window.setTimeout = ()=>0', 'window.setInterval = ()=>0',
            'for (let i=1; i<=rafHigh; i++)',
            'for (let i=1; i<=timerHigh; i++)',
            'document.getAnimations', "querySelectorAll('video,audio')",
            'animation-play-state:paused', 'transition:none', 'window.stop()',
            'Emulation.setVirtualTimePolicy',
        ):
            self.assertIn(marker, self.src)

    def test_original_quality_thresholds_are_unchanged(self) -> None:
        for marker in (
            'stability["diff_pixels"] == 0',
            'ab["diff_pixels"] > 100',
            'ab["diff_fraction_full_canvas"] < 0.02',
            'ab["diff_fraction_full_canvas"] > 0.001',
            'ratio < 1.35',
            'geometry["src"].endswith("/augen_blink/blink_000.png")',
            'sha256_file(live) == got_live',
        ):
            self.assertIn(marker, self.base)
        # Wrapper changes the freeze mechanism and evidence schema only.
        self.assertNotIn('diff_fraction_full_canvas', self.src)
        self.assertNotIn('ratio <', self.src)

    def test_new_schema_is_explicit(self) -> None:
        self.assertIn('GO_AVATAR_EYE_MATCHED_QUIESCED_AB/v3', self.src)
        self.assertIn('FULL_RUNTIME_QUIESCENCE', self.src)
        self.assertIn('"quiesce": quiesce_state', self.src)


if __name__ == "__main__":
    unittest.main()
