#!/usr/bin/env python3
"""Regression tests for the semantic eye shadow builder.

These tests lock the live 2026-09-12 blink split: blinzeln() schedules the
sequence, while blinzelAbspielen() owns terminal opacity cleanup.
"""

from __future__ import annotations

import unittest

from build_semantic_shadow_html import rewrite_blink_functions


LIVE_SPLIT_FIXTURE = r'''
function blinzeln(zeitplanNeu = true){
  if(_sonderLaeuft){
    if(zeitplanNeu) blinzelWeiterPlanen(); // Kette haelt, kein zweiter Strang
    return;
  }
  const schritte = [];
  for(let f = 0; f <= 8; f++) schritte.push([f, blinzelDauerSchliessen(), f < 7 ? "halb1" : "zu"]);
  schritte.push([8, blinzelDauerGeschlossenHalten(), "zu"]);
  for(let f = 9; f <= 11; f++) schritte.push([f, blinzelDauerOeffnen(), "halb2"]);
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
'''


class BlinkScopeRegressionTest(unittest.TestCase):
    def test_rewrites_scheduler_guard_and_player_terminal_cleanup(self) -> None:
        out, meta = rewrite_blink_functions(LIVE_SPLIT_FIXTURE)
        self.assertNotIn("if(_sonderLaeuft)", out)
        self.assertNotIn('$("augen-blink").style.opacity = "0";', out)
        self.assertIn('$("augen-blink").src = BLINK_BILDER[0];', out)
        self.assertIn('$("augen-blink").style.opacity = "1";', out)
        self.assertTrue(meta["blink_scheduler_rewritten"])
        self.assertTrue(meta["blink_player_rewritten"])
        self.assertEqual(meta["terminal_cleanup_scope"], "blinzelAbspielen")

    def test_fails_closed_if_terminal_cleanup_moves_again(self) -> None:
        drifted = LIVE_SPLIT_FIXTURE.replace(
            '$("augen-blink").style.opacity = "0";',
            'hideBlinkLayer();',
        )
        with self.assertRaisesRegex(RuntimeError, "blink terminal opacity"):
            rewrite_blink_functions(drifted)


if __name__ == "__main__":
    unittest.main()
