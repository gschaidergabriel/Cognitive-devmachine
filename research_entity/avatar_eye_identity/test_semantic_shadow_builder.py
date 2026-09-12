#!/usr/bin/env python3
"""Regression tests for canonical-eye semantic-shadow rewrites.

These tests pin the two defects found on the real 2026-09-12 subject:

1. terminal opacity belongs to blinzelAbspielen(), not blinzeln();
2. invariants must inspect an extracted function body rather than regex-scanning
   into later functions that may legitimately contain _sonderLaeuft.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "eye_shadow_builder", HERE / "build_semantic_shadow_html.py"
)
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


FIXTURE = r'''
function blinzeln(zeitplanNeu = true){
  if(_sonderLaeuft){
    if(zeitplanNeu) blinzelWeiterPlanen();
    return;
  }
  const schritte = [];
  for(let f = 0; f <= 8; f++) schritte.push([f, 10, "halb1"]);
  schritte.push([8, 15, "zu"]);
  for(let f = 9; f <= 11; f++) schritte.push([f, 20, "halb2"]);
  blinzelAbspielen(schritte, 0, zeitplanNeu);
}
function blinzelAbspielen(schritte, idx, zeitplanNeu){
  if(idx >= schritte.length){
    $("augen-blink").style.opacity = "0";
    blinzelPhase = null;
    gesichtNeuZeichnen(false);
    if(zeitplanNeu) blinzelWeiterPlanen();
    return;
  }
  const [frame, dauer, phase] = schritte[idx];
  $("augen-blink").src = BLINK_BILDER[frame];
  $("augen-blink").style.opacity = "1";
  blinzelPhase = phase;
  setTimeout(() => blinzelAbspielen(schritte, idx + 1, zeitplanNeu), dauer);
}
function gazeSchritt(){
  $("pupillen-glow").style.opacity = _sonderLaeuft ? "0" : String(ziel.opazitaet);
}
'''


class SplitBlinkRewriteTests(unittest.TestCase):
    def test_scheduler_guard_removed_but_later_special_state_preserved(self) -> None:
        rewritten, meta = MOD.rewrite_blink_function(FIXTURE)
        _, _, scheduler = MOD.extract_function(
            rewritten, "function blinzeln(zeitplanNeu = true){", "blinzeln"
        )
        _, _, gaze = MOD.extract_function(
            rewritten, "function gazeSchritt(){", "gazeSchritt"
        )
        self.assertNotIn("_sonderLaeuft", scheduler)
        self.assertIn("_sonderLaeuft", gaze)
        self.assertTrue(meta["blink_scheduler_rewritten"])
        self.assertGreater(meta["removed_guard_bytes"], 0)

    def test_player_terminal_state_is_rewritten_in_player_not_scheduler(self) -> None:
        scheduler_rewritten, _ = MOD.rewrite_blink_function(FIXTURE)
        rewritten, meta = MOD.rewrite_blink_player(scheduler_rewritten)
        _, _, scheduler = MOD.extract_function(
            rewritten, "function blinzeln(zeitplanNeu = true){", "blinzeln"
        )
        _, _, player = MOD.extract_function(
            rewritten,
            "function blinzelAbspielen(schritte, idx, zeitplanNeu){",
            "blinzelAbspielen",
        )
        self.assertNotIn('style.opacity = "0"', scheduler)
        self.assertNotIn('style.opacity = "0"', player)
        self.assertIn('$("augen-blink").src = BLINK_BILDER[0];', player)
        self.assertIn('$("augen-blink").style.opacity = "1";', player)
        self.assertTrue(meta["blink_player_end_rewritten"])
        self.assertTrue(meta["blink_player_open_plate_restored"])

    def test_extract_function_stops_at_balanced_closing_brace(self) -> None:
        _, _, scheduler = MOD.extract_function(
            FIXTURE, "function blinzeln(zeitplanNeu = true){", "blinzeln"
        )
        self.assertIn("blinzelAbspielen(schritte, 0, zeitplanNeu);", scheduler)
        self.assertNotIn("function blinzelAbspielen", scheduler)
        self.assertNotIn("function gazeSchritt", scheduler)

    def test_player_rewrite_fails_closed_on_unexpected_subject(self) -> None:
        malformed = FIXTURE.replace(
            '$("augen-blink").style.opacity = "0";',
            '$("augen-blink").hidden = true;',
            1,
        )
        with self.assertRaisesRegex(RuntimeError, "expected one occurrence"):
            MOD.rewrite_blink_player(malformed)

    def test_double_terminal_opacity_fails_closed(self) -> None:
        doubled = FIXTURE.replace(
            '$("augen-blink").style.opacity = "0";',
            '$("augen-blink").style.opacity = "0";\n'
            '    $("augen-blink").style.opacity = "0";',
            1,
        )
        with self.assertRaisesRegex(RuntimeError, "got 2"):
            MOD.rewrite_blink_player(doubled)


if __name__ == "__main__":
    unittest.main()
