#!/usr/bin/env python3
from __future__ import annotations

import json
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
PART = HERE / "mini_entity_part03.inc"
PRESET = HERE.parent / "presets" / "zero_blog_state_box.json"


class NativeStateBoxBinaryNeutralityTests(unittest.TestCase):
    def test_replaceable_zero_blog_display_language_is_not_native_source(self) -> None:
        source = PART.read_text(encoding="utf-8")
        forbidden = (
            "SYSTEM STATE",
            "MODEL SELF-REPORT",
            "AUSWERTUNG",
            "kanonische Messfelder sind UNKNOWN",
            "Systemwerte und Modell-Selbstbericht bleiben getrennte Evidenzspuren",
        )
        for text in forbidden:
            self.assertNotIn(text, source)

    def test_default_preset_owns_headings_and_interpretation_text(self) -> None:
        cfg = json.loads(PRESET.read_text(encoding="utf-8"))
        self.assertEqual(cfg["render"]["sections"], ["SYSTEM STATE", "MODEL SELF-REPORT", "AUSWERTUNG"])
        templates = cfg["interpretation"]["templates"]
        self.assertIn("{count}", templates["unknown"])
        self.assertTrue(templates["no_comparison"])

    def test_native_renderer_reads_replaceable_config(self) -> None:
        source = PART.read_text(encoding="utf-8")
        self.assertIn('jget(render,"sections")', source)
        self.assertIn('jstr(templates,"unknown",NULL)', source)
        self.assertIn('jstr(templates,"no_comparison",NULL)', source)
        self.assertIn('buf_add_count_template', source)


if __name__ == "__main__":
    unittest.main()
