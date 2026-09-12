#!/usr/bin/env python3
from pathlib import Path
import unittest


class HardFreezeMatchedEyeGateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.src = (Path(__file__).with_name("validate_matched_eye_hardfreeze_ab.py")).read_text()

    def test_instrumentation_precedes_reload_and_freeze_precedes_screenshot(self) -> None:
        add = self.src.index('Page.addScriptToEvaluateOnNewDocument')
        reload_ = self.src.index('Page.reload', add)
        freeze = self.src.index('__goHardFreeze', reload_)
        first_shot_marker = self.src.index('01_frozen_eye_off.png') if '01_frozen_eye_off.png' in self.src else -1
        # The wrapper patches the base validator at runtime, so the screenshot
        # literal stays in the base; verify the patch is anchored before geometry.
        geometry = self.src.index('geometry = json.loads', freeze)
        self.assertLess(add, reload_)
        self.assertLess(reload_, freeze)
        self.assertLess(freeze, geometry)
        self.assertEqual(first_shot_marker, -1)

    def test_all_scheduler_classes_and_animation_plane_are_frozen(self) -> None:
        for marker in (
            'requestAnimationFrame', 'cancelAnimationFrame',
            'setTimeout', 'clearTimeout', 'setInterval', 'clearInterval',
            'document.getAnimations', "querySelectorAll('video,audio')",
            'animation-play-state:paused', 'transition:none',
        ):
            self.assertIn(marker, self.src)

    def test_no_acceptance_threshold_is_weakened(self) -> None:
        base = (Path(__file__).with_name("validate_matched_eye_ab.py")).read_text()
        for marker in (
            'stability["diff_pixels"] == 0',
            'ab["diff_pixels"] > 100',
            'ab["diff_fraction_full_canvas"] < 0.02',
            'ab["diff_fraction_full_canvas"] > 0.001',
            'ratio < 1.35',
        ):
            self.assertIn(marker, base)
        self.assertNotIn('0.02', self.src)
        self.assertNotIn('1.35', self.src)

    def test_evidence_schema_is_new_not_relabelled_v1(self) -> None:
        self.assertIn('GO_AVATAR_EYE_MATCHED_HARDFREEZE_AB/v2', self.src)
        self.assertIn('TRACKED_SCHEDULERS_HARD_FROZEN', self.src)


if __name__ == "__main__":
    unittest.main()
